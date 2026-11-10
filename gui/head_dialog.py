"""Kendi karakterimin işaret alanını seçme diyaloğu (yeni balık sistemi).

Yanında başka oyuncular da balık tutuyorsa onların kafasında da balık işareti çıkar. Bot sadece burada
seçilen alandaki (kendi karakterinin kafasının üstündeki) işarete tepki verir. Alan client'ın ORTASINA
göre saklanır: Metin2'de kamera karakteri ortada tutar, pencere boyutu değişse de doğru yeri bulur.
"""
from __future__ import annotations

from core.i18n import T

import cv2
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.timing import BiteWatcher
from core.winapi import GameWindow, WindowCapture

from . import theme
from .widgets import SelectableImage


class HeadAreaDialog(QDialog):
    def __init__(self, game: GameWindow, cfg, parent=None):
        super().__init__(parent)
        self.game, self.cfg = game, cfg
        self.setWindowTitle(T("Kendi karakterimin işaret alanı"))
        self.setObjectName("root")
        self.resize(960, 760)
        self.raw = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        t = QLabel(T("🎯  Kendi karakterimin işaret alanı"))
        t.setObjectName("h1")
        lay.addWidget(t)
        hint = QLabel(T("Yanında balık tutan başka oyuncular varsa onların kafasında da işaret çıkar; bot sadece "
                      "burada seçtiğin alana bakar.\n"
                      "1) Oyunda oltayı at. İşaret çıktığında (ya da karakterin göründüğü herhangi bir anda) "
                      "'📷 Görüntü al'a bas.\n"
                      "2) KENDİ karakterinin kafasının üstünü (işaretin çıktığı yeri) fareyle çerçeve içine al. "
                      "Yandaki oyuncuların kafaları çerçevenin DIŞINDA kalsın. İşaretin tamamı sığsın.\n"
                      "3) 'Çizdiğim alanı kaydet'. Mor çerçeve = kayıtlı alan, mavi = alan seçilmezse "
                      "botun baktığı yer, yeşil = ekranda bulunan işaretler."))
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self.view = SelectableImage()
        lay.addWidget(self.view, 1)
        self.info = QLabel("")
        self.info.setWordWrap(True)
        lay.addWidget(self.info)

        row = QHBoxLayout()
        b_cap = QPushButton(T("📷  Görüntü al"))
        b_save = QPushButton(T("✓  Çizdiğim alanı kaydet"))
        b_save.setObjectName("primary")
        b_clear = QPushButton(T("Alanı sil (otomatik)"))
        b_clear.setObjectName("danger")
        b_close = QPushButton(T("Kapat"))
        row.addWidget(b_cap)
        row.addWidget(b_save)
        row.addStretch()
        row.addWidget(b_clear)
        row.addWidget(b_close)
        lay.addLayout(row)
        b_cap.clicked.connect(self.capture)
        b_save.clicked.connect(self.save_drawn)
        b_clear.clicked.connect(self.clear)
        b_close.clicked.connect(self.accept)
        self._show_saved()
        self.capture()

    def _show_saved(self) -> None:
        a = self.cfg["bite_area"]
        if isinstance(a, dict):
            self.info.setStyleSheet(f"color:{theme.SUCCESS};")
            self.info.setText(T('Kayıtlı alan: {0}×{1} px (client ortasına göre {2:+d}, {3:+d}). Bot sadece bu alandaki işarete tepki verir.').format((a['w']), (a['h']), (a['dx']), (a['dy'])))
        else:
            self.info.setStyleSheet(f"color:{theme.WARNING};")
            self.info.setText(T("Kayıtlı alan yok — bot ekranın ortasındaki karakterin (seninkinin) üstüne bakar ve "
                              "ortaya en yakın işareti seçer. Yanında oyuncu varsa alanı seçmen önerilir."))

    def capture(self) -> None:
        img = WindowCapture(self.game.hwnd).grab()
        if img is None:
            self.info.setText(T("Görüntü alınamadı (oyun penceresi simge durumunda olabilir)."))
            return
        self.raw = img
        shown = img.copy()
        bw = BiteWatcher(self.cfg)
        # alan seçilmezse botun baktığı yer (mavi)
        x0, y0, x1, y1 = bw.auto_region(img.shape)
        cv2.rectangle(shown, (x0, y0), (x1, y1), (255, 160, 40), 1)
        ua = bw.user_area(img.shape)
        if ua is not None:
            cv2.rectangle(shown, (ua[0], ua[1]), (ua[2], ua[3]), (255, 40, 200), 2)
        n = 0
        if bw.templates:                           # ekrandaki tüm işaretleri göster (yeşil)
            thr = float(self.cfg["bite_threshold"])
            for im, m, _n in bw.templates:
                if im.shape[0] >= img.shape[0] or im.shape[1] >= img.shape[1]:
                    continue
                r = cv2.matchTemplate(img, im, cv2.TM_CCOEFF_NORMED, mask=m) if m is not None else \
                    cv2.matchTemplate(img, im, cv2.TM_CCOEFF_NORMED)
                for _ in range(8):
                    _, v, _, (x, y) = cv2.minMaxLoc(r)
                    if v < thr:
                        break
                    th, tw = im.shape[:2]
                    cv2.rectangle(shown, (x - 2, y - 2), (x + tw + 2, y + th + 2), (60, 230, 60), 2)
                    r[max(0, y - th): y + th, max(0, x - tw): x + tw] = -1
                    n += 1
        self.view.set_image(shown, raw=img)
        if bw.templates:
            self._show_saved()
            self.info.setText(self.info.text() + T('  •  Ekranda {0} işaret bulundu (yeşil).').format((n)))

    def save_drawn(self) -> None:
        r = self.view.selection_rect()
        if r is None or self.raw is None:
            self.info.setText(T("Önce görüntüde kendi karakterinin kafasının üstünü fareyle çerçeve içine al."))
            return
        H, W = self.raw.shape[:2]
        self.cfg.set("bite_area", {"dx": int(r.x() - W / 2), "dy": int(r.y() - H / 2),
                                   "w": int(r.width()), "h": int(r.height())})
        self.cfg.save()
        self._show_saved()
        self.capture()

    def clear(self) -> None:
        self.cfg.set("bite_area", None)
        self.cfg.save()
        self._show_saved()
        self.capture()
