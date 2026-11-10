"""Açılış ekranı: güncelleme denetimi ve indirme (arayüz dilinde, anlık MB göstergesiyle)."""
from __future__ import annotations

import time

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core import updater
from core.i18n import T
from core.version import VERSION

from . import theme
from .fx import BrandMark, ThinBar


class _Job(QObject):
    status = Signal(str, str)          # ana yazı, ayrıntı
    progress = Signal(float, str)      # 0..1, "12.4 / 98.0 MB"
    finished = Signal(str)             # "devam" | "kur" | "hata"

    def __init__(self, repo: str):
        super().__init__()
        self.repo = repo
        self.cancelled = False

    def run(self) -> None:
        try:
            self.status.emit(T("Güncellemeler denetleniyor…"), "")
            rel = updater.check(self.repo)
        except Exception:
            self.finished.emit("devam")            # internet yoksa / GitHub cevap vermezse normal açıl
            return
        if rel is None:
            self.finished.emit("devam")
            return
        if not updater.is_frozen():
            self.status.emit(T("Yeni sürüm var: {v}").format(v=rel.version),
                             T("Kaynak koddan çalışıyor — güncellemeyi GitHub'dan indir."))
            time.sleep(2.5)
            self.finished.emit("devam")
            return
        self.status.emit(T("Bot güncelleniyor…"), T("Sürüm {a} → {b}").format(a=VERSION, b=rel.version))
        t0 = [time.time(), 0]

        def prog(done: int, total: int) -> None:
            now = time.time()
            if now - t0[0] < 0.1 and done < total:
                return
            speed = (done - t0[1]) / max(1e-3, now - t0[0]) / 1048576
            t0[0], t0[1] = now, done
            mb = done / 1048576
            txt = (f"{mb:.1f} / {total / 1048576:.1f} MB" if total else f"{mb:.1f} MB") + f"  ·  {speed:.1f} MB/s"
            self.progress.emit(done / total if total else 0.0, txt)

        try:
            z = updater.download(rel, prog, cancel=lambda: self.cancelled)
            self.status.emit(T("Güncelleme kuruluyor…"), T("Bot birazdan yeniden açılacak."))
            self.progress.emit(1.0, "")
            updater.install(z)
            self.finished.emit("kur")
        except Exception as e:  # noqa: BLE001
            self.status.emit(T("Güncelleme yapılamadı"), str(e)[:160])
            time.sleep(2.5)
            self.finished.emit("devam")


class SplashScreen(QDialog):
    """exec() sonrası self.result_kind: "devam" (giriş ekranına geç) ya da "kur" (program kapanmalı)."""

    def __init__(self, repo: str):
        super().__init__()
        self.result_kind = "devam"
        self.setWindowTitle("FishBot")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(460, 280)
        self.setObjectName("splash")
        self.setStyleSheet(f"QDialog#splash {{ background:{theme.SURFACE}; border:1px solid {theme.BORDER_2};"
                           "border-radius:14px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(32, 30, 32, 26)
        v.setSpacing(0)
        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(BrandMark(46))
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("FishBot")
        t.setStyleSheet("font-size:22px; font-weight:700;")
        ver = QLabel(T("Sürüm {v}").format(v=VERSION))
        ver.setObjectName("faint")
        col.addWidget(t)
        col.addWidget(ver)
        top.addLayout(col, 1)
        v.addLayout(top)
        v.addStretch()
        self.status = QLabel(T("Başlatılıyor…"))
        self.status.setStyleSheet("font-size:14px; font-weight:600;")
        self.detail = QLabel("")
        self.detail.setObjectName("muted")
        self.detail.setWordWrap(True)
        v.addWidget(self.status)
        v.addSpacing(4)
        v.addWidget(self.detail)
        v.addSpacing(14)
        self.bar = ThinBar()
        v.addWidget(self.bar)
        v.addSpacing(8)
        row = QHBoxLayout()
        self.mb = QLabel("")
        self.mb.setObjectName("faint")
        row.addWidget(self.mb, 1)
        self.skip = QPushButton(T("Atla"))
        self.skip.setObjectName("ghost")
        self.skip.setVisible(False)
        self.skip.clicked.connect(self._skip)
        row.addWidget(self.skip)
        v.addLayout(row)

        self._spin = 0.0
        self._busy = QTimer(self)
        self._busy.timeout.connect(self._animate)
        self._busy.start(30)
        self._indeterminate = True

        self._thread = QThread(self)
        self._job = _Job(repo)
        self._job.moveToThread(self._thread)
        self._thread.started.connect(self._job.run)
        self._job.status.connect(self._on_status)
        self._job.progress.connect(self._on_progress)
        self._job.finished.connect(self._done)
        QTimer.singleShot(150, self._thread.start)

    def _animate(self) -> None:
        if self._indeterminate:
            self._spin = (self._spin + 0.012) % 1.0
            self.bar.set(0.15 + 0.85 * abs(1 - 2 * self._spin) * 0.6, theme.ACCENT)

    def _on_status(self, s: str, d: str) -> None:
        self.status.setText(s)
        self.detail.setText(d)

    def _on_progress(self, f: float, txt: str) -> None:
        self._indeterminate = False
        self.bar.set(f, theme.ACCENT)
        self.mb.setText(txt)
        self.skip.setVisible(f < 1.0)

    def _skip(self) -> None:
        self._job.cancelled = True

    def _done(self, kind: str) -> None:
        self.result_kind = kind
        self._thread.quit()
        self._thread.wait(2000)
        self.accept()
