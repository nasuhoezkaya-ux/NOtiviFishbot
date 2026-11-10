"""Programın klasörleri.

Kaynak koddan çalışırken: proje klasörü.
Tek dosya .exe olarak çalışırken: kullanıcının kendi klasörü %LOCALAPPDATA%\\FishBot
  (assets\\ öğrenilen resimler, data\\ ayarlar ve kayıtlar). Böylece kullanıcı sadece FishBot.exe'yi indirir;
  exe'yi nereye koyarsa koysun ayarları ve öğrendikleri kaybolmaz. Exe'nin içindeki hazır resimler ilk
  açılışta (ve her yeni sürümde) bu klasöre kopyalanır."""
import os
import shutil
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))

if FROZEN:
    BUNDLE = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    APP_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "FishBot"
else:
    APP_DIR = Path(__file__).resolve().parent.parent
    BUNDLE = APP_DIR

ASSETS = APP_DIR / "assets"
DATA = APP_DIR / "data"
EXE = Path(sys.executable).resolve() if FROZEN else None


def sync_assets() -> None:
    """Exe'nin içindeki hazır resimleri kullanıcı klasörüne kopyala.
    Eksik dosyalar her zaman, var olanlar sadece sürüm değiştiyse yenilenir (öğrenilen resimlere dokunulmaz)."""
    if not FROZEN:
        return
    src = BUNDLE / "assets"
    if not src.is_dir():
        return
    from .version import VERSION
    DATA.mkdir(parents=True, exist_ok=True)
    marker = DATA / "assets_surum.txt"
    try:
        old = marker.read_text(encoding="utf-8").strip()
    except OSError:
        old = ""
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        dst = ASSETS / f.relative_to(src)
        if dst.exists() and old == VERSION:
            continue
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
        except OSError:
            pass
    try:
        marker.write_text(VERSION, encoding="utf-8")
    except OSError:
        pass


def cleanup_old_exe() -> None:
    """Güncellemeden kalan FishBot.old.exe'yi sil."""
    if EXE is None:
        return
    for p in EXE.parent.glob(EXE.stem + "*.old.exe"):
        try:
            p.unlink()
        except OSError:
            pass


def restart_env() -> dict:
    """Programı kendi içinden yeniden başlatırken kullanılacak ortam (tek dosya exe'de geçici klasör
    paylaşılmasın diye PyInstaller'a "temiz başla" denir)."""
    env = dict(os.environ)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    for k in ("_MEIPASS2", "_PYI_APPLICATION_HOME_DIR", "_PYI_ARCHIVE_FILE", "_PYI_PARENT_PROCESS_LEVEL"):
        env.pop(k, None)
    return env
