"""Bot motoru — YENİ balık sistemi (zamanlama penceresi + ödül çarkı).

Bir tur:
  1) Space ile olta atılır.
  2) Karakterin kafasında balık işareti çıkınca (BiteWatcher) Space'e basılır.
  3) Zamanlama penceresi: siyah balık kutucuğun tam ortasına (mor nokta) varırken Space'e basılır
     (TimingController: balığın hızı ölçülür, tuş gecikmesi her turda öğrenilir).
  4) Ödül çarkı kendiliğinden döner; pencere kapanınca baştan başlanır.
Her bekleme anında ekranda captcha var mı diye bakılır (core/captcha.py).
Birden fazla client aynı anda çalışabilir: oyun tuşu yalnızca öndeki pencereden aldığı için tuşa basılan
kısa anlar ve zamanlama penceresi CONTROL_LOCK ile sırayla yapılır.
"""
from __future__ import annotations

from .paths import DATA

import contextlib
import random
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from .captcha import CaptchaSolver
from .config import Config
from .i18n import T, ascii_name, lang
from .reward import RewardReader, add_total, item_name
from .streak import StreakJudge, read_glyph, same, stable
from .timing import BarReader, BiteWatcher, TimingController, _txt, draw_bar, draw_bite, precise_sleep
from .winapi import (CONTROL_LOCK, GameWindow, WindowCapture, beep, client_rect_screen, focus_window,
                     get_cursor, make_input, mouse_click, mouse_down, set_cursor, window_alive)


@dataclass
class BotStats:
    casts: int = 0
    success: int = 0          # isabet: balık kutucuğun içinde durdu
    fail: int = 0             # ıska
    timeouts: int = 0         # balık işareti gelmedi
    false_alarms: int = 0     # işarete basıldı ama zamanlama penceresi açılmadı
    captchas: int = 0
    rewards: int = 0          # dönen ödül çarkı sayısı
    verified: int = 0         # sonucu oyunun "Seri" sayacıyla doğrulanan tur
    corrected: int = 0        # seri sayacına göre düzeltilen tur
    no_press: int = 0         # Space'e basılamadan kapanan pencere
    captcha_seen: int = 0     # görülen captcha
    captcha_manual: int = 0   # elle çözülen
    captcha_fail: int = 0     # otomatik çözülemeyen
    last_err: float | None = None    # son turda balığın durduğu yerin hedefe uzaklığı (px)
    abs_err_sum: float = 0.0
    err_n: int = 0
    latency_ms: float = 0.0
    catches: dict = field(default_factory=dict)
    items: dict = field(default_factory=dict)       # eşya -> toplam adet (ödül çarkından)
    item_wins: dict = field(default_factory=dict)   # eşya -> kaç kez çıktı
    started_at: float = field(default_factory=time.time)

    @property
    def rounds(self) -> int:
        return self.success + self.fail

    @property
    def rate(self) -> float:
        return (self.success / self.rounds * 100) if self.rounds else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["rounds"] = self.rounds
        d["rate"] = self.rate
        d["avg_err"] = (self.abs_err_sum / self.err_n) if self.err_n else None
        d["uptime"] = time.time() - self.started_at
        return d


class BotWorker(threading.Thread):
    def __init__(self, game: GameWindow, cfg: Config,
                 on_log: Callable[[int, str], None] | None = None,
                 on_state: Callable[[int, str], None] | None = None,
                 on_stats: Callable[[int, dict], None] | None = None,
                 license_check: Callable[[], bool] | None = None,
                 on_frame: Callable[[int, object], None] | None = None,
                 want_frames: Callable[[int], bool] | None = None,
                 on_round: Callable[[int, dict], None] | None = None,
                 on_scan: Callable[[int, str], None] | None = None):
        super().__init__(daemon=True, name=f"bot-{game.pid}")
        self.game = game
        self.cfg = cfg
        self.on_log = on_log or (lambda pid, m: None)
        self.on_state = on_state or (lambda pid, s: None)
        self.on_stats = on_stats or (lambda pid, d: None)
        self.on_round = on_round or (lambda pid, d: None)
        self.on_scan = on_scan
        self.on_frame = on_frame
        self.want_frames = want_frames or (lambda pid: False)
        self.license_check = license_check or (lambda: True)
        self.stop_event = threading.Event()
        self.rng = random.Random()
        self.stats = BotStats()
        self.capture = WindowCapture(game.hwnd)
        self._input_method = cfg["input_method"]
        self.input = make_input(self._input_method, game.hwnd)
        self._apply_capture_mode()
        self.captcha = CaptchaSolver(cfg)
        self.bar_reader = BarReader()
        self.bite = BiteWatcher(cfg)
        self.reward = RewardReader()
        self._lat = max(0.0, float(cfg["timing_latency_ms"]) / 1000.0)
        self.stats.latency_ms = self._lat * 1000
        self._has_lock = False
        self._captcha_wait = None
        self._cap_last_frame = None
        self._last_shape = None
        self._t_emit = 0.0
        self._bite_miss = 0
        self._result_note = None
        self._next_break = None
        self.extra_wait = 0.0
        self._scan_file = None
        self._scan_last_emit = 0.0
        self._scan_last_flush = 0.0
        self.streak = StreakJudge()        # "Seri: N" sayacından gerçek sonuç
        self._g_start = None
        self._rid = 0
        self._rounds: dict[int, dict] = {}  # tur no -> arayüze gönderilen tur (sonradan düzeltmek için)
        self._last_stop = None
        self._seri_seen_change = False      # seri sayısı hiç değişti mi (sayaç gerçekten okunuyor mu)
        self._seri_judged = 0
        self._seri_off = False
        self._g_prev_end = None

    def _apply_capture_mode(self) -> None:
        # arka plan (PostMessage) modunda pencereler üst üste olabilir: ekrandan kopyalama yanlış pencereyi
        # okur, her client kendi penceresinden (PrintWindow) yakalanır
        if getattr(self.input, "real_cursor", False):
            self.capture.fast_ok = None if self.capture.fast_ok is False else self.capture.fast_ok
        else:
            self.capture.fast_ok = False

    # ---------------------------------------------------------- ana döngü
    def run(self) -> None:
        self.log(T("Bot başlatıldı."))
        try:
            last_license = time.time()
            while not self.stop_event.is_set():
                if not window_alive(self.game.hwnd):
                    self.log(T("Oyun penceresi kapandı, bot durduruluyor."))
                    break
                if time.time() - last_license > 300:
                    last_license = time.time()
                    if not self.license_check():
                        self.log(T("Üyelik doğrulanamadı, bot durduruluyor."))
                        break
                if self._input_method != self.cfg["input_method"]:     # ayar değişti
                    self._input_method = self.cfg["input_method"]
                    self.input = make_input(self._input_method, self.game.hwnd)
                    self._apply_capture_mode()
                if self._maybe_break():
                    continue
                if self._captcha_wait is not None:
                    self._captcha_wait_loop()
                    continue
                self._cycle_timing()
        except Exception as e:  # noqa: BLE001
            self.state(T("Hata"))
            self.log(T('Hata: {0!r}').format((e)))
            return
        finally:
            try:
                if self._scan_file is not None:
                    self._scan_file.close()
            except Exception:
                pass
        self.state(T("Durdu"))
        self.log(T("Bot durdu."))

    def log(self, msg: str) -> None:
        self.on_log(self.game.pid, msg)
        self.scan(f"▶ {msg}", important=True)

    def state(self, s: str) -> None:
        self.on_state(self.game.pid, s)

    def stop(self) -> None:
        self.stop_event.set()

    def sleep(self, seconds: float) -> bool:
        """Durdurulursa True döner."""
        return self.stop_event.wait(max(0.0, seconds))

    def jitter_ms(self, base_ms: int) -> float:
        return base_ms / 1000 * self.rng.uniform(0.85, 1.3)

    def scan(self, line: str, important: bool = False) -> None:
        """Tarama kaydı: her kare data/tarama/ altına yazılır, arayüzdeki Tarama penceresine
        saniyede ~10 satır gönderilir (önemli olaylar her zaman)."""
        now = time.time()
        stamp = time.strftime("%H:%M:%S", time.localtime(now)) + f".{int(now * 1000) % 1000:03d}"
        text = f"{stamp}  {line}"
        try:
            if self._scan_file is None:
                import os
                from .config import DATA_DIR
                d = os.path.join(DATA_DIR, "tarama")
                os.makedirs(d, exist_ok=True)
                fn = os.path.join(d, time.strftime("tarama_%Y%m%d_", time.localtime(now)) + f"{self.game.pid}.log")
                self._scan_file = open(fn, "a", encoding="utf-8")
            self._scan_file.write(text + "\n")
            if now - self._scan_last_flush > 1.0 or important:
                self._scan_file.flush()
                self._scan_last_flush = now
        except Exception:
            pass
        if self.on_scan is not None and (important or now - self._scan_last_emit >= 0.1):
            self._scan_last_emit = now
            self.on_scan(self.game.pid, text)

    def _maybe_break(self) -> bool:
        """Akıllı mola: belirli aralıklarla birkaç dakika dinlen (insansı davranış)."""
        cfg = self.cfg
        if not cfg["break_enabled"]:
            self._next_break = None
            return False
        now = time.time()
        if self._next_break is None:
            lo, hi = cfg["break_every_min"]
            self._next_break = now + self.rng.uniform(lo, max(lo, hi)) * 60
            return False
        if now < self._next_break:
            return False
        lo, hi = cfg["break_len_min"]
        dur = self.rng.uniform(lo, max(lo, hi)) * 60
        self.state(T("Molada"))
        self.log(T('Akıllı mola: {0:.1f} dakika dinleniliyor.').format((dur / 60)))
        self._next_break = None
        if self._sleep_watch(dur, solve=False) == "captcha":
            self.log(T("Molada captcha penceresi göründü — mola bitirildi."))
        return True

    def _press_cast(self) -> None:
        cfg = self.cfg
        hold = self.rng.uniform(int(cfg["key_hold_min_ms"]), max(int(cfg["key_hold_min_ms"]),
                                                                  int(cfg["key_hold_max_ms"]))) / 1000
        self.input.key(cfg["cast_key"], hold=hold)

    def _reset_capture_region(self):
        if hasattr(self.capture, "region"):
            self.capture.region = None

    @contextlib.contextmanager
    def _control(self, urgent: bool = False):
        """Klavye/fare odağını KISA süreliğine al: aynı anda iki client tuşa basmasın / odak kapmasın."""
        if self._has_lock:
            yield True
            return
        got = False
        while not got and not self.stop_event.is_set():
            got = CONTROL_LOCK.acquire(timeout=0.1, urgent=urgent)
        if not got:
            CONTROL_LOCK.leave()
            yield False
            return
        self._has_lock = True
        try:
            yield True
        finally:
            self._has_lock = False
            CONTROL_LOCK.release()

    def _key_now(self, name: str, hold: float = 0.04) -> None:
        f = getattr(self.input, "key_now", None)
        if f is not None:
            f(name, hold=hold)
        else:
            self.input.key(name, hold=hold)

    def _emit_due(self) -> bool:
        """Canlı görüntüye yeni kare gönderme zamanı mı? (en fazla ~30 kare/sn; çizim boşuna yapılmasın)"""
        return self.on_frame is not None and self.want_frames(self.game.pid) and \
            time.time() - self._t_emit >= 1.0 / max(5, min(120, int(self.cfg["preview_fps"])))

    def _emit_img(self, img, force: bool = False) -> None:
        """Canlı görüntüye hazır çizilmiş bir resim gönder."""
        if self.on_frame is None or img is None or not self.want_frames(self.game.pid):
            return
        if not force and time.time() - self._t_emit < 1.0 / max(5, min(120, int(self.cfg["preview_fps"]))):
            return
        self._t_emit = time.time()
        self.on_frame(self.game.pid, {"img": img, "raw": None, "boxes": []})

    def _cycle_timing(self) -> None:
        cfg = self.cfg
        self._reset_capture_region()
        fr = self.capture.grab()
        if fr is None:
            self.sleep(0.5)
            return
        self._last_shape = fr.shape
        if cfg["captcha_enabled"] and self._gate_any(fr):
            return
        bar = self.bar_reader.find(fr)
        if bar is not None:                        # önceki turun penceresi hâlâ açık (çark dönüyor olabilir)
            self._await_close(bar)
            self.streak.pending = None
            return
        if self.extra_wait > 0 and self._sleep_watch(self.extra_wait):
            return
        # 1) olta
        self.state(T("Olta atılıyor"))
        self.log(T("Olta atılıyor…"))
        with self._control() as ok:
            if not ok:
                return
            self._press_cast()
        self.stats.casts += 1
        t_cast = time.time()
        if self._sleep_watch(float(cfg["bite_settle_s"])):
            return
        # 2) kafadaki balık işareti -> Space
        hit, bar = self._await_bite(t_cast)
        if hit is None and bar is None:
            return
        if hit is not None:
            lo, hi = int(cfg["bite_react_min_ms"]), int(cfg["bite_react_max_ms"])
            if self.sleep(self.rng.uniform(lo, max(lo, hi)) / 1000):
                return
            with self._control(urgent=True) as ok:
                if not ok:
                    return
                self._key_now(cfg["cast_key"], hold=self.rng.uniform(0.04, 0.07))
            how = T("resimle") if hit.how == "resim" else T("değişimle")
            self.log(T("Balık işareti göründü ({0}) — Space'e basıldı.").format((how)))
            self.scan("▶ " + T("işaret {0} {1} kutu {2}").format(how, f"{hit.score:.2f}", hit.box), important=True)
            self.state(T("Zamanlama penceresi bekleniyor"))
            bar = self._await_window(3.0)
            if bar is None:
                self.stats.false_alarms += 1
                self.log(T("Space'e basıldı ama zamanlama penceresi açılmadı (yanlış alarm ya da geç kalındı) — "
                         "olta yeniden atılacak."))
                self.on_stats(self.game.pid, self.stats.to_dict())
                self._sleep_watch(1.0)
                return
            saved = self.bite.confirm(self._last_shape or fr.shape, hit)
            if saved:
                self.log(T('✓ Balık işareti öğrenildi ({0}) — sonraki turlarda resimle aranacak.').format((Path(saved).name)))
        # 3) zamanlama penceresi: balık kutucuğun ortasına gelince Space
        self.state(T("Zamanlama"))
        with self._control(urgent=True) as ok:
            if not ok:
                return
            res = self._play_timing(bar)
        self._reset_capture_region()
        if res is None:
            return
        g_start = self._g_start
        if g_start is not None and self._g_prev_end is not None and not same(g_start, self._g_prev_end):
            self._seri_seen_change = True
        for rid, ok in self.streak.window_start(g_start):          # önceki turun sonucu şimdi kesinleşti
            self._fix_round(rid, ok, later=True)
        rnd = self._timing_result(*res)
        # 4) ödül çarkı kendiliğinden döner: durunca kazanılan eşya ve adedi okunur; pencere kapanınca baştan
        rew, g_end = self._await_close(bar, count=True)
        self._g_prev_end = g_end
        if g_start is not None and g_end is not None:
            self._seri_judged += 1
            if not same(g_start, g_end):
                self._seri_seen_change = True
        self._seri_sanity()
        done = self.streak.window_end(rnd["rid"], g_start, g_end)
        v = next((ok for r_, ok in done if r_ == rnd["rid"]), None)
        self.scan(T("seri sayacı: başta {0}, sonda {1} → {2}").format(
            T("okundu") if g_start is not None else T("okunamadı"),
            T("okundu") if g_end is not None else T("okunamadı"),
            T("isabet") if v else (T("ıska") if v is False else T("henüz belli değil (botun ölçümü geçerli)"))))
        for rid, ok in done:
            self._fix_round(rid, ok, later=rid != rnd["rid"])
        self._record_reward(rew, rnd)
        lo, hi = int(cfg["cooldown_min_ms"]), int(cfg["cooldown_max_ms"])
        self._sleep_watch(self.rng.uniform(lo, max(lo, hi)) / 1000)

    def _await_bite(self, t_cast: float):
        """(işaret, None) • (None, çubuk) pencere işaretsiz açıldıysa • (None, None) zaman aşımı/durdu/captcha."""
        cfg = self.cfg
        self.state(T("Balık bekleniyor"))
        self.bite.reset()
        deadline = t_cast + float(cfg["bite_timeout_s"])
        next_cap = time.time() + 0.7
        next_full = 0.0
        try:
            while time.time() < deadline and not self.stop_event.is_set():
                t0 = time.time()
                full = t0 >= next_full
                if full:                       # ~0,4 sn'de bir tüm pencere: zamanlama penceresi / captcha kontrolü
                    self._reset_capture_region()
                fr = self.capture.grab()
                if fr is None:
                    if self.sleep(0.1):
                        break
                    continue
                self._last_shape = fr.shape
                if full:
                    next_full = t0 + 0.4
                    b = self.bar_reader.find(fr)
                    if b is not None:
                        self.log(T("Zamanlama penceresi açık (işaret görülmeden) — oynanıyor."))
                        return None, b
                    if cfg["captcha_enabled"] and t0 >= next_cap:
                        next_cap = t0 + 0.7
                        if self.captcha.quick(fr) and self._gate_any(fr):
                            return None, None
                    # arada sadece kafa bölgesi yakalanır (çok daha hızlı)
                    if hasattr(self.capture, "set_region"):
                        x0, y0, x1, y1 = self.bite.region(fr.shape)
                        pad = 64
                        self.capture.set_region(max(0, x0 - pad), max(0, y0 - pad), x1 - x0 + 2 * pad,
                                                y1 - y0 + 2 * pad)
                hit = self.bite.check(fr)
                if self._emit_due() or hit is not None:
                    area = T("secili alan") if self.bite.user_area(fr.shape) else T("otomatik alan")
                    note = (T("balik bekleniyor {s} sn").format(s=f"{t0 - t_cast:4.1f}") + f"  [{area}, " +
                            (T("{n} isaret resmi").format(n=len(self.bite.templates)) + "]" if self.bite.templates
                             else T("isaret resmi yok: degisimle") + "]"))
                    self._emit_img(draw_bite(fr, self.bite._reg, hit, note, anchor=self.bite._anchor,
                                             seen=self.bite.seen, foreign=self.bite.foreign), force=hit is not None)
                if hit is not None:
                    self._bite_miss = 0
                    return hit, None
                rest = 1.0 / max(5, min(120, int(cfg["scan_fps"]))) - (time.time() - t0)
                if rest > 0 and self.sleep(rest):
                    break
        finally:
            self._reset_capture_region()
        if not self.stop_event.is_set():
            self.stats.timeouts += 1
            self._bite_miss = getattr(self, "_bite_miss", 0) + 1
            if self._bite_miss >= 2 and cfg["bite_pos"] is not None:
                cfg.set("bite_pos", None)          # kamera değişmiş olabilir: kafayı yine geniş alanda ara
                self.log(T("Arka arkaya işaret görülmedi — kafa konumu unutuldu, geniş alanda aranacak."))
            self.on_stats(self.game.pid, self.stats.to_dict())
            self.log(T('{0:.0f} sn içinde balık işareti görülmedi — olta yeniden atılacak. (İşaret hiç görülmüyorsa: Ayarlar > Yeni balık sistemi > İşaret testi)').format((float(cfg['bite_timeout_s']))))
        return None, None

    def _await_window(self, timeout: float):
        end = time.time() + timeout
        while time.time() < end and not self.stop_event.is_set():
            self._reset_capture_region()
            fr = self.capture.grab()
            if fr is not None:
                self._last_shape = fr.shape
                b = self.bar_reader.find(fr)
                if b is not None:
                    return b
            if self.sleep(0.04):
                break
        return None

    def _play_timing(self, bar):
        """Balığı izle, kutucuğun ortasına varacağı anda (gecikme kadar önce) Space'e bas.
        (isabet, merkeze_hata_px, ölçülen_gecikme, açıklama) döner; durdurulduysa None."""
        cfg = self.cfg
        ctrl = TimingController(self._lat)
        x, y, w, h = bar
        f = getattr(self.input, "focus", None)
        if f is not None:
            try:
                f()                                # basış anında odak işlemiyle vakit kaybetmemek için şimdi
            except Exception:
                pass
        if hasattr(self.capture, "set_region"):
            # çubuk + kutucuğun çubuk dışındaki lacivert çerçevesi + başlıktaki "Seri" sayacı
            top = int(1.35 * h)
            pad = max(10, int(0.35 * h))
            self.capture.set_region(max(0, x - 6), max(0, y - top), w + 12, h + top + pad)
        self._g_start = None
        self._last_stop = None
        glyphs: list = []
        t_start = time.time()
        press = None
        after: list[tuple[float, float]] = []
        lost = 0
        last_rd = None
        last_fr = None
        while not self.stop_event.is_set():
            ta = time.time()
            fr = self.capture.grab()
            tb = time.time()
            if fr is None:
                lost += 1
                if lost > 40:
                    break
                time.sleep(0.005)
                continue
            rd = self.bar_reader.read(fr, bar)
            if rd.fish is None and rd.box is None:
                lost += 1
                if lost >= 12 and (press is not None or self.bar_reader.find(fr) is None):
                    break                          # pencere kapandı
                continue
            lost = 0
            last_rd = rd
            tm = (ta + tb) / 2                     # karenin alındığı an
            if press is None and len(glyphs) < 4:  # pencere başındaki seri sayısı
                try:
                    glyphs.append(read_glyph(fr, bar))
                except Exception:
                    glyphs.append(None)
                if len(glyphs) == 4:
                    self._g_start = stable(glyphs)
            if press is None:
                ctrl.update(tm, rd)
                wait = ctrl.decide(time.time())
                if wait is None and time.time() - t_start > float(cfg["timing_max_s"]):
                    bx = ctrl.box
                    if bx is not None and rd.fish is not None and bx[0] <= rd.fish_x <= bx[1]:
                        wait = 0.0                 # çok uzadı: balık kutucuktayken bas
                if wait is not None:
                    if wait > 0:
                        precise_sleep(wait)
                    t_press = time.time()
                    self._key_now(cfg["cast_key"], hold=0.04)
                    press = (t_press, ctrl.predict(t_press + ctrl.lat), wait)
                    vel = ctrl.tr.velocity()
                    bx = ctrl.box
                    self._speed = abs(vel[0]) if vel else None
                    self.scan(T("zamanlama: kutu {0}-{1} ({2}{3})  balık x={4} hız {5} px/sn  → {6} ms sonra "
                                "basıldı (gecikme payı {7} ms, {8} örnek)").format(
                        f"{bx[0]:.0f}", f"{bx[1]:.0f}", ctrl.how,
                        (", " + T("{n} kez yer değiştirdi").format(n=ctrl.moves)) if ctrl.moves else "",
                        f"{rd.fish_x:.0f}", f"{vel[0] if vel else 0:+.0f}", f"{1000 * wait:.0f}",
                        f"{1000 * ctrl.lat:.0f}", len(ctrl.tr.s)), important=True)
            else:
                if rd.fish is not None:
                    after.append((tm, rd.fish_x))
                if tm - press[0] > 0.6:
                    break
            if self._emit_due():
                sx_ = ctrl.stop_x(after) if press else None
                self._emit_img(draw_bar(fr, rd, ctrl.lat * 1000,
                                        pred_x=None if press else ctrl.predict(time.time() + ctrl.lat),
                                        press_x=press[1] if press else None,
                                        note=T("BASILDI") if press else T(ctrl.why), box=ctrl.box, stop_x=sx_))
            last_fr = fr
        if self.stop_event.is_set():
            return None
        if self._g_start is None and glyphs:
            self._g_start = stable(glyphs)
        if press is None:
            self._speed = None
            self.stats.no_press += 1
            return False, None, None, T("Space'e basılamadan pencere kapandı")
        bx = ctrl.box
        if bx is None:
            return False, None, None, T("kutucuk görülemedi")
        c, half = (bx[0] + bx[1]) / 2, (bx[1] - bx[0]) / 2
        sx = ctrl.stop_x(after)
        self._last_stop = sx
        meas = None
        if last_fr is not None and last_rd is not None:           # sonucu canlı görüntüde bir süre göster
            note = (T("DURDU: hedefe {d} px").format(d=f"{sx - c:+.0f}") + "  " +
                    (T("ISABET") if bx[0] <= sx <= bx[1] else T("ISKA")) if sx is not None else T("balik durmadi"))
            self._emit_img(draw_bar(last_fr, last_rd, ctrl.lat * 1000, box=bx, stop_x=sx, note=note), force=True)
        if sx is not None:
            err = sx - c
            hit = bx[0] <= sx <= bx[1]
            if cfg["timing_autolearn"]:
                meas = ctrl.learn(press[0], sx)
                if meas is not None:
                    self._lat = ctrl.lat
                    cfg.set("timing_latency_ms", int(round(self._lat * 1000)))
            how = T("balık x={0}'da durdu").format(f"{sx:.0f}")
        elif press[1] is not None:
            err = press[1] - c
            hit = abs(err) <= half
            how = T("tahmini (balık durmadı)")
        else:
            return False, None, None, T("balık izlenemedi")
        spd = T(", balık hızı {0} px/sn").format(f"{self._speed:.0f}") if getattr(self, "_speed", None) else ""
        return hit, err, meas, T("{0}, merkeze {1} px (kutucuk yarısı {2} px{3})").format(
            how, f"{err:+.0f}", f"{half:.0f}", spd)

    def _timing_result(self, hit: bool, err, meas, desc: str) -> None:
        txt = desc + (T(" • ölçülen gecikme {0} ms → {1} ms").format(f"{meas * 1000:.0f}", f"{self._lat * 1000:.0f}")
                      if meas is not None else "")
        if hit:
            self.stats.success += 1
            self.stats.catches["isabet"] = self.stats.catches.get("isabet", 0) + 1
            self.log(T('✓ İsabet — {0}').format((txt)))
        else:
            self.stats.fail += 1
            self.log(T('✗ Iska — {0}').format((txt)))
        self.scan(f"▶ {'✓' if hit else '✗'} {T('İSABET') if hit else T('ISKA')}: {txt}", important=True)
        self._result_note = ((T("ISABET") if hit else T("ISKA")) +
                             (T("  hedefe {e} px").format(e=f"{err:+.0f}") if err is not None else ""),
                             time.time(), bool(hit))
        self.on_stats(self.game.pid, self.stats.to_dict())
        self._rid += 1
        rnd = {"ok": bool(hit), "kind": "isabet" if hit else "iska", "depth": None,
               "err": err, "desc": (f"{err:+.0f} px" if err is not None else desc),
               "intentional": False, "time": time.time(), "rid": self._rid,
               "speed": getattr(self, "_speed", None), "sent": False, "geo": bool(hit)}
        self._rounds[self._rid] = rnd
        for k in [k for k in self._rounds if k < self._rid - 20]:
            del self._rounds[k]
        self.stats.latency_ms = self._lat * 1000
        if err is not None:
            self.stats.last_err = float(err)
            self.stats.abs_err_sum += abs(float(err))
            self.stats.err_n += 1
        self.on_stats(self.game.pid, self.stats.to_dict())
        # sonuç HEMEN arayüze: ödül çarkının bitmesi beklenmez
        rnd["sent"] = True
        self.on_round(self.game.pid, dict(rnd))
        try:
            self.cfg.save()
        except Exception:
            pass
        return rnd

    def _record_reward(self, rew, rnd: dict) -> None:
        """Kazanılan eşyayı say, toplamlara ekle, turu arayüze bildir."""
        if rew is not None and rew.item:
            n = rew.count if rew.count is not None else 0
            st = self.stats
            st.items[rew.item] = st.items.get(rew.item, 0) + n
            st.item_wins[rew.item] = st.item_wins.get(rew.item, 0) + 1
            name = item_name(rew.item, lang())
            cnt = str(rew.count) if rew.count is not None else "?"
            self.log(T("🎁 Ödül: {n} × {name}").format(n=cnt, name=name) +
                     (T(" (yeni eşya resmi kaydedildi: assets\\olta\\odul\\{f}.png — adını değiştirebilirsin)").format(f=rew.item)
                      if rew.new_item else ""))
            self.scan("▶ " + T("ödül: {0} × {1} (benzerlik {2})").format(name, cnt, f"{rew.score:.2f}"),
                      important=True)
            add_total(rew.item, n)
            rnd["reward"] = (rew.item, rew.count)
            self.on_stats(self.game.pid, st.to_dict())
        else:
            self.scan("▶ " + T("ödül okunamadı"), important=True)

    def _seri_sanity(self) -> None:
        """Seri sayısı birçok turdur HİÇ değişmiyorsa (bot isabet ölçtüğü halde) sayaç okunamıyor demektir:
        seri kontrolü kapatılır ve onun yaptığı düzeltmeler geri alınır."""
        if self._seri_off or self._seri_seen_change or self._seri_judged < 5:
            return
        geo_hits = sum(1 for r in self._rounds.values() if r.get("geo"))
        if geo_hits < 3:
            return
        self._seri_off = True
        self.log(T("Seri sayacı hiç değişmiyor — bu client'ta seri kontrolü kapatıldı, botun kendi ölçümü "
                   "kullanılıyor."))
        for rid, r in list(self._rounds.items()):
            if r.get("fixed"):
                self._fix_round(rid, bool(r.get("geo")), later=True, force=True)

    def _fix_round(self, rid: int, ok: bool, later: bool, force: bool = False) -> None:
        """Seri sayacının söylediği GERÇEK sonuç botun ölçümüyle çelişiyorsa turu düzelt."""
        if (self._seri_off or not self.cfg["streak_check"]) and not force:
            return
        rnd = self._rounds.get(rid)
        if rnd is None:
            return
        st = self.stats
        if not force and not rnd.get("streak"):
            rnd["streak"] = True
            st.verified += 1
        if bool(rnd["ok"]) == bool(ok):
            self.on_stats(self.game.pid, st.to_dict())
            return
        if ok:
            st.success += 1
            st.fail = max(0, st.fail - 1)
        else:
            st.fail += 1
            st.success = max(0, st.success - 1)
        rnd["ok"] = bool(ok)
        rnd["kind"] = "isabet" if ok else "iska"
        rnd["fixed"] = not force
        st.corrected += 1 if not force else -1
        st.corrected = max(0, st.corrected)
        if force:
            if rnd.get("streak"):
                rnd["streak"] = False
                st.verified = max(0, st.verified - 1)
            self.on_stats(self.game.pid, st.to_dict())
            if rnd.get("sent"):
                self.on_round(self.game.pid, dict(rnd, fix=True))
            return
        msg = (T("⚠ Seri sayacına göre önceki tur aslında: {0}") if later else
               T("⚠ Seri sayacına göre bu tur aslında: {0}")).format(T("İSABET") if ok else T("ISKA"))
        if not ok:
            msg += T(" (kutucuk yanlış okunmuş olabilir)")
        self.log(msg)
        self.scan("▶ " + msg, important=True)
        self._result_note = (T("ISABET") if ok else T("ISKA"), time.time(), bool(ok))
        self.on_stats(self.game.pid, st.to_dict())
        if rnd.get("sent"):
            self.on_round(self.game.pid, dict(rnd, fix=True))

    def _await_close(self, bar, count: bool = False):
        """Ödül çarkı dönerken bekle; pencere kapanınca döner. (Ekran görüntüsü KAYDEDİLMEZ.)

        Çark durunca kazanılan eşya ve adet okunur. Mavi su sürekli dalgalandığı için "durdu mu" kararı
        sadece çark şeridine bakılarak verilir; ayrıca her karede okunur ve ART ARDA AYNI okunan son sonuç
        kazanan sayılır (dönerken her kare başka okunur, durunca aynı kalır). Pencere çok çabuk kapanırsa
        son karelerden okunur. Dönen değer: (RewardRead ya da None, pencere sonundaki seri sayısı resmi)."""
        self.state(T("Ödül çarkı dönüyor"))
        t0 = time.time()
        gone = 0
        prev = None
        reading = None                 # kesinleşen okuma
        last_read = None               # bir önceki karenin okuması
        last_frames: list = []         # son kareler (pencere birden kapanırsa)
        glyphs: list = []
        learned = False

        def key(r):
            return None if r is None else (r.item, r.count)

        while time.time() - t0 < 30 and not self.stop_event.is_set():
            if self.sleep(0.08):
                break
            self._reset_capture_region()
            fr = self.capture.grab()
            if fr is None:
                continue
            b = self.bar_reader.find(fr)
            if b is None:
                gone += 1
                if gone >= 3:
                    break
                continue
            gone = 0
            bar = b
            try:
                glyphs = (glyphs + [read_glyph(fr, bar)])[-6:]
            except Exception:
                pass
            x, y, w, h = bar
            strip = fr[y + h: min(fr.shape[0], y + h + int(2.2 * h)), x: x + w]
            g = cv2.cvtColor(strip, cv2.COLOR_BGR2GRAY).astype(np.int16) if strip.size else None
            moving = True
            if g is not None and prev is not None and prev.shape == g.shape:
                moving = float(np.abs(g - prev).mean()) >= 3.0
            prev = g
            r = None
            if time.time() - t0 > 0.3:
                try:
                    r = self.reward.read(fr, bar, learn=False)
                except Exception:
                    r = None
                # aynı sonuç art arda iki karede ve çark şeridi durgunsa: kesin
                if r is not None and (r.count is not None or r.item) and key(r) == key(last_read) and \
                        (not moving or r.item is not None):
                    if reading is None or key(r) != key(reading) or (r.item and not reading.item):
                        reading = r
                        self.scan(T("ödül çarkı: {0} × {1} (benzerlik {2})").format(r.item or "?", r.count, f"{r.score:.2f}"))
            last_read = r
            last_frames = (last_frames + [(fr, bar, r)])[-3:]
            if self._emit_due():
                # canlı görüntüde sadece çubuk (ödül çarkı gösterilmez) + turun sonucu
                rn = self._result_note
                note = rn[0] if rn and time.time() - rn[1] < 4.0 else ""
                try:
                    self._emit_img(draw_bar(fr, self.bar_reader.read(fr, bar), self._lat * 1000, note=note,
                                            stop_x=self._last_stop))
                except Exception:
                    pass
        # pencere kapanmadan önceki son iki kare aynı okunduysa çarkın SON hali odur
        tail = [t[2] for t in last_frames[-2:]]
        if len(tail) == 2 and tail[0] is not None and key(tail[0]) == key(tail[1]) and \
                (tail[1].item or tail[1].count is not None):
            if reading is None or key(reading) != key(tail[1]):
                reading = tail[1]
        # hiç okuma olmadıysa (pencere çok çabuk kapandı) son karelerden oku
        if reading is None or reading.item is None:
            for fr, b, _r in reversed(last_frames):
                try:
                    r = self.reward.read(fr, b, learn=False)
                except Exception:
                    r = None
                if r is not None and (r.count is not None or r.item) and (reading is None or r.item):
                    reading = r
                    if r.item:
                        break
        # eşya tanınmadıysa (yeni eşya) resmini bir kez öğren
        if reading is not None and reading.item is None and last_frames and not learned:
            for fr, b, _r in reversed(last_frames):
                try:
                    r = self.reward.read(fr, b, learn=True)
                except Exception:
                    r = None
                if r is not None and r.item:
                    reading = r
                    break
        if count:
            self.stats.rewards += 1
            self.on_stats(self.game.pid, self.stats.to_dict())
        self.log(T("Ödül çarkı bitti, pencere kapandı."))
        return reading, stable(glyphs[-4:])

    def _captcha_seen(self) -> bool:
        """Hızlı bakış (pencere resmiyle, OCR'siz)."""
        try:
            self._reset_capture_region()
            fr = self.capture.grab()
            self._cap_last_frame = fr
            if not self.captcha.win_tpls:
                return self.captcha.detect(fr, allow_full_ocr=False) is not None
            return self.captcha.quick(fr)
        except Exception:
            return False

    def _sleep_watch(self, seconds: float, solve: bool = True):
        """Beklerken ~0,7 sn'de bir captcha penceresine bak (captcha süresi kısa).
        True: bot durduruldu • "captcha": captcha göründü (solve=True ise çözülmeye çalışıldı) • False: süre doldu."""
        if not self.cfg["captcha_enabled"]:
            return self.sleep(seconds)
        end = time.time() + max(0.0, seconds)
        while True:
            left = end - time.time()
            if left <= 0:
                return False
            if self.sleep(min(0.7, left)):
                return True
            if self._captcha_seen():
                if solve:
                    self._gate_any(self.capture.grab())
                return "captcha"

    def _gate_any(self, frame, full: bool = False) -> bool:
        """Captcha kontrolü. Fare kullanılacağı için önce sırayı (odak kilidini) alır."""
        if frame is None:
            return False
        if self._has_lock:
            return self._captcha_gate(frame, full)
        if self.captcha.detect(frame, allow_full_ocr=full or not self.captcha.win_tpls) is None:
            return False
        with self._control(urgent=True) as ok:
            if not ok:
                return False
            self._reset_capture_region()
            return self._captcha_gate(self.capture.grab(), full)

    def _captcha_gate(self, frame, full: bool = False) -> bool:
        """Ekranda captcha var mı? Varsa çözmeyi dener. True: captcha vardı (tur yeniden başlamalı)."""
        if frame is None:
            return False
        # pencere resmi varsa ekranın tamamını OCR ile taramak gereksiz (yavaş); yoksa her seferinde okunur
        found = self.captcha.detect(frame, allow_full_ocr=full or not self.captcha.win_tpls)
        if found is None:
            return False
        cfg = self.cfg
        self.state(T("CAPTCHA"))
        shot = self._save_captcha_shot(frame, "captcha")
        self.stats.captcha_seen += 1
        self.on_stats(self.game.pid, self.stats.to_dict())
        self.log(T('⚠ CAPTCHA algılandı: “{0}”').format((found.instruction)) + (f" → istenen: {found.target}" if found.target else ""))
        self.scan("▶ ⚠ CAPTCHA: “{0}” ({1}) — ".format(found.instruction, found.by) + T("ekran görüntüsü: {0}").format(shot), important=True)
        if cfg["captcha_sound"]:
            beep("uyari")
        if cfg["captcha_autosolve"]:
            for attempt in range(3):
                hit = self.captcha.find_click(frame, found)
                if hit is None:
                    break
                x, y, how = hit
                self.log(T('Captcha: {0} seçiliyor (deneme {1}).').format((how), (attempt + 1)))
                frame0, found0 = frame, found
                self._human_click(x, y, frame.shape)
                if self.sleep(self.rng.uniform(1.0, 1.5)):
                    return True
                self._reset_capture_region()
                frame = self.capture.grab()
                f2 = self.captcha.detect(frame, allow_full_ocr=not self.captcha.win_tpls)
                if f2 is None:
                    self.log(T("✓ Captcha çözüldü, bot devam ediyor."))
                    self.scan("▶ " + T("✓ Captcha çözüldü, bot devam ediyor."), important=True)
                    self.stats.captchas += 1
                    if "ocr" in found0.by:
                        self.captcha.learn_title(frame0, found0)   # sonra OCR'siz de tanınsın
                    return True
                found = f2                                          # yeni bir captcha geldi: tekrar dene
            if not found.target:
                why = T("ne istendiği okunamadı (Windows OCR kurulu mu? Ayarlar > Captcha testi)")
            elif not self.captcha.has_item(found.target):
                why = (T('“{0}” simgesi henüz kayıtlı değil — bir kez ELLE çözersen bot o simgeyi öğrenir (ya da assets\\captcha\\esya\\{1}.png olarak ekle)').format((found.target), (found.target)))
            else:
                why = T('“{0}” simgesi ekranda bulunamadı').format((found.target))
            self.log(T('Captcha otomatik çözülemedi: {0}.').format((why)))
            self.stats.captcha_fail += 1
        self.log(T("Captcha'yı lütfen ELLE çöz — bot bekliyor, fareyi bırakır; çözülünce kendiliğinden devam eder."))
        self._captcha_wait = (found, time.time(), frame)
        self._captcha_wait_loop()       # (gerçek fare modunda kilit bizde: diğer client'lar imleci oynatmaz)
        return True

    def _captcha_wait_loop(self) -> None:
        """Elle çözülmesini bekle. Kullanıcının tıkladığı yer izlenir: bilinmeyen bir simgeyse öğrenilir."""
        found, t0, frame0 = self._captcha_wait if len(self._captcha_wait) == 3 else (*self._captcha_wait, None)
        self.state(T("CAPTCHA — elle çözülmesi bekleniyor"))
        limit = float(self.cfg["captcha_wait_min"]) * 60
        gone = 0
        next_beep = time.time() + 20
        next_chk = time.time() + 1.0
        last_click = None          # (x, y, zaman, o anki kare) kare koordinatında
        was_down = False
        self._cap_last_frame = frame0
        while not self.stop_event.is_set():
            if self.sleep(0.03):
                break
            down = mouse_down()
            if down and not was_down:
                try:
                    cx, cy = get_cursor()
                    ox, oy, pw, ph = client_rect_screen(self.game.hwnd)
                    fr_c = self._cap_last_frame if self._cap_last_frame is not None else frame0
                    if fr_c is not None and pw > 0 and ph > 0:
                        fx = (cx - ox) * fr_c.shape[1] / pw
                        fy = (cy - oy) * fr_c.shape[0] / ph
                        last_click = (int(fx), int(fy), time.time(), fr_c)
                except Exception:
                    pass
            was_down = down
            if time.time() < next_chk:
                continue
            next_chk = time.time() + 0.8
            seen = self._captcha_seen()
            gone = 0 if seen else gone + 1
            if gone >= 2:
                if last_click is not None and time.time() - last_click[2] < 3.0:
                    fc = last_click[3]
                    f_c = self.captcha.detect(fc, allow_full_ocr=False)     # tıklandığı andaki captcha
                    if f_c is not None and f_c.target and not self.captcha.has_item(f_c.target):
                        p = self.captcha.learn_icon(fc, f_c, last_click[0], last_click[1])
                        if p:
                            self.log(T('✓ “{0}” simgesi öğrenildi ({1}) — bir dahakine bot kendisi çözer.').format((f_c.target), (Path(p).name)))
                self.log(T("✓ Captcha kapandı, bot devam ediyor."))
                self.stats.captcha_manual += 1
                self.on_stats(self.game.pid, self.stats.to_dict())
                self._captcha_wait = None
                return
            if self.cfg["captcha_sound"] and time.time() > next_beep:
                beep("uyari")
                next_beep = time.time() + 30
            if time.time() - t0 > limit:
                self.log(T('Captcha {0:.0f} dakikadır çözülmedi — bot durduruluyor.').format((limit / 60)))
                self._captcha_wait = None
                self.stop_event.set()
                return
        self._captcha_wait = None

    def _save_captcha_shot(self, frame, tag: str) -> str:
        try:
            if frame is None:
                return ""
            d = DATA / "captcha"
            d.mkdir(parents=True, exist_ok=True)
            p = d / f"{time.strftime('%Y%m%d_%H%M%S')}_{self.game.pid}_{tag}.png"
            cv2.imwrite(str(p), frame)
            from .config import prune_data
            prune_data(int(self.cfg["captcha_keep"]))
            return str(p)
        except Exception:
            return ""

    def _human_click(self, fx: float, fy: float, shape) -> None:
        """Kare koordinatındaki noktaya insan gibi git ve tıkla (gerçek fare)."""
        ch, cw = shape[0], shape[1]
        ox, oy, pw, ph = client_rect_screen(self.game.hwnd)
        sx, sy = ox + fx * pw / max(1, cw), oy + fy * ph / max(1, ch)
        try:
            focus_window(self.game.hwnd, timeout=0.3)
        except Exception:
            pass
        x0, y0 = get_cursor()
        n = self.rng.randint(16, 26)
        bow = self.rng.uniform(-0.12, 0.12) * float(np.hypot(sx - x0, sy - y0))
        nx, ny = -(sy - y0), (sx - x0)
        nl = max(1e-6, float(np.hypot(nx, ny)))
        for i in range(1, n + 1):
            t = i / n
            e = t * t * (3 - 2 * t)                       # yumuşak başla, yumuşak dur
            b = bow * np.sin(np.pi * t)
            set_cursor(x0 + (sx - x0) * e + nx / nl * b, y0 + (sy - y0) * e + ny / nl * b)
            time.sleep(self.rng.uniform(0.010, 0.022))
        set_cursor(sx + self.rng.uniform(-1.5, 1.5), sy + self.rng.uniform(-1.5, 1.5))
        time.sleep(self.rng.uniform(0.08, 0.2))
        mouse_click(hold=self.rng.uniform(0.05, 0.11))
