"""Giriş ekranı."""
from __future__ import annotations

from core.i18n import T

import json
import os

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QVBoxLayout, QWidget)

from core.auth import AuthError, AuthProvider, Session
from core.config import DATA_DIR

from core.version import APP_NAME
from . import theme
from .fx import HeroPanel

REMEMBER_PATH = os.path.join(DATA_DIR, "remember.json")


class _LoginJob(QObject):
    done = Signal(object, str)  # Session | None, hata

    def __init__(self, provider: AuthProvider, user: str, pw: str):
        super().__init__()
        self.provider, self.user, self.pw = provider, user, pw

    def run(self):
        try:
            self.done.emit(self.provider.login(self.user, self.pw), "")
        except AuthError as e:
            self.done.emit(None, str(e))
        except Exception as e:  # noqa: BLE001
            self.done.emit(None, f"Beklenmeyen hata: {e}")


class LoginWindow(QDialog):
    def __init__(self, provider: AuthProvider):
        super().__init__()
        self.provider = provider
        self.session: Session | None = None
        self._thread: QThread | None = None
        self.setWindowTitle(APP_NAME + " • " + T("Giriş"))
        self.setObjectName("root")
        self.setFixedSize(860, 540)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(HeroPanel(), 11)

        right = QWidget()
        right.setObjectName("root")
        outer.addWidget(right, 10)
        lay = QVBoxLayout(right)
        lay.setContentsMargins(48, 56, 48, 36)
        lay.setSpacing(0)

        eyebrow = QLabel(T("HOŞ GELDİN"))
        eyebrow.setObjectName("eyebrow")
        title = QLabel(T("Hesabına giriş yap"))
        title.setStyleSheet("font-size:22px; font-weight:600;")
        sub = QLabel(T("Devam etmek için kullanıcı adını ve şifreni gir."))
        sub.setObjectName("pageSub")
        sub.setWordWrap(True)
        lay.addWidget(eyebrow)
        lay.addSpacing(6)
        lay.addWidget(title)
        lay.addSpacing(6)
        lay.addWidget(sub)
        lay.addSpacing(30)

        def field_label(text: str) -> QLabel:
            lb = QLabel(text)
            lb.setStyleSheet(f"color:{theme.MUTED}; font-size:12px; font-weight:600;")
            return lb

        lay.addWidget(field_label(T("Kullanıcı adı")))
        lay.addSpacing(6)
        self.user = QLineEdit()
        self.user.setObjectName("big")
        self.user.setPlaceholderText(T("Kullanıcı adınız"))
        lay.addWidget(self.user)
        lay.addSpacing(16)

        lay.addWidget(field_label(T("Şifre")))
        lay.addSpacing(6)
        prow = QHBoxLayout()
        prow.setSpacing(8)
        self.pw = QLineEdit()
        self.pw.setObjectName("big")
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setPlaceholderText("••••••••")
        prow.addWidget(self.pw, 1)
        self.show_pw = QPushButton(T("Göster"))
        self.show_pw.setObjectName("ghost")
        self.show_pw.setCheckable(True)
        self.show_pw.setCursor(Qt.PointingHandCursor)
        self.show_pw.toggled.connect(self._toggle_pw)
        prow.addWidget(self.show_pw)
        lay.addLayout(prow)
        lay.addSpacing(14)

        self.remember = QCheckBox(T("Kullanıcı adını hatırla"))
        lay.addWidget(self.remember)
        lay.addSpacing(10)

        self.error = QLabel("")
        self.error.setObjectName("error")
        self.error.setWordWrap(True)
        self.error.setMinimumHeight(20)
        lay.addWidget(self.error)
        lay.addSpacing(8)

        self.btn = QPushButton(T("Giriş Yap"))
        self.btn.setObjectName("primary")
        self.btn.setMinimumHeight(46)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet("font-size:14px;")
        self.btn.clicked.connect(self._login)
        lay.addWidget(self.btn)
        lay.addStretch()

        foot = QLabel(T("Hesabın yoksa yöneticiden üyelik iste."))
        foot.setObjectName("faint")
        foot.setAlignment(Qt.AlignCenter)
        lay.addWidget(foot)

        self.pw.returnPressed.connect(self._login)
        self.user.returnPressed.connect(self.pw.setFocus)
        self._load_remember()
        try:
            no_users = hasattr(provider, "store") and not provider.store.load()
        except Exception:
            no_users = False
        if no_users:
            self.error.setText(T("Henüz hiç üye yok. Bot klasöründeki uye_ekle.bat ile bir üye oluştur."))

    def _toggle_pw(self, on: bool) -> None:
        self.pw.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password)
        self.show_pw.setText(T("Gizle") if on else T("Göster"))

    def _load_remember(self) -> None:
        try:
            with open(REMEMBER_PATH, "r", encoding="utf-8") as f:
                name = json.load(f).get("username", "")
            if name:
                self.user.setText(name)
                self.remember.setChecked(True)
                self.pw.setFocus()
        except (OSError, json.JSONDecodeError):
            pass

    def _save_remember(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        data = {"username": self.user.text().strip()} if self.remember.isChecked() else {}
        with open(REMEMBER_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _login(self) -> None:
        if self._thread is not None:
            return
        self.error.setText("")
        self.btn.setEnabled(False)
        self.btn.setText(T("Doğrulanıyor…"))
        self._thread = QThread(self)
        self._job = _LoginJob(self.provider, self.user.text(), self.pw.text())
        self._job.moveToThread(self._thread)
        self._thread.started.connect(self._job.run)
        self._job.done.connect(self._finished)
        self._thread.start()

    def _finished(self, session, err: str) -> None:
        self._thread.quit()
        self._thread.wait()
        self._thread = None
        self.btn.setEnabled(True)
        self.btn.setText(T("Giriş Yap"))
        if session is None:
            self.error.setText(T(err))
            self.pw.clear()
            self.pw.setFocus()
            return
        self._save_remember()
        self.session = session
        self.accept()
