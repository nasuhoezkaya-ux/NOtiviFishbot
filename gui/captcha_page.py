"""Captcha menüsü: ayarlar, test, öğrenilen simgeler, yakalanan captcha resimleri ve olaylar — hepsi bir yerde."""
from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QCheckBox, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget,
                               QListWidgetItem, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSpinBox,
                               QVBoxLayout, QWidget)

from core.i18n import T
from core.paths import DATA

from core.version import APP_NAME
from . import theme
from .dashboard import button, card_with_title, page_header
from .help import H
from .widgets import StatCard, bgr_to_qimage

if TYPE_CHECKING:
    from .main_window import MainWindow

SHOT_DIR = DATA / "captcha"


class ClickImage(QLabel):
    """Resmi sığdırarak gösterir; tıklanan noktayı resim koordinatıyla bildirir."""
    clicked = Signal(int, int)

    def __init__(self):
        super().__init__(T("Bir rapor seç"))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"background:{theme.LIVE_BG}; border-radius:10px; color:{theme.FAINT};")
        self.setCursor(Qt.CrossCursor)
        self._img = None
        self._geo = None

    def set_image(self, img) -> None:
        self._img = img
        pm = QPixmap.fromImage(bgr_to_qimage(img))
        sc = pm.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._geo = ((self.width() - sc.width()) // 2, (self.height() - sc.height()) // 2,
                     sc.width() / max(1, img.shape[1]))
        self.setPixmap(sc)

    def mousePressEvent(self, e):
        if self._img is None or self._geo is None:
            return
        ox, oy, f = self._geo
        p = e.position() if hasattr(e, "position") else e.pos()
        x, y = int((p.x() - ox) / f), int((p.y() - oy) / f)
        if 0 <= x < self._img.shape[1] and 0 <= y < self._img.shape[0]:
            self.clicked.emit(x, y)


def _open(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(path))   # noqa: S606
    except Exception:
        pass


class CaptchaPage(QScrollArea):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        cfg = win.cfg
        self.setWidgetResizable(True)
        body = QWidget()
        body.setObjectName("root")
        self.setWidget(body)
        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        head = QHBoxLayout()
        sub = QLabel(T("Sunucu \"Atın üzerine tıklayın\" gibi bir doğrulama penceresi açınca bot balık tutmayı "
                       "durdurur, ne istendiğini okur ve doğru simgeye tıklar. Çözemezse sesli uyarır ve sen "
                       "çözene kadar bekler; elle çözdüğün simgeyi öğrenir."))
        sub.setWordWrap(True)
        head.addLayout(page_header("Captcha", sub), 1)
        lay.addLayout(head)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.c_seen = StatCard("Görülen", color=theme.WARNING)
        self.c_auto = StatCard("Otomatik çözülen", color=theme.SUCCESS)
        self.c_manual = StatCard("Elle çözülen", color=theme.ACCENT)
        self.c_fail = StatCard("Otomatik çözülemeyen", color=theme.DANGER)
        for c in (self.c_seen, self.c_auto, self.c_manual, self.c_fail):
            stats.addWidget(c)
        lay.addLayout(stats)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # ---- ayarlar
        sc, sv = card_with_title("Ayarlar", None, "captcha")
        self.on = QCheckBox(T("Captcha'yı denetle"))
        self.on.setChecked(bool(cfg["captcha_enabled"]))
        self.auto = QCheckBox(T("Otomatik çöz"))
        self.auto.setChecked(bool(cfg["captcha_autosolve"]))
        self.sound = QCheckBox(T("Sesli uyar"))
        self.sound.setChecked(bool(cfg["captcha_sound"]))
        for w in (self.on, self.auto, self.sound):
            sv.addWidget(w)
            w.toggled.connect(self._save)
        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        self.keep = QSpinBox()
        self.keep.setRange(5, 1000)
        self.keep.setValue(int(cfg["captcha_keep"]))
        for r, (lbl, w, key) in enumerate(((T("Saklanacak captcha resmi"), self.keep, "captcha_keep"),)):
            lb = QLabel(lbl)
            lb.setObjectName("kvKey")
            lb.setToolTip(H.get(key, ""))
            form.addWidget(lb, r, 0)
            form.addWidget(w, r, 1)
            w.valueChanged.connect(self._save)
        sv.addLayout(form)
        self.saved = QLabel("")
        self.saved.setObjectName("faint")
        sv.addWidget(self.saved)
        sv.addStretch()
        grid.addWidget(sc, 0, 0)

        # ---- test
        tc, tv = card_with_title("Test", None, "captcha_test")
        hint = QLabel(T("Captcha ekrandayken \"Captcha testi\"ne bas: bot ne okuduğunu ve nereye tıklayacağını "
                        "gösterir (tıklamaz). Önce Client'lar sayfasında bir client seç."))
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        tv.addWidget(hint)
        row = QHBoxLayout()
        b_test = button("Captcha testi", "primary")
        b_test.clicked.connect(self._test)
        row.addWidget(b_test)
        row.addStretch()
        tv.addLayout(row)
        self.test_lbl = QLabel("")
        self.test_lbl.setWordWrap(True)
        self.test_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        tv.addWidget(self.test_lbl)
        self.test_img = QLabel()
        self.test_img.setAlignment(Qt.AlignCenter)
        self.test_img.setMinimumHeight(160)
        self.test_img.setStyleSheet(f"background:{theme.LIVE_BG}; border-radius:10px; color:{theme.FAINT};")
        self.test_img.setText(T("Test görüntüsü burada görünür"))
        tv.addWidget(self.test_img, 1)
        grid.addWidget(tc, 0, 1)

        # ---- öğrenilen simgeler
        self.icons_lbl = QLabel("")
        self.icons_lbl.setObjectName("faint")
        ic, iv = card_with_title("Öğrenilen simgeler", self.icons_lbl)
        d = QLabel(T("Bot bu resimlerle doğru simgeyi bulur. Dosya adı = simgenin adı (kalkan, kilic, at…). "
                     "Bilinmeyen bir simge istenirse bir kez elle çözmen yeter: bot onu buraya ekler."))
        d.setObjectName("muted")
        d.setWordWrap(True)
        iv.addWidget(d)
        self.icons = QListWidget()
        self.icons.setViewMode(QListWidget.IconMode)
        self.icons.setIconSize(QSize(56, 56))
        self.icons.setGridSize(QSize(96, 92))
        self.icons.setResizeMode(QListWidget.Adjust)
        self.icons.setMovement(QListWidget.Static)
        self.icons.setMinimumHeight(220)
        self.icons.setStyleSheet(f"QListWidget {{ background:{theme.LIVE_BG}; border-radius:10px; padding:6px; }}")
        iv.addWidget(self.icons, 1)
        brow = QHBoxLayout()
        for text, fn in (("Yeniden adlandır", self._rename_icon), ("Sil", self._delete_icon),
                         ("Klasörü aç", self._open_icons), ("Yenile", self.reload_icons),
                         ("Depoya aktar…", self._export)):
            b = button(text, "ghost")
            b.clicked.connect(fn)
            brow.addWidget(b)
        brow.addStretch()
        iv.addLayout(brow)
        grid.addWidget(ic, 1, 0)

        # ---- yakalanan captcha'lar
        self.shots_lbl = QLabel("")
        self.shots_lbl.setObjectName("faint")
        hc, hv = card_with_title("Yakalanan captcha'lar", self.shots_lbl)
        hrow = QHBoxLayout()
        self.shots = QListWidget()
        self.shots.setMinimumWidth(190)
        self.shots.setMaximumWidth(240)
        self.shots.currentItemChanged.connect(self._show_shot)
        hrow.addWidget(self.shots)
        self.shot_img = QLabel(T("Bir kayıt seç"))
        self.shot_img.setAlignment(Qt.AlignCenter)
        self.shot_img.setMinimumHeight(220)
        self.shot_img.setStyleSheet(f"background:{theme.LIVE_BG}; border-radius:10px; color:{theme.FAINT};")
        hrow.addWidget(self.shot_img, 1)
        hv.addLayout(hrow, 1)
        brow2 = QHBoxLayout()
        for text, fn in (("Klasörü aç", lambda: _open(SHOT_DIR)), ("Tümünü sil", self._clear_shots),
                         ("Yenile", self.reload_shots)):
            b = button(text, "ghost")
            b.clicked.connect(fn)
            brow2.addWidget(b)
        brow2.addStretch()
        hv.addLayout(brow2)
        grid.addWidget(hc, 1, 1)

        # ---- üyelerden gelen bilinmeyen captcha'lar
        self.rep_lbl = QLabel("")
        self.rep_lbl.setObjectName("faint")
        rc, rv = card_with_title("Üyelerden gelen captcha'lar", self.rep_lbl)
        d2 = QLabel(T("Üyelerde bot tanımadığı bir captcha görünce resmi buraya gelir. Resimde DOĞRU yere tıkla ve "
                      "'Çözüm olarak kaydet'e bas: bot o captcha'yı öğrenir. Sonra 'Depoya aktar…' + yeni sürüm: "
                      "bütün üyelerde otomatik çözülür. Üye elle çözdüyse tıkladığı yer mavi daireyle görünür."))
        d2.setObjectName("muted")
        d2.setWordWrap(True)
        rv.addWidget(d2)
        rrow = QHBoxLayout()
        self.reports = QListWidget()
        self.reports.setMinimumWidth(220)
        self.reports.setMaximumWidth(280)
        self.reports.currentItemChanged.connect(self._show_report)
        rrow.addWidget(self.reports)
        self.rep_img = ClickImage()
        self.rep_img.setMinimumHeight(280)
        self.rep_img.clicked.connect(self._report_click)
        rrow.addWidget(self.rep_img, 1)
        rv.addLayout(rrow, 1)
        rb = QHBoxLayout()
        for text, fn, kind in (("Çözüm olarak kaydet", self._report_learn, "primary"),
                               ("Üyenin tıkladığı yer doğru", self._report_use_member, ""),
                               ("Çözüldü işaretle", lambda: self._report_done(False), "ghost"),
                               ("Sil", lambda: self._report_done(True), "ghost"),
                               ("Yenile", self.reload_reports, "ghost")):
            b = button(text, kind)
            b.clicked.connect(fn)
            rb.addWidget(b)
        rb.addStretch()
        rv.addLayout(rb)
        self.rep_status = QLabel("")
        self.rep_status.setObjectName("faint")
        rv.addWidget(self.rep_status)
        grid.addWidget(rc, 2, 0, 1, 2)
        self._reports: list[dict] = []
        self._rep_pick = None

        # ---- olaylar
        ec, ev = card_with_title("Captcha olayları")
        self.events = QPlainTextEdit()
        self.events.setObjectName("console")
        self.events.setReadOnly(True)
        self.events.setMaximumBlockCount(1000)
        self.events.setMinimumHeight(150)
        ev.addWidget(self.events)
        grid.addWidget(ec, 3, 0, 1, 2)
        lay.addLayout(grid)
        lay.addStretch()

        win.bridge.test_result.connect(self._on_test)
        self._test_frame = None
        self.reload_icons()
        self.reload_shots()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, self.reload_reports)
        self._rep_timer = QTimer(self)
        self._rep_timer.timeout.connect(self.reload_reports)
        self._rep_timer.start(120_000)            # üyelerden yeni rapor gelmiş mi (2 dakikada bir)

    # ------------------------------------------------------------ ayarlar
    def _save(self, *_):
        c = self.win.cfg
        c.set("captcha_enabled", self.on.isChecked())
        c.set("captcha_autosolve", self.auto.isChecked())
        c.set("captcha_sound", self.sound.isChecked())
        c.set("captcha_keep", int(self.keep.value()))
        c.save()
        self.saved.setText(T("✓ Kaydedildi ({0}).").format(datetime.now().strftime("%H:%M:%S")))

    def tick(self) -> None:
        st = list(self.win.dashboard.stats.values())
        tot = lambda k: sum(int(d.get(k, 0) or 0) for d in st)      # noqa: E731
        self.c_seen.set(str(tot("captcha_seen")))
        self.c_auto.set(str(tot("captchas")))
        self.c_manual.set(str(tot("captcha_manual")))
        self.c_fail.set(str(tot("captcha_fail")))

    def add_event(self, line: str) -> None:
        self.events.appendPlainText(line)
        if "algılandı" in line or "CAPTCHA" in line or "detected" in line or "erkannt" in line:
            self.reload_shots()

    # ------------------------------------------------------------ simgeler
    def _reload_solvers(self) -> None:
        for w in self.win.workers.values():
            try:
                w.captcha.reload()
            except Exception:
                pass

    def reload_icons(self) -> None:
        from core.captcha import ITEM_DIR
        ITEM_DIR.mkdir(parents=True, exist_ok=True)
        self.icons.clear()
        files = sorted(ITEM_DIR.glob("*.png"), key=lambda p: p.stem.lower())
        for p in files:
            it = QListWidgetItem(QIcon(QPixmap(str(p))), p.stem)
            it.setData(Qt.UserRole, str(p))
            it.setToolTip(p.name)
            self.icons.addItem(it)
        self.icons_lbl.setText(T("{n} simge").format(n=len(files)))

    def _sel_icon(self) -> Path | None:
        it = self.icons.currentItem()
        return Path(it.data(Qt.UserRole)) if it else None

    def _rename_icon(self) -> None:
        p = self._sel_icon()
        if p is None:
            return
        name, ok = QInputDialog.getText(self, T("Yeniden adlandır"), T("Simgenin adı (ör. kalkan, at):"), text=p.stem)
        name = (name or "").strip().replace(" ", "_")
        if not ok or not name or name == p.stem:
            return
        dst = p.with_name(name + ".png")
        k = 2
        while dst.exists():
            dst = p.with_name(f"{name}_{k}.png")
            k += 1
        p.rename(dst)
        self.reload_icons()
        self._reload_solvers()

    def _delete_icon(self) -> None:
        p = self._sel_icon()
        if p is None:
            return
        if QMessageBox.question(self, APP_NAME, T("“{0}” simgesi silinsin mi?").format(p.stem)) != \
                QMessageBox.StandardButton.Yes:
            return
        p.unlink(missing_ok=True)
        self.reload_icons()
        self._reload_solvers()

    def _open_icons(self) -> None:
        from core.captcha import ITEM_DIR
        _open(ITEM_DIR)

    def _export(self) -> None:
        """Öğrenilen captcha resimlerini GitHub deposunun klasörüne kopyala: commit + yayın sonrası bütün
        üyelere güncellemeyle gider."""
        import shutil
        from PySide6.QtWidgets import QFileDialog
        from core.paths import ASSETS, FROZEN
        if not FROZEN:
            QMessageBox.information(self, APP_NAME, T("Bot kaynak koddan çalışıyor: öğrenilen resimler zaten "
                                                     "projenin assets\\captcha klasöründe. GitHub Desktop'ta "
                                                     "Commit + Push yap, sonra yeni sürüm yayınla."))
            return
        d = QFileDialog.getExistingDirectory(self, T("GitHub deposunun klasörünü seç (içinde main.py olan)"))
        if not d:
            return
        dst = Path(d) / "assets" / "captcha"
        if not (Path(d) / "main.py").exists():
            QMessageBox.warning(self, APP_NAME, T("Bu klasörde main.py yok — deponun ana klasörünü seç."))
            return
        n = 0
        src = ASSETS / "captcha"
        for f in src.rglob("*.png"):
            t = dst / f.relative_to(src)
            t.parent.mkdir(parents=True, exist_ok=True)
            if not t.exists() or t.read_bytes() != f.read_bytes():
                shutil.copy2(f, t)
                n += 1
        QMessageBox.information(self, APP_NAME, T("{n} resim depoya kopyalandı. GitHub Desktop'ta Commit + Push "
                                                  "yap, sonra yeni sürüm yayınla: üyelere güncellemeyle gider.").format(n=n))

    # ------------------------------------------------------------ yakalanan resimler
    def reload_shots(self) -> None:
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
        cur = self.shots.currentItem().data(Qt.UserRole) if self.shots.currentItem() else None
        self.shots.clear()
        files = sorted(SHOT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in files:
            parts = p.stem.split("_")
            try:
                when = datetime.strptime(parts[0] + parts[1], "%Y%m%d%H%M%S").strftime("%d.%m  %H:%M:%S")
                label = f"{when}   PID {parts[2]}"
            except Exception:
                label = p.stem
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, str(p))
            self.shots.addItem(it)
            if str(p) == cur:
                self.shots.setCurrentItem(it)
        self.shots_lbl.setText(T("{n} kayıt").format(n=len(files)))

    def _show_shot(self, it, _prev=None) -> None:
        if it is None:
            return
        pm = QPixmap(it.data(Qt.UserRole))
        if pm.isNull():
            return
        self.shot_img.setPixmap(pm.scaled(self.shot_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _clear_shots(self) -> None:
        if QMessageBox.question(self, APP_NAME, T("Yakalanan bütün captcha resimleri silinsin mi?")) != \
                QMessageBox.StandardButton.Yes:
            return
        for p in SHOT_DIR.glob("*.png"):
            p.unlink(missing_ok=True)
        self.shot_img.setText(T("Bir kayıt seç"))
        self.reload_shots()

    # ------------------------------------------------------------ üye raporları
    def reload_reports(self) -> None:
        p, s = self.win.provider, self.win.session
        self.rep_status.setText(T("Sunucuyla konuşuluyor…"))

        def run():
            try:
                rows = p.captcha_reports(s)
                err = ""
            except Exception as e:  # noqa: BLE001
                rows, err = [], str(e)
            self._rep_rows, self._rep_err = rows, err
            self.win.bridge.test_result.emit("\x01rep")
        threading.Thread(target=run, daemon=True).start()

    def _on_reports(self) -> None:
        self._reports = getattr(self, "_rep_rows", [])
        err = getattr(self, "_rep_err", "")
        self.reports.clear()
        for r in self._reports:
            at = r.get("created_at")
            when = at.strftime("%d.%m %H:%M") if at else "?"
            mark = "✓ " if r.get("done") else ("● " if r.get("solved") else "○ ")
            it = QListWidgetItem(f"{mark}{when}  {r.get('username') or '?'}")
            it.setToolTip(r.get("title") or "")
            self.reports.addItem(it)
        new = sum(1 for r in self._reports if not r.get("done"))
        self.rep_lbl.setText(T("{n} yeni").format(n=new))
        self.rep_status.setText(T(err) if err else "")

    def _cur_report(self):
        i = self.reports.currentRow()
        return (i, self._reports[i]) if 0 <= i < len(self._reports) else (None, None)

    def _report_frame(self, r):
        import base64
        import numpy as np
        buf = np.frombuffer(base64.b64decode(r["image"]), np.uint8)
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)

    def _show_report(self, *_):
        _i, r = self._cur_report()
        if r is None:
            return
        img = self._report_frame(r)
        if img is None:
            return
        self._rep_pick = None
        self._rep_cur = img
        self._draw_report()
        self.rep_status.setText((r.get("title") or T("(soru okunamadı)")) +
                                ("  ·  " + T("üye elle çözdü") if r.get("solved") else ""))

    def _draw_report(self) -> None:
        img = self._rep_cur.copy()
        _i, r = self._cur_report()
        if r and r.get("click_x") is not None:
            cv2.circle(img, (int(r["click_x"]), int(r["click_y"])), 14, (255, 160, 40), 2)
        if self._rep_pick:
            cv2.circle(img, self._rep_pick, 16, (255, 40, 200), 3)
            cv2.drawMarker(img, self._rep_pick, (255, 40, 200), cv2.MARKER_CROSS, 14, 2)
        self.rep_img.set_image(img)

    def _report_click(self, x: int, y: int) -> None:
        if getattr(self, "_rep_cur", None) is None:
            return
        self._rep_pick = (x, y)
        self._draw_report()

    def _report_use_member(self) -> None:
        _i, r = self._cur_report()
        if r is None or r.get("click_x") is None:
            self.rep_status.setText(T("Bu raporda üyenin tıkladığı bir yer yok."))
            return
        self._rep_pick = (int(r["click_x"]), int(r["click_y"]))
        self._report_learn()

    def _report_learn(self) -> None:
        i, r = self._cur_report()
        if r is None or self._rep_pick is None:
            self.rep_status.setText(T("Önce resimde doğru yere tıkla."))
            return
        from dataclasses import replace

        import numpy as np
        from core.captcha import CaptchaSolver
        img = self._rep_cur
        # resmi büyük bir kareye yerleştir (pencere bulma ekranın kenarlarına bakmaz)
        H, W = img.shape[:2]
        big = np.full((H + 200, W + 200, 3), 20, np.uint8)
        big[100:100 + H, 100:100 + W] = img
        sol = CaptchaSolver(self.win.cfg)
        found = sol.detect(big, allow_full_ocr=True)
        if found is None:
            self.rep_status.setText(T("Bu resimde captcha penceresi bulunamadı."))
            return
        x, y = self._rep_pick[0] + 100, self._rep_pick[1] + 100
        if found.target:
            name = found.target
        else:
            name, ok = QInputDialog.getText(self, T("Captcha adı"),
                                            T("Bu captcha'ya kısa bir ad ver (ör. canta):"),
                                            text=sol.new_name())
            if not ok or not name.strip():
                return
            name = name.strip().lower().replace(" ", "_")
        f2 = replace(found, target=name)
        pi = sol.learn_patch(big, f2, x, y, name)
        pt = sol.learn_title(big, f2, variant=True) if not found.target else None
        if pi:
            self.rep_status.setText(T("✓ Öğrenildi: {0}. 'Depoya aktar…' + yeni sürümle üyelere gider.").format(
                ", ".join(Path(p).name for p in (pi, pt) if p)))
            self._reload_solvers()
            self.reload_icons()
            self._report_done(False)
        else:
            self.rep_status.setText(T("Kaydedilemedi — başka bir noktaya tıklayıp tekrar dene."))

    def _report_done(self, delete: bool) -> None:
        i, r = self._cur_report()
        if r is None:
            return
        p, s = self.win.provider, self.win.session

        def run():
            try:
                p.captcha_report_done(s, r["id"], delete)
            except Exception:
                pass
            self.reload_reports()
        threading.Thread(target=run, daemon=True).start()

    # ------------------------------------------------------------ test
    def _test(self) -> None:
        pid = self.win.preview_pid
        game = self.win.dashboard.games.get(pid) if pid else None
        if game is None:
            self.test_lbl.setText(T("Captcha: önce Panel'de bir client seç (F7 veya listeden tıkla)."))
            return
        self.test_lbl.setText(T("Captcha: ekran okunuyor…"))

        def run():
            img = None
            try:
                from core import ocr
                from core.captcha import CaptchaSolver
                from core.winapi import WindowCapture
                frame = WindowCapture(game.hwnd).grab()
                if frame is None:
                    msg = T("Captcha: oyun penceresinin görüntüsü alınamadı.")
                else:
                    sol = CaptchaSolver(self.win.cfg)
                    st = ocr.status()
                    found = sol.detect(frame)
                    img = frame.copy()
                    if found is None:
                        msg = T('Captcha: ekranda captcha bulunamadı. [{0}] ').format(st)
                    else:
                        hit = sol.find_click(frame, found)
                        msg = T("Captcha bulundu: “{0}” → istenen: {1}.").format(found.instruction, found.target or "?")
                        if hit:
                            msg += " " + T("Tıklanacak: {0} (x={1}, y={2}).").format(hit[2], hit[0], hit[1])
                            cv2.circle(img, (int(hit[0]), int(hit[1])), 18, (255, 40, 200), 3)
                        else:
                            msg += " " + T("Tıklanacak yer BULUNAMADI — bir kez elle çöz, bot simgeyi öğrensin.")
                        msg += T(' [{0}] Kayıtlı resimler: {1}').format(st, ', '.join(sol.item_names) or '—')
            except Exception as e:  # noqa: BLE001
                msg = T('Captcha testi hatası: {0!r}').format(e)
            self._test_frame = img
            self.win.bridge.test_result.emit("\x01cpg" + msg)

        threading.Thread(target=run, daemon=True).start()

    def _on_test(self, m: str) -> None:
        if m.startswith("\x01rep"):
            self._on_reports()
            return
        if not m.startswith("\x01cpg"):
            return
        self.test_lbl.setText(m[4:])
        img = self._test_frame
        if img is not None:
            pm = QPixmap.fromImage(bgr_to_qimage(img))
            self.test_img.setPixmap(pm.scaled(self.test_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
