"""Ödül çarkını okur: çark durunca işaretin (▲) gösterdiği kutudaki eşyayı ve altındaki ADEDİ bulur.

• Eşya: assets/olta/odul/<ad>.png resimleriyle karşılaştırılır (ör. mini_balik.png, istiridye.png).
  Tanınmayan bir eşya çıkarsa resmi oraya bilinmeyen_N.png olarak kaydedilir; dosyanın adını eşyanın adıyla
  değiştirirsen (ör. inci.png) bir dahaki sefere o adla sayılır.
• Adet: kutunun sağ altındaki koyu kutucuktaki rakamlar. Oyunun rakamları 7 parçalı (dijital saat gibi) çizildiği
  için her rakam, parçalarının dolu/boş olmasına bakılarak okunur — resim gerekmez, 0-9'un hepsi tanınır.
"""
from __future__ import annotations

from .paths import ASSETS, DATA

import json
import re
import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

ITEM_DIR = ASSETS / "olta" / "odul"
TOTALS = DATA / "odul_toplam.json"   # tüm zamanların toplamı (küçük)
_tot_lock = threading.Lock()


def load_totals() -> dict:
    """{eşya: {"adet": toplam, "kez": kaç kez}} — tüm zamanlar."""
    try:
        return json.loads(TOTALS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def add_total(key: str, n: int) -> None:
    with _tot_lock:
        d = load_totals()
        e = d.setdefault(key, {"adet": 0, "kez": 0})
        e["adet"] = int(e.get("adet", 0)) + int(n)
        e["kez"] = int(e.get("kez", 0)) + 1
        try:
            TOTALS.parent.mkdir(parents=True, exist_ok=True)
            TOTALS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass


def reset_totals() -> None:
    with _tot_lock:
        try:
            TOTALS.unlink()
        except Exception:
            pass

# bilinen eşyaların dillerdeki adları (dosya adı -> tr / en / de)
NAMES = {
    "mini_balik": ("Mini balık", "Minnow", "Elritze"),
    "istiridye": ("İstiridye", "Oyster", "Auster"),
    "yuzuk": ("Yüzük", "Ring", "Ring"),
}

# 7 parça: üst, sol üst, sağ üst, orta, sol alt, sağ alt, alt
_SEG = {
    0: (1, 1, 1, 0, 1, 1, 1), 1: (0, 0, 1, 0, 0, 1, 0), 2: (1, 0, 1, 1, 1, 0, 1), 3: (1, 0, 1, 1, 0, 1, 1),
    4: (0, 1, 1, 1, 0, 1, 0), 5: (1, 1, 0, 1, 0, 1, 1), 6: (1, 1, 0, 1, 1, 1, 1), 7: (1, 0, 1, 0, 0, 1, 0),
    8: (1, 1, 1, 1, 1, 1, 1), 9: (1, 1, 1, 1, 0, 1, 1),
}


def item_name(key: str, lang: str = "tr") -> str:
    i = {"tr": 0, "en": 1, "de": 2}.get(lang, 0)
    if key in NAMES:
        return NAMES[key][i]
    m = re.match(r"bilinmeyen_?(\d+)$", key)
    if m:
        return ("Bilinmeyen eşya ", "Unknown item ", "Unbekannter Gegenstand ")[i] + m.group(1)
    return key.replace("_", " ").strip().capitalize()


@dataclass
class RewardRead:
    item: str | None          # eşya anahtarı (dosya adı) — None: tanınmadı
    count: int | None         # adet — None: okunamadı
    score: float              # eşya benzerliği
    slot: tuple[int, int, int, int]   # kazanan kutu (kare koordinatı)
    digits: str = ""          # okunan rakamlar ("?" = emin olunamayan)
    new_item: bool = False    # bilinmeyen eşya olarak kaydedildi


def _read_digit(g: np.ndarray) -> tuple[int | None, int]:
    """Tek rakam. g: kutuya göre 0-1 arası normalleştirilmiş gri (koyu zemin 0, rakam 1). (rakam, hata)."""
    cols = np.where(g.max(0) > 0.5)[0]
    if len(cols) == 0 or g.shape[0] < 5:
        return None, 9
    g = g[:, cols[0]: cols[-1] + 1]
    H_, W_ = g.shape
    mid = g[int(H_ * 2 / 7): int(round(H_ * 5 / 7))] if H_ >= 7 else g[1:-1]
    lit = mid.mean(0) > 0.55
    # tek dikey çubuk (genişliği ≤2) ve dışı boş: "1" ya da "7"
    if lit.any():
        idx = np.where(lit)[0]
        others = np.delete(mid.mean(0), idx)
        if idx[-1] - idx[0] <= 1 and (others.size == 0 or others.max() < 0.5):
            top_wide = (g[0] > 0.45).sum() >= max(3, W_ - 1)
            bot_wide = (g[-1] > 0.45).sum() >= max(3, W_ - 1)
            return (7 if top_wide and not bot_wide else 1), 0
    n = cv2.resize(g.astype(np.float32), (4, 7), interpolation=cv2.INTER_AREA)
    s = (n[0, 1:3].mean(), n[1:3, 0].mean(), n[1:3, 3].mean(), n[3, 1:3].mean(),
         n[4:6, 0].mean(), n[4:6, 3].mean(), n[6, 1:3].mean())
    on = tuple(int(v > 0.5) for v in s)
    best = min(_SEG.items(), key=lambda kv: sum(a != b for a, b in zip(kv[1], on)))
    err = sum(a != b for a, b in zip(best[1], on))
    return (best[0] if err <= 1 else None), err


class RewardReader:
    def __init__(self):
        self.items: list[tuple[str, np.ndarray, np.ndarray | None]] = []
        self._scale: float | None = None
        self.reload()

    def reload(self) -> None:
        ITEM_DIR.mkdir(parents=True, exist_ok=True)
        self.items = []
        for p in sorted(ITEM_DIR.glob("*.png")):
            im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
            if im is None or im.shape[0] < 8 or im.shape[1] < 8:
                continue
            mask = None
            if im.ndim == 3 and im.shape[2] == 4:
                if (im[:, :, 3] < 128).any():
                    mask = (im[:, :, 3] > 128).astype(np.uint8) * 255
                im = im[:, :, :3]
            self.items.append((p.stem, im, mask))

    # ------------------------------------------------------------ kutular
    @staticmethod
    def _row(bar, shape):
        x, y, w, h = bar
        H, W = shape[:2]
        return (max(0, x - 6), min(H, y + h + int(0.10 * h)), min(W, x + w + 6), min(H, y + h + int(1.95 * h)))

    def count_boxes(self, frame: np.ndarray, bar) -> list[tuple[int, int, int, int]]:
        """Eşyaların altındaki koyu adet kutucukları (x, y, w, h) — kare koordinatı.
        Kutucuk: üst ve alt kenarı çok koyu düz bir çizgi, içinde açık renkli rakamlar."""
        x0, y0, x1, y1 = self._row(bar, frame.shape)
        if x1 - x0 < 40 or y1 - y0 < 10:
            return []
        h = bar[3]
        g = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.int16)
        H_, W_ = g.shape
        lo_w, hi_w = max(5, int(0.15 * h)), int(0.80 * h)
        lo_h, hi_h = max(6, int(0.18 * h)), max(8, int(0.42 * h))
        found: list[tuple[int, int, int, int]] = []
        dark = g <= 26
        semi = g <= 33                               # kenar çizgisinde tek tük biraz açık piksel olabilir
        gapfill = semi[:, 1:-1] & dark[:, :-2] & dark[:, 2:]
        dark[:, 1:-1] |= gapfill
        for r in range(H_ - lo_h):
            row = dark[r]
            c = 0
            while c < W_:
                if not row[c]:
                    c += 1
                    continue
                s_ = c
                while c < W_ and row[c]:
                    c += 1
                if s_ > 0 and semi[r, s_ - 1]:
                    s_ -= 1                              # kenar pikseli biraz açık olabilir
                L = c - s_
                if not (lo_w <= L <= hi_w):
                    continue
                if r > 0 and dark[r - 1, s_:c].mean() > 0.6:      # üst kenar değil (koyu alanın içi)
                    continue
                for bh in range(lo_h, min(hi_h, H_ - r - 1) + 1):
                    if (g[r + bh, s_:c] <= 40).mean() < 0.85:
                        continue
                    inner = g[r + 1: r + bh, s_ + 1: c - 1]
                    if inner.size and int((inner > 110).sum()) >= 4 and \
                            (g[r + 1: r + bh, s_] <= 34).mean() > 0.7:
                        found.append((x0 + s_, y0 + r, L, bh + 1))
                        break
        out: list[tuple[int, int, int, int]] = []
        for b in sorted(found, key=lambda b: (b[0], b[1])):
            if not any(abs(b[0] - o[0]) < 4 and abs(b[1] - o[1]) < 4 for o in out):
                out.append(b)
        return out

    def read_count(self, frame: np.ndarray, box) -> tuple[int | None, str]:
        bx, by, bw, bh = box
        g = cv2.cvtColor(frame[by + 1: by + bh - 1, bx + 1: bx + bw - 1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        if g.size == 0:
            return None, ""
        bg, gm = float(np.percentile(g, 10)), float(g.max())
        if gm - bg < 40:
            return None, ""
        g = np.clip((g - bg) / (gm - bg), 0, 1)
        rows = np.where(g.max(1) > 0.35)[0]
        if len(rows) < 4:
            return None, ""
        g = g[rows[0]: rows[-1] + 1]
        cols = g.max(0) > 0.42
        runs, s = [], None
        for i, v in enumerate(list(cols) + [False]):
            if v and s is None:
                s = i
            elif not v and s is not None:
                runs.append((s, i))
                s = None
        txt, ok = "", True
        for a, b in runs:
            d, _err = _read_digit(g[:, a:b])
            if d is None:
                txt += "?"
                ok = False
            else:
                txt += str(d)
        return (int(txt) if ok and txt else None), txt

    # ------------------------------------------------------------ eşya
    def match_item(self, icon: np.ndarray) -> tuple[str | None, float]:
        """Eşya resmini kutudaki simgeyle karşılaştır. Simgenin alt kısmı (adet kutucuğu ve çarkın ▲ işareti
        üstüne biniyor) karşılaştırmaya alınmaz. (anahtar, benzerlik) — ikinci en iyiden belirgin farklıysa."""
        scores: dict[str, float] = {}
        scales = (self._scale,) if self._scale else (1.25, 1.0, 1.2, 1.3, 1.15, 1.1, 1.35)
        for key, im, mask in self.items:
            for sc in (scales if not key.startswith("bilinmeyen") else (1.0,)):
                t = im if abs(sc - 1) < 1e-3 else cv2.resize(im, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
                m = np.full(t.shape[:2], 255, np.uint8) if mask is None else \
                    cv2.resize(mask, (t.shape[1], t.shape[0]), interpolation=cv2.INTER_NEAREST)
                m[int(t.shape[0] * 0.62):, :] = 0
                if t.shape[0] > icon.shape[0] or t.shape[1] > icon.shape[1]:
                    continue
                r = cv2.matchTemplate(icon, t, cv2.TM_CCOEFF_NORMED, mask=m)
                v = float(np.nan_to_num(r, nan=-1.0, posinf=-1.0).max())
                if v > scores.get(key, -1.0):
                    scores[key] = v
                    if v > getattr(self, "_best_v", -1.0) and not key.startswith("bilinmeyen"):
                        self._best_scale, self._best_v = sc, v
        self._best_v = -1.0
        if not scores:
            return None, 0.0
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        key, v = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else -1.0
        if v < 0.62 or v - second < (0.03 if v >= 0.85 else 0.06):
            return None, v
        return key, v

    # ------------------------------------------------------------ çark
    def read(self, frame: np.ndarray, bar, learn: bool = True) -> RewardRead | None:
        """İşaretin (çubuğun ortası) gösterdiği kutu: eşya + adet."""
        x, y, w, h = bar
        cx = x + w / 2
        boxes = self.count_boxes(frame, bar)
        if not boxes:
            return None
        # eşya kutusu ≈ 1,30h genişlikte; adet kutucuğunun sağ kenarı eşya kutusunun sağından ~0,21h içeride
        cand = [b for b in boxes if b[0] + b[2] - 1.09 * h <= cx <= b[0] + b[2] + 0.21 * h]
        if not cand:
            cand = boxes
        box = min(cand, key=lambda b: abs((b[0] + b[2] - 0.44 * h) - cx))
        count, digits = self.read_count(frame, box)
        rx1 = int(box[0] + box[2] + 0.21 * h)
        rx0 = int(rx1 - 1.30 * h)
        ry0 = int(y + h + 0.45 * h)
        ry1 = int(box[1] + box[3] + 0.18 * h)
        H, W = frame.shape[:2]
        rx0, ry0, rx1, ry1 = max(0, rx0), max(0, ry0), min(W, rx1), min(H, ry1)
        icon = frame[ry0:ry1, rx0:rx1]
        if icon.size == 0:
            return None
        key, score = self.match_item(icon)
        new = False
        if key is None and learn:
            key, new = self._learn_unknown(frame, (rx0, ry0, rx1 - rx0, box[1] - ry0)), True
            score = 1.0
        if key and not new and score >= 0.75 and getattr(self, "_best_scale", None) and not key.startswith("bilinmeyen"):
            self._scale = self._best_scale
        return RewardRead(key, count, score, (rx0, ry0, rx1 - rx0, ry1 - ry0), digits, new)

    def _learn_unknown(self, frame, rect) -> str | None:
        """Tanınmayan eşyanın resmini (adet kutusu hariç üst kısmı) bilinmeyen_N.png olarak kaydet."""
        x, y, w, h = rect
        if w < 10 or h < 10:
            return None
        crop = frame[y + 2: y + h - 1, x + 3: x + w - 3].copy()
        ITEM_DIR.mkdir(parents=True, exist_ok=True)
        if len(list(ITEM_DIR.glob("bilinmeyen_*.png"))) >= 20:   # sınır: klasör şişmesin
            return None
        k = 1
        while (ITEM_DIR / f"bilinmeyen_{k}.png").exists():
            k += 1
        key = f"bilinmeyen_{k}"
        try:
            cv2.imwrite(str(ITEM_DIR / f"{key}.png"), crop)
            self.items.append((key, crop, None))
        except Exception:
            return None
        return key
