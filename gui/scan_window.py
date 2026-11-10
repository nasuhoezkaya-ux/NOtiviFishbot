"""Tarama: botun her adımda ne gördüğünü ve ne karar verdiğini canlı gösterir.

ScanPanel paneldeki kartın içinde durur (Client'lar ekranı ve client detayı); ScanWindow aynı paneli ayrı ve
büyük bir pencerede açar. Satırlar: balık işareti, zamanlama penceresi (kutucuk, balık hızı, basış anı),
sonuç (İSABET / ISKA, hedefe uzaklık), seri sayacı, öğrenilen tuş gecikmesi, captcha.
Aynı kayıtlar data/tarama/ klasörüne de yazılır.
"""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from core.config import DATA_DIR
from core.i18n import T

from . import theme



def open_scan_dir() -> None:
    d = os.path.join(DATA_DIR, "tarama")
    os.makedirs(d, exist_ok=True)
    if sys.platform == "win32":
        os.startfile(d)  # noqa: S606
    else:
        subprocess.Popen(["xdg-open", d])


class ScanPanel(QWidget):
    """Canlı tarama kaydı. pid=None: bütün client'lar (satır başına PID yazılır)."""

    def __init__(self, parent=None, events_only: bool = False, compact: bool = True, on_popout=None):
        super().__init__(parent)
        self.pid: int | None = None
        self.paused = False
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        bar = QHBoxLayout()
        bar.setSpacing(4)
        self.only_events = QCheckBox(T("Sadece olaylar"))
        self.only_events.setChecked(events_only)
        self.only_events.setToolTip(T("Sadece ▶ ile başlayan olayları (işaret, isabet, ıska, captcha vb.) göster"))
        bar.addWidget(self.only_events)
        bar.addStretch()
        self.btn_pause = QPushButton(T("Duraklat"))
        self.btn_pause.setObjectName("ghost")
        self.btn_pause.setCheckable(True)
        self.btn_pause.toggled.connect(self._toggle_pause)
        b_clear = QPushButton(T("Temizle"))
        b_clear.setObjectName("ghost")
        b_dir = QPushButton(T("Klasör"))
        b_dir.setObjectName("ghost")
        b_dir.setToolTip(T("Her satır data/tarama/ klasörüne de kaydedilir. Sorun olursa o dosyayı gönderebilirsin."))
        for b in (self.btn_pause, b_clear, b_dir):
            b.setCursor(Qt.PointingHandCursor)
            bar.addWidget(b)
        if on_popout is not None:
            b_pop = QPushButton(T("Büyüt"))
            b_pop.setObjectName("ghost")
            b_pop.setCursor(Qt.PointingHandCursor)
            b_pop.setToolTip(T("Tarama kaydını ayrı, büyük bir pencerede aç"))
            b_pop.clicked.connect(on_popout)
            bar.addWidget(b_pop)
        v.addLayout(bar)
        self.text = QPlainTextEdit()
        self.text.setObjectName("console")
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(2500)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if compact
                                  else QPlainTextEdit.LineWrapMode.NoWrap)
        self.text.setMinimumHeight(170)
        v.addWidget(self.text, 1)
        b_clear.clicked.connect(self.text.clear)
        b_dir.clicked.connect(open_scan_dir)

    def set_pid(self, pid: int | None) -> None:
        if pid != self.pid:
            self.text.clear()
        self.pid = pid

    def _toggle_pause(self, on: bool) -> None:
        self.paused = on
        self.btn_pause.setText(T("Devam") if on else T("Duraklat"))

    def add_line(self, pid: int, line: str) -> None:
        if self.paused or (self.pid is not None and pid != self.pid):
            return
        event = "▶" in line or "⚠" in line
        if self.only_events.isChecked() and not event:
            return
        if self.pid is None:
            line = f"[{pid}] {line}"
        fmt = QTextCharFormat()
        if "✗" in line or "⚠" in line:
            fmt.setForeground(QColor(theme.DANGER))
        elif "✓" in line:
            fmt.setForeground(QColor(theme.SUCCESS))
        elif event:
            fmt.setForeground(QColor(theme.ACCENT))
        else:
            fmt.setForeground(QColor("#aab5c5"))
        sb = self.text.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 4
        cur = self.text.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(line + "\n", fmt)
        if at_bottom:
            sb.setValue(sb.maximum())


class ScanWindow(QDialog):
    """Tarama kaydı ayrı, büyük pencerede (satırlar kaydırılmaz, tek satırda)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("Tarama — canlı kayıt"))
        self.resize(1100, 600)
        self.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        head = QHBoxLayout()
        self.title = QLabel(T("Tarama — canlı kayıt"))
        self.title.setObjectName("section")
        head.addWidget(self.title)
        head.addStretch()
        lay.addLayout(head)
        self.panel = ScanPanel(self, compact=False)
        lay.addWidget(self.panel, 1)

    def set_pid(self, pid: int | None) -> None:
        self.panel.set_pid(pid)
        self.title.setText(T("Tarama — canlı kayıt") + (f"  ·  PID {pid}" if pid else ""))

    def add_line(self, pid: int, line: str) -> None:
        if self.panel.pid is not None and pid != self.panel.pid:
            return
        self.panel.add_line(pid, line)
