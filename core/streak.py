"""Zamanlama penceresinin sağ üstündeki "Seri: N" sayacı — turun GERÇEK sonucunu oyunun kendisinden öğrenmek için.

Isabette seri bir artar, ıskada sıfırlanır (ya da sıfırda kalır). Bot balığın kutucukta durup durmadığına
kendi ölçümüyle karar verir; kutucuk yanlış algılanırsa bu karar da yanlış olur. Seri sayacı oyunun verdiği
kesin cevaptır: bot her pencerede sayının RESMİNİ okur ve bir önceki pencereyle karşılaştırır:

  • sayı değişmedi        → ıska (seri 0'da kaldı; o resim "0" olarak öğrenilir)
  • sayı "0"a döndü       → ıska (seri sıfırlandı)
  • sayı arttı / 0'dan çıktı → isabet

Rakam tanıma gerekmez: oyunun yazı tipi sabit olduğu için aynı sayı her seferinde piksel piksel aynı çizilir.
Oyun sayıyı pencere açıkken (Space'ten hemen sonra) güncelliyorsa sonuç aynı turda, ancak bir sonraki
pencerede güncelliyorsa bir tur sonra kesinleşir; bot bunu kendisi anlar.
"""
from __future__ import annotations

import cv2
import numpy as np


def read_glyph(frame: np.ndarray | None, bar) -> np.ndarray | None:
    """Seri sayısının (en sağdaki kelime) siyah-beyaz resmi; okunamazsa None."""
    if frame is None or bar is None:
        return None
    x, y, w, h = bar
    H, W = frame.shape[:2]
    y0, y1 = max(0, y - int(1.3 * h)), max(0, y - 2)
    x0, x1 = max(0, x + int(0.55 * w)), min(W, x + w + 4)
    if y1 - y0 < 8 or x1 - x0 < 20:
        return None
    reg = frame[y0:y1, x0:x1]
    b, g, r = (c.astype(np.int16) for c in cv2.split(reg))
    m = (r > 150) & (g > 120) & (r - b > 25)            # krem rengi yazı
    cols = np.where(m.any(0))[0]
    if len(cols) == 0:
        return None
    # boşluklarla gruplara ayır; son grup sayıdır ("Seri:" ile sayı arasında geniş boşluk var)
    groups, s_, prev = [], int(cols[0]), int(cols[0])
    for c in cols[1:]:
        c = int(c)
        if c - prev > 3:
            groups.append((s_, prev))
            s_ = c
        prev = c
    groups.append((s_, prev))
    if len(groups) < 2:                                  # "Seri:" de görünmeli: yoksa başka bir şey
        return None
    a, e = groups[-1]
    g_ = m[:, a: e + 1]
    rows = np.where(g_.any(1))[0]
    if len(rows) == 0:
        return None
    g_ = g_[rows[0]: rows[-1] + 1]
    if not (5 <= g_.shape[0] <= 2 * h) or g_.shape[1] > 0.15 * w or g_.sum() < 6:
        return None
    return g_.astype(np.uint8)


def same(a: np.ndarray | None, b: np.ndarray | None) -> bool:
    if a is None or b is None:
        return False
    if a.shape != b.shape:
        return False
    return float((a == b).mean()) >= 0.95


def stable(glyphs: list) -> np.ndarray | None:
    """Birkaç okumadan en çok tekrarlananı (tek tük okuma hatası sonucu bozmasın)."""
    gl = [g for g in glyphs if g is not None]
    if not gl:
        return None
    best, best_n = None, 0
    for g in gl:
        n = sum(1 for o in gl if same(o, g))
        if n > best_n:
            best, best_n = g, n
    return best if best_n >= max(1, len(gl) // 2) else None


class StreakJudge:
    """Seri sayacından tur sonucunu çıkarır (bkz. modül açıklaması).

    "0" resmi şöyle öğrenilir: (1) sayı bir turda hiç değişmediyse o sayı 0'dır (isabette mutlaka artar);
    (2) bir sayıya İKİ FARKLI sayıdan geçildiyse o sayı 0'dır (her N+1'in tek bir öncesi vardır: N; 0'a ise
    her sayıdan dönülür); (3) basamak sayısı azaldıysa yeni sayı 0'dır. "0" öğrenilene kadar belirsiz kalan
    turlar saklanır ve öğrenilince geriye dönük düzeltilir."""

    def __init__(self):
        self.zero: np.ndarray | None = None       # "0" sayısının resmi (öğrenilir)
        self.inwin: bool | None = None            # oyun sayıyı pencere açıkken mi güncelliyor
        self.pending: tuple | None = None         # (tur no, pencere başındaki sayı) — sonraki pencerede kesinleşir
        self.unresolved: list[tuple[int, np.ndarray, np.ndarray]] = []   # (tur no, önce, sonra)
        self.preds: list[tuple[np.ndarray, np.ndarray]] = []             # görülen değişimler (önce, sonra)

    def _learn_zero(self, g: np.ndarray, out: list) -> None:
        if self.zero is not None or g is None:
            return
        self.zero = g
        for rid, before, after in self.unresolved:          # bekleyen turlar artık belli
            out.append((rid, not same(after, self.zero)))
        self.unresolved = []

    def _change(self, rid: int, before: np.ndarray, after: np.ndarray, out: list) -> None:
        """Sayı değişti: isabet mi ıska mı? Sonucu out'a ekler (belli değilse saklar)."""
        if self.zero is None:
            # bu sayıya daha önce BAŞKA bir sayıdan geçildiyse bu sayı 0'dır
            if any(same(a, after) and not same(b, before) for b, a in self.preds):
                self._learn_zero(after, out)
            elif after.shape[1] + 3 <= before.shape[1]:
                self._learn_zero(after, out)                 # basamak azaldı: sıfırlandı
            self.preds = (self.preds + [(before, after)])[-40:]
        if self.zero is not None:
            out.append((rid, not same(after, self.zero)))     # 0'a döndüyse ıska, değilse arttı: isabet
            return
        if after.shape[1] >= before.shape[1] + 3:
            out.append((rid, True))                          # basamak arttı (9 → 10)
            return
        self.unresolved = (self.unresolved + [(rid, before, after)])[-30:]

    def window_start(self, g: np.ndarray | None) -> list[tuple[int, bool]]:
        """Yeni pencere açıldı, sayı g. Kesinleşen [(tur no, isabet)] listesi döner."""
        out: list[tuple[int, bool]] = []
        if self.pending is not None and g is not None:
            rid, before = self.pending
            if same(g, before):
                self._learn_zero(before, out)                # isabette sayı mutlaka değişir: değişmediyse 0'dı
                out.append((rid, False))
            else:
                self.inwin = False                           # pencere içinde değişmedi ama arada değişti
                self._change(rid, before, g, out)
        self.pending = None
        return out

    def window_end(self, rid: int, start: np.ndarray | None, end: np.ndarray | None) -> list[tuple[int, bool]]:
        """Pencere kapanırken. Kesinleşen [(tur no, isabet)] listesi döner (bu tur belli değilse içinde yoktur;
        gerekirse sonraki pencerede belli olur)."""
        out: list[tuple[int, bool]] = []
        if start is None or end is None:
            self.pending = None
            return out
        if not same(start, end):
            self.inwin = True
            self._change(rid, start, end, out)
            return out
        if self.inwin:
            self._learn_zero(start, out)
            out.append((rid, False))                         # oyun pencerede günceller ve sayı değişmedi: ıska
            return out
        self.pending = (rid, start)                          # bir sonraki pencerede belli olur
        return out
