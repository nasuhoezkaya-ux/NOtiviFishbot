"""Windows'un YERLEŞİK metin tanıma (OCR) motoru — Tesseract vb. ek program kurmaya gerek yok.

Windows 10/11'de 'Windows.Media.Ocr' hazır gelir; Python'dan pywinrt (winrt-* paketleri) ile kullanılır.
Türkçe dil paketi Windows'ta kuruluysa Türkçe, değilse kullanıcının dillerinden biriyle okur.
Kullanılamıyorsa available() False döner ve bot captcha'yı sadece şablon resimleriyle arar.

ÖNEMLİ: WinRT, iş parçacığının COM ortamını kullanır. Qt'nin ana iş parçacığı STA olduğu için
OCR her zaman ayrı bir iş parçacığında çağrılır (recognize bunu kendisi yapar).
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


@dataclass
class OcrWord:
    text: str
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class OcrLine:
    text: str
    words: list[OcrWord] = field(default_factory=list)

    @property
    def box(self) -> tuple[float, float, float, float]:
        if not self.words:
            return 0.0, 0.0, 0.0, 0.0
        x0 = min(w.x for w in self.words)
        y0 = min(w.y for w in self.words)
        x1 = max(w.x + w.w for w in self.words)
        y1 = max(w.y + w.h for w in self.words)
        return x0, y0, x1 - x0, y1 - y0


_lock = threading.Lock()
_state: dict = {"tried": False, "mods": None, "engine": None, "error": "", "lang": ""}


def _load():
    if _state["tried"]:
        return _state["mods"]
    _state["tried"] = True
    mods = None
    for base in ("winrt", "winsdk"):
        try:
            ocr = __import__(f"{base}.windows.media.ocr", fromlist=["OcrEngine"])
            glob = __import__(f"{base}.windows.globalization", fromlist=["Language"])
            img = __import__(f"{base}.windows.graphics.imaging", fromlist=["SoftwareBitmap"])
            st = __import__(f"{base}.windows.storage.streams", fromlist=["DataWriter"])
            mods = (ocr, glob, img, st)
            break
        except Exception as e:  # noqa: BLE001
            _state["error"] = f"{base}: {e}"
    _state["mods"] = mods
    return mods


def _engine(mods):
    if _state["engine"] is not None:
        return _state["engine"]
    ocr, glob, _img, _st = mods
    eng = None
    for tag in ("tr-TR", "tr"):
        try:
            lang = glob.Language(tag)
            if ocr.OcrEngine.is_language_supported(lang):
                eng = ocr.OcrEngine.try_create_from_language(lang)
                if eng is not None:
                    _state["lang"] = tag
                    break
        except Exception:
            pass
    if eng is None:
        try:
            eng = ocr.OcrEngine.try_create_from_user_profile_languages()
            _state["lang"] = "kullanıcı dili"
        except Exception as e:  # noqa: BLE001
            _state["error"] = f"OCR motoru açılamadı: {e}"
    _state["engine"] = eng
    return eng


def _to_bitmap(mods, bgr: np.ndarray):
    _ocr, _glob, img, st = mods
    h, w = bgr.shape[:2]
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA) if bgr.ndim == 3 else cv2.cvtColor(bgr, cv2.COLOR_GRAY2BGRA)
    data = np.ascontiguousarray(bgra).tobytes()
    dw = st.DataWriter()
    try:
        dw.write_bytes(data)
    except TypeError:
        dw.write_bytes(list(data))
    buf = dw.detach_buffer()
    fmt = img.BitmapPixelFormat.BGRA8
    try:
        return img.SoftwareBitmap.create_copy_from_buffer(buf, fmt, w, h, img.BitmapAlphaMode.PREMULTIPLIED)
    except TypeError:
        return img.SoftwareBitmap.create_copy_from_buffer(buf, fmt, w, h)


def _run(bgr: np.ndarray, scale: float) -> list[OcrLine]:
    import asyncio
    mods = _load()
    if mods is None or cv2 is None:
        return []
    eng = _engine(mods)
    if eng is None:
        return []
    im = bgr
    if scale != 1.0:
        im = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    sb = _to_bitmap(mods, im)

    async def go():
        return await eng.recognize_async(sb)

    res = asyncio.run(go())
    out: list[OcrLine] = []
    for ln in res.lines:
        words = []
        for wd in ln.words:
            r = wd.bounding_rect
            words.append(OcrWord(str(wd.text), r.x / scale, r.y / scale, r.width / scale, r.height / scale))
        out.append(OcrLine(str(ln.text), words))
    return out


def recognize(bgr: np.ndarray, scale: float = 2.0, timeout: float = 4.0) -> list[OcrLine]:
    """Görüntüdeki yazıları satır satır okur (koordinatlar verilen görüntüye göre). Hata/yoksa []."""
    if bgr is None or bgr.size == 0:
        return []
    box: dict = {}

    def work():
        try:
            with _lock:
                box["r"] = _run(bgr, scale)
        except Exception as e:  # noqa: BLE001
            _state["error"] = f"OCR hatası: {e!r}"
            box["r"] = []

    t = threading.Thread(target=work, daemon=True)
    t.start()
    t.join(timeout)
    return box.get("r", [])


def available() -> bool:
    """OCR kullanılabilir mi? (ilk çağrıda ayrı iş parçacığında motoru dener)"""
    if not _state["tried"] or (_state["mods"] is not None and _state["engine"] is None and not _state["error"]):
        def probe():
            try:
                with _lock:
                    m = _load()
                    if m is not None:
                        _engine(m)
            except Exception as e:  # noqa: BLE001
                _state["error"] = f"{e!r}"
        t = threading.Thread(target=probe, daemon=True)
        t.start()
        t.join(5.0)
    return _state["mods"] is not None and _state["engine"] is not None


def status() -> str:
    if available():
        return f"Windows OCR hazır ({_state['lang']})"
    return "Windows OCR kullanılamıyor" + (f" — {_state['error']}" if _state["error"] else "")


# ------------------------------------------------------------------ Türkçe metin yardımcıları
_TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})
_ASCII = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"})


def tr_lower(s: str) -> str:
    return s.translate(_TR_LOWER).lower()


def fold(s: str) -> str:
    """Karşılaştırma için: küçük harf, Türkçe karakterler sadeleşir, harf dışı atılır."""
    s = tr_lower(s).translate(_ASCII)
    return "".join(ch for ch in s if ch.isalnum() or ch == " ").strip()
