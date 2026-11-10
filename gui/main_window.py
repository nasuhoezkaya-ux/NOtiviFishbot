"""Ana pencere: Client'lar, Ayarlar, Kayıtlar."""
from __future__ import annotations

from core.paths import DATA

import time
from datetime import datetime

from PySide6.QtCore import QObject, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
                               QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

from core.auth import AuthProvider, Session
from core.bot import BotWorker
from core.config import Config
from core.i18n import LANGS, T
from core.timing import BarReader, BiteWatcher, draw_bar, draw_bite
from core.winapi import (INPUT_METHODS, KEY_NAMES, GameWindow, WindowCapture, key_down, list_game_windows,
                         make_input, window_alive, window_under_cursor)

from core.version import APP_NAME
from . import theme
from .help import H, help_label, tip
from .captcha_page import CaptchaPage
from .dashboard import DashboardPage
from .fx import AccountCard, Brand, NavButton
from .widgets import Card, StatusDot


MAX_CLIENTS = 4      # aynı anda en fazla bu kadar client (zamanlama basışları çakışmasın diye)


class Bridge(QObject):
    """Bot thread'lerinden arayüze güvenli sinyal köprüsü."""
    log = Signal(int, str)
    state = Signal(int, str)
    stats = Signal(int, object)
    frame = Signal(int, object)
    round = Signal(int, object)
    test_result = Signal(str)
    scan = Signal(int, str)


def fmt_duration(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


# ====================================================================== Ayarlar
class SettingsPage(QScrollArea):
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
        tcol = QVBoxLayout()
        t = QLabel(T("Ayarlar"))
        t.setObjectName("h1")
        sub = QLabel(T("Her ayarın yanındaki <b style='color:%s'>?</b> simgesinin üstüne gel: ne işe yaradığı, "
                       "önerilen değer ve artırınca / azaltınca ne olacağı yazar.") % theme.ACCENT)
        sub.setObjectName("pageSub")
        sub.setWordWrap(True)
        tcol.addWidget(t)
        tcol.addWidget(sub)
        head.addLayout(tcol, 1)
        btn_rec = QPushButton(T("↺  Önerilen ayarlar"))
        btn_rec.setToolTip(tip(T("Önerilen ayarlar"),
                               T("Bütün alanları önerilen değerlere getirir. Kaydet'e basana kadar uygulanmaz. "
                               "Seçtiğin işaret alanı, öğrenilen gecikme ve kısayollar değişmez.")))
        btn_rec.clicked.connect(self._recommended)
        head.addWidget(btn_rec, 0, Qt.AlignTop)
        lay.addLayout(head)

        class Section:
            """Başlıklı kart + açıklamalı form satırları."""

            def __init__(self, icon: str, title: str, desc: str = ""):
                card = Card()
                v = QVBoxLayout(card)
                v.setContentsMargins(22, 18, 22, 18)
                v.setSpacing(8)
                hr = QHBoxLayout()
                ic = QLabel(icon)
                ic.setStyleSheet("font-size:18px;")
                h = QLabel(T(title))
                h.setObjectName("section")
                hr.addWidget(ic)
                hr.addWidget(h)
                hr.addStretch(1)
                v.addLayout(hr)
                if desc:
                    d = QLabel(T(desc))
                    d.setObjectName("sectionDesc")
                    d.setWordWrap(True)
                    v.addWidget(d)
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet(f"background:{theme.BORDER};")
                v.addWidget(line)
                self.f = QFormLayout()
                self.f.setHorizontalSpacing(28)
                self.f.setVerticalSpacing(12)
                self.f.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
                v.addLayout(self.f)
                lay.addWidget(card)

            def add(self, text: str, key: str | None, field) -> None:
                lbl = help_label(text, H.get(key) if key else None)
                lbl.setMinimumWidth(230)
                if isinstance(field, QWidget):
                    if key and H.get(key):
                        field.setToolTip(H[key])
                    self.f.addRow(lbl, field)
                else:
                    self.f.addRow(lbl, field)

        def keybox(val: str) -> QComboBox:
            c = QComboBox()
            c.addItems(KEY_NAMES)
            c.setCurrentText(str(val).upper())
            return c

        def spin(lo, hi, val, suffix="", step=1) -> QSpinBox:
            sp = QSpinBox()
            sp.setRange(lo, hi)
            sp.setSingleStep(step)
            sp.setValue(int(val))
            sp.setSuffix(T(suffix))
            sp.setMaximumWidth(180)
            return sp

        def dspin(lo, hi, val, step=0.1, suffix="") -> QDoubleSpinBox:
            sp = QDoubleSpinBox()
            sp.setRange(lo, hi)
            sp.setSingleStep(step)
            sp.setValue(float(val))
            sp.setSuffix(T(suffix))
            sp.setMaximumWidth(180)
            return sp

        def pair(a, mid: str, b) -> QHBoxLayout:
            r = QHBoxLayout()
            r.addWidget(a)
            m = QLabel(T(mid))
            m.setObjectName("muted")
            r.addWidget(m)
            r.addWidget(b)
            r.addStretch(1)
            return r

        # --- 1. Balık sistemi
        sec = Section("🐟", T("Balık sistemi"),
                      T("Space ile olta atılır → karakterinin kafasında balık işareti çıkınca Space → açılan pencerede "
                      "siyah balık kutucuğun ORTASINA (mor nokta) gelince Space → ödül çarkı kendiliğinden döner → "
                      "pencere kapanınca baştan. Kutucuğun yeri her seferinde bulunur; tuş gecikmesi her turda "
                      "ölçülüp öğrenilir."))
        self.bite_to = spin(5, 300, cfg["bite_timeout_s"], " sn")
        self.react_min = spin(0, 2000, cfg["bite_react_min_ms"], " ms", 10)
        self.react_max = spin(0, 2000, cfg["bite_react_max_ms"], " ms", 10)
        self.lat = spin(0, 400, cfg["timing_latency_ms"], " ms", 5)
        self.lat_auto = QCheckBox(T("her turda kendisi öğrensin"))
        self.lat_auto.setChecked(bool(cfg["timing_autolearn"]))
        lrow = QHBoxLayout()
        lrow.addWidget(self.lat)
        lrow.addWidget(self.lat_auto)
        lrow.addStretch(1)
        self.bite_chg = QCheckBox(T("İşaret resimle bulunamazsa ani beliren şekille de ara (yedek)"))
        self.bite_chg.setChecked(bool(cfg["bite_change"]))
        self.tm_lbl = QLabel(T("Pencere açıkken \"Pencere testi\"ne bas: bot kutucuğu ve balığı bulabiliyor mu gösterir."))
        self.tm_lbl.setObjectName("muted")
        self.tm_lbl.setWordWrap(True)
        b_bar = QPushButton(T("Pencere testi"))
        b_bar.clicked.connect(self._test_bar)
        b_sign = QPushButton(T("İşaret testi"))
        b_sign.clicked.connect(self._test_sign)
        b_sdir = QPushButton(T("İşaret klasörü"))
        b_sdir.clicked.connect(self._open_sign_dir)
        trow0 = QHBoxLayout()
        for b_ in (b_bar, b_sign, b_sdir):
            trow0.addWidget(b_)
        trow0.addWidget(self.tm_lbl, 1)
        b_head = QPushButton(T("🎯  Alanı seç…"))
        b_head.clicked.connect(self._pick_head)
        self.head_lbl = QLabel()
        self.head_lbl.setObjectName("muted")
        self.head_lbl.setWordWrap(True)
        hrow = QHBoxLayout()
        hrow.addWidget(b_head)
        hrow.addWidget(self.head_lbl, 1)
        self._head_text()
        sec.add(T("Kendi karakterimin işaret alanı"), "bite_area", hrow)
        sec.add(T("Balık işaretini en fazla bekle"), "bite_timeout", self.bite_to)
        sec.add(T("İşareti görünce basmadan önce"), "bite_react", pair(self.react_min, "ile", self.react_max))
        sec.add(T("Tuş gecikmesi payı"), "timing_latency", lrow)
        sec.add(T("İşaret arama"), "bite_change", self.bite_chg)
        self.streak = QCheckBox(T("Sonucu oyunun Seri sayacıyla doğrula ve gerekirse düzelt"))
        self.streak.setChecked(bool(cfg["streak_check"]))
        sec.add(T("Seri kontrolü"), "streak_check", self.streak)
        sec.add(T("Test"), "timing_test", trow0)
        win.bridge.test_result.connect(lambda m: self.tm_lbl.setText(m[4:]) if m.startswith("\x01bar") else None)

        # --- 2. Olta, mola ve giriş
        sec = Section("🎣", T("Olta ve giriş"), T("Tuşun oyuna nasıl gönderileceği ve turlar arasındaki bekleme."))
        self.cast_key = keybox(cfg["cast_key"])
        self.cast_key.setMaximumWidth(180)
        self.cd_min = spin(0, 20000, cfg["cooldown_min_ms"], " ms", 100)
        self.cd_max = spin(0, 20000, cfg["cooldown_max_ms"], " ms", 100)
        self.method = QComboBox()
        for key, text in INPUT_METHODS.items():
            if key == "paralel":
                continue                     # fare mesajı modu: yeni sistemde fare yok
            self.method.addItem(text, key)
        self.method.setCurrentIndex(max(0, self.method.findData(cfg["input_method"])))
        self.method.setMaximumWidth(360)
        trow = QHBoxLayout()
        btn_test = QPushButton(T("⌨  Tuşu test et"))
        btn_test.setToolTip(H["key_test"])
        btn_test.clicked.connect(self._test_key)
        self.test_lbl = QLabel(T("Karakterin elinde olta varken bas."))
        self.test_lbl.setObjectName("muted")
        self.test_lbl.setWordWrap(True)
        trow.addWidget(btn_test)
        trow.addWidget(self.test_lbl, 1)
        win.bridge.test_result.connect(lambda m: self.test_lbl.setText(m[4:]) if m.startswith("\x01key") else None)
        self.brk = QCheckBox(T("Açık"))
        self.brk.setChecked(bool(cfg["break_enabled"]))
        b_every, b_len = cfg["break_every_min"], cfg["break_len_min"]
        self.brk_e1 = spin(5, 600, b_every[0], " dk")
        self.brk_e2 = spin(5, 600, b_every[1], " dk")
        self.brk_l1 = spin(1, 120, b_len[0], " dk")
        self.brk_l2 = spin(1, 120, b_len[1], " dk")
        self.pfps = spin(5, 120, cfg["preview_fps"], " kare/sn")
        self.sfps = spin(5, 120, cfg["scan_fps"], " kare/sn")
        self.lang = QComboBox()
        for code, name in LANGS.items():
            self.lang.addItem(name, code)
        self.lang.setCurrentIndex(max(0, self.lang.findData(cfg["language"])))
        self.lang.setMaximumWidth(220)
        sec.add(T("Tuş"), "cast_key", self.cast_key)
        sec.add(T("Giriş yöntemi"), "input_method", self.method)
        sec.add(T("Tuş testi"), "key_test", trow)
        sec.add(T("Ödülden sonra olta atmadan önce"), "cooldown", pair(self.cd_min, "ile", self.cd_max))
        sec.add(T("Akıllı mola"), "break", self.brk)
        sec.add(T("Mola sıklığı"), "break_every", pair(self.brk_e1, "ile", self.brk_e2))
        sec.add(T("Mola süresi"), "break_len", pair(self.brk_l1, "ile", self.brk_l2))
        sec.add(T("Canlı görüntü kare hızı"), "preview_fps", self.pfps)
        sec.add(T("İşaret arama hızı"), "scan_fps", self.sfps)
        sec.add(T("Dil / Language / Sprache"), "language", self.lang)

        # --- 4. Client'lar ve kısayollar
        sec = Section("🖥", T("Client'lar ve kısayollar"), T("Hangi pencerelerin oyun client'ı sayılacağı."))
        self.filter = QLineEdit(cfg["process_filter"])
        self.filter.setMaximumWidth(360)
        self.pick_key = keybox(cfg["pick_key"])
        self.pick_key.setMaximumWidth(180)
        self.known_lbl = QLabel()
        self.known_lbl.setObjectName("muted")
        self.known_lbl.setWordWrap(True)
        clr = QPushButton(T("Temizle"))
        clr.clicked.connect(self._clear_known)
        krow = QHBoxLayout()
        krow.addWidget(self.known_lbl, 1)
        krow.addWidget(clr)
        self.blocked_lbl = QLabel()
        self.blocked_edit = QLineEdit(", ".join(cfg["blocked_exes"] or []))
        sec.add(T("Client seçme tuşu"), "pick_key", self.pick_key)
        sec.add(T("Süreç filtresi"), "filter", self.filter)
        sec.add(T("Hatırlanan client'lar"), "known", krow)
        sec.add(T("Engellenen programlar"), "blocked", self.blocked_edit)
        self.refresh_known()

        row = QHBoxLayout()
        row.addStretch()
        self.saved = QLabel("")
        self.saved.setObjectName("muted")
        save = QPushButton(T("Kaydet"))
        save.setObjectName("primary")
        save.setMinimumWidth(160)
        save.clicked.connect(self.save)
        row.addWidget(self.saved)
        row.addWidget(save)
        lay.addLayout(row)
        lay.addStretch()
    def showEvent(self, e) -> None:
        """Sayfa açılınca botun öğrendiği değerleri (gecikme) göster."""
        self.lat.setValue(int(self.win.cfg["timing_latency_ms"]))
        self._head_text()
        super().showEvent(e)

    def _recommended(self) -> None:
        """Alanları önerilen değerlere getirir (Kaydet'e basılana kadar uygulanmaz)."""
        self.bite_to.setValue(40)
        self.react_min.setValue(90)
        self.react_max.setValue(200)
        self.lat_auto.setChecked(True)
        self.bite_chg.setChecked(True)
        self.cd_min.setValue(1200)
        self.cd_max.setValue(1800)
        self.method.setCurrentIndex(max(0, self.method.findData("karma")))
        self.pfps.setValue(60)
        self.sfps.setValue(60)
        self.saved.setText(T("Önerilen değerler yüklendi — uygulamak için Kaydet'e bas."))

    def _selected_game(self):
        pid = self.win.preview_pid
        return self.win.dashboard.games.get(pid) if pid else None

    def _head_text(self) -> None:
        a = self.win.cfg["bite_area"]
        self.head_lbl.setText(T('Seçili: {0}×{1} px — bot sadece buradaki işarete tepki verir.').format((a['w']), (a['h'])) if isinstance(a, dict)
                              else T("Seçilmedi: ekranın ortasındaki (kendi) karakterine en yakın işaret kullanılır. "
                                   "Yanında balık tutan oyuncular varsa alanı seç."))

    def _pick_head(self) -> None:
        game = self._selected_game()
        if game is None:
            self.head_lbl.setText(T("Önce Panel'de bir client seç (F7 veya listeden tıkla)."))
            return
        from .head_dialog import HeadAreaDialog
        HeadAreaDialog(game, self.win.cfg, self).exec()
        self._head_text()

    def _test_bar(self) -> None:
        """Seçili client'ta zamanlama penceresini arar; kutucuk ve balık bulunuyor mu yazar."""
        game = self._selected_game()
        if game is None:
            self.tm_lbl.setText(T("Pencere testi: önce Panel'de bir client seç (F7 veya listeden tıkla)."))
            return
        self.tm_lbl.setText(T("Pencere testi: ekran okunuyor…"))
        import threading

        def run():
            try:
                from pathlib import Path
                import cv2
                from core.timing import BarReader, draw_bar
                from core.winapi import WindowCapture
                frame = WindowCapture(game.hwnd).grab()
                if frame is None:
                    msg = T("Pencere testi: oyun penceresinin görüntüsü alınamadı.")
                else:
                    r = BarReader()
                    bar = r.find(frame)
                    if bar is None:
                        msg = (T("Pencere testi: zamanlama penceresi bulunamadı. Pencere ekrandayken (siyah balık "
                               "giderken) tekrar dene."))
                    else:
                        rd = r.read(frame, bar)
                        d = DATA
                        d.mkdir(parents=True, exist_ok=True)
                        cv2.imwrite(str(d / "pencere_testi.png"), draw_bar(frame, rd, float(self.win.cfg["timing_latency_ms"])))
                        parts = [T("çubuk {w}×{h} px").format(w=bar[2], h=bar[3])]
                        parts.append(T("kutucuk x={a}-{b}").format(a=f"{rd.box[0]:.0f}", b=f"{rd.box[1]:.0f}") if rd.box
                                     else T("KUTUCUK BULUNAMADI"))
                        parts.append(T("balık x={x}").format(x=f"{rd.fish_x:.0f}") if rd.fish else T("BALIK BULUNAMADI"))
                        if rd.box:
                            parts[-2] += " (" + (T("lacivert çerçeveden") if rd.box_how == "cerceve"
                                                 else T("renkten — yedek yöntem")) + ")"
                        if rd.box and rd.fish:
                            parts.append(T("balık kutucuk ortasına {d} px").format(d=f"{rd.fish_x - rd.box_c:+.0f}"))
                        from core.streak import read_glyph
                        parts.append(T("seri sayısı okundu") if read_glyph(frame, bar) is not None
                                     else T("SERİ SAYISI OKUNAMADI"))
                        msg = T("Pencere testi: ✓ pencere bulundu — ") + ", ".join(parts) + " (data\\pencere_testi.png)"
            except Exception as e:  # noqa: BLE001
                msg = T('Pencere testi: hata — {0}').format((e))
            self.win.bridge.test_result.emit("\x01bar" + msg)

        threading.Thread(target=run, daemon=True).start()

    def _test_sign(self) -> None:
        """Kafadaki balık işareti resimleriyle seçili client'ı tarar."""
        game = self._selected_game()
        if game is None:
            self.tm_lbl.setText(T("İşaret testi: önce Panel'de bir client seç (F7 veya listeden tıkla)."))
            return
        import threading

        def run():
            try:
                import cv2
                from core.timing import BiteWatcher
                from core.winapi import WindowCapture
                frame = WindowCapture(game.hwnd).grab()
                bw = BiteWatcher(self.win.cfg)
                if frame is None:
                    msg = T("İşaret testi: oyun penceresinin görüntüsü alınamadı.")
                elif not bw.templates:
                    msg = (T("İşaret testi: henüz işaret resmi yok. Bot ilk balıkta işareti kendisi öğrenir; istersen "
                           "işaretin ekran görüntüsünü kırpıp assets\\olta\\isaret klasörüne koy."))
                else:
                    x0, y0, x1, y1 = bw.region(frame.shape)
                    roi = frame[y0:y1, x0:x1]
                    best = 0.0
                    for im, m, _n in bw.templates:
                        if im.shape[0] < roi.shape[0] and im.shape[1] < roi.shape[1]:
                            r = cv2.matchTemplate(roi, im, cv2.TM_CCOEFF_NORMED, mask=m) if m is not None else \
                                cv2.matchTemplate(roi, im, cv2.TM_CCOEFF_NORMED)
                            best = max(best, float(r.max()))
                    thr = float(self.win.cfg["bite_threshold"])
                    msg = (T('İşaret testi: {0} resim, en iyi benzerlik {1:.2f} (eşik {2:.2f}) — ').format((len(bw.templates)), (best), (thr))
                           + (T("✓ işaret ekranda.") if best >= thr else T("işaret şu an ekranda değil "
                              "(işaret görünürken tekrar dene).")))
            except Exception as e:  # noqa: BLE001
                msg = T('İşaret testi: hata — {0}').format((e))
            self.win.bridge.test_result.emit("\x01bar" + msg)

        threading.Thread(target=run, daemon=True).start()

    def _open_sign_dir(self) -> None:
        import os
        from core.timing import SIGN_DIR
        SIGN_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(SIGN_DIR)   # noqa: S606
        except Exception as e:  # noqa: BLE001
            self.tm_lbl.setText(T('İşaret klasörü: {0} ({1})').format((SIGN_DIR), (e)))

    def _test_key(self) -> None:
        pid = self.win.preview_pid
        game = self.win.dashboard.games.get(pid) if pid else None
        if game is None:
            self.test_lbl.setText(T("Önce Panel'de bir client seç (F7 veya listeden tıkla)."))
            return
        method = self.method.currentData()
        key = self.cast_key.currentText()
        self.test_lbl.setText(T('{0} gönderiliyor → PID {1} ({2})…').format((key), (pid), (method)))
        import threading

        def run():
            try:
                make_input(method, game.hwnd).key(key)
                msg = (T("✓ {0} gönderildi (PID {1}, {2}). Oyunda olta atıldıysa bu yöntem çalışıyor; Kaydet'e bas. Atılmadıysa başka bir yöntem dene.").format((key), (pid), (method)))
            except Exception as e:  # noqa: BLE001
                msg = T('Hata: {0}').format((e))
            self.win.bridge.log.emit(0, msg)
            self.win.bridge.test_result.emit("\x01key" + msg)   # thread'den arayüze güvenli

        threading.Thread(target=run, daemon=True).start()

    def refresh_known(self) -> None:
        known = ", ".join(self.win.cfg["known_exes"] or []) or "—"
        self.known_lbl.setText(T("Hatırlanan client'lar: {0}").format((known)))
        self.blocked_edit.setText(", ".join(self.win.cfg["blocked_exes"] or []))

    def _clear_known(self) -> None:
        self.win.cfg.set("known_exes", [])
        self.win.cfg.save()
        self.refresh_known()

    def save(self) -> None:
        c = self.win.cfg
        c.set("bite_timeout_s", int(self.bite_to.value()))
        c.set("bite_react_min_ms", min(self.react_min.value(), self.react_max.value()))
        c.set("bite_react_max_ms", max(self.react_min.value(), self.react_max.value()))
        c.set("timing_latency_ms", int(self.lat.value()))
        c.set("timing_autolearn", self.lat_auto.isChecked())
        c.set("bite_change", self.bite_chg.isChecked())
        c.set("cast_key", self.cast_key.currentText())
        c.set("cooldown_min_ms", min(self.cd_min.value(), self.cd_max.value()))
        c.set("cooldown_max_ms", max(self.cd_min.value(), self.cd_max.value()))
        c.set("input_method", self.method.currentData())
        c.set("break_enabled", self.brk.isChecked())
        c.set("break_every_min", [min(self.brk_e1.value(), self.brk_e2.value()), max(self.brk_e1.value(), self.brk_e2.value())])
        c.set("break_len_min", [min(self.brk_l1.value(), self.brk_l2.value()), max(self.brk_l1.value(), self.brk_l2.value())])
        c.set("preview_fps", self.pfps.value())
        c.set("scan_fps", self.sfps.value())
        lang_changed = self.lang.currentData() != c["language"]
        if lang_changed:
            c.set("language", self.lang.currentData())
        c.set("streak_check", self.streak.isChecked())
        c.set("process_filter", self.filter.text().strip())
        c.set("pick_key", self.pick_key.currentText())
        c.set("blocked_exes", [e.strip() for e in self.blocked_edit.text().split(",") if e.strip()])
        c.save()
        self.saved.setText(T('✓ Kaydedildi ({0}). Çalışan botlar yeni ayarları hemen kullanır.').format((time.strftime('%H:%M:%S'))))
        if lang_changed:
            self.win.ask_restart_for_language()


# ====================================================================== Kayıtlar
class LogPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        head = QHBoxLayout()
        t = QLabel(T("Kayıtlar"))
        t.setObjectName("h1")
        head.addWidget(t)
        head.addStretch()
        clr = QPushButton(T("Temizle"))
        head.addWidget(clr)
        lay.addLayout(head)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(5000)
        self.text.setStyleSheet("font-family: Consolas, 'Cascadia Mono', monospace; font-size: 12px;")
        lay.addWidget(self.text, 1)
        clr.clicked.connect(self.text.clear)

    def add(self, line: str) -> None:
        self.text.appendPlainText(line)


# ====================================================================== Pencere
class MainWindow(QMainWindow):
    def __init__(self, session: Session, provider: AuthProvider, cfg: Config):
        super().__init__()
        self.session, self.provider, self.cfg = session, provider, cfg
        self.workers: dict[int, BotWorker] = {}
        self.preview_pid: int | None = None
        self.picked: dict[int, GameWindow] = {}     # F7 ile seçilen pencereler
        self.hidden_hwnds: set[int] = set()         # kullanıcının listeden kaldırdığı pencereler
        self._bar_reader = BarReader()
        self._bite_prev = BiteWatcher(cfg)
        self.bridge = Bridge()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)
        self.setMinimumSize(1100, 680)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # --- kenar çubuğu
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(240)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(16, 20, 16, 16)
        sv.setSpacing(4)
        sv.addWidget(Brand())
        sv.addSpacing(26)
        menu = QLabel(T("MENÜ"))
        menu.setObjectName("eyebrow")
        menu.setContentsMargins(6, 0, 0, 6)
        sv.addWidget(menu)

        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(self)
        self.captcha_page = CaptchaPage(self) if session.is_admin else None     # sadece yönetici
        self.settings = SettingsPage(self)
        self.logs = LogPage()
        pages = [("clients", T("Client'lar"), self.dashboard,
                  tip(T("Client'lar"), T("Açık oyun pencereleri. Bir client'a tıkla: canlı görüntü, istatistik, "
                                       "turlar ve Başlat/Durdur. F7 ile fare altındaki pencereyi seçebilirsin."))),
                 ("settings", T("Ayarlar"), self.settings,
                  tip(T("Ayarlar"), T("Balık sistemi, işaret alanı, tuş ve client ayarları — hepsi açıklamalı."))),
                 ("logs", T("Kayıtlar"), self.logs,
                  tip(T("Kayıtlar"), T("Botun olay günlüğü: atılan oltalar, isabetler, uyarılar.")))]
        if session.is_admin:
            pages.insert(1, ("captcha", T("Captcha"), self.captcha_page,
                             tip(T("Captcha"), T("Captcha ayarları, test, öğrenilen simgeler ve yakalanan captcha "
                                                 "resimleri. Yeni simgeleri sadece yönetici öğretir; üyelere "
                                                 "güncellemeyle gider."))))
            from .members_page import MembersPage
            self.members_page = MembersPage(self)
            pages.append(("members", T("Üyeler"), self.members_page,
                          tip(T("Üyeler"), T("Üye ekle, süre ver (süresiz dahil), askıya al, cihaz kilidi, sil."))))
        self.nav_buttons: list[QPushButton] = []
        for i, (icon, name, page, tp) in enumerate(pages):
            self.stack.addWidget(page)
            b = NavButton(icon, name)
            b.clicked.connect(lambda _=False, i=i: self.go(i, from_nav=True))
            b.setToolTip(tp)
            sv.addWidget(b)
            self.nav_buttons.append(b)
        sv.addStretch()

        keys = QLabel(T("<span style='color:{0}'>{1}</span>&nbsp; client seç&nbsp;&nbsp;·&nbsp;&nbsp;"
                        "<span style='color:{0}'>{2}</span>&nbsp; hepsini durdur").format(
            theme.MUTED, cfg["pick_key"], cfg["stop_key"]))
        keys.setObjectName("faint")
        keys.setContentsMargins(6, 0, 0, 8)
        sv.addWidget(keys)
        self.account = AccountCard(session.username)
        sv.addWidget(self.account)

        h.addWidget(side)
        h.addWidget(self.stack, 1)
        self.go(0)
        self._update_vip()

        self.bridge.log.connect(self.log_line)
        self.bridge.state.connect(self.dashboard.set_state)
        self.bridge.stats.connect(self.dashboard.update_stats)
        self.bridge.frame.connect(self.dashboard.show_frame)
        self.bridge.round.connect(self.dashboard.add_round)
        self.scan_win = None
        self.bridge.scan.connect(self._on_scan)

        # bot çalışmayan client seçiliyse canlı görüntüyü arayüz kendisi üretir
        self._pick_down = False
        self._stop_down = False
        self.pick_poll = QTimer(self)
        self.pick_poll.timeout.connect(self._poll_pick_key)
        self.pick_poll.start(40)

        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._idle_preview)
        self.preview_timer.start(250)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.dashboard.tick)
        if self.captcha_page is not None:
            self.timer.timeout.connect(self.captcha_page.tick)
        self.timer.start(1000)
        self.vip_timer = QTimer(self)
        self.vip_timer.timeout.connect(self._update_vip)
        self.vip_timer.start(30_000)

        self.log_line(0, T('Hoş geldin {0}. Üyelik bitişi: {1}').format(
            session.username, T("Süresiz") if session.expires_at is None else f"{session.expires_at:%d.%m.%Y %H:%M}"))
        self.dashboard.refresh()
        from core.winapi import is_admin
        if not is_admin():
            QTimer.singleShot(800, self._warn_not_admin)

    def _warn_not_admin(self) -> None:
        msg = T("Bot yönetici olarak çalışmıyor. Oyun yönetici olarak açıksa Windows izin vermez: {0} ile client "
                "seçilmez ve tuşlar oyuna gitmez. Botu kapatıp sağ tık → 'Yönetici olarak çalıştır' ile aç.").format(
            self.cfg["pick_key"])
        self.log_line(0, "⚠ " + msg)
        QMessageBox.warning(self, APP_NAME, msg)

    def go(self, i: int, from_nav: bool = False) -> None:
        if i == 0 and from_nav and self.stack.currentIndex() == 0:
            self.dashboard.show_overview()      # Panel'e tekrar basınca client listesine dön
        self.stack.setCurrentIndex(i)
        for j, b in enumerate(self.nav_buttons):
            b.setChecked(i == j)

    def _update_vip(self) -> None:
        # sunucudaki değişiklik (süre uzatma, askıya alma) arayüze de yansısın
        if not getattr(self, "_vip_busy", False):
            import threading
            self._vip_busy = True

            def chk():
                try:
                    self._vip_ok = self.provider.verify(self.session)
                finally:
                    self._vip_busy = False
            threading.Thread(target=chk, daemon=True).start()
        self.account.set_expiry(self.session.expires_at)
        if getattr(self, "_vip_ok", True) is False:
            self._vip_ok = True
            self.stop_all()
            QMessageBox.warning(self, APP_NAME, T("Üyelik doğrulanamadı, bot durduruluyor."))
            return
        if not self.session.is_valid:
            self.stop_all()
            QMessageBox.warning(self, APP_NAME, T("Üyeliğinin süresi doldu. Botlar durduruldu."))

    def _on_scan(self, pid: int, line: str) -> None:
        self.dashboard.on_scan(pid, line)
        if self.scan_win is not None and self.scan_win.isVisible():
            self.scan_win.add_line(pid, line)

    def find_clients(self) -> list[GameWindow]:
        games = list_game_windows(self.cfg["process_filter"], self.cfg["known_exes"],
                                  self.cfg["blocked_exes"], self.hidden_hwnds)
        have = {g.hwnd for g in games}
        for pid, g in list(self.picked.items()):
            if not window_alive(g.hwnd):
                self.picked.pop(pid)
            elif g.hwnd not in have:
                games.append(g)
        games.sort(key=lambda g: g.pid)
        return games

    def remove_client(self, game: GameWindow, block_exe: bool) -> None:
        """Client'ı listeden kaldır; istenirse programı tamamen engelle."""
        w = self.workers.get(game.pid)
        if w and w.is_alive():
            w.stop()
        self.picked.pop(game.pid, None)
        self.hidden_hwnds.add(game.hwnd)
        if block_exe:
            exe = game.exe.lower()
            self.cfg.set("known_exes", [e for e in (self.cfg["known_exes"] or []) if e.lower() != exe])
            blocked = list(self.cfg["blocked_exes"] or [])
            if exe not in {b.lower() for b in blocked}:
                blocked.append(game.exe)
            self.cfg.set("blocked_exes", blocked)
            self.cfg.save()
            self.log_line(0, T('{0} engellendi; artık client olarak listelenmeyecek.').format((game.exe)))
        else:
            self.log_line(0, T('PID {0} listeden kaldırıldı (bu oturum için).').format((game.pid)))
        self.dashboard.refresh()
        self.settings.refresh_known()

    def _poll_pick_key(self) -> None:
        down = key_down(self.cfg["pick_key"])
        if down and not self._pick_down:
            self.pick_client()
        self._pick_down = down
        sdown = key_down(self.cfg["stop_key"])
        if sdown and not self._stop_down:
            if any(w.is_alive() for w in self.workers.values()):
                self.stop_all()
                self.dashboard.flash_pick(T('■ {0} ile tüm botlar durduruldu.').format((self.cfg['stop_key'])), ok=False)
                self.log_line(0, T('{0} ile tüm botlar durduruldu.').format((self.cfg['stop_key'])))
        self._stop_down = sdown

    def pick_client(self) -> None:
        w = window_under_cursor()
        if w is None:
            self.dashboard.flash_pick(T("Farenin altında bir pencere bulunamadı. Fareyi oyun penceresinin "
                                      "üstüne getirip tekrar dene."), ok=False)
            return
        self.picked[w.pid] = w
        self.hidden_hwnds.discard(w.hwnd)
        blocked = [e for e in (self.cfg["blocked_exes"] or []) if e.lower() != w.exe.lower()]
        if len(blocked) != len(self.cfg["blocked_exes"] or []):
            self.cfg.set("blocked_exes", blocked)
        exes = list(self.cfg["known_exes"] or [])
        if w.exe and w.exe != "?" and w.exe.lower() not in {e.lower() for e in exes}:
            exes.append(w.exe)
            self.cfg.set("known_exes", exes)
            self.cfg.save()
        self.dashboard.refresh(check_pid=w.pid)
        self.dashboard.flash_pick(T("✓ Client seçildi: PID {0} • {1} ({2}). İşaretlendi, 'Seçilileri Başlat' ile başlatabilirsin.").format((w.pid), (w.title), (w.exe)))
        self.log_line(0, T('{0} ile client seçildi: PID {1} • {2} ({3})').format((self.cfg['pick_key']), (w.pid), (w.title), (w.exe)))
        try:
            import winsound
            winsound.MessageBeep()
        except Exception:
            pass

    def _idle_preview(self) -> None:
        """Bot çalışmayan client seçiliyse önizleme: zamanlama penceresi açıksa kutucuk/balık, değilse
        kafa arama alanı ve bulunan işaretler çizilir."""
        pid = self.preview_pid
        if pid is None or not self.dashboard.detail_visible():
            return
        w = self.workers.get(pid)
        if w and w.is_alive():
            return  # bot kendi karelerini gönderiyor
        game = self.dashboard.games.get(pid)
        if game is None:
            return
        frame = WindowCapture(game.hwnd).grab()
        if frame is None:
            return
        try:
            bar = self._bar_reader.find(frame)
            if bar is not None:
                rd = self._bar_reader.read(frame, bar)
                img = draw_bar(frame, rd, float(self.cfg["timing_latency_ms"]), note=T("onizleme (bot calismiyor)"))
            else:
                b = self._bite_prev
                b._t_reset = 0.0
                hit = b.check(frame)
                img = draw_bite(frame, b._reg, hit, T("onizleme (bot calismiyor)"), anchor=b._anchor, seen=b.seen)
        except Exception:
            img = frame
        self.dashboard.show_frame(pid, {"img": img, "raw": None, "boxes": []})

    def log_line(self, pid: int, msg: str) -> None:
        tag = f"[{pid}]" if pid else "[sistem]"
        line = f"{datetime.now():%H:%M:%S}  {tag:<9} {msg}"
        self.logs.add(line)
        if "aptcha" in msg or "CAPTCHA" in msg:
            if self.captcha_page is not None:
                self.captcha_page.add_event(line)

    def start_bot(self, game: GameWindow) -> None:
        w = self.workers.get(game.pid)
        if w and w.is_alive():
            return
        member_lim = int(self.session.max_clients or 0)
        lim = min(MAX_CLIENTS, member_lim) if member_lim else MAX_CLIENTS
        running = sum(1 for x in self.workers.values() if x.is_alive() and not x.stop_event.is_set())
        if running >= lim:
            QMessageBox.information(self, APP_NAME,
                                    T("Üyeliğin aynı anda en fazla {n} client'a izin veriyor.").format(n=lim)
                                    if member_lim and member_lim < MAX_CLIENTS else
                                    T("Bot aynı anda en fazla {n} client çalıştırır.").format(n=MAX_CLIENTS))
            return
        w = BotWorker(game, self.cfg,
                      on_log=self.bridge.log.emit,
                      on_state=self.bridge.state.emit,
                      on_stats=self.bridge.stats.emit,
                      license_check=lambda: self.provider.verify(self.session),
                      on_frame=self.bridge.frame.emit,
                      want_frames=lambda pid: pid == self.preview_pid,
                      on_round=self.bridge.round.emit,
                      on_scan=self.bridge.scan.emit,
                      admin=self.session.is_admin,
                      on_captcha_report=self._send_captcha_report)
        self.workers[game.pid] = w
        w.start()
        self.dashboard.set_state(game.pid, "Çalışıyor")

    def stop_bot(self, pid: int) -> None:
        w = self.workers.get(pid)
        if w:
            w.stop()

    def stop_all(self) -> None:
        for w in self.workers.values():
            w.stop()
        self.dashboard.tick()

    def _send_captcha_report(self, rep: dict) -> None:
        """(bot iş parçacığından) tanınmayan captcha'yı yöneticiye gönder."""
        import threading

        def run():
            try:
                self.provider.report_captcha(self.session, rep.get("title", ""), rep["image"], rep.get("click"),
                                             rep.get("solved", False))
            except Exception as e:  # noqa: BLE001
                self.bridge.log.emit(0, T("Captcha raporu gönderilemedi: {0}").format(e))
        threading.Thread(target=run, daemon=True).start()

    def ask_restart_for_language(self) -> None:
        """Dil değişti: arayüzün tamamı yeni dilde olsun diye program yeniden açılır."""
        n = sum(1 for x in self.workers.values() if x.is_alive())
        msg = T("Dil değişti. Arayüzün tamamının yeni dilde görünmesi için program yeniden açılsın mı?")
        if n:
            msg += "\n" + T("Çalışan {n} bot durdurulacak.").format(n=n)
        if QMessageBox.question(self, APP_NAME, msg) != QMessageBox.StandardButton.Yes:
            return
        import sys
        from PySide6.QtCore import QProcess
        from PySide6.QtWidgets import QApplication
        self.stop_all()
        for w in self.workers.values():
            w.join(timeout=2)
        from core.paths import restart_env
        os_env = restart_env()
        import os as _os
        _os.environ.clear()
        _os.environ.update(os_env)
        if getattr(sys, "frozen", False):
            QProcess.startDetached(sys.executable, [])
        else:
            import os
            QProcess.startDetached(sys.executable, [os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "main.py")])
        QApplication.quit()

    def closeEvent(self, e):
        self.stop_all()
        for w in self.workers.values():
            w.join(timeout=2)
        super().closeEvent(e)
