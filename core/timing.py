"""YENİ BALIK SİSTEMİ: olta → kafada balık işareti → zamanlama penceresi → ödül çarkı.

Akış (bot.py: BotWorker._cycle_timing):
  1) Space ile olta atılır.
  2) Karakterin kafasında balık işareti çıkınca (BiteWatcher) hemen Space'e basılır.
  3) Zamanlama penceresi açılır: mavi çubukta siyah bir balık gidip gelir, çubuğun bir yerinde (her
     seferinde başka yerde) lacivert çerçeveli bir kutucuk vardır (BarReader). Balık kutucuğun TAM ORTASINA
     geldiği anda Space'e basılır. Bot balığın hızını ölçer ve tuşun oyuna ulaşma gecikmesini hesaba
     katarak basar (FishTracker); gecikmeyi her turda balığın durduğu yere bakarak kendisi öğrenir.
  4) Alttaki ödül çarkı kendiliğinden döner; pencere kapanınca baştan başlanır.
"""
from __future__ import annotations

from .paths import ASSETS

import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .i18n import T

ASSET_DIR = ASSETS / "olta"
SIGN_DIR = ASSET_DIR / "isaret"          # kafadaki balık işaretinin resimleri (bot ilk seferde kendisi öğrenir)


def precise_sleep(dt: float) -> None:
    """Milisaniye hassasiyetinde bekle (Windows'ta time.sleep ~15 ms kayabilir; son kısım döngüyle)."""
    end = time.perf_counter() + max(0.0, dt)
    while True:
        left = end - time.perf_counter()
        if left <= 0:
            return
        if left > 0.004:
            time.sleep(left - 0.003)


# ====================================================================== zamanlama çubuğu
@dataclass
class BarRead:
    bar: tuple[int, int, int, int]                 # çubuk (x, y, w, h) — kare koordinatı
    box: tuple[float, float] | None = None         # kutucuğun sol / sağ kenarı (x)
    fish: tuple[float, float] | None = None        # balığın sol / sağ kenarı (x)
    box_how: str = ""                              # "cerceve" (lacivert çerçeve, kesin) ya da "renk" (yedek)

    @property
    def fish_x(self) -> float | None:
        return None if self.fish is None else (self.fish[0] + self.fish[1]) / 2

    @property
    def box_c(self) -> float | None:
        return None if self.box is None else (self.box[0] + self.box[1]) / 2

    @property
    def box_half(self) -> float:
        return 0.0 if self.box is None else (self.box[1] - self.box[0]) / 2


class BarReader:
    """Zamanlama penceresindeki mavi çubuğu, kutucuğu ve siyah balığı bulur (resim gerekmez: renk ve şekil)."""

    @staticmethod
    def _water(img: np.ndarray) -> np.ndarray:
        b, g, r = (c.astype(np.int16) for c in cv2.split(img))
        return ((b > 110) & (b - r > 38) & (b - g > 10)).astype(np.uint8)

    def find(self, frame: np.ndarray | None) -> tuple[int, int, int, int] | None:
        """Tüm karede çubuğu ara. (x, y, w, h) ya da None."""
        if frame is None or frame.size == 0:
            return None
        H, W = frame.shape[:2]
        D = 0.5
        sm = cv2.resize(frame, None, fx=D, fy=D, interpolation=cv2.INTER_AREA)
        m = self._water(sm)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 11), np.uint8))
        n, _lab, st, _c = cv2.connectedComponentsWithStats(m)
        best = None
        g_sm = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
        for i in range(1, n):
            x, y, w, h, area = (int(v) for v in st[i])
            if w < max(60, 0.12 * W * D) or not (7 <= h <= 60) or w < 5 * h:
                continue
            fill = area / float(w * h)
            if fill < 0.6:
                continue
            hdr = g_sm[max(0, y - h): max(0, y - 2), x: x + w]         # üstünde koyu başlık şeridi olmalı
            if hdr.size == 0 or float(hdr.mean()) > 80:
                continue
            score = w * fill
            if best is None or score > best[0]:
                best = (score, x, y, w, h)
        if best is None:
            return None
        _s, x, y, w, h = best
        # tam çözünürlükte kenarları netleştir
        X0, Y0 = max(0, int(x / D) - 6), max(0, int(y / D) - 6)
        X1, Y1 = min(W, int((x + w) / D) + 6), min(H, int((y + h) / D) + 6)
        mm = self._water(frame[Y0:Y1, X0:X1])
        rows = np.where(mm.mean(1) > 0.45)[0]
        if len(rows) < 8:
            return None
        r0, r1 = int(rows[0]), int(rows[-1])
        colf = mm[r0:r1 + 1].mean(0) > 0.35
        # en uzun sütun koşusu (kutucuğun/balığın kısa boşlukları birleştirilir)
        best, s_, gap = None, None, 0
        for i, v in enumerate(list(colf) + [False] * 72):
            if v:
                if s_ is None:
                    s_ = i
                gap, e_ = 0, i
            elif s_ is not None:
                gap += 1
                if gap > 70:          # kutucuk / balık sütunları çubuğu bölmesin
                    if best is None or e_ - s_ > best[1] - best[0]:
                        best = (s_, e_)
                    s_, gap = None, 0
        if best is None or best[1] - best[0] < 40:
            return None
        return int(X0 + best[0]), int(Y0 + r0), int(best[1] - best[0] + 1), int(r1 - r0 + 1)

    @staticmethod
    def _navy(img: np.ndarray) -> np.ndarray:
        """Kutucuğun 1 piksellik LACİVERT çerçevesi (oyunda RGB ≈ 2,35,66). Bu renk ne suda ne pencere
        çerçevesinde var; çerçevenin üst/alt çizgisi mavi çubuğun 2-4 piksel DIŞINDA durur (su dokusu,
        ışık oyunları ve balık oraya hiç değmez)."""
        b, g, r = (c.astype(np.int16) for c in cv2.split(img))
        return (b >= 38) & (b <= 135) & (r <= 45) & (b - r >= 30) & (g * 100 <= b * 80) & (g * 100 >= b * 25)

    def box_outline(self, frame: np.ndarray, bar) -> tuple[float, float] | None:
        """Kutucuğu lacivert çerçevesinin çubuğun hemen üstünde ve altında kalan yatay çizgilerinden bul.
        (sol, sağ) ya da None."""
        x, y, w, h = bar
        H, W = frame.shape[:2]
        band = max(7, int(round(0.28 * h)))
        need = max(10, int(0.03 * w))
        found: list[tuple[int, int, int]] = []          # (sol, sağ, bant: 0 üst / 1 alt)
        for k, (r0, r1) in enumerate(((y - band, y), (y + h, y + h + band))):
            r0, r1 = max(0, r0), min(H, r1)
            if r1 - r0 < 2:
                continue
            m = self._navy(frame[r0:r1, max(0, x): min(W, x + w)])
            for row in m:
                if row.sum() < need:
                    continue
                d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
                st, en = np.where(d == 1)[0], np.where(d == -1)[0]
                for a, b in zip(st, en):
                    if b - a >= need and b - a <= 0.4 * w:
                        found.append((int(a) + max(0, x), int(b) + max(0, x), k))
        if not found:
            return None
        # üstte ve altta aynı yerde bulunan çizgi en güveniliri; yoksa en uzun çizgi
        best, best_sc = None, -1.0
        for a, b, k in found:
            twin = any(k2 != k and abs(a2 - a) <= 3 and abs(b2 - b) <= 3 for a2, b2, k2 in found)
            sc = (b - a) * (2.0 if twin else 1.0)
            if sc > best_sc:
                best, best_sc = (a, b), sc
        a, b = best
        # çizginin uçları köşelerde 1 piksel içeride biter: dikey kenarlar çizginin bir dışında
        m = self._navy(frame[max(0, y): min(H, y + h), max(0, a - 3): min(W, b + 3)])
        cols = m.mean(0) if m.size else np.zeros(0)
        left, right = a - 1, b
        if len(cols):
            lo_ = min(6, len(cols))
            li = int(np.argmax(cols[:lo_]))
            ri = max(0, len(cols) - 6) + int(np.argmax(cols[max(0, len(cols) - 6):]))
            if cols[li] > 0.25:                         # balık kenarın önündeyse az görünür: yine en belirgini
                left = max(0, a - 3) + li
            if cols[ri] > 0.25:
                right = max(0, a - 3) + ri
        return float(left), float(right + 1)

    def window_rect(self, bar, shape) -> tuple[int, int, int, int]:
        """Tüm pencere (başlık + çubuk + ödül çarkı) — çubuğa göre yaklaşık."""
        x, y, w, h = bar
        H, W = shape[:2]
        x0, y0 = max(0, x - int(0.03 * w)), max(0, y - int(1.25 * h))
        x1, y1 = min(W, x + w + int(0.03 * w)), min(H, y + h + int(2.2 * h))
        return x0, y0, x1 - x0, y1 - y0

    def read(self, frame: np.ndarray, bar: tuple[int, int, int, int], ox: int = 0, oy: int = 0) -> BarRead:
        """Çubuktaki kutucuk ve balık. frame bir bölge kopyasıysa (ox, oy) o bölgenin kare içindeki yeri."""
        x, y, w, h = bar
        lx, ly = x - ox, y - oy
        mg = max(2, int(h * 0.12))
        ex = max(4, int(w * 0.012))           # çubuğun yuvarlak uçları (koyu çerçeve) hariç
        x0, x1 = lx + ex, lx + w - ex
        y0, y1 = ly + mg, ly + h - mg
        out = BarRead(bar)
        if x0 < 0 or y0 < 0 or x1 > frame.shape[1] or y1 > frame.shape[0] or x1 - x0 < 30 or y1 - y0 < 6:
            return out
        roi = frame[y0:y1, x0:x1]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        rh = roi.shape[0]
        # --- balık: koyu leke (kutucuğun ince koyu kenar çizgileri yatay açma ile silinir)
        dark = (gray < 62).astype(np.uint8)
        dk = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((1, 5), np.uint8))
        dk = cv2.morphologyEx(dk, cv2.MORPH_OPEN, np.ones((2, 1), np.uint8))
        n, _lab, st, _c = cv2.connectedComponentsWithStats(dk)
        best = None
        for i in range(1, n):
            bx, by, bw, bh, area = (int(v) for v in st[i])
            if area < max(12, 0.03 * rh * rh) or bh < 0.25 * rh or bw > 0.25 * (x1 - x0):
                continue
            if bx <= 0 or bx + bw >= (x1 - x0):           # çubuğun ucuna yapışık koyu kenar: balık değil
                continue
            if best is None or area > best[0]:
                best = (area, bx, bw)
        if best is not None:
            _a, bx, bw = best
            out.fish = (float(ox + x0 + bx), float(ox + x0 + bx + bw))
        # --- kutucuk 1) LACİVERT ÇERÇEVE (kesin; su dokusundan ve balıktan etkilenmez)
        if ox == 0 and oy == 0:
            try:
                ol = self.box_outline(frame, bar)
            except Exception:
                ol = None
            if ol is not None:
                out.box = ol
                out.box_how = "cerceve"
                return out
        # --- kutucuk 2) yedek: RENK TONU suyunkinden farklı sütunlar. Su dokusundaki parlak ışık desenleri üç kanalı
        #     birlikte artırır; kanal FARKLARI (R-B, G-B) bundan etkilenmez, kutucuğun sarımsı tonu ise belirgindir.
        valid = (gray >= 62) & (gray < 250)
        cnt = valid.sum(0).astype(np.float32)
        bb = roi[:, :, 0].astype(np.float32)
        f1 = ((roi[:, :, 2].astype(np.float32) - bb) * valid).sum(0) / np.maximum(1.0, cnt)
        f2 = ((roi[:, :, 1].astype(np.float32) - bb) * valid).sum(0) / np.maximum(1.0, cnt)
        ok = cnt >= 0.3 * rh
        if ok.sum() < 20:
            return out
        idx = np.arange(len(f1))
        f1 = np.interp(idx, idx[ok], f1[ok])
        f2 = np.interp(idx, idx[ok], f2[ok])
        m1, m2 = np.median(f1), np.median(f2)
        dist = np.hypot(f1 - m1, f2 - m2)
        mad = float(np.median(np.abs(dist - np.median(dist)))) + 1e-3
        thr = max(9.0, float(np.median(dist)) + 4.0 * mad)
        hi = dist > thr
        # kısa boşlukları kapat, en uzun koşuyu al
        runs, s = [], None
        for i_, v in enumerate(hi):
            if v and s is None:
                s = i_
            elif not v and s is not None:
                runs.append([s, i_ - 1])
                s = None
        if s is not None:
            runs.append([s, len(hi) - 1])
        merged: list[list[int]] = []
        for r in runs:
            if merged and r[0] - merged[-1][1] <= 6:
                merged[-1][1] = r[1]
            else:
                merged.append(r)
        cand = [r for r in merged if r[1] - r[0] + 1 >= max(10, 0.035 * (x1 - x0))]
        if cand:
            r = max(cand, key=lambda r: float(dist[r[0]: r[1] + 1].mean()) * (r[1] - r[0] + 1))
            out.box = (float(ox + x0 + r[0]), float(ox + x0 + r[1] + 1))
            out.box_how = "renk"
        return out


# ====================================================================== balık takibi
class FishTracker:
    """Balığın konum geçmişi; hız ve kutucuk ortasına varış zamanı."""

    def __init__(self):
        self.s: deque[tuple[float, float]] = deque(maxlen=60)

    def reset(self) -> None:
        self.s.clear()

    def add(self, t: float, x: float) -> None:
        if self.s and t <= self.s[-1][0]:
            return
        self.s.append((t, x))

    def last(self) -> tuple[float, float] | None:
        return self.s[-1] if self.s else None

    def velocity(self, window: float = 0.12) -> tuple[float, float, float] | None:
        """(hız px/sn, son zaman, son konum — doğruya oturtulmuş). Yön değişiminden sonraki örnekler kullanılır."""
        if len(self.s) < 3:
            return None
        pts = list(self.s)
        t_last = pts[-1][0]
        # son yön değişimi
        start = 0
        sgn = 0
        for i in range(len(pts) - 1, 0, -1):
            d = pts[i][1] - pts[i - 1][1]
            if abs(d) < 0.6:
                continue
            s_ = 1 if d > 0 else -1
            if sgn == 0:
                sgn = s_
            elif s_ != sgn:
                start = i
                break
        pts = [p for p in pts[start:] if t_last - p[0] <= window]
        if len(pts) < 3:
            return None
        t = np.array([p[0] for p in pts]) - t_last
        x = np.array([p[1] for p in pts])
        A = np.vstack([np.ones_like(t), t]).T
        (a, v), *_ = np.linalg.lstsq(A, x, rcond=None)
        return float(v), float(t_last), float(a)

    def fit(self, window: float = 0.15) -> tuple[float, float, float, float] | None:
        """Hareket modeli: (son zaman, konum, hız, ivme). Balık hızlanıp yavaşlıyorsa (ör. seri arttıkça ya da
        uçlara yaklaşırken) ivme de hesaba katılır; ivme belirgin değilse sabit hız varsayılır."""
        lin = self.velocity(window)
        if lin is None:
            return None
        v, tl, x0 = lin
        pts = list(self.s)
        # yön değişiminden sonraki, biraz daha uzun bir pencere (ivme için)
        start = 0
        sgn = 0
        for i in range(len(pts) - 1, 0, -1):
            d = pts[i][1] - pts[i - 1][1]
            if abs(d) < 0.6:
                continue
            s_ = 1 if d > 0 else -1
            if sgn == 0:
                sgn = s_
            elif s_ != sgn:
                start = i
                break
        pts = [p for p in pts[start:] if tl - p[0] <= max(window, 0.22)]
        if len(pts) < 7 or pts[-1][0] - pts[0][0] < 0.07:
            return tl, x0, v, 0.0
        t = np.array([p[0] for p in pts]) - tl
        x = np.array([p[1] for p in pts])
        A = np.vstack([np.ones_like(t), t, t * t]).T
        (c0, c1, c2), *_ = np.linalg.lstsq(A, x, rcond=None)
        A1 = A[:, :2]
        (l0, l1), *_ = np.linalg.lstsq(A1, x, rcond=None)
        r1 = float(np.sqrt(np.mean((A1 @ np.array([l0, l1]) - x) ** 2)))
        r2 = float(np.sqrt(np.mean((A @ np.array([c0, c1, c2]) - x) ** 2)))
        # ivme ancak doğruya göre belirgin iyileşme sağlıyorsa (gürültüye uydurmamak için)
        if r1 - r2 < 0.35 or r1 < 0.8:
            return tl, x0, v, 0.0
        return tl, float(c0), float(c1), float(2 * c2)


def _pos(fit, at: float) -> float:
    tl, x, v, a = fit
    dt = at - tl
    return x + v * dt + 0.5 * a * dt * dt


def _time_to(fit, target: float) -> float | None:
    """Modele göre balığın target'a varacağı an (mutlak). Varamayacaksa (önce dönecekse) None."""
    tl, x, v, a = fit
    d = target - x
    if abs(a) < 1e-6:
        if abs(v) < 1e-6:
            return None
        return tl + d / v
    disc = v * v + 2 * a * d
    if disc < 0:
        return None                                   # yavaşlayıp hedefe varmadan dönüyor
    r = np.sqrt(disc)
    roots = [(-v + r) / a, (-v - r) / a]
    ok = [t for t in roots if t >= -0.08]
    if not ok:
        return None
    t = min(ok)
    if v * (v + a * t) < 0:
        return None                                   # o ana kadar yön değiştirmiş olur
    return tl + float(t)


class TimingController:
    """Space'e NE ZAMAN basılacağına karar verir.

    Balığın hızı son ~0,12 sn'den ölçülür; balık kutucuğun ortasına varmadan 'gecikme' kadar önce basılır
    (tuşun oyuna ulaşması ve oyunun onu işlemesi zaman alır). Gecikme her turda balığın DURDUĞU yere
    bakılarak öğrenilir: balık hedeften ileride durduysa gecikme büyüktür, geride durduysa küçüktür."""

    LOCK_N = 6            # kutucuk bu kadar okumada aynı yerde görülünce SABİTLENİR
    WARMUP = 0.40         # pencere açıldıktan sonra en az bu kadar izle (balık hareket etmeye başlasın)
    MIN_TRAVEL = 0.6      # balık en az kutucuk yarı genişliğinin bu katı kadar yol almış olsun
    MIN_SPEED = 40.0      # px/sn — bundan yavaşsa "hareket etmiyor" sayılır

    def __init__(self, latency_s: float = 0.04):
        self.lat = float(latency_s)
        self.tr = FishTracker()
        self.boxes: deque[tuple[float, float]] = deque(maxlen=15)
        self.locked: tuple[float, float] | None = None
        self.t0: float | None = None
        self.x_first: float | None = None
        self.travel = 0.0
        self._xprev: float | None = None
        self._pre: tuple[float, float, float] | None = None      # basış anındaki (hız, zaman, konum)
        self.why = ""
        self.how = ""                     # kutucuk nasıl bulundu: "cerceve" / "renk"
        self._moved: list[tuple[float, float]] = []
        self.moves = 0                    # kutucuk tur içinde yer değiştirdi mi (kaç kez)

    def reset(self) -> None:
        self.tr.reset()
        self.boxes.clear()
        self.locked = None
        self.t0 = None
        self.travel = 0.0
        self._xprev = None
        self._pre = None
        self._moved = []
        self.moves = 0
        self.how = ""

    def update(self, t: float, rd: BarRead) -> None:
        if self.t0 is None:
            self.t0 = t
        exact = rd.box_how == "cerceve"
        if rd.box is not None and self.locked is None:
            # lacivert çerçeveden okunan kutucuk kesindir: 3 aynı okuma yeter; renkle okunan için 6
            if exact and self.boxes and self.how != "cerceve":
                self.boxes.clear()                 # renkle yapılmış eski (belki yanlış) okumaları at
            self.boxes.append(rd.box)
            self.how = rd.box_how or self.how
            n = 3 if exact else self.LOCK_N
            if len(self.boxes) >= n:
                a = np.array(self.boxes)[-n:]
                med = np.median(a, axis=0)
                # son okumaların çoğu medyana yakınsa kutucuk sabittir: kilitle (titreme biter)
                close = (np.abs(a - med).max(axis=1) <= max(2.5, 0.06 * (med[1] - med[0]))).sum()
                if close >= n - (0 if exact else 1):
                    self.locked = (float(med[0]), float(med[1]))
        elif rd.box is not None and self.locked is not None:
            # kilitliyken kutucuk YER DEĞİŞTİRİRSE (oyun kaydırırsa ya da ilk kilit renkle yanlış yapıldıysa)
            # birkaç tutarlı okumadan sonra yeni yere geçilir
            L = self.locked
            tol = max(3.0, 0.08 * (L[1] - L[0]))
            if abs(rd.box[0] - L[0]) <= tol and abs(rd.box[1] - L[1]) <= tol:
                self._moved = []
            elif exact or self.how != "cerceve":
                if self._moved and (abs(rd.box[0] - self._moved[-1][0]) > tol or
                                    abs(rd.box[1] - self._moved[-1][1]) > tol):
                    self._moved = []
                self._moved.append(rd.box)
                if len(self._moved) >= (3 if exact else 6):
                    a = np.array(self._moved)
                    self.locked = (float(np.median(a[:, 0])), float(np.median(a[:, 1])))
                    self.how = rd.box_how or self.how
                    self._moved = []
                    self.moves += 1
        if rd.fish is not None:
            x = rd.fish_x
            if self._xprev is not None:
                self.travel += abs(x - self._xprev)
            self._xprev = x
            self.tr.add(t, x)

    @property
    def box(self) -> tuple[float, float] | None:
        if self.locked is not None:
            return self.locked
        if not self.boxes:
            return None
        a = np.array(self.boxes)
        return float(np.median(a[:, 0])), float(np.median(a[:, 1]))

    def frame_dt(self) -> float:
        s = list(self.tr.s)[-8:]
        if len(s) < 3:
            return 0.02
        return float(np.median(np.diff([p[0] for p in s])))

    def predict(self, at: float) -> float | None:
        f = self.tr.fit()
        if f is None:
            return None
        return _pos(f, at)

    def decide(self, now: float) -> float | None:
        """None: henüz değil. Sayı: basmadan önce beklenecek süre (sn; 0 = hemen bas).

        Erken basmayı önleyen koşullar: kutucuk sabitlenmiş olmalı, pencere en az WARMUP süredir izleniyor
        olmalı, balık hareket etmeye başlamış (yol almış ve hızı ölçülebilir) ve ortaya DOĞRU geliyor olmalı."""
        box = self.locked
        vel = self.tr.velocity(window=0.15)
        if box is None:
            self.why = "kutucuk sabitleniyor"
            return None
        if self.t0 is None or now - self.t0 < self.WARMUP:
            self.why = "izleniyor"
            return None
        if vel is None:
            self.why = "hiz olculuyor"
            return None
        c, half = (box[0] + box[1]) / 2, (box[1] - box[0]) / 2
        v, tl, xl = vel
        if self.travel < self.MIN_TRAVEL * half or abs(v) < self.MIN_SPEED:
            self.why = "balik henuz hareket etmiyor"
            return None
        if (c - xl) * v < -0.15 * half:
            self.why = "balik ortadan uzaklasiyor"
            return None
        self.why = "bekleniyor"
        fit = self.tr.fit(window=0.15) or (tl, xl, v, 0.0)
        t_c = _time_to(fit, c)                             # balığın ortada olacağı an
        if t_c is None:
            return None
        wait = t_c - self.lat - now
        dt = self.frame_dt()
        if wait > dt * 1.3:
            return None                                    # bir sonraki karede de yetişiriz
        land = _pos(fit, now + max(0.0, wait) + self.lat)
        if abs(land - c) > 0.55 * half:
            return None                                    # ortayı kaçırdık: dönüşünü bekle
        self._pre = fit
        return max(0.0, wait)

    def stop_x(self, after: list[tuple[float, float]]) -> float | None:
        """Basıştan sonraki örneklerde balık durduysa durduğu yer."""
        if len(after) < 3:
            return None
        for i in range(len(after) - 3, -1, -1):
            seg = after[i:]
            xs = [p[1] for p in seg]
            if max(xs) - min(xs) <= 1.5 and seg[-1][0] - seg[0][0] >= 0.04:
                return float(np.mean(xs))
        return None

    def learn(self, t_press: float, stop_x: float) -> float | None:
        """Gecikmeyi balığın durduğu yerden ölç ve güncelle. Ölçülen gecikmeyi (sn) döner."""
        if self._pre is None:
            return None
        if abs(self._pre[2]) < 60:
            return None
        t_at = _time_to(self._pre, stop_x)
        if t_at is None:
            return None
        meas = t_at - t_press
        if not (-0.02 <= meas <= 0.35):
            return None
        self.lat = max(0.0, 0.65 * self.lat + 0.35 * meas)
        return meas


# ====================================================================== kafadaki balık işareti
@dataclass
class BiteHit:
    box: tuple[int, int, int, int]        # kare koordinatı (x, y, w, h)
    score: float
    how: str                               # "resim" | "değişim"
    crop: np.ndarray | None = None
    scale: float | None = None


@dataclass
class _Cand:
    box: tuple[int, int, int, int]
    n: int = 1
    crop: np.ndarray | None = None


class BiteWatcher:
    """Karakterin kafasında çıkan balık işaretini bekler.

    • assets/olta/isaret/*.png resimleri varsa onlarla arar (en güvenilir yol).
    • Yoksa (ilk kullanım) kafa bölgesindeki ANİ ve SABİT duran yeni bir şekli arar. İşaret doğrulanınca
      (Space'e basınca zamanlama penceresi açıldıysa) resmi kaydedilir; sonraki turlarda resimle aranır.
      Kafanın ekrandaki yeri de öğrenilir ve arama oraya daraltılır."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.templates: list[tuple[np.ndarray, np.ndarray | None, str]] = []
        self._scale: float | None = None
        self._ema: np.ndarray | None = None
        self._cand: _Cand | None = None
        self._reg = (0, 0, 1, 1)
        self._anchor = (0.0, 0.0)
        self._t_reset = 0.0
        self.foreign: list[tuple[int, int, int, int]] = []    # BAŞKA oyuncuların işaretleri (bu tur)
        self.seen: list[tuple[int, int, int, int]] = []       # son karede görülen tüm işaretler (çizim için)
        self.reload()

    def reload(self) -> None:
        SIGN_DIR.mkdir(parents=True, exist_ok=True)
        self.templates = []
        for p in sorted(SIGN_DIR.glob("*.png")):
            im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
            if im is None or im.shape[0] < 6 or im.shape[1] < 6:
                continue
            mask = None
            if im.ndim == 3 and im.shape[2] == 4:
                mask = (im[:, :, 3] > 40).astype(np.uint8) * 255
                im = im[:, :, :3]
            elif im.ndim == 2:
                im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
            self.templates.append((im, mask, p.name))

    # ---------------------------------------------------------------- arama bölgesi
    def user_area(self, shape) -> tuple[int, int, int, int] | None:
        """Kullanıcının seçtiği 'kendi karakterimin işaret alanı' (client ortasına göre saklanır)."""
        a = self.cfg["bite_area"]
        if not isinstance(a, dict):
            return None
        H, W = shape[:2]
        x0 = int(W / 2 + int(a.get("dx", 0)))
        y0 = int(H / 2 + int(a.get("dy", 0)))
        x1, y1 = x0 + int(a.get("w", 0)), y0 + int(a.get("h", 0))
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        return (x0, y0, x1, y1) if x1 - x0 >= 8 and y1 - y0 >= 8 else None

    def region(self, shape) -> tuple[int, int, int, int]:
        H, W = shape[:2]
        ua = self.user_area(shape)
        if ua is not None:                                   # en güvenilir: kullanıcı kendi kafasını seçti
            self._anchor = ((ua[0] + ua[2]) / 2, (ua[1] + ua[3]) / 2)
            return ua
        return self.auto_region(shape)

    def auto_region(self, shape) -> tuple[int, int, int, int]:
        """Kullanıcı alan seçmediyse bakılan yer (öğrenilen kafa konumu ya da ekranın ortası)."""
        H, W = shape[:2]
        pos = self.cfg["bite_pos"]
        if isinstance(pos, (list, tuple)) and len(pos) == 2:  # bot öğrendi
            cx, cy = float(pos[0]) * W, float(pos[1]) * H
            x0, x1 = int(cx - 0.07 * W), int(cx + 0.07 * W)
            y0, y1 = int(cy - 0.09 * H), int(cy + 0.09 * H)
            self._anchor = (cx, cy)
        else:      # karakter ekranın ORTASINDA; işaret kafasının üstünde. Yandakiler kenarlarda kalır.
            x0, x1 = int(0.38 * W), int(0.62 * W)
            y0, y1 = int(0.06 * H), int(0.52 * H)
            self._anchor = (W / 2, 0.30 * H)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W, x1), min(H, y1)
        return x0, y0, x1, y1

    def reset(self) -> None:
        self._ema = None
        self._cand = None
        self._t_reset = time.time()
        self.foreign = []
        self.seen = []

    def _is_foreign(self, box) -> bool:
        cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
        tol = getattr(self, "_tol_x", None)
        if tol is not None and abs(cx - self._anchor[0]) > tol:
            return True                                  # kendi kafamızın üstünde değil
        return any(abs(cx - (f[0] + f[2] / 2)) < max(f[2], 12) and abs(cy - (f[1] + f[3] / 2)) < max(f[3], 12)
                   for f in self.foreign)

    def _dist(self, box) -> float:
        ax, ay = self._anchor
        return float(np.hypot(box[0] + box[2] / 2 - ax, (box[1] + box[3] / 2 - ay) * 0.6))

    # ---------------------------------------------------------------- kontrol
    def check(self, frame: np.ndarray | None) -> BiteHit | None:
        if frame is None or frame.size == 0:
            return None
        x0, y0, x1, y1 = self._reg = self.region(frame.shape)
        W = frame.shape[1]
        # alan seçilmediyse: kamera kendi karakterimizi yatayda ORTADA tutar; yanımızdaki oyuncuların
        # işaretleri ortadan uzakta kalır ve kabul edilmez
        if self.user_area(frame.shape) is not None:
            self._tol_x = None
        else:
            self._tol_x = 0.045 * W if isinstance(self.cfg["bite_pos"], (list, tuple)) else 0.05 * W
        roi = frame[y0:y1, x0:x1]
        if roi.size == 0:
            return None
        if self.templates:
            hit = self._by_template(roi, x0, y0)
            if hit is not None:
                return hit
            if not bool(self.cfg["bite_change"]):
                return None
        return self._by_change(roi, x0, y0, strict=bool(self.templates), H=frame.shape[0])

    # işaret resmi oyundakinden farklı boyutta kırpılmış olabilir: ilk bulunuşta geniş ölçek aralığı
    # taranır, bulunan ölçek kaydedilir (bite_scale) ve sonra sadece o ölçek kullanılır (hızlı)
    WIDE = tuple(round(0.30 * 1.10 ** i, 3) for i in range(16))          # 0.30 … 1.25

    def _scales(self) -> tuple[float, ...]:
        if self._scale is not None:
            return (self._scale,)
        s = self.cfg["bite_scale"]
        if s:
            s = float(s)
            return (s, round(s * 0.94, 3), round(s * 1.06, 3))
        return self.WIDE

    def _by_template(self, roi, ox, oy) -> BiteHit | None:
        scales = self._scales()
        if len(scales) > 3:                       # ölçek henüz bilinmiyor: geniş taramayı seyrek yap
            now = time.time()
            if now - getattr(self, "_t_wide", 0.0) < 0.25:
                return None
            self._t_wide = now
        thr = float(self.cfg["bite_threshold"])
        rg = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        cands: list[tuple[float, tuple[int, int, int, int], float, int]] = []
        small_cache: dict[float, np.ndarray] = {}
        for ti, (im, mask, _n) in enumerate(self.templates):
            ig = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            for sc in scales:
                th_full = im.shape[0] * sc
                d = min(1.0, 30.0 / max(1.0, th_full))          # işaret ~30 px boyunda aransın (hızlı)
                d = round(d, 2)
                if d not in small_cache:
                    small_cache[d] = rg if d >= 0.999 else cv2.resize(rg, None, fx=d, fy=d,
                                                                      interpolation=cv2.INTER_AREA)
                rs = small_cache[d]
                f = sc * d
                t = cv2.resize(ig, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
                m = None if mask is None else cv2.resize(mask, (t.shape[1], t.shape[0]),
                                                        interpolation=cv2.INTER_NEAREST)
                if t.shape[0] < 6 or t.shape[1] < 6 or t.shape[0] >= rs.shape[0] or t.shape[1] >= rs.shape[1]:
                    continue
                r = cv2.matchTemplate(rs, t, cv2.TM_CCOEFF_NORMED, mask=m) if m is not None else \
                    cv2.matchTemplate(rs, t, cv2.TM_CCOEFF_NORMED)
                r = np.nan_to_num(r, nan=-1.0, posinf=-1.0, neginf=-1.0)
                th, tw = t.shape[:2]
                for _ in range(6):                  # birden fazla oyuncu: eşiğe yakın TÜM adaylar
                    _, v, _, (x, y) = cv2.minMaxLoc(r)
                    if v < thr - 0.10:
                        break
                    box = (int(ox + x / d), int(oy + y / d), int(round(im.shape[1] * sc)), int(round(im.shape[0] * sc)))
                    cands.append((float(v), box, sc, ti))
                    r[max(0, y - th // 2): y + th // 2 + 1, max(0, x - tw // 2): x + tw // 2 + 1] = -1.0
        # adayları tam çözünürlükte doğrula (kesin konum ve benzerlik)
        peaks: list[tuple[float, tuple[int, int, int, int], float, np.ndarray]] = []
        for v0, box, sc, ti in sorted(cands, key=lambda c: -c[0])[:8]:
            if any(_iou(box, p[1]) > 0.3 for p in peaks):
                continue
            ref = self._refine(roi, ox, oy, box, sc, ti)
            if ref is not None and ref[0] >= thr:
                peaks.append(ref)
        self.seen = [p[1] for p in peaks]
        if not peaks:
            return None
        if time.time() - self._t_reset < 0.5:
            # olta yeni atıldı: bizim balığımız bu kadar çabuk gelmez -> şu an görünenler BAŞKALARININ
            self.foreign.extend(p[1] for p in peaks if not any(_iou(p[1], f) > 0.3 for f in self.foreign))
            return None
        mine = [p for p in peaks if not self._is_foreign(p[1])]
        if not mine:
            return None
        v, box, sc, crop = min(mine, key=lambda p: self._dist(p[1]))      # kendi kafamıza en yakın olan
        self._scale = sc
        return BiteHit(box, v, "resim", crop.copy(), scale=sc)

    def _refine(self, roi, ox, oy, box, sc, ti):
        im, mask, _n = self.templates[ti]
        t = cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_LINEAR)
        m = None if mask is None else cv2.resize(mask, (t.shape[1], t.shape[0]), interpolation=cv2.INTER_NEAREST)
        th, tw = t.shape[:2]
        pad = max(4, int(0.12 * max(th, tw)))
        x, y = box[0] - ox, box[1] - oy
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(roi.shape[1], x + tw + pad), min(roi.shape[0], y + th + pad)
        win = roi[y0:y1, x0:x1]
        if win.shape[0] < th or win.shape[1] < tw:
            return None
        r = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED, mask=m) if m is not None else \
            cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
        r = np.nan_to_num(r, nan=-1.0, posinf=-1.0, neginf=-1.0)
        _, v, _, (bx, by) = cv2.minMaxLoc(r)
        X, Y = x0 + bx, y0 + by
        return float(v), (ox + X, oy + Y, tw, th), sc, roi[Y:Y + th, X:X + tw]

    def _by_change(self, roi, ox, oy, strict: bool, H: int) -> BiteHit | None:
        g = cv2.GaussianBlur(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), (3, 3), 0).astype(np.float32)
        if self._ema is None or self._ema.shape != g.shape:
            self._ema = g.copy()
            self._cand = None
            return None
        d = np.abs(g - self._ema)
        T = 45.0 if strict else 38.0
        mask = (d > T).astype(np.uint8)
        # arka plan yavaşça uyum sağlar; yeni çıkan sabit şekil hemen emilmez
        a = np.where(mask > 0, 0.02, 0.15).astype(np.float32)
        self._ema += a * (g - self._ema)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, _lab, st, _c = cv2.connectedComponentsWithStats(mask)
        lo, hi = 0.018 * H, 0.10 * H          # işaretin boyu: ekranın ~%2-10'u
        cands = []
        for i in range(1, n):
            x, y, w, h, area = (int(v) for v in st[i])
            if not (lo <= w <= hi * 1.6 and lo <= h <= hi) or area < 0.35 * w * h:
                continue
            box = (ox + x, oy + y, w, h)
            if self._is_foreign(box):
                continue
            cands.append((self._dist(box), x, y, w, h, float(d[y:y + h, x:x + w].mean())))
        if not cands:
            self._cand = None
            return None
        _d, x, y, w, h, contrast = min(cands)          # kendi kafamıza en yakın olan
        box = (ox + x, oy + y, w, h)
        self.seen = [(ox + c[1], oy + c[2], c[3], c[4]) for c in cands]
        crop = roi[max(0, y - 3): y + h + 3, max(0, x - 3): x + w + 3].copy()
        c = self._cand
        # işaret YERİNDE durur: kayan su parıltısı / geçen oyuncu her karede yer değiştirir
        if c is not None and _steady(c.box, box) and _same_look(c.crop, crop):
            c.n += 1
            c.box = box
            c.crop = crop
        else:
            self._cand = c = _Cand(box, 1, crop)
        need = 4 if strict else 3
        if c.n >= need:
            self._cand = None
            return BiteHit(box, contrast, "değişim", crop)
        return None

    # ---------------------------------------------------------------- öğrenme
    def confirm(self, frame_shape, hit: BiteHit) -> str | None:
        """İşaret gerçekten balıkmış (pencere açıldı): kafanın yerini öğren, resmi yoksa kaydet."""
        H, W = frame_shape[:2]
        x, y, w, h = hit.box
        cx, cy = (x + w / 2) / W, (y + h / 2) / H
        if self.user_area(frame_shape) is not None:
            cx, cy = None, None                     # kullanıcı alanı seçmiş: konum öğrenmeye gerek yok
        pos = self.cfg["bite_pos"]
        if cx is not None:
            if isinstance(pos, (list, tuple)) and len(pos) == 2:
                cx, cy = 0.7 * float(pos[0]) + 0.3 * cx, 0.7 * float(pos[1]) + 0.3 * cy
            self.cfg.set("bite_pos", [round(cx, 4), round(cy, 4)])
        if hit.how == "resim" and hit.scale:
            self.cfg.set("bite_scale", round(float(hit.scale), 3))      # bulunan ölçeği hatırla
        saved = None
        learned = [t for t in self.templates if t[2].startswith("ogrenilen")]
        if hit.how == "değişim" and hit.crop is not None and len(learned) < 4 and hit.crop.size > 0:
            SIGN_DIR.mkdir(parents=True, exist_ok=True)
            k = 1
            while (SIGN_DIR / f"ogrenilen_{k}.png").exists():
                k += 1
            p = SIGN_DIR / f"ogrenilen_{k}.png"
            cv2.imwrite(str(p), hit.crop)
            self.templates.append((hit.crop.copy(), None, p.name))
            saved = str(p)
        return saved


def _steady(a, b) -> bool:
    """İki kutu aynı yerde mi (merkez kayması ve boy değişimi küçük)?"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    s = max(aw, ah, bw, bh)
    d = float(np.hypot(ax + aw / 2 - bx - bw / 2, ay + ah / 2 - by - bh / 2))
    return d <= max(3.0, 0.12 * s) and 0.75 <= (bw * bh) / max(1.0, aw * ah) <= 1.33


def _same_look(a: np.ndarray | None, b: np.ndarray | None) -> bool:
    if a is None or b is None or a.size == 0 or b.size == 0:
        return False
    b2 = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    return float(np.abs(a.astype(np.int16) - b2.astype(np.int16)).mean()) < 22.0


def _iou(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


# ====================================================================== canlı görüntü çizimi
PURPLE = (255, 40, 200)


def _txt(img, text, org, scale=0.5, color=(255, 255, 255)):
    """Okunaklı yazı: koyu zemin kutusu + yazı (OpenCV Türkçe/Almanca harf çizemez: sadeleştirilir)."""
    from .i18n import ascii_name
    text = ascii_name(text)
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    x, y = int(org[0]), int(org[1])
    x0, y0 = max(0, x - 3), max(0, y - th - 4)
    x1, y1 = min(img.shape[1], x + tw + 3), min(img.shape[0], y + base + 2)
    if x1 > x0 and y1 > y0:
        img[y0:y1, x0:x1] = (img[y0:y1, x0:x1] * 0.25).astype(img.dtype)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)


def draw_bar(frame: np.ndarray, rd: BarRead | None, lat_ms: float, pred_x: float | None = None,
             press_x: float | None = None, note: str = "", box: tuple[float, float] | None = None,
             stop_x: float | None = None) -> np.ndarray:
    """Zamanlama penceresi (canlı görüntü): kutucuk YEŞİL çerçeve, tam ortası KALIN MOR nokta (hedef),
    siyah balık KIRMIZI çerçeve, balığın tuş oyuna ulaştığında olacağı yer SARI nokta. Basınca balığın
    durduğu yer ve hedefe uzaklığı yazılır."""
    if rd is None:
        out = frame.copy()
        _txt(out, note or T("pencere yok"), (8, 20))
        return out
    x, y, w, h = rd.bar
    H, W = frame.shape[:2]
    x0, y0 = max(0, x - 10), max(0, y - int(1.3 * h))
    x1, y1 = min(W, x + w + 10), min(H, y + h + int(0.3 * h))        # alttaki ödül çarkı görünmez
    out = frame[y0:y1, x0:x1].copy()
    # okunaklı olsun diye büyüt; altına bilgi şeridi ekle
    k = 2 if out.shape[1] < 700 else 1
    if k > 1:
        out = cv2.resize(out, None, fx=k, fy=k, interpolation=cv2.INTER_LINEAR)
    out = cv2.copyMakeBorder(out, 0, 34, 0, 0, cv2.BORDER_CONSTANT, value=(24, 24, 24))

    def X(v):
        return int(round((v - x0) * k))
    top, bot = (y - y0) * k, (y + h - y0) * k
    mid = (top + bot) // 2
    bx = box if box is not None else rd.box
    if bx is not None:
        cv2.rectangle(out, (X(bx[0]), top - 3), (X(bx[1]), bot + 3), (60, 230, 60), 2)
    if rd.fish is not None:
        cv2.rectangle(out, (X(rd.fish[0]) - 2, top + 3), (X(rd.fish[1]) + 2, bot - 3), (40, 40, 255), 2)
        _txt(out, T("balik"), (X(rd.fish[0]), top - 8), 0.45, (120, 120, 255))
    if pred_x is not None:
        cv2.circle(out, (X(pred_x), bot + 10), 5, (0, 220, 255), -1, cv2.LINE_AA)
    if bx is not None:
        c = X((bx[0] + bx[1]) / 2)
        cv2.circle(out, (c, mid), 10, (0, 0, 0), -1, cv2.LINE_AA)
        cv2.circle(out, (c, mid), 8, PURPLE, -1, cv2.LINE_AA)        # HEDEF: kutucuğun tam ortası
        cv2.line(out, (c, top - 10), (c, top - 2), PURPLE, 2)
        cv2.line(out, (c, bot + 2), (c, bot + 10), PURPLE, 2)
    if stop_x is not None:
        cv2.drawMarker(out, (X(stop_x), mid), (255, 255, 255), cv2.MARKER_TILTED_CROSS, 18, 2)
    if press_x is not None and stop_x is None:
        cv2.drawMarker(out, (X(press_x), bot + 12), PURPLE, cv2.MARKER_TRIANGLE_UP, 14, 2)
    line = T("gecikme payi {ms} ms").format(ms=f"{lat_ms:.0f}")
    if bx is not None and rd.fish is not None and stop_x is None:
        line += "   " + T("balik hedefe {d} px").format(d=f"{rd.fish_x - (bx[0] + bx[1]) / 2:+.0f}")
    _txt(out, line, (10, out.shape[0] - 11), 0.6)
    if note:
        good = T("ISABET") in note
        _txt(out, note, (out.shape[1] // 2, out.shape[0] - 11), 0.65,
             (120, 255, 120) if good else ((120, 120, 255) if T("ISKA") in note else (255, 255, 255)))
    return out


def draw_bite(frame: np.ndarray, reg, hit: BiteHit | None, note: str = "", anchor=None,
              seen=None, foreign=None) -> np.ndarray:
    """Balık beklerken: arama alanı MAVİ, kendi kafamız MOR artı, başka oyuncuların işaretleri GRİ (yok
    sayılır), bizim işaretimiz YEŞİL."""
    x0, y0, x1, y1 = reg
    H, W = frame.shape[:2]
    pad = 60
    X0, Y0 = max(0, x0 - pad), max(0, y0 - pad)
    X1, Y1 = min(W, x1 + pad), min(H, y1 + pad)
    out = frame[Y0:Y1, X0:X1].copy()
    cv2.rectangle(out, (x0 - X0, y0 - Y0), (x1 - X0 - 1, y1 - Y0 - 1), (255, 160, 40), 2)
    others: list = []
    for b in list(foreign or []) + list(seen or []):
        if (hit is None or _iou(b, hit.box) < 0.3) and not any(_iou(b, o) > 0.3 for o in others):
            others.append(b)
    for b in others:                       # başka oyuncuların işaretleri: yok sayılır
        bx, by, bw, bh = b
        cv2.rectangle(out, (bx - X0, by - Y0), (bx - X0 + bw, by - Y0 + bh), (150, 150, 150), 1)
        cv2.line(out, (bx - X0, by - Y0), (bx - X0 + bw, by - Y0 + bh), (150, 150, 150), 1)
        _txt(out, T("baskasi"), (bx - X0, by - Y0 - 5), 0.4, (200, 200, 200))
    if anchor is not None:
        cv2.drawMarker(out, (int(anchor[0]) - X0, int(anchor[1]) - Y0), PURPLE, cv2.MARKER_CROSS, 16, 2)
    if hit is not None:
        x, y, w, h = hit.box
        cv2.rectangle(out, (x - X0 - 3, y - Y0 - 3), (x - X0 + w + 3, y - Y0 + h + 3), (60, 230, 60), 2)
        _txt(out, T("BENIM ISARETIM"), (x - X0 - 10, y - Y0 - 8), 0.45, (120, 255, 120))
    if note:
        _txt(out, note, (6, 18))
    return out
