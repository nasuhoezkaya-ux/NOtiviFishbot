"""Ortak bileşenler."""
from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from core.i18n import T, lang
from PySide6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QRubberBand, QVBoxLayout, QWidget)


def shadow(widget: QWidget, blur: int = 30, alpha: int = 120) -> None:
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, 6)
    eff.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(eff)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")


class StatCard(Card):
    """Sayı kartı: renkli nokta + başlık, büyük değer, altında küçük açıklama."""

    def __init__(self, title: str, value: str = "0", color: str | None = None, parent=None, caption: str = ""):
        super().__init__(parent)
        from . import theme
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 13, 16, 13)
        lay.setSpacing(3)
        head = QHBoxLayout()
        head.setSpacing(7)
        dot = QLabel()
        dot.setFixedSize(7, 7)
        dot.setStyleSheet(f"background:{color or theme.FAINT}; border-radius:3px;")
        t = QLabel(T(title).upper())
        t.setObjectName("cardTitle")
        head.addWidget(dot)
        head.addWidget(t, 1)
        lay.addLayout(head)
        self.value = QLabel(value)
        self.value.setObjectName("cardValue")
        if color:
            self.value.setStyleSheet(f"color: {color};")
        lay.addWidget(self.value)
        self.caption = QLabel(caption)
        self.caption.setObjectName("cardCaption")
        lay.addWidget(self.caption)

    def set(self, text: str, caption: str | None = None) -> None:
        self.value.setText(text)
        if caption is not None:
            self.caption.setText(caption)


class StatusDot(QWidget):
    def __init__(self, color: str = "#8a9bb8", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self.setFixedSize(10, 10)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 10, 10)


def bgr_to_qimage(img: np.ndarray) -> QImage:
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()


class SelectableImage(QLabel):
    """Görüntü gösterir; fareyle dikdörtgen seçilebilir (orijinal piksel koordinatı döner)."""

    selectionChanged = Signal(QRect)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(QSize(480, 360))
        self.setStyleSheet("background:#070c17; border:1px solid #1f2c4a; border-radius:12px;")
        self._img: np.ndarray | None = None
        self._raw: np.ndarray | None = None
        self._pix: QPixmap | None = None
        self._origin = QPoint()
        self._band = QRubberBand(QRubberBand.Rectangle, self)
        self._sel: QRect | None = None
        self.setText(T("Önce bir client seçip 'Ekran görüntüsü al'a bas"))

    # --- görüntü
    def set_image(self, img: np.ndarray, raw: np.ndarray | None = None) -> None:
        """img: gösterilen; raw: şablon kesimi için temiz görüntü (çizimsiz)."""
        self._img = img
        self._raw = raw if raw is not None else img
        self._pix = QPixmap.fromImage(bgr_to_qimage(img))
        self._sel = None
        self._band.hide()
        self._refresh()

    def image(self) -> np.ndarray | None:
        return self._raw

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._refresh()

    def _refresh(self) -> None:
        if self._pix is None:
            return
        self.setPixmap(self._pix.scaled(self.size() - QSize(4, 4), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self._band.hide()

    def _geom(self):
        pm = self.pixmap()
        if pm is None or pm.isNull() or self._img is None:
            return None
        ox = (self.width() - pm.width()) / 2
        oy = (self.height() - pm.height()) / 2
        scale = self._img.shape[1] / pm.width()
        return ox, oy, scale, pm.width(), pm.height()

    # --- seçim
    def mousePressEvent(self, e):
        if self._geom() is None:
            return
        self._origin = e.position().toPoint()
        self._band.setGeometry(QRect(self._origin, QSize()))
        self._band.show()

    def mouseMoveEvent(self, e):
        if self._band.isVisible():
            self._band.setGeometry(QRect(self._origin, e.position().toPoint()).normalized())

    def mouseReleaseEvent(self, e):
        g = self._geom()
        if g is None or not self._band.isVisible():
            return
        ox, oy, scale, pw, ph = g
        r = self._band.geometry()
        x1 = int((max(r.left(), ox) - ox) * scale)
        y1 = int((max(r.top(), oy) - oy) * scale)
        x2 = int((min(r.right(), ox + pw) - ox) * scale)
        y2 = int((min(r.bottom(), oy + ph) - oy) * scale)
        if x2 - x1 >= 6 and y2 - y1 >= 6:
            self._sel = QRect(x1, y1, x2 - x1, y2 - y1)
            self.selectionChanged.emit(self._sel)
        else:
            self._sel = None
            self._band.hide()

    def selection_rect(self) -> QRect | None:
        return self._sel

    def selection_crop(self) -> np.ndarray | None:
        if self._raw is None or self._sel is None:
            return None
        r = self._sel
        return self._raw[r.y(): r.y() + r.height(), r.x(): r.x() + r.width()].copy()


class LiveView(QLabel):
    """Canlı görüntü. Bir nesneye tıklanınca (kategori, kesit, buton, ekran konumu) yayar.

    Akıcılık için her karede yeni QPixmap ölçeklemek yerine görüntü doğrudan paintEvent içinde
    (donanım hızlandırmalı yumuşak ölçekleme ile) çizilir; saniyede 60 kare rahatça gösterilir."""

    objectClicked = Signal(str, object, object, object)
    emptyClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self._payload: dict | None = None
        self._qimg: QImage | None = None
        self._target = QRectF()

    def set_payload(self, payload: dict) -> None:
        self._payload = payload
        self._qimg = bgr_to_qimage(payload["img"])
        if self.text():
            self.setText("")
        self.update()

    def clear_view(self, text: str) -> None:
        self._payload = None
        self._qimg = None
        self.clear()
        self.setText(text)

    def _calc_target(self) -> QRectF:
        if self._qimg is None or self._qimg.isNull():
            return QRectF()
        iw, ih = self._qimg.width(), self._qimg.height()
        w, h = max(1, self.width() - 4), max(1, self.height() - 4)
        sc = min(w / iw, h / ih)
        tw, th = iw * sc, ih * sc
        return QRectF((self.width() - tw) / 2, (self.height() - th) / 2, tw, th)

    def paintEvent(self, e):
        if self._qimg is None or self._qimg.isNull():
            super().paintEvent(e)
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        self._target = self._calc_target()
        p.drawImage(self._target, self._qimg)
        p.end()

    def mousePressEvent(self, e):
        p = self._payload
        if not p or p.get("raw") is None or self._qimg is None:
            return
        r = self._target if not self._target.isNull() else self._calc_target()
        if r.width() <= 0:
            return
        img_w = p["img"].shape[1]
        sc = img_w / r.width()
        x = (e.position().x() - r.x()) * sc
        y = (e.position().y() - r.y()) * sc
        hits = [b for b in p["boxes"] if b[0] - 6 <= x <= b[0] + b[2] + 6 and b[1] - 6 <= y <= b[1] + b[3] + 6]
        if not hits:
            self.emptyClicked.emit()
            return
        bx, by, bw, bh, kind = min(hits, key=lambda b: b[2] * b[3])
        raw = p["raw"]
        crop = raw[max(0, by - 2): by + bh + 2, max(0, bx - 2): bx + bw + 2].copy()
        if crop.size == 0:
            return
        self.objectClicked.emit(kind, crop, e.button(), e.globalPosition().toPoint())


from .theme import DANGER as DANGER_C, MUTED as MUTED_C, SUCCESS as SUCCESS_C  # noqa: E402


def round_text(r: dict) -> tuple[str, str, str]:
    """(başlık, açıklama, renk) — tur sonucu metni: isabet/ıska, hedefe uzaklık ve kazanılan ödül."""
    from core.i18n import T, lang
    parts = []
    if r.get("err") is not None:
        parts.append(T("hedefe {e} px").format(e=f"{r['err']:+.0f}"))
    elif r.get("desc"):
        parts.append(r["desc"])
    if r.get("speed"):
        parts.append(T("hız {v} px/sn").format(v=f"{r['speed']:.0f}"))
    if r.get("fixed"):
        parts.append(T("seri sayacına göre düzeltildi"))
    desc = "  •  ".join(parts)
    if r.get("ok"):
        return "✓  " + T("İSABET"), desc, SUCCESS_C
    return "✗  " + T("ISKA"), desc, DANGER_C


class ResultBanner(QLabel):
    """Canlı görüntünün üstünde birkaç saniye görünen büyük sonuç bandı."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_result(self, r: dict) -> None:
        title, desc, color = round_text(r)
        self.setText(T("<div style='font-size:26px; font-weight:800;'>{0}</div><div style='font-size:15px; font-weight:600;'>{1}</div>").format((title), (desc)))
        self.setStyleSheet(f"background: {color}; color: white; border-radius: 12px; padding: 10px;")
        p = self.parentWidget()
        w = min(360, p.width() - 40)
        self.setGeometry((p.width() - w) // 2, 18, w, 84)
        self.raise_()
        self.show()
        self._timer.start(2600)


class RoundList(QListWidget):
    """Son turların renkli listesi."""

    def __init__(self, parent=None, max_items: int = 100):
        super().__init__(parent)
        self.max_items = max_items
        self.setStyleSheet("QListWidget::item { padding: 8px 10px; border-radius: 7px; margin: 2px 0; }")

    @staticmethod
    def _fill(it, pid: int, r: dict) -> None:
        import time as _t
        title, desc, color = round_text(r)
        t = _t.strftime("%H:%M:%S", _t.localtime(r.get("time", _t.time())))
        it.setText(f"{t}   {title}   {desc}" + (f"   [PID {pid}]" if pid else ""))
        it.setForeground(QColor(color))
        bg = QColor(color)
        bg.setAlpha(20)
        it.setBackground(bg)

    def add_round(self, pid: int, r: dict, real_pid: int | None = None) -> None:
        tag = f"{real_pid if real_pid is not None else pid}:{r.get('rid')}"
        if r.get("fix"):                        # daha önce eklenen tur düzeltildi: yerinde güncelle
            for i in range(min(self.count(), 30)):
                it = self.item(i)
                if it is not None and it.data(Qt.UserRole) == tag:
                    self._fill(it, pid, r)
                    return
            return
        it = QListWidgetItem("")
        self._fill(it, pid, r)
        it.setData(Qt.UserRole, tag)
        self.insertItem(0, it)
        while self.count() > self.max_items:
            self.takeItem(self.count() - 1)


class SummaryGrid(QWidget):
    """Anahtar / değer satırları (iki sütun). set_rows([(etiket, değer, renk|None), ...])."""

    def __init__(self, parent=None, cols: int = 1):
        super().__init__(parent)
        self.cols = cols
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(8)
        self._cells: list[tuple[QLabel, QLabel]] = []

    def set_rows(self, rows: list[tuple[str, str, str | None]]) -> None:
        if len(rows) != len(self._cells):
            for k, v in self._cells:
                k.setParent(None)
                v.setParent(None)
            self._cells = []
            for i in range(len(rows)):
                k = QLabel()
                k.setObjectName("kvKey")
                v = QLabel()
                v.setObjectName("kvVal")
                v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                r, c = i // self.cols, (i % self.cols) * 2
                self.grid.addWidget(k, r, c)
                self.grid.addWidget(v, r, c + 1)
                self._cells.append((k, v))
        for (k, v), (label, value, color) in zip(self._cells, rows):
            k.setText(label)
            v.setText(value)
            v.setStyleSheet(f"color:{color};" if color else "")
