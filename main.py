"""FishBot — giriş noktası.

    python main.py
"""
import os
import sys
import traceback
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from core.paths import BUNDLE, DATA  # noqa: E402

LOG_PATH = os.path.join(str(DATA), "hata.log")


def write_log(text: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} =====\n{text}\n")


def show_error(text: str) -> None:
    """Hata penceresi (Qt yoksa konsola yaz)."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841
        box = QMessageBox()
        box.setIcon(QMessageBox.Critical)
        box.setWindowTitle("NOtivi Fishbot — Hata")
        try:
            from core.i18n import T
        except Exception:
            T = str  # noqa: N806
        box.setText(T("Beklenmeyen bir hata oluştu. Ayrıntı data\\hata.log dosyasına yazıldı."))
        box.setDetailedText(text)
        box.exec()
    except Exception:
        print(text, file=sys.stderr)


def excepthook(exc_type, exc, tb) -> None:
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    write_log(text)
    print(text, file=sys.stderr)
    show_error(text)


def main() -> int:
    sys.excepthook = excepthook   # arayüzdeki hatalar sessizce kaybolmasın
    try:
        from PySide6.QtWidgets import QApplication

        from core.auth import make_provider
        from core.config import Config
        cfg = Config()
        try:
            from core.config import prune_data
            from core.i18n import set_lang
            set_lang(cfg["language"])      # arayüz dili — gui modülleri yüklenmeden ÖNCE
            prune_data(int(cfg["captcha_keep"]))   # eski kayıtları temizle (disk dolmasın)
        except Exception:
            pass
        from gui.login_window import LoginWindow
        from gui.main_window import MainWindow
        from gui.theme import QSS
    except ImportError as e:
        msg = (f"Gerekli bir paket eksik: {e}\n\n"
               "Programı yeniden indir ya da baslat.bat dosyasını çalıştır.")
        write_log(traceback.format_exc())
        print(msg, file=sys.stderr)
        show_error(msg)
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("NOtivi Fishbot")
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    ico = os.path.join(str(BUNDLE), "assets", "app.ico")
    if os.path.exists(ico):
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(ico))
    if sys.platform == "win32":                      # görev çubuğunda Python değil FishBot simgesi
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FishBot.App")
        except Exception:
            pass

    # exe'nin açılırken gösterdiği resmi kapat (artık bizim açılış ekranımız var)
    try:
        import pyi_splash   # noqa: F401  (sadece exe'de vardır)
        pyi_splash.close()
    except Exception:
        pass

    # açılış ekranı: dosyalar, güncelleme, sunucu bağlantısı. Sorun yoksa giriş ekranına geçer.
    from core import server
    from gui.splash import SplashScreen
    sp = SplashScreen(server.UPDATE_REPO)
    sp.exec()
    if sp.result_kind != "devam":
        return 0                            # "kur": yeni sürüm kendini açacak; "kapat": kullanıcı kapattı

    # üyelik: core/server.py'de Supabase ayarlıysa Supabase, değilse data/users.json
    provider = make_provider()

    login = LoginWindow(provider)
    if login.exec() != LoginWindow.Accepted or login.session is None:
        return 0

    win = MainWindow(login.session, provider, cfg)
    win.show()
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        text = traceback.format_exc()
        write_log(text)
        print(text, file=sys.stderr)
        show_error(text)
        sys.exit(1)
