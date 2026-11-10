"""Sunucu ayarları: üyelik (Supabase) ve otomatik güncelleme (GitHub).

Bot dağıtılmadan önce buraya kendi değerlerini yaz (ya da programın klasörüne aynı anahtarlarla
server.json koy; o dosya buradakileri ezer).

SUPABASE_URL      : Supabase > Project Settings > API > Project URL   (https://xxxx.supabase.co)
SUPABASE_ANON_KEY : Supabase'deki "Publishable key" (sb_publishable_…) ya da eski "anon public" anahtarı.
                    Bu anahtar programın içinde durabilir: tablolar RLS ile kapalıdır, bot sadece
                    sql/supabase_kurulum.sql içindeki fonksiyonları çağırabilir.
                    "service_role" anahtarını ASLA buraya yazma.
UPDATE_REPO       : GitHub deposu "kullanici/depo" (ör. "nasuh/FishBot"). Boşsa güncelleme denetlenmez.
Hepsi boşsa bot yerel üye dosyasıyla (data/users.json) çalışır.
"""
import json

from .paths import APP_DIR

SUPABASE_URL = "https://mrjxvhnxbketvrbhvohv.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_qFqZE-6z_Arnu2u8K-XeHg_4togS1_i"
UPDATE_REPO = "nasuhoezkaya-ux/NOtiviFishbot"

try:
    _o = json.loads((APP_DIR / "server.json").read_text(encoding="utf-8"))
    SUPABASE_URL = _o.get("SUPABASE_URL", SUPABASE_URL)
    SUPABASE_ANON_KEY = _o.get("SUPABASE_ANON_KEY", SUPABASE_ANON_KEY)
    UPDATE_REPO = _o.get("UPDATE_REPO", UPDATE_REPO)
except Exception:
    pass


def supabase_ready() -> bool:
    return bool(SUPABASE_URL.strip() and SUPABASE_ANON_KEY.strip())
