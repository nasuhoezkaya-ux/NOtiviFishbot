"""CAPTCHA algılama ve otomatik çözme.

Sunucunun captcha'sı (örnek):
    ┌──────── "Atın üzerine tıklayın" ────────┐
    │  3x3 ızgarada simgeler: kılıç, at, kitap, │
    │  iksir, balık, kalkan …  (yerleri rastgele)│
    └──────────── "Kalan Süre: 00:08" ──────────┘
Süre kısa (~10 sn) olduğu için bot bekleme anlarında sık sık hızlıca bakar.

Nasıl çalışır:
  1) PENCEREYİ BULMA: assets/captcha/pencere/*.png (ör. hiç değişmeyen "Kalan Süre:" yazısı) ekranda
     aranır — çok hızlıdır. Yanındaki .json dosyası pencerenin, başlığın ve ızgaranın bu resme göre
     nerede olduğunu söyler. (Pencere resmi yoksa / bulunamazsa ekranın ortası yazı tanımayla okunur.)
  2) NE İSTENİYOR: başlık Windows OCR ile okunur ("Atın üzerine tıklayın" -> "at"). OCR yoksa başlık
     assets/captcha/yazi/<isim>.png resimleriyle karşılaştırılır. OCR ile çözülen her captcha'nın başlığı
     otomatik olarak yazi/ klasörüne eklenir (bot zamanla OCR'siz de tanır).
  3) NEREYE TIKLANACAK: ızgarada assets/captcha/esya/<isim>.png simgesi aranır (şekil + çevresindeki koyu
     zemin birlikte karşılaştırılır). Seçenekler yazıysa doğrudan yazıya tıklanır.
Bulamazsa bot sesli uyarır, ekran görüntüsünü data/captcha/ klasörüne kaydeder ve elle çözülmesini bekler.
"""
from __future__ import annotations

from .paths import ASSETS

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from . import ocr

ASSET_DIR = ASSETS / "captcha"
WINDOW_DIR = ASSET_DIR / "pencere"
ITEM_DIR = ASSET_DIR / "esya"
TEXT_DIR = ASSET_DIR / "yazi"

# yönerge kelimeleri (sadeleştirilmiş: küçük harf, Türkçe karakter yok)
ACTION_WORDS = ("sec", "secin", "seciniz", "secer", "tikla", "tiklayin", "tiklayiniz", "tiklayn", "tikiayin",
                "bul", "bulun", "isaretle", "isaretleyin", "select", "click", "choose")
FILLER_WORDS = ("uzerine", "ustune", "uzerini", "resmine", "resmini", "simgesine", "simgeyi", "olana", "olani",
                "resmi", "esyayi", "nesneyi", "gorseli", "on", "the")
TRIGGER_WORDS = ("captcha", "dogrulama", "dogrula", "robot", "bot kontrol", "guvenlik kontrol",
                 "insan misin", "anti bot", "antibot", "kalan sure")

# isimlerin okunuşu (ekran yazısı -> dosya adı); dosya adları Türkçe karaktersiz yazılabilir
DISPLAY = {"at": "At", "kilic": "Kılıç", "kitap": "Kitap", "iksir": "İksir", "balik": "Balık", "kalkan": "Kalkan"}


@dataclass
class CaptchaFound:
    instruction: str
    target: str | None                    # sadeleştirilmiş hedef adı ("at")
    region: tuple[int, int, int, int]     # simgelerin aranacağı bölge (x, y, w, h) — kare koordinatı
    lines: list = field(default_factory=list)
    by: str = "ocr"
    line_box: tuple[float, float, float, float] | None = None
    title_box: tuple[int, int, int, int] | None = None
    window_box: tuple[int, int, int, int] | None = None


def _stems(word: str) -> list[str]:
    """'kalkani' -> [..,'kalkan'], 'atin' -> [..,'at'], 'kilicin' -> [..,'kilic'], 'baligin' -> [..,'balik']"""
    w = ocr.fold(word).replace(" ", "")
    out = [w]
    for suf in ("nin", "nun", "yi", "yu", "ni", "nu", "in", "un", "i", "u", "a", "e"):
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            out.append(w[: -len(suf)])
    more = []
    for s in out:
        if s.endswith("g"):
            more.append(s[:-1] + "k")         # ğ -> k (balığın -> balık, bıçağı -> bıçak)
        if s.endswith("b"):
            more.append(s[:-1] + "p")         # kitabın -> kitap
        if s.endswith("d"):
            more.append(s[:-1] + "t")
    seen, res = set(), []
    for s in out + more:
        if s and s not in seen:
            seen.add(s)
            res.append(s)
    return res


def base_name(word: str) -> str:
    """En kısa kök: 'Atın' -> 'at', 'Kitabın' -> 'kitap' (sert ünsüzle biten tercih edilir)."""
    st = _stems(word)
    if not st:
        return ocr.fold(word)
    m = min(len(x) for x in st)
    short = [x for x in st if len(x) == m]
    return next((x for x in short if x[-1] in "ptkc"), short[0])


def name_matches(label: str, target: str) -> bool:
    """Yazı/dosya adı hedefle aynı şeyi mi söylüyor? (ek, büyük-küçük harf, Türkçe karakter farkı yok sayılır)"""
    if not label or not target:
        return False
    a = set(_stems(label))
    b = set(_stems(target))
    if a & b:
        return True
    la, lb = ocr.fold(label).replace(" ", ""), ocr.fold(target).replace(" ", "")
    return len(lb) >= 4 and len(la) >= 4 and (la.startswith(lb) or lb.startswith(la))


def _file_name(p: Path) -> str:
    return re.sub(r"[_\-\s]*\d+$", "", p.stem)


class CaptchaSolver:
    def __init__(self, cfg=None):
        self.cfg = cfg
        self.win_tpls: list[tuple[np.ndarray, dict | None, str]] = []
        self.items: list[tuple[str, np.ndarray, np.ndarray | None]] = []
        self.texts: list[tuple[str, np.ndarray]] = []
        self._last_scale: float | None = None
        self._tpl_gray = None
        self.reload()

    # ------------------------------------------------------------------ referanslar
    def reload(self) -> None:
        self.win_tpls, self.items, self.texts = [], [], []
        for d in (WINDOW_DIR, ITEM_DIR, TEXT_DIR):
            d.mkdir(parents=True, exist_ok=True)
        for p in sorted(WINDOW_DIR.glob("*.png")):
            im = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if im is None or im.shape[0] < 6 or im.shape[1] < 12:
                continue
            geo = None
            js = p.with_suffix(".json")
            if js.exists():
                try:
                    geo = json.loads(js.read_text(encoding="utf-8"))
                except Exception:
                    geo = None
            self.win_tpls.append((im, geo, p.stem))
        for p in sorted(ITEM_DIR.glob("*.png")):
            im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
            if im is None or im.shape[0] < 8 or im.shape[1] < 8:
                continue
            mask = None
            if im.ndim == 3 and im.shape[2] == 4:
                mask = (im[:, :, 3] > 40).astype(np.uint8) * 255
                im = im[:, :, :3]
            self.items.append((_file_name(p), im, mask))
        for p in sorted(TEXT_DIR.glob("*.png")):
            im = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if im is not None and im.shape[0] >= 6 and im.shape[1] >= 12:
                self.texts.append((_file_name(p), im))
        self._tpl_gray = None

    @property
    def item_names(self) -> list[str]:
        return sorted({n for n, _i, _m in self.items})

    def canon(self, target: str | None) -> str | None:
        """OCR'da okunan kelimeyi kayıtlı simge adına çevir ('Kitabın' -> 'kitap')."""
        if not target:
            return target
        for n in self.item_names:
            if name_matches(n, target):
                return n
        return base_name(target)

    def has_item(self, target: str | None) -> bool:
        return bool(target) and any(name_matches(n, target) for n in self.item_names)

    # ------------------------------------------------------------------ pencere
    @staticmethod
    def _center(frame: np.ndarray) -> tuple[np.ndarray, int, int]:
        """Ekranın ortası (captcha penceresi genelde burada açılır)."""
        h, w = frame.shape[:2]
        x0, y0 = int(w * 0.12), int(h * 0.06)
        return frame[y0: int(h * 0.82), x0: int(w * 0.88)], x0, y0

    @staticmethod
    def _search_area(frame: np.ndarray) -> tuple[np.ndarray, int, int]:
        h, w = frame.shape[:2]
        x0, y0 = int(w * 0.08), int(h * 0.04)
        x1, y1 = int(w * 0.92), int(h * 0.96)
        return frame[y0:y1, x0:x1], x0, y0

    # kaba arama ölçekleri (yarım çözünürlükte, bulanıklaştırılmış gri resimde)
    COARSE = tuple(round(0.66 * 1.07 ** i, 3) for i in range(13))      # 0.66 … 1.49

    def _prep_templates(self) -> None:
        self._tpl_gray = []
        for t, geo, name in self.win_tpls:
            g = cv2.cvtColor(t, cv2.COLOR_BGR2GRAY)
            self._tpl_gray.append((t, g, geo, name))

    def _match_window(self, frame: np.ndarray):
        """Pencere şablonunu bul: (x, y, w, h, ölçek, geometri) ya da None.

        1) Kaba: yarım çözünürlükte, hafif bulanık gri resimde birçok ölçek (hızlı, ölçek farkına toleranslı).
        2) İnce: en iyi adayların çevresinde tam çözünürlükte, renkli, küçük ölçek adımlarıyla doğrulama."""
        if not self.win_tpls:
            return None
        if getattr(self, "_tpl_gray", None) is None or len(self._tpl_gray) != len(self.win_tpls):
            self._prep_templates()
        sub, ox, oy = self._search_area(frame)
        g = cv2.cvtColor(sub, cv2.COLOR_BGR2GRAY)
        D = 0.5
        gs = cv2.GaussianBlur(cv2.resize(g, None, fx=D, fy=D, interpolation=cv2.INTER_AREA), (3, 3), 0.8)
        if self._last_scale is not None:
            ls = self._last_scale
            near = [s for s in self.COARSE if abs(s / ls - 1) < 0.1]
            orders = [near or [ls], [s for s in self.COARSE if s not in near]]
        else:
            orders = [list(self.COARSE)]
        for scales in orders:
            cands = []
            for ti, (t, tg, geo, name) in enumerate(self._tpl_gray):
                for sc in scales:
                    f = sc * D
                    tt = cv2.resize(tg, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
                    if tt.shape[0] < 5 or tt.shape[1] < 10 or tt.shape[0] >= gs.shape[0] or tt.shape[1] >= gs.shape[1]:
                        continue
                    tt = cv2.GaussianBlur(tt, (3, 3), 0.8)
                    r = cv2.matchTemplate(gs, tt, cv2.TM_CCOEFF_NORMED)
                    _, v, _, loc = cv2.minMaxLoc(r)
                    if v >= 0.55:
                        cands.append((v, ti, sc, loc))
            cands.sort(key=lambda c: -c[0])
            best = None
            for v, ti, sc, (lx, ly) in cands[:5]:          # en iyi DOĞRULANAN aday kazanır (ilk geçen değil)
                hit = self._refine(sub, ti, sc, lx / D, ly / D)
                if hit is not None and (best is None or hit[0] > best[0]):
                    best = hit
            if best is not None:
                _v, x, y, w, h, s2, geo = best
                self._last_scale = s2
                return ox + x, oy + y, w, h, s2, geo
        return None

    def _refine(self, sub: np.ndarray, ti: int, sc: float, x: float, y: float):
        t, _tg, geo, _name = self._tpl_gray[ti]
        best = None
        cand = [sc * (1 + 0.01 * k) for k in range(-5, 6)]
        if abs(sc - 1) <= 0.06:
            cand.append(1.0)                  # oyun arayüzü genelde ölçeksizdir: tam 1.0'ı mutlaka dene
        for s2 in cand:
            tt = cv2.resize(t, None, fx=s2, fy=s2, interpolation=cv2.INTER_AREA if s2 < 1 else cv2.INTER_LINEAR) \
                if abs(s2 - 1) > 1e-3 else t
            th, tw = tt.shape[:2]
            pad = 6
            x0, y0 = int(max(0, x - pad)), int(max(0, y - pad))
            x1, y1 = int(min(sub.shape[1], x + tw + pad)), int(min(sub.shape[0], y + th + pad))
            roi = sub[y0:y1, x0:x1]
            if roi.shape[0] < th or roi.shape[1] < tw:
                continue
            r = cv2.matchTemplate(roi, tt, cv2.TM_CCOEFF_NORMED)
            _, v, _, loc = cv2.minMaxLoc(r)
            if best is None or v > best[0]:
                best = (v, x0 + loc[0], y0 + loc[1], tw, th, s2)
        if best is None or best[0] < 0.78:
            return None
        v, bx, by, w, h, s2 = best
        return v, bx, by, w, h, s2, geo

    def quick(self, frame: np.ndarray | None) -> bool:
        """Hızlı kontrol (sadece pencere resmiyle, OCR'siz): ekranda captcha penceresi var mı?"""
        if frame is None or frame.size == 0:
            return False
        return self._match_window(frame) is not None

    # ------------------------------------------------------------------ yönerge
    def _instruction(self, lines) -> tuple[object | None, str | None]:
        best = None
        for ln in lines:
            raw = ln.text.strip()
            if ":" in raw or len(raw) < 3:          # sohbet satırları ("İsim: mesaj") ve "Kalan Süre: …" hariç
                continue
            f = ocr.fold(raw)
            words = f.split()
            if not words or len(words) > 7:
                continue
            trig = any(t in f for t in TRIGGER_WORDS)
            act_idx = next((i for i, wd in enumerate(words) if wd in ACTION_WORDS or
                            (len(wd) >= 6 and wd.startswith("tikla"))), None)
            if act_idx is None and not trig:
                continue
            target = None
            if act_idx is not None:
                j = act_idx - 1
                while j >= 0 and words[j] in FILLER_WORDS:
                    j -= 1
                if j >= 0:
                    target = words[j]
            score = (2 if act_idx is not None else 0) + (1 if trig else 0) + (1 if target else 0)
            if best is None or score > best[0]:
                best = (score, ln, target)
        if best is None:
            return None, None
        return best[1], best[2]

    def _target_from_text_templates(self, frame: np.ndarray, box) -> tuple[str | None, float]:
        """OCR yoksa: başlık bölgesini yazi/<isim>.png resimleriyle karşılaştır."""
        if not self.texts or box is None:
            return None, 0.0
        x, y, w, h = box
        strip = cv2.cvtColor(frame[max(0, y): y + h, max(0, x): x + w], cv2.COLOR_BGR2GRAY)
        if strip.size == 0:
            return None, 0.0
        best = (None, 0.0)
        sc0 = self._last_scale or 1.0
        for name, t in self.texts:
            for sc in sorted({1.0 if abs(sc0 - 1) < 0.02 else sc0} | {sc0 * (1 + 0.02 * k) for k in (-3, -2, -1, 1, 2, 3)}):
                tt = cv2.resize(t, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA) if abs(sc - 1) > 1e-3 else t
                if tt.shape[0] > strip.shape[0] or tt.shape[1] > strip.shape[1]:
                    continue
                r = cv2.matchTemplate(strip, tt, cv2.TM_CCOEFF_NORMED)
                v = float(r.max())
                if v > best[1]:
                    best = (name, v)
        return (best[0], best[1]) if best[1] >= 0.80 else (None, best[1])

    def learn_title(self, frame: np.ndarray, found: CaptchaFound) -> None:
        """OCR ile doğru çözülen captcha'nın başlığını sakla (sonra OCR'siz de tanınır)."""
        try:
            if not found.target or found.title_box is None:
                return
            name = base_name(found.target)
            if any(n == name for n, _t in self.texts):
                return
            x, y, w, h = found.title_box
            g = cv2.cvtColor(frame[y: y + h, x: x + w], cv2.COLOR_BGR2GRAY)
            m = g > max(90, int(np.percentile(g, 80)))
            ys, xs = np.where(m)
            if len(xs) < 20:
                return
            crop = frame[max(0, y + ys.min() - 3): y + ys.max() + 4, max(0, x + xs.min() - 3): x + xs.max() + 4]
            TEXT_DIR.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(TEXT_DIR / f"{name}.png"), crop)
            self.texts.append((name, cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)))
        except Exception:
            pass

    # ------------------------------------------------------------------ algılama
    def detect(self, frame: np.ndarray | None, allow_full_ocr: bool = True) -> CaptchaFound | None:
        if frame is None or frame.size == 0:
            return None
        H, W = frame.shape[:2]
        win = self._match_window(frame)
        if win is not None:
            x, y, w, h, sc, geo = win
            g = geo or {"window": [-0.6 * w / sc, -18 * h / sc, 6.2 * w / sc, 19.5 * h / sc],
                        "title": [-0.6 * w / sc, -17 * h / sc, 6.2 * w / sc, 2.2 * h / sc],
                        "grid": [-0.6 * w / sc, -15 * h / sc, 6.2 * w / sc, 15 * h / sc]}

            def rect(key):
                rx, ry, rw, rh = g[key]
                X0 = int(round(x + rx * sc))
                Y0 = int(round(y + ry * sc))
                X0c, Y0c = max(0, X0), max(0, Y0)
                X1, Y1 = min(W, int(round(X0 + rw * sc))), min(H, int(round(Y0 + rh * sc)))
                return X0c, Y0c, max(1, X1 - X0c), max(1, Y1 - Y0c)

            wbox, tbox, gbox = rect("window"), rect("title"), rect("grid")
            instruction, target, lines, lbox = "", None, [], None
            if ocr.available():
                tx, ty, tw, th = tbox
                lines = ocr.recognize(frame[ty: ty + th, tx: tx + tw], scale=3.0)
                for ln in lines:
                    for wd in ln.words:
                        wd.x += tx
                        wd.y += ty
                ln, target = self._instruction(lines)
                if ln is not None:
                    instruction, lbox = ln.text.strip(), ln.box
                elif lines:
                    instruction = " ".join(l.text for l in lines)
                # seçenekler yazıysa onları da okuyabilmek için ızgarayı da oku
                gx, gy, gw, gh = gbox
                glines = ocr.recognize(frame[gy: gy + gh, gx: gx + gw], scale=2.0)
                for l2 in glines:
                    for wd in l2.words:
                        wd.x += gx
                        wd.y += gy
                lines = lines + glines
            target = self.canon(target)
            by = "pencere+ocr" if target else "pencere"
            if not target:
                name, v = self._target_from_text_templates(frame, tbox)
                if name:
                    target, by = name, f"pencere+yazı resmi ({v:.2f})"
                    instruction = instruction or f"{DISPLAY.get(name, name)} (başlık resmiyle tanındı)"
            return CaptchaFound(instruction or "(captcha penceresi)", target, gbox, lines, by, lbox, tbox, wbox)

        if not allow_full_ocr or not ocr.available():
            return None
        # pencere resmi yok/bulunamadı: ekranın ortasını oku
        x0, y0 = int(W * 0.12), int(H * 0.06)
        sub = frame[y0: int(H * 0.82), x0: int(W * 0.88)]
        lines = ocr.recognize(sub, scale=2.0 if max(sub.shape[:2]) < 1100 else 1.5)
        for ln in lines:
            for wd in ln.words:
                wd.x += x0
                wd.y += y0
        ln, target = self._instruction(lines)
        if ln is None:
            return None
        target = self.canon(target)
        bx, by_, bw, bh = ln.box
        rx0 = int(max(0, bx - 0.30 * W))
        rx1 = int(min(W, bx + bw + 0.30 * W))
        ry0 = int(max(0, by_ - 0.05 * H))
        ry1 = int(min(H, by_ + bh + 0.55 * H))
        tb = (int(max(0, bx - 10)), int(max(0, by_ - 4)), int(bw + 20), int(bh + 8))
        return CaptchaFound(ln.text.strip(), target, (rx0, ry0, rx1 - rx0, ry1 - ry0), lines, "ocr",
                            (bx, by_, bw, bh), tb)

    # ------------------------------------------------------------------ çözme
    def find_click(self, frame: np.ndarray, found: CaptchaFound) -> tuple[int, int, str] | None:
        """Tıklanacak nokta (kare koordinatı) ve nasıl bulunduğu. Bulunamazsa None."""
        if not found.target:
            return None
        rx, ry, rw, rh = found.region
        # a) seçenekler yazıysa: yönerge satırı dışındaki, hedefle aynı yazıya tıkla
        lb = found.line_box
        tb = found.title_box
        for ln in found.lines:
            for wd in ln.words:
                if tb is not None and tb[0] <= wd.cx <= tb[0] + tb[2] and tb[1] <= wd.cy <= tb[1] + tb[3]:
                    continue          # başlığın kendisi
                if lb is not None and abs(wd.cy - (lb[1] + lb[3] / 2)) < max(6.0, lb[3] * 0.6) \
                        and lb[0] - 4 <= wd.cx <= lb[0] + lb[2] + 4:
                    continue
                if ":" in wd.text or not (rx <= wd.cx <= rx + rw and ry <= wd.cy <= ry + rh):
                    continue
                if name_matches(wd.text, found.target):
                    return int(wd.cx), int(wd.cy), f"yazı “{wd.text}”"
        # b) seçenekler resimse: assets/captcha/esya/<isim>.png
        refs = [(n, im, m) for n, im, m in self.items if name_matches(n, found.target)]
        if not refs:
            return None
        reg = frame[ry: ry + rh, rx: rx + rw]
        sc0 = self._last_scale or 1.0
        scales = sorted({round(sc0 * f, 3) for f in (0.9, 0.95, 1.0, 1.05, 1.1)} |
                        ({0.8, 0.9, 1.0, 1.12, 1.25} if self._last_scale is None else set()))
        best = None
        for n, im, m in refs:
            for sc in scales:
                t = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA) if sc != 1.0 else im
                mm = None
                if m is not None:
                    mm = cv2.resize(m, (t.shape[1], t.shape[0]), interpolation=cv2.INTER_NEAREST)
                if t.shape[0] >= reg.shape[0] or t.shape[1] >= reg.shape[1]:
                    continue
                r = cv2.matchTemplate(reg, t, cv2.TM_CCOEFF_NORMED, mask=mm) if mm is not None else \
                    cv2.matchTemplate(reg, t, cv2.TM_CCOEFF_NORMED)
                r = np.nan_to_num(r, nan=-1.0, posinf=-1.0, neginf=-1.0)
                _, v, _, loc = cv2.minMaxLoc(r)
                if best is None or v > best[0]:
                    best = (v, loc, t.shape[1], t.shape[0], n)
        if best is None or best[0] < 0.70:
            return None
        v, (x, y), w, h, n = best
        return rx + x + w // 2, ry + y + h // 2, f"simge “{DISPLAY.get(n, n)}” (benzerlik {v:.2f})"

    def learn_icon(self, frame: np.ndarray, found: CaptchaFound, x: int, y: int) -> str | None:
        """Kullanıcı bilinmeyen bir simgeyi elle tıklayıp captcha'yı çözdüyse o simgeyi öğren.
        (x, y): tıklanan nokta (kare koordinatı). Kaydedilen dosya yolunu döner."""
        try:
            if not found.target or self.has_item(found.target):
                return None
            rx, ry, rw, rh = found.region
            if not (rx <= x <= rx + rw and ry <= y <= ry + rh):
                return None
            sc = self._last_scale or 1.0
            half = int(round(48 * sc))
            x0, y0 = max(rx, x - half), max(ry, y - half)
            x1, y1 = min(rx + rw, x + half), min(ry + rh, y + half)
            sq = frame[y0:y1, x0:x1]
            g = cv2.cvtColor(sq, cv2.COLOR_BGR2GRAY)
            m = (g > 105).astype(np.uint8)
            m = cv2.dilate(m, np.ones((11, 11), np.uint8))
            n, lab, st, cen = cv2.connectedComponentsWithStats(m)
            if n <= 1:
                return None
            px, py = x - x0, y - y0
            best = None
            for i in range(1, n):
                bx, by, bw, bh, area = st[i]
                if area < 150:
                    continue
                d = 0.0 if (bx <= px <= bx + bw and by <= py <= by + bh) else \
                    float(np.hypot(cen[i][0] - px, cen[i][1] - py))
                if best is None or d < best[0]:
                    best = (d, i)
            if best is None or best[0] > 30 * sc:
                return None
            i = best[1]
            bx, by, bw, bh, _a = st[i]
            mask = (lab == i).astype(np.uint8) * 255
            crop = sq[by: by + bh, bx: bx + bw]
            rgba = np.dstack([crop, mask[by: by + bh, bx: bx + bw]])
            name = base_name(found.target)
            ITEM_DIR.mkdir(parents=True, exist_ok=True)
            p = ITEM_DIR / f"{name}.png"
            k = 2
            while p.exists():
                p = ITEM_DIR / f"{name}_{k}.png"
                k += 1
            cv2.imwrite(str(p), rgba)
            self.items.append((name, crop.copy(), mask[by: by + bh, bx: bx + bw].copy()))
            return str(p)
        except Exception:
            return None

    def score_all(self, frame: np.ndarray, found: CaptchaFound) -> list[tuple[str, float, int, int]]:
        """Test için: her kayıtlı simgenin ızgaradaki en iyi eşleşmesi."""
        out = []
        for n in self.item_names:
            f2 = CaptchaFound(found.instruction, n, found.region, [], found.by)
            hit = self.find_click(frame, f2)
            out.append((n, float(re.findall(r"benzerlik ([\d.]+)", hit[2])[0]) if hit and "benzerlik" in hit[2]
                        else 0.0, hit[0] if hit else -1, hit[1] if hit else -1))
        return out
