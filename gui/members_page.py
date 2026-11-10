"""Üyeler (yönetici paneli): üye ekle / düzenle, süre ver (süresiz dahil), askıya al, cihaz kilidi, sil.

Sadece yönetici (is_admin) üyelere görünür. Üyeler Supabase'de (ya da sunucu ayarlı değilse data/users.json)."""
from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from PySide6.QtCore import QDateTime, QObject, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QDateTimeEdit, QDialog, QFormLayout, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QSpinBox,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from core.auth import AuthError, Member
from core.i18n import T

from . import theme
from .dashboard import button, card_with_title, page_header
from .widgets import StatCard

if TYPE_CHECKING:
    from .main_window import MainWindow


def fmt_left(m: Member) -> tuple[str, str]:
    """(kalan süre metni, renk)."""
    if not m.active:
        return T("Askıda"), theme.FAINT
    if m.expires_at is None:
        return T("Süresiz"), theme.SUCCESS
    sec = (m.expires_at - datetime.now()).total_seconds()
    if sec <= 0:
        return T("Süresi doldu"), theme.DANGER
    d, h = int(sec // 86400), int(sec % 86400 // 3600)
    txt = T("{d} gün {h} saat").format(d=d, h=h) if d else T("{h} saat {m} dk").format(h=h, m=int(sec % 3600 // 60))
    return txt, (theme.ACCENT if d > 7 else theme.WARNING if d > 2 else theme.DANGER)


class _Bus(QObject):
    done = Signal(object, object)       # (sonuç, hata metni)


class MemberDialog(QDialog):
    """Yeni üye / üye düzenle."""

    def __init__(self, parent, m: Member | None):
        super().__init__(parent)
        self.orig = m
        self.setWindowTitle(T("Yeni üye") if m is None else T("Üyeyi düzenle"))
        self.setMinimumWidth(460)
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 22, 24, 20)
        v.setSpacing(14)
        t = QLabel(T("Yeni üye") if m is None else m.username)
        t.setStyleSheet("font-size:18px; font-weight:600;")
        v.addWidget(t)
        f = QFormLayout()
        f.setHorizontalSpacing(18)
        f.setVerticalSpacing(11)
        self.user = QLineEdit(m.username if m else "")
        self.pw = QLineEdit()
        self.pw.setPlaceholderText(T("değiştirmek için yaz") if m else T("zorunlu"))
        gen = QPushButton(T("Oluştur"))
        gen.setObjectName("ghost")
        gen.clicked.connect(self._gen_pw)
        prow = QHBoxLayout()
        prow.addWidget(self.pw, 1)
        prow.addWidget(gen)
        self.unl = QCheckBox(T("Süresiz üyelik"))
        self.exp = QDateTimeEdit()
        self.exp.setCalendarPopup(True)
        self.exp.setDisplayFormat("dd.MM.yyyy  HH:mm")
        base = (m.expires_at if m and m.expires_at else datetime.now() + timedelta(days=30))
        self.exp.setDateTime(QDateTime(base.year, base.month, base.day, base.hour, base.minute, 0))
        self.unl.setChecked(bool(m and m.expires_at is None))
        self.unl.toggled.connect(lambda on: self.exp.setEnabled(not on))
        self.exp.setEnabled(not self.unl.isChecked())
        quick = QHBoxLayout()
        quick.setSpacing(6)
        for d in (1, 7, 30, 90, 365):
            b = QPushButton(f"+{d} " + T("gün"))
            b.setObjectName("ghost")
            b.clicked.connect(lambda _=False, d=d: self._add_days(d))
            quick.addWidget(b)
        quick.addStretch()
        self.active = QCheckBox(T("Aktif (kapalıysa giriş yapamaz)"))
        self.active.setChecked(m.active if m else True)
        self.admin = QCheckBox(T("Yönetici (Üyeler sayfasını görür)"))
        self.admin.setChecked(bool(m and m.is_admin))
        self.maxc = QSpinBox()
        self.maxc.setRange(0, 50)
        self.maxc.setSpecialValueText(T("Sınırsız"))
        self.maxc.setValue(m.max_clients if m else 0)
        self.lock = QCheckBox(T("Sadece ilk giriş yaptığı bilgisayarda çalışsın"))
        self.lock.setChecked(bool(m and m.hwid_lock))
        self.note = QLineEdit(m.note if m else "")
        f.addRow(T("Kullanıcı adı"), self.user)
        f.addRow(T("Şifre"), prow)
        f.addRow(T("Üyelik"), self.unl)
        f.addRow(T("Bitiş"), self.exp)
        f.addRow("", quick)
        f.addRow(T("Durum"), self.active)
        f.addRow("", self.admin)
        f.addRow(T("En fazla client"), self.maxc)
        f.addRow(T("Cihaz kilidi"), self.lock)
        f.addRow(T("Not"), self.note)
        v.addLayout(f)
        self.err = QLabel("")
        self.err.setObjectName("error")
        self.err.setWordWrap(True)
        v.addWidget(self.err)
        row = QHBoxLayout()
        row.addStretch()
        c = QPushButton(T("Vazgeç"))
        c.clicked.connect(self.reject)
        ok = QPushButton(T("Kaydet"))
        ok.setObjectName("primary")
        ok.clicked.connect(self._ok)
        row.addWidget(c)
        row.addWidget(ok)
        v.addLayout(row)

    def _gen_pw(self) -> None:
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        pw = "".join(secrets.choice(alphabet) for _ in range(10))
        self.pw.setText(pw)
        self.pw.setEchoMode(QLineEdit.Normal)

    def _add_days(self, d: int) -> None:
        self.unl.setChecked(False)
        cur = self.exp.dateTime().toPython()
        base = max(cur, datetime.now())
        n = base + timedelta(days=d)
        self.exp.setDateTime(QDateTime(n.year, n.month, n.day, n.hour, n.minute, 0))

    def _ok(self) -> None:
        if not self.user.text().strip():
            self.err.setText(T("Kullanıcı adı boş olamaz."))
            return
        if self.orig is None and not self.pw.text():
            self.err.setText(T("Yeni üye için şifre gerekli."))
            return
        self.accept()

    def result_member(self) -> tuple[Member, str | None]:
        m = Member(username=self.user.text().strip(),
                   expires_at=None if self.unl.isChecked() else self.exp.dateTime().toPython(),
                   active=self.active.isChecked(), is_admin=self.admin.isChecked(),
                   max_clients=int(self.maxc.value()), hwid_lock=self.lock.isChecked(), note=self.note.text().strip())
        return m, (self.pw.text() or None)


class MembersPage(QWidget):
    COLS = ["Kullanıcı", "Şifre", "Rol", "Durum", "Kalan süre", "Bitiş", "Client", "Cihaz kilidi", "Çevrimiçi",
            "Son giriş", "Son görülme", "Oluşturulma", "Not"]

    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.members: list[Member] = []
        self._bus = _Bus()
        self._bus.done.connect(self._on_done)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        head = QHBoxLayout()
        self.sub = QLabel()
        head.addLayout(page_header("Üyeler", self.sub), 1)
        b_new = button("+  Yeni üye", "primary")
        b_new.clicked.connect(self.new_member)
        b_ref = button("⟳  Yenile")
        b_ref.clicked.connect(self.reload)
        head.addWidget(b_ref, 0, Qt.AlignVCenter)
        head.addWidget(b_new, 0, Qt.AlignVCenter)
        lay.addLayout(head)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.c_all = StatCard("Toplam üye", color=theme.ACCENT)
        self.c_act = StatCard("Aktif", color=theme.SUCCESS)
        self.c_unl = StatCard("Süresiz", color=theme.TEXT)
        self.c_soon = StatCard("7 gün içinde bitecek", color=theme.WARNING)
        self.c_exp = StatCard("Süresi dolmuş / askıda", color=theme.DANGER)
        for c in (self.c_all, self.c_act, self.c_unl, self.c_soon, self.c_exp):
            stats.addWidget(c)
        lay.addLayout(stats)

        tc, tv = card_with_title("Üye listesi")
        frow = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(T("Ara: kullanıcı adı ya da not"))
        self.search.textChanged.connect(self._fill)
        frow.addWidget(self.search, 1)
        tv.addLayout(frow)
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels([T(c) for c in self.COLS])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setStretchLastSection(True)
        self.table.doubleClicked.connect(lambda *_: self.edit_member())
        self.table.itemSelectionChanged.connect(self._show_detail)
        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self.table, 3)
        self.detail = QWidget()
        self.detail.setMinimumWidth(300)
        self.detail.setMaximumWidth(380)
        dv = QVBoxLayout(self.detail)
        dv.setContentsMargins(14, 12, 14, 12)
        dv.setSpacing(8)
        self.detail.setObjectName("detailBox")
        self.detail.setStyleSheet(f"QWidget#detailBox {{ background:{theme.SURFACE_2}; border:1px solid {theme.BORDER};"
                                  "border-radius:10px; }")
        self.d_title = QLabel(T("Bir üye seç"))
        self.d_title.setStyleSheet("font-size:16px; font-weight:600; background:transparent;")
        dv.addWidget(self.d_title)
        self.d_grid = QFormLayout()
        self.d_grid.setHorizontalSpacing(12)
        self.d_grid.setVerticalSpacing(6)
        self.d_vals: dict[str, QLabel] = {}
        for k, lbl in (("id", "Kimlik (ID)"), ("username", "Kullanıcı adı"), ("password", "Şifre"),
                       ("role", "Rol"), ("state", "Durum"), ("left", "Kalan süre"), ("expires", "Bitiş"),
                       ("clients", "En fazla client"), ("lock", "Cihaz kilidi"), ("hwid", "Cihaz kimliği"),
                       ("online", "Çevrimiçi"), ("last_login", "Son giriş"), ("last_seen", "Son görülme"),
                       ("created", "Oluşturulma"), ("note", "Not")):
            kl = QLabel(T(lbl))
            kl.setObjectName("kvKey")
            vl = QLabel("—")
            vl.setWordWrap(True)
            vl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            vl.setStyleSheet("font-weight:600; background:transparent;")
            self.d_grid.addRow(kl, vl)
            self.d_vals[k] = vl
        dv.addLayout(self.d_grid)
        dv.addStretch()
        b_pw = button("Şifre değiştir", "primary")
        b_pw.clicked.connect(self.change_password)
        dv.addWidget(b_pw)
        body.addWidget(self.detail, 1)
        tv.addLayout(body, 1)
        arow = QHBoxLayout()
        arow.setSpacing(8)
        for text, fn, kind in (("Düzenle", self.edit_member, ""), ("+30 gün", lambda: self.add_days(30), ""),
                               ("Süresiz yap", self.make_unlimited, ""), ("Askıya al / Aç", self.toggle_active, ""),
                               ("Cihaz kilidini sıfırla", self.reset_hwid, ""), ("Oturumu kapat", self.kick, ""),
                               ("Sil", self.delete_member, "danger")):
            b = button(text, kind)
            b.clicked.connect(fn)
            arow.addWidget(b)
        arow.addStretch()
        self.status = QLabel("")
        self.status.setObjectName("faint")
        arow.addWidget(self.status)
        tv.addLayout(arow)
        lay.addWidget(tc, 3)

        lc, lv = card_with_title("Giriş kayıtları")
        self.log = QPlainTextEdit()
        self.log.setObjectName("console")
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(120)
        lv.addWidget(self.log)
        lay.addWidget(lc, 1)
        self.reload()

    # ------------------------------------------------------------ arka planda sunucu işlemleri
    def _run(self, fn, after=None) -> None:
        self.status.setText(T("Sunucuyla konuşuluyor…"))

        def job():
            try:
                self._bus.done.emit((fn(), after), None)
            except (AuthError, ConnectionError) as e:
                self._bus.done.emit((None, None), T(str(e)))
            except Exception as e:  # noqa: BLE001
                self._bus.done.emit((None, None), repr(e))
        threading.Thread(target=job, daemon=True).start()

    def _on_done(self, res, err) -> None:
        value, after = res
        if err:
            self.status.setText("")
            QMessageBox.warning(self, "FishBot", err)
            return
        self.status.setText(T("✓ Güncellendi ({0}).").format(datetime.now().strftime("%H:%M:%S")))
        if after:
            after(value)

    def reload(self) -> None:
        p, s = self.win.provider, self.win.session

        def fetch():
            return p.list_members(s), p.login_log(s)
        self._run(fetch, self._loaded)

    def _loaded(self, val) -> None:
        self.members, logs = val
        self._fill()
        lines = []
        for r in logs[:200]:
            at = r.get("at")
            when = at.strftime("%d.%m %H:%M") if at else "?"
            ok = "✓" if r.get("ok") else "✗ " + str(r.get("reason") or "")
            lines.append(f"{when}   {r.get('username', '?'):<18} {ok}")
        self.log.setPlainText("\n".join(lines) if lines else T("Kayıt yok (yerel üyelikte giriş kaydı tutulmaz)."))

    def _fill(self) -> None:
        q = self.search.text().strip().lower()
        rows = [m for m in self.members if not q or q in m.username.lower() or q in (m.note or "").lower()]
        self.table.setRowCount(len(rows))
        now = datetime.now()
        for r, m in enumerate(rows):
            left, col = fmt_left(m)
            state = T("Askıda") if not m.active else (T("Süresi doldu") if m.expired else T("Aktif"))
            fmt = lambda d: d.strftime("%d.%m.%Y %H:%M") if d else "—"      # noqa: E731
            cells = [m.username, "••••••", T("Yönetici") if m.is_admin else T("Üye"), state, left,
                     T("Süresiz") if m.expires_at is None else fmt(m.expires_at),
                     str(m.max_clients) if m.max_clients else "∞",
                     T("kilitli") if m.hwid_lock else T("serbest"),
                     (T("● çevrimiçi") + (f" ({m.sessions})" if m.sessions > 1 else "")) if m.sessions else "—",
                     fmt(m.last_login), fmt(m.last_seen), fmt(m.created_at), m.note or ""]
            for c, txt in enumerate(cells):
                it = QTableWidgetItem(txt)
                it.setData(Qt.UserRole, m.username)
                if c == 4:
                    it.setForeground(QColor(col))
                elif c == 8 and m.sessions:
                    it.setForeground(QColor(theme.SUCCESS))
                elif c == 3:
                    it.setForeground(QColor(theme.SUCCESS if m.active and not m.expired else theme.DANGER))
                self.table.setItem(r, c, it)
        act = [m for m in self.members if m.active and not m.expired]
        self.c_all.set(str(len(self.members)))
        self.c_act.set(str(len(act)))
        self.c_unl.set(str(sum(1 for m in self.members if m.expires_at is None)))
        self.c_soon.set(str(sum(1 for m in act if m.expires_at and m.expires_at - now < timedelta(days=7))))
        self.c_exp.set(str(len(self.members) - len(act)))
        src = T("Supabase") if self.win.provider.name == "supabase" else T("yerel dosya (data/users.json)")
        self.sub.setText(T("{n} üye  ·  kaynak: {src}").format(n=len(self.members), src=src))

    def _selected(self) -> Member | None:
        r = self.table.currentRow()
        if r < 0 or self.table.item(r, 0) is None:
            QMessageBox.information(self, "FishBot", T("Önce listeden bir üye seç."))
            return None
        name = self.table.item(r, 0).data(Qt.UserRole)
        return next((m for m in self.members if m.username == name), None)

    def _show_detail(self) -> None:
        r = self.table.currentRow()
        it = self.table.item(r, 0) if r >= 0 else None
        m = next((x for x in self.members if it and x.username == it.data(Qt.UserRole)), None)
        if m is None:
            return
        fmt = lambda d: d.strftime("%d.%m.%Y %H:%M") if d else "—"      # noqa: E731
        left, col = fmt_left(m)
        vals = {"id": m.id or "—", "username": m.username,
                "password": T("•••••• (şifreli saklanır — 'Şifre değiştir' ile yenisini ver)"),
                "role": T("Yönetici") if m.is_admin else T("Üye"),
                "state": T("Askıda") if not m.active else (T("Süresi doldu") if m.expired else T("Aktif")),
                "left": left, "expires": T("Süresiz") if m.expires_at is None else fmt(m.expires_at),
                "clients": str(m.max_clients) if m.max_clients else T("Sınırsız"),
                "lock": T("kilitli") if m.hwid_lock else T("serbest"), "hwid": m.hwid or "—",
                "online": (T("● çevrimiçi") + f" ({m.sessions})") if m.sessions else T("çevrimdışı"),
                "last_login": fmt(m.last_login), "last_seen": fmt(m.last_seen), "created": fmt(m.created_at),
                "note": m.note or "—"}
        self.d_title.setText(m.username + ("  ★" if m.is_admin else ""))
        for k, v in vals.items():
            self.d_vals[k].setText(v)
        self.d_vals["left"].setStyleSheet(f"font-weight:600; background:transparent; color:{col};")

    def _creds(self, m: Member, pw: str | None) -> None:
        if pw:
            exp = T("Süresiz") if m.expires_at is None else m.expires_at.strftime("%d.%m.%Y %H:%M")
            CredentialsDialog(self, m.username, pw, exp).exec()

    # ------------------------------------------------------------ işlemler
    def _save(self, m: Member, pw: str | None, original: str | None) -> None:
        p, s = self.win.provider, self.win.session

        def after(_):
            self._creds(m, pw)
            self.reload()
        self._run(lambda: p.save_member(s, m, pw, original), after)

    def change_password(self) -> None:
        m = self._selected()
        if m is None:
            return
        import secrets
        import string
        from PySide6.QtWidgets import QInputDialog
        sug = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
        pw, ok = QInputDialog.getText(self, T("Şifre değiştir"),
                                      T("“{0}” için yeni şifre:").format(m.username), QLineEdit.Normal, sug)
        if ok and pw.strip():
            self._save(m, pw.strip(), m.username)

    def new_member(self) -> None:
        d = MemberDialog(self, None)
        if d.exec():
            m, pw = d.result_member()
            self._save(m, pw, None)

    def edit_member(self) -> None:
        m = self._selected()
        if m is None:
            return
        d = MemberDialog(self, m)
        if d.exec():
            nm, pw = d.result_member()
            nm.hwid = m.hwid
            self._save(nm, pw, m.username)

    def add_days(self, n: int) -> None:
        m = self._selected()
        if m is None:
            return
        if m.expires_at is None:
            QMessageBox.information(self, "FishBot", T("Bu üye zaten süresiz."))
            return
        m.expires_at = max(m.expires_at, datetime.now()) + timedelta(days=n)
        self._save(m, None, m.username)

    def make_unlimited(self) -> None:
        m = self._selected()
        if m is None:
            return
        m.expires_at = None
        self._save(m, None, m.username)

    def toggle_active(self) -> None:
        m = self._selected()
        if m is None:
            return
        m.active = not m.active
        self._save(m, None, m.username)

    def reset_hwid(self) -> None:
        m = self._selected()
        if m is None:
            return
        p, s = self.win.provider, self.win.session
        self._run(lambda: p.reset_hwid(s, m.username), lambda _: self.reload())

    def kick(self) -> None:
        m = self._selected()
        if m is None:
            return
        p, s = self.win.provider, self.win.session
        self._run(lambda: p.kick(s, m.username), lambda _: self.reload())

    def delete_member(self) -> None:
        m = self._selected()
        if m is None:
            return
        if QMessageBox.question(self, "FishBot", T("“{0}” üyesi kalıcı olarak silinsin mi?").format(m.username)) != \
                QMessageBox.StandardButton.Yes:
            return
        p, s = self.win.provider, self.win.session
        self._run(lambda: p.delete_member(s, m.username), lambda _: self.reload())


class CredentialsDialog(QDialog):
    """Üyeye gönderilecek giriş bilgileri (şifre sadece burada, bir kez görünür)."""

    def __init__(self, parent, username: str, password: str, expires: str):
        super().__init__(parent)
        self.setWindowTitle(T("Giriş bilgileri"))
        self.setMinimumWidth(420)
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 22, 24, 20)
        v.setSpacing(12)
        t = QLabel(T("Bu bilgileri üyeye gönder"))
        t.setStyleSheet("font-size:16px; font-weight:600;")
        v.addWidget(t)
        info = QLabel(T("Şifre güvenlik için şifrelenmiş saklanır; bu pencere kapanınca bir daha gösterilemez. "
                        "Unutulursa yeni şifre verilir."))
        info.setObjectName("muted")
        info.setWordWrap(True)
        v.addWidget(info)
        self.text = (f"{T('Kullanıcı adı')}: {username}\n{T('Şifre')}: {password}\n{T('Bitiş')}: {expires}")
        box = QPlainTextEdit(self.text)
        box.setObjectName("console")
        box.setReadOnly(True)
        box.setFixedHeight(90)
        v.addWidget(box)
        row = QHBoxLayout()
        row.addStretch()
        cp = QPushButton(T("Kopyala"))
        cp.setObjectName("primary")
        cp.clicked.connect(self._copy)
        ok = QPushButton(T("Kapat"))
        ok.clicked.connect(self.accept)
        row.addWidget(cp)
        row.addWidget(ok)
        v.addLayout(row)

    def _copy(self) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.text)
