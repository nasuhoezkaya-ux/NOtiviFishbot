"""Dil desteği: Türkçe (varsayılan), English, Deutsch.

Metinler kaynakta Türkçe yazılır ve T("...") ile sarılır; seçili dile göre core/i18n_tablo.py'deki
çeviri kullanılır (yoksa Türkçe metin gösterilir). Dil, programın başında ayarlardan okunur
(değişiklik yeniden başlatınca uygulanır)."""
from __future__ import annotations

import unicodedata

LANGS = {"tr": "Türkçe", "en": "English", "de": "Deutsch"}
_lang = "tr"
_table: dict | None = None


def set_lang(code: str) -> None:
    global _lang
    _lang = code if code in LANGS else "tr"


def lang() -> str:
    return _lang


def T(text: str) -> str:
    """Türkçe metnin seçili dildeki karşılığı."""
    global _table
    if _lang == "tr" or not text:
        return text
    if _table is None:
        try:
            from .i18n_tablo import TABLO
            _table = TABLO
        except Exception:
            _table = {}
    tr = _table.get(text)
    if not tr:
        return text
    return tr[0] if _lang == "en" else tr[1]


def ascii_name(text: str) -> str:
    """Canlı görüntüye (OpenCV yazısı Türkçe karakter çizemez) yazmak için: 'Mini balık' -> 'Mini balik'."""
    t = text.replace("ı", "i").replace("İ", "I").replace("ş", "s").replace("Ş", "S").replace("ğ", "g")
    t = t.replace("Ğ", "G").replace("ü", "u").replace("Ü", "U").replace("ö", "o").replace("Ö", "O")
    t = t.replace("ç", "c").replace("Ç", "C").replace("ß", "ss")
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
