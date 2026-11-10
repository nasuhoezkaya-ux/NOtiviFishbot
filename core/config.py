"""Bot ayarları: varsayılanlar + config.json okuma/yazma."""
from __future__ import annotations

from .paths import APP_DIR

import json
import os
import threading
from copy import deepcopy

BASE_DIR = str(APP_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

DEFAULTS: dict = {
    # --- Olta ve tur ---
    "cast_key": "SPACE",          # olta / balık işareti / zamanlama tuşu
    "key_hold_min_ms": 120,       # olta atarken tuşu basılı tutma süresi (insansı)
    "key_hold_max_ms": 250,
    "cooldown_min_ms": 1200,      # ödül çarkı kapanınca oltayı tekrar atmadan önce bekleme
    "cooldown_max_ms": 1800,
    "break_enabled": False,       # akıllı molalar
    "break_every_min": [40, 70],  # bu kadar dakikada bir mola ver
    "break_len_min": [2, 6],      # mola süresi (dakika)

    # --- Balık işareti (karakterin kafasında) ---
    "bite_timeout_s": 40,         # olta atıldıktan sonra işaret bu sürede görülmezse olta yeniden atılır
    "bite_settle_s": 1.2,         # atıştan sonra işaret aramaya başlamadan önce (atma animasyonu)
    "bite_react_min_ms": 90,      # işareti görünce Space'e basmadan önce insan gibi bekleme
    "bite_react_max_ms": 200,
    "bite_threshold": 0.70,       # işaret resmi eşleşme eşiği
    "bite_scale": None,           # işaret resminin oyundaki ölçeği (ilk bulunuşta öğrenilir)
    "bite_change": True,          # işaret resmi bulunamazsa "aniden çıkıp yerinde duran yeni şekil" ile de ara
    "bite_pos": None,             # öğrenilen kafa konumu [x, y] (ekran oranı)
    "bite_area": None,            # kullanıcının seçtiği kendi karakterinin işaret alanı {dx, dy, w, h} (client ortasına göre)

    # --- Zamanlama penceresi ---
    "timing_latency_ms": 45,      # tuşun oyuna ulaşma gecikmesi (otomatik öğrenilir)
    "timing_autolearn": True,
    "timing_max_s": 12,           # pencere bu kadar sürede bitmezse balık kutucuktayken basılır

    # --- Captcha ---
    "captcha_enabled": True,      # beklerken ekranda captcha var mı bakılır
    "captcha_autosolve": True,    # "Atın üzerine tıklayın" gibi yönergeyi okuyup doğru simgeye tıklar
    "captcha_sound": True,        # captcha gelince sesli uyarı
    "captcha_keep": 30,           # data/captcha içinde tutulacak en yeni captcha resmi sayısı
    "streak_check": True,         # sonucu oyunun "Seri" sayacıyla doğrula
    "captcha_wait_min": 10,       # çözülemezse elle çözülmesi için en fazla bekleme (dakika)

    # --- Giriş ve görüntü ---
    "input_method": "karma",      # "karma" (önerilen) | "postmessage" (arka plan) | "sendinput" (ön plan)
    "preview_fps": 60,            # arayüzdeki canlı görüntü kare hızı (en fazla 120)
    "scan_fps": 60,               # balık beklerken ekrana saniyede kaç kez bakılır (en fazla 120)
    "language": "tr",             # arayüz dili: tr | en | de

    # --- Client'lar ---
    "process_filter": "metin2",   # süreç adı / pencere başlığında aranacak metin
    "known_exes": [],             # F7 ile seçilen client'ların exe adları (otomatik bulunur)
    "blocked_exes": [             # bu programlar asla client olarak listelenmez
        "firefox.exe", "chrome.exe", "msedge.exe", "opera.exe", "opera_gx.exe", "brave.exe",
        "vivaldi.exe", "iexplore.exe", "explorer.exe", "discord.exe", "steam.exe", "steamwebhelper.exe",
        "telegram.exe", "whatsapp.exe", "spotify.exe", "code.exe", "notepad.exe", "notepad++.exe",
        "teams.exe", "ms-teams.exe", "obs64.exe", "python.exe", "pythonw.exe", "cmd.exe",
        "windowsterminal.exe", "powershell.exe", "applicationframehost.exe", "textinputhost.exe",
        "searchhost.exe", "startmenuexperiencehost.exe", "shellexperiencehost.exe",
    ],
    "pick_key": "F7",             # fare client üstündeyken basılınca o client seçilir
    "stop_key": "F8",             # tüm botları anında durdur
    "config_version": 21,
}


class Config:
    """Thread-safe ayar nesnesi."""

    def __init__(self, path: str = CONFIG_PATH):
        self.path = path
        self._lock = threading.Lock()
        self._data = deepcopy(DEFAULTS)
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.path):
            self.save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            with self._lock:
                for k, v in loaded.items():
                    if k in DEFAULTS:            # eski (kancalı sistem) ayarlar okunmaz, kaydederken silinir
                        if isinstance(DEFAULTS[k], dict) and isinstance(v, dict):
                            merged = deepcopy(DEFAULTS[k])
                            merged.update(v)
                            v = merged
                        self._data[k] = v
                ver = int(loaded.get("config_version", 1))
                if ver < 2:
                    self._data["input_method"] = "karma"
                if ver < 21:                     # yeni balık sistemi: daha akıcı canlı görüntü
                    self._data["preview_fps"] = 60
                self._data["config_version"] = DEFAULTS["config_version"]
        except (OSError, json.JSONDecodeError, ValueError):
            pass

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with self._lock:
            data = deepcopy(self._data)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str):
        with self._lock:
            v = self._data.get(key, DEFAULTS.get(key))
            return deepcopy(v) if isinstance(v, (dict, list)) else v

    def set(self, key: str, value) -> None:
        with self._lock:
            self._data[key] = value

    def snapshot(self) -> dict:
        with self._lock:
            return deepcopy(self._data)

    def __getitem__(self, key: str):
        return self.get(key)


def prune_data(max_captcha_shots: int = 30, keep_scan_days: int = 10) -> None:
    """Disk dolmasın: eski captcha görüntülerini ve eski tarama kayıtlarını sil."""
    import time as _t
    try:
        d = os.path.join(DATA_DIR, "captcha")
        if os.path.isdir(d):
            files = sorted((os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".png")),
                           key=os.path.getmtime)
            for f in files[:-max_captcha_shots]:
                os.remove(f)
        d = os.path.join(DATA_DIR, "tarama")
        if os.path.isdir(d):
            limit = _t.time() - keep_scan_days * 86400
            for f in os.listdir(d):
                fp = os.path.join(d, f)
                if f.endswith(".log") and os.path.getmtime(fp) < limit:
                    os.remove(fp)
        d = os.path.join(DATA_DIR, "oduller")             # eski sürümün kaydettiği çark görüntüleri
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(".png"):
                    os.remove(os.path.join(d, f))
    except Exception:
        pass
