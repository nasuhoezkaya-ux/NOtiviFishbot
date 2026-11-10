"""Çizimle yapılan arayüz parçaları: logo, menü simgeleri, hesap kartı, durum göstergesi.

Emoji yerine vektör simgeler kullanılır (her ekranda ve her ölçeklemede keskin görünür)."""
from __future__ import annotations

import math
from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.i18n import T

from core.version import APP_NAME
from . import theme


# ====================================================================== simgeler
def paint_icon(p: QPainter, name: str, r: QRectF, color: QColor, width: float = 1.7) -> None:
    """Basit çizgi simgeleri (r: simgenin kutusu)."""
    pen = QPen(color, width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.save()
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    x, y, w, h = r.x(), r.y(), r.width(), r.height()
    if name == "clients":                       # 2x2 pencere
        g = w * 0.12
        s = (w - g) / 2
        for i in range(2):
            for j in range(2):
                p.drawRoundedRect(QRectF(x + i * (s + g), y + j * (s + g), s, s), 2.5, 2.5)
    elif name == "settings":                    # ayar sürgüleri
        for k, kx in enumerate((0.30, 0.70, 0.45)):
            yy = y + h * (0.2 + 0.3 * k)
            p.drawLine(QPointF(x, yy), QPointF(x + w, yy))
            p.setBrush(QColor(theme.SURFACE))
            p.drawEllipse(QPointF(x + w * kx, yy), w * 0.12, w * 0.12)
            p.setBrush(Qt.NoBrush)
    elif name == "logs":                        # satırlı belge
        p.drawRoundedRect(QRectF(x + w * 0.1, y, w * 0.8, h), 3, 3)
        for k in range(3):
            yy = y + h * (0.3 + 0.2 * k)
            p.drawLine(QPointF(x + w * 0.3, yy), QPointF(x + w * (0.7 if k < 2 else 0.55), yy))
    elif name == "captcha":                     # kalkan + tik
        path = QPainterPath()
        path.moveTo(x + w * 0.5, y)
        path.lineTo(x + w * 0.92, y + h * 0.16)
        path.lineTo(x + w * 0.88, y + h * 0.55)
        path.quadTo(x + w * 0.8, y + h * 0.86, x + w * 0.5, y + h)
        path.quadTo(x + w * 0.2, y + h * 0.86, x + w * 0.12, y + h * 0.55)
        path.lineTo(x + w * 0.08, y + h * 0.16)
        path.closeSubpath()
        p.drawPath(path)
        p.drawPolyline([QPointF(x + w * 0.33, y + h * 0.5), QPointF(x + w * 0.46, y + h * 0.63),
                        QPointF(x + w * 0.68, y + h * 0.38)])
    elif name == "members":                     # iki kişi
        p.drawEllipse(QPointF(x + w * 0.36, y + h * 0.3), w * 0.16, w * 0.16)
        p.drawArc(QRectF(x + w * 0.06, y + h * 0.56, w * 0.6, h * 0.7), 0, 180 * 16)
        p.drawEllipse(QPointF(x + w * 0.72, y + h * 0.36), w * 0.12, w * 0.12)
        p.drawArc(QRectF(x + w * 0.56, y + h * 0.6, w * 0.42, h * 0.5), 0, 180 * 16)
    elif name == "clock":
        p.drawEllipse(r.adjusted(1, 1, -1, -1))
        c = r.center()
        p.drawLine(c, QPointF(c.x(), y + h * 0.28))
        p.drawLine(c, QPointF(x + w * 0.68, c.y()))
    p.restore()


class NavButton(QPushButton):
    """Kenar menüsü düğmesi: vektör simge + yazı, seçiliyken solda vurgu çizgisi."""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(text, parent)
        self.icon_name = icon
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")

    def sizeHint(self) -> QSize:
        return QSize(190, 40)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        on, hover = self.isChecked(), self.underMouse()
        if on or hover:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.SURFACE_3 if on else theme.SURFACE_2))
            p.drawRoundedRect(r, 8, 8)
        if on:
            p.setBrush(QColor(theme.ACCENT))
            p.drawRoundedRect(QRectF(r.left(), r.top() + 10, 3, r.height() - 20), 1.5, 1.5)
        col = QColor(theme.TEXT if on else (theme.TEXT if hover else theme.MUTED))
        paint_icon(p, self.icon_name, QRectF(16, r.center().y() - 8, 16, 16),
                   QColor(theme.ACCENT) if on else col)
        f = QFont(self.font())
        f.setWeight(QFont.Weight.DemiBold if on else QFont.Weight.Medium)
        p.setFont(f)
        p.setPen(col)
        p.drawText(r.adjusted(44, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, self.text())
        p.end()


# ====================================================================== logo
class BrandMark(QWidget):
    """Uygulama logosu: degrade kare içinde balık."""

    def __init__(self, size: int = 34, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = float(self.width())
        g = QLinearGradient(0, 0, s, s)
        g.setColorAt(0, QColor(theme.ACCENT))
        g.setColorAt(1, QColor(theme.ACCENT_2))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.28, s * 0.28)
        fish = QPainterPath()
        fish.addEllipse(QPointF(s * 0.45, s * 0.5), s * 0.23, s * 0.145)
        tail = QPainterPath()
        tail.moveTo(s * 0.62, s * 0.5)
        tail.lineTo(s * 0.82, s * 0.35)
        tail.lineTo(s * 0.78, s * 0.5)
        tail.lineTo(s * 0.82, s * 0.65)
        tail.closeSubpath()
        p.setBrush(QColor("white"))
        p.drawPath(fish.united(tail))
        p.setBrush(QColor(theme.ACCENT))
        p.drawEllipse(QPointF(s * 0.34, s * 0.47), s * 0.035, s * 0.035)
        p.end()


class Brand(QWidget):
    """Logo + ürün adı."""

    def __init__(self, parent=None, mark: int = 34, title_px: int = 17):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(11)
        h.addWidget(BrandMark(mark))
        v = QVBoxLayout()
        v.setSpacing(0)
        t = QLabel(APP_NAME)
        t.setStyleSheet(f"font-size:{title_px}px; font-weight:700;")
        from core.version import VERSION
        sub = QLabel(T("Balık otomasyonu") + f"  ·  v{VERSION}")
        sub.setStyleSheet(f"color:{theme.FAINT}; font-size:11px;")
        v.addWidget(t)
        v.addWidget(sub)
        h.addLayout(v)
        h.addStretch()


# ====================================================================== hesap kartı
class Avatar(QWidget):
    def __init__(self, name: str, size: int = 38, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = float(self.width())
        g = QLinearGradient(0, 0, s, s)
        g.setColorAt(0, QColor(theme.ACCENT))
        g.setColorAt(1, QColor(theme.ACCENT_2))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QRectF(0, 0, s, s))
        parts = [w for w in self.name.replace("_", " ").replace(".", " ").split() if w]
        ini = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")) if parts else "?"
        f = QFont(self.font())
        f.setPixelSize(int(s * 0.38))
        f.setWeight(QFont.Weight.Bold)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, ini.upper())
        p.end()


class ThinBar(QWidget):
    """İnce ilerleme çubuğu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frac = 0.0
        self.color = QColor(theme.ACCENT)
        self.setFixedHeight(6)

    def set(self, frac: float, color: str) -> None:
        self.frac = max(0.0, min(1.0, frac))
        self.color = QColor(color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.SURFACE_3))
        p.drawRoundedRect(r, 3, 3)
        if self.frac > 0:
            p.setBrush(self.color)
            p.drawRoundedRect(QRectF(r.x(), r.y(), max(6.0, r.width() * self.frac), r.height()), 3, 3)
        p.end()


def remaining_text(expires_at: datetime) -> str:
    """'23 gün 4 saat' / '5 saat 12 dk' / 'Süresi doldu'."""
    sec = int((expires_at - datetime.now()).total_seconds())
    if sec <= 0:
        return T("Süresi doldu")
    d, h, m = sec // 86400, sec % 86400 // 3600, sec % 3600 // 60
    if d > 0:
        return T("{d} gün {h} saat").format(d=d, h=h)
    return T("{h} saat {m} dk").format(h=h, m=m)


class AccountCard(QFrame):
    """Kenar menüsünün altında kullanıcı adı ve kalan üyelik süresi."""

    PERIOD_DAYS = 30.0

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(10)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(Avatar(username))
        col = QVBoxLayout()
        col.setSpacing(1)
        self.name = QLabel(username)
        self.name.setStyleSheet("font-size:14px; font-weight:600;")
        self.status = QLabel()
        col.addWidget(self.name)
        col.addWidget(self.status)
        top.addLayout(col, 1)
        v.addLayout(top)
        line = QFrame()
        line.setObjectName("divider")
        v.addWidget(line)
        k = QLabel(T("KALAN SÜRE"))
        k.setObjectName("eyebrow")
        v.addWidget(k)
        self.left = QLabel("—")
        self.left.setStyleSheet("font-size:18px; font-weight:600;")
        v.addWidget(self.left)
        self.bar = ThinBar()
        v.addWidget(self.bar)
        row = QHBoxLayout()
        a = QLabel(T("Bitiş"))
        a.setObjectName("faint")
        self.until = QLabel("—")
        self.until.setStyleSheet(f"color:{theme.MUTED}; font-size:12px;")
        row.addWidget(a)
        row.addStretch()
        row.addWidget(self.until)
        v.addLayout(row)

    def set_expiry(self, expires_at: datetime | None) -> None:
        left_s = 10 ** 12 if expires_at is None else (expires_at - datetime.now()).total_seconds()
        days = left_s / 86400
        if expires_at is None or days > 36500:
            self.left.setText(T("Süresiz"))
            self.until.setText("—")
            self.bar.set(1.0, theme.SUCCESS)
            color = theme.SUCCESS
        else:
            self.left.setText(remaining_text(expires_at))
            self.until.setText(f"{expires_at:%d.%m.%Y  ·  %H:%M}")
            color = theme.ACCENT if days > 7 else (theme.WARNING if days > 2 else theme.DANGER)
            self.bar.set(days / self.PERIOD_DAYS, color)
        active = left_s > 0
        self.status.setText(("●  " + T("Aktif üyelik")) if active else ("●  " + T("Üyelik sona erdi")))
        self.status.setStyleSheet(f"color:{theme.SUCCESS if active else theme.DANGER}; font-size:11px;")


# ====================================================================== genel durum
class StatusPill(QWidget):
    """Botların genel durumu: çalışıyor (nabız gibi atan nokta) / durduruldu."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = 0
        self._t = 0.0
        self.setFixedSize(176, 30)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def set_running(self, n: int) -> None:
        self.running = n
        self.update()

    def _tick(self) -> None:
        self._t += 0.05
        if self.running:
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        on = self.running > 0
        col = QColor(theme.SUCCESS if on else theme.FAINT)
        bg = QColor(col)
        bg.setAlpha(28 if on else 18)
        border = QColor(col)
        border.setAlpha(110 if on else 90)
        p.setPen(QPen(border, 1))
        p.setBrush(bg)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        c = QPointF(r.left() + 16, r.center().y())
        if on:
            k = (math.sin(self._t * 4) + 1) / 2
            halo = QColor(col)
            halo.setAlpha(int(100 * (1 - k)))
            p.setPen(Qt.NoPen)
            p.setBrush(halo)
            p.drawEllipse(c, 4 + 5 * k, 4 + 5 * k)
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawEllipse(c, 4, 4)
        f = QFont(self.font())
        f.setPixelSize(12)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor(theme.TEXT if on else theme.MUTED))
        text = T("Çalışıyor  ·  {n} bot").format(n=self.running) if on else T("Durduruldu")
        p.drawText(r.adjusted(30, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
        p.end()


# ====================================================================== giriş ekranı sol paneli
class HeroPanel(QWidget):
    """Giriş ekranının sol tarafı: degrade zemin, ince dalga çizgileri, logo ve kısa tanıtım."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(360)
        v = QVBoxLayout(self)
        v.setContentsMargins(40, 44, 40, 36)
        v.setSpacing(0)
        v.addWidget(BrandMark(52), 0, Qt.AlignLeft)
        v.addSpacing(26)
        t = QLabel(APP_NAME)
        t.setStyleSheet("font-size:30px; font-weight:700; color:white; background:transparent;")
        v.addWidget(t)
        v.addSpacing(6)
        sub = QLabel(T("Metin2 için akıllı balık tutma asistanı"))
        sub.setWordWrap(True)
        sub.setStyleSheet("font-size:14px; color:rgba(255,255,255,0.72); background:transparent;")
        v.addWidget(sub)
        v.addSpacing(30)
        for line in (T("Kutucuğu ve balığı canlı izler"), T("Tuş gecikmesini her turda kendisi öğrenir"),
                     T("Sonucu oyunun seri sayacıyla doğrular"), T("Birden fazla client'ı aynı anda yönetir")):
            row = QHBoxLayout()
            row.setSpacing(10)
            dot = QLabel("✓")
            dot.setFixedSize(20, 20)
            dot.setAlignment(Qt.AlignCenter)
            dot.setStyleSheet("background:rgba(255,255,255,0.14); color:white; border-radius:10px;"
                              "font-size:11px; font-weight:700;")
            lb = QLabel(line)
            lb.setStyleSheet("color:rgba(255,255,255,0.86); font-size:13px; background:transparent;")
            row.addWidget(dot)
            row.addWidget(lb, 1)
            v.addLayout(row)
            v.addSpacing(12)
        v.addStretch()
        from core.version import VERSION
        foot = QLabel("© " + APP_NAME + f"  ·  v{VERSION}")
        foot.setStyleSheet("color:rgba(255,255,255,0.45); font-size:11px; background:transparent;")
        v.addWidget(foot)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor("#1b3a8a"))
        g.setColorAt(0.55, QColor("#2a3fb0"))
        g.setColorAt(1, QColor("#4b3bb8"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRect(r)
        # ince dalga çizgileri (su)
        for k in range(7):
            path = QPainterPath()
            y0 = r.height() * (0.58 + 0.06 * k)
            amp = 10 + 2 * k
            path.moveTo(0, y0)
            steps = 48
            for i in range(steps + 1):
                x = r.width() * i / steps
                path.lineTo(x, y0 + amp * math.sin(i / steps * math.tau * 1.3 + k * 0.6))
            col = QColor(255, 255, 255, 18 + 3 * k)
            p.setPen(QPen(col, 1.2))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
        p.end()
