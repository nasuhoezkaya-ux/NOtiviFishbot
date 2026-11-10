"""Açılış ekranı: güncelleme denetimi ve indirme (arayüz dilinde, anlık MB göstergesiyle)."""
from __future__ import annotations

import time

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core import updater
from core.i18n import T
from core.version import APP_NAME, VERSION

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
        # 1) dosyalar
        self.status.emit(T("Dosyalar hazırlanıyor…"), "")
        try:
            from core.paths import cleanup_old_exe, sync_assets
            cleanup_old_exe()
            sync_assets()
        except Exception:
            pass
        # 2) güncelleme
        self.up_to_date = False
        self.note = ""
        if self.repo.strip():
            kind = self._update()
            if kind != "devam":
                self.finished.emit(kind)
                return
        # 3) üyelik sunucusu
        from core import server
        if server.supabase_ready():
            self.status.emit(T("Sunucu bağlantısı denetleniyor…"), "")
            self.progress.emit(-1.0, "")
            if not self._server_ok(server.SUPABASE_URL, server.SUPABASE_ANON_KEY):
                self.status.emit(T("Sunucuya bağlanılamadı"),
                                 T("İnternet bağlantını kontrol et, sonra 'Tekrar dene'ye bas."))
                self.finished.emit("hata")
                return
        self.progress.emit(1.0, "")
        self.status.emit(T("Bot güncel — sürüm {v}").format(v=VERSION) if self.up_to_date else T("Hazır"),
                         self.note or T("Her şey hazır. Başlamak için 'Başlat'a bas."))
        self.finished.emit("hazir")

    @staticmethod
    def _server_ok(url: str, key: str) -> bool:
        """Üyelik sunucusu cevap veriyor mu? (geçersiz bir oturumla fb_verify çağrılır: cevap gelirse bağlantı var)"""
        import json
        import urllib.error
        import urllib.request
        from core.auth import SupabaseAuthProvider
        h = SupabaseAuthProvider(url, key)._headers()
        req = urllib.request.Request(url.rstrip("/") + "/rest/v1/rpc/fb_verify", method="POST", headers=h,
                                     data=json.dumps({"p_token": "00000000-0000-0000-0000-000000000000"}).encode())
        for _ in range(2):
            try:
                with urllib.request.urlopen(req, timeout=8):
                    return True
            except urllib.error.HTTPError:
                return True                          # sunucu cevap verdi (hata koduyla da olsa)
            except Exception:
                time.sleep(1.0)
        return False

    def _update(self) -> str:
        try:
            self.status.emit(T("Güncellemeler denetleniyor…"), "")
            self.progress.emit(-1.0, "")
            rel = updater.check(self.repo)
        except Exception:
            self.note = T("Güncelleme denetlenemedi (GitHub'a ulaşılamadı).")
            return "devam"                           # GitHub cevap vermezse normal açıl
        if rel is None:
            self.up_to_date = True
            return "devam"
        if not updater.is_frozen():
            self.status.emit(T("Yeni sürüm var: {v}").format(v=rel.version),
                             T("Kaynak koddan çalışıyor — güncellemeyi GitHub'dan indir."))
            time.sleep(2.5)
            return "devam"
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
            path = updater.download(rel, prog, cancel=lambda: self.cancelled)
            self.status.emit(T("Güncelleme kuruluyor…"), T("Bot birazdan yeniden açılacak."))
            self.progress.emit(1.0, "")
            updater.install(path)
            return "kur"
        except Exception as e:  # noqa: BLE001
            self.status.emit(T("Güncelleme yapılamadı"), str(e)[:160])
            time.sleep(2.5)
            return "devam"


class SplashScreen(QDialog):
    """exec() sonrası self.result_kind: "devam" (giriş ekranına geç) ya da "kur" (program kapanmalı)."""

    def __init__(self, repo: str):
        super().__init__()
        self.result_kind = "devam"
        self.setWindowTitle(APP_NAME)
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
        t = QLabel(APP_NAME)
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
        self.start = QPushButton(T("▶  Başlat"))
        self.start.setObjectName("primary")
        self.start.setMinimumWidth(130)
        self.start.setVisible(False)
        self.start.setDefault(True)
        self.start.clicked.connect(self._go)
        self.retry = QPushButton(T("Tekrar dene"))
        self.retry.setObjectName("primary")
        self.retry.setVisible(False)
        self.retry.clicked.connect(self._retry)
        self.close_btn = QPushButton(T("Kapat"))
        self.close_btn.setVisible(False)
        self.close_btn.clicked.connect(self._close)
        row.addWidget(self.close_btn)
        row.addWidget(self.retry)
        row.addWidget(self.start)
        v.addLayout(row)

        self._spin = 0.0
        self._busy = QTimer(self)
        self._busy.timeout.connect(self._animate)
        self._busy.start(30)
        self._indeterminate = True

        self.repo = repo
        self._start_job()

    def _start_job(self) -> None:
        self._thread = QThread(self)
        self._job = _Job(self.repo)
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
        if f < 0:
            self._indeterminate = True
            self.mb.setText("")
            self.skip.setVisible(False)
            return
        self._indeterminate = False
        self.bar.set(f, theme.ACCENT)
        self.mb.setText(txt)
        self.skip.setVisible(f < 1.0)

    def _skip(self) -> None:
        self._job.cancelled = True

    def _done(self, kind: str) -> None:
        self._thread.quit()
        self._thread.wait(2000)
        if kind == "hata":                       # sorun var: giriş ekranına geçme, tekrar denet
            self._indeterminate = False
            self.bar.set(1.0, theme.DANGER)
            self.retry.setVisible(True)
            self.close_btn.setVisible(True)
            return
        if kind == "hazir":                      # her şey yolunda: kullanıcı "Başlat"a basınca giriş ekranı
            self._indeterminate = False
            self.bar.set(1.0, theme.SUCCESS)
            self.skip.setVisible(False)
            self.start.setVisible(True)
            self.close_btn.setVisible(True)
            self.start.setFocus()
            return
        self.result_kind = kind
        self.accept()

    def _go(self) -> None:
        self.result_kind = "devam"
        self.accept()

    def _retry(self) -> None:
        self.start.setVisible(False)
        self.retry.setVisible(False)
        self.close_btn.setVisible(False)
        self._start_job()

    def _close(self) -> None:
        self.result_kind = "kapat"
        self.reject()
