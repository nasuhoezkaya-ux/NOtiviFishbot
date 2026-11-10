"""Panel: Client'lar (genel bakış) + Client detay ekranı (yeni balık sistemi).

Genel bakış: her client bir kart (önizleme, durum, sayılar, başlat/durdur).
Bir karta tıklanınca (veya F7 ile seçilince) sadece o client'a ait detay ekranı açılır.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import TYPE_CHECKING

import cv2
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from core.i18n import T, lang
from core.winapi import GameWindow, WindowCapture, client_info

from . import theme
from .help import H, HelpIcon, help_label
from .fx import StatusPill
from .scan_window import ScanPanel
from .widgets import Card, LiveView, ResultBanner, RoundList, StatCard, SummaryGrid, bgr_to_qimage, round_text

if TYPE_CHECKING:
    from .main_window import MainWindow

PAD = 24          # sayfa kenar boşluğu
GAP = 16          # bileşenler arası boşluk
BTN_H = 38        # tüm düğmelerin yüksekliği


def fmt_duration(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def button(text: str, kind: str = "", tip: str = "") -> QPushButton:
    b = QPushButton(T(text))
    if kind:
        b.setObjectName(kind)
    b.setMinimumHeight(BTN_H)
    b.setCursor(Qt.PointingHandCursor)
    if tip:
        b.setToolTip(tip)
    return b


def section_title(text: str) -> QLabel:
    t = QLabel(text)
    t.setObjectName("section")
    return t


def card_with_title(title: str, right: QWidget | None = None, help_key: str | None = None) -> tuple[Card, QVBoxLayout]:
    title = T(title)
    c = Card()
    v = QVBoxLayout(c)
    v.setContentsMargins(18, 16, 18, 16)
    v.setSpacing(12)
    h = QHBoxLayout()
    h.addWidget(section_title(title))
    if help_key and H.get(help_key):
        h.addWidget(HelpIcon(H[help_key]))
    h.addStretch()
    if right is not None:
        h.addWidget(right)
    v.addLayout(h)
    return c, v


def run_button_style(b: QPushButton, running: bool, stopping: bool = False, big: bool = False) -> None:
    pad = "8px 22px" if big else "6px 14px"
    if stopping:
        b.setText(T("…  Duruyor"))
        b.setEnabled(False)
        b.setStyleSheet(f"padding:{pad};")
    elif running:
        b.setText(T("■  Durdur"))
        b.setEnabled(True)
        b.setStyleSheet(f"padding:{pad}; background:{theme.DANGER}; color:white; border:none; font-weight:700;")
    else:
        b.setText(T("▶  Başlat"))
        b.setEnabled(True)
        b.setStyleSheet(f"padding:{pad}; background:{theme.SUCCESS}; color:#04210f; border:none; font-weight:700;")


class StatePill(QLabel):
    """Küçük durum etiketi (karta ve detay başlığına)."""

    def set_state(self, text: str, running: bool) -> None:
        colors = {T(k): v for k, v in theme.STATE_COLORS.items()}
        text = T(text)
        c = colors.get(text, theme.ACCENT) if running else theme.MUTED
        self.setText(("●  " if running else "■  ") + (text if running else T("Durduruldu")))
        self.setStyleSheet(f"color:{c}; background: rgba(255,255,255,0.04); border:1px solid {c};"
                           "border-radius:11px; padding:3px 10px; font-weight:600; font-size:12px;")


# ====================================================================== client kartı
class ClientTile(QFrame):
    W, H = 300, 318

    def __init__(self, dash: "DashboardPage", game: GameWindow):
        super().__init__()
        self.dash, self.game = dash, game
        self.setObjectName("tile")
        self.setFixedSize(self.W, self.H)
        self.setCursor(Qt.PointingHandCursor)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(9)
        self.thumb = QLabel(T("önizleme"))
        self.thumb.setFixedSize(self.W - 28, 132)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet(f"background:{theme.LIVE_BG}; border-radius:9px; color:{theme.FAINT};")
        v.addWidget(self.thumb)
        trow = QHBoxLayout()
        trow.setSpacing(6)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.title = QLabel()
        self.title.setStyleSheet("font-weight:600; font-size:14px;")
        self.sub = QLabel()
        self.sub.setObjectName("faint")
        col.addWidget(self.title)
        col.addWidget(self.sub)
        trow.addLayout(col, 1)
        rm = QPushButton("✕")
        rm.setObjectName("iconBtn")
        rm.setFixedSize(26, 26)
        rm.setCursor(Qt.PointingHandCursor)
        rm.setToolTip(T("Listeden kaldır"))
        rm.clicked.connect(lambda: self.dash.remove_client(self.game.pid))
        trow.addWidget(rm, 0, Qt.AlignTop)
        v.addLayout(trow)
        prow = QHBoxLayout()
        self.pill = StatePill()
        prow.addWidget(self.pill)
        prow.addStretch()
        self.up = QLabel()
        self.up.setObjectName("faint")
        prow.addWidget(self.up)
        v.addLayout(prow)
        mrow = QHBoxLayout()
        mrow.setSpacing(0)
        self.m: dict[str, QLabel] = {}
        for k, label, color in (("ok", "İsabet", theme.SUCCESS), ("fail", "Iska", theme.DANGER),
                                ("rate", "Oran", theme.TEXT)):
            box = QVBoxLayout()
            box.setSpacing(0)
            val = QLabel("0")
            val.setStyleSheet(f"font-size:17px; font-weight:600; color:{color};")
            cap = QLabel(T(label).upper())
            cap.setObjectName("cardTitle")
            box.addWidget(val)
            box.addWidget(cap)
            mrow.addLayout(box, 1)
            self.m[k] = val
        v.addLayout(mrow)
        brow = QHBoxLayout()
        brow.setSpacing(8)
        self.run = button("▶  Başlat")
        self.run.clicked.connect(lambda: self.dash.toggle(self.game.pid))
        self.more = button("Detay  →")
        self.more.clicked.connect(lambda: self.dash.open_client(self.game.pid))
        brow.addWidget(self.run, 1)
        brow.addWidget(self.more, 1)
        v.addLayout(brow)
        self.update_view()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.dash.open_client(self.game.pid)

    def set_thumb(self, img) -> None:
        pm = QPixmap.fromImage(bgr_to_qimage(img))
        pm = pm.scaled(self.thumb.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        pm = pm.copy(max(0, (pm.width() - self.thumb.width()) // 2), max(0, (pm.height() - self.thumb.height()) // 2),
                     self.thumb.width(), self.thumb.height())
        # yuvarlatılmış köşeler
        out = QPixmap(pm.size())
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pm.width(), pm.height(), 9, 9)
        p.setClipPath(path)
        p.drawPixmap(0, 0, pm)
        p.end()
        self.thumb.setPixmap(out)

    def update_view(self) -> None:
        g, d = self.game, self.dash
        title = g.title if len(g.title) <= 28 else g.title[:27] + "…"
        self.title.setText(title)
        self.title.setToolTip(f"{g.title}\n{g.exe}")
        ci = client_info(g.hwnd)
        res = f"  ·  {ci['w']}×{ci['h']}" if ci else ""
        self.sub.setText(f"{g.exe}  ·  PID {g.pid}{res}")
        w = d.win.workers.get(g.pid)
        running = bool(w and w.is_alive())
        self.pill.set_state(d.states.get(g.pid, "Hazır"), running)
        s = d.stats.get(g.pid) or {}
        up = time.time() - w.stats.started_at if running else s.get("uptime", 0)
        self.up.setText(fmt_duration(up) if (running or up) else "")
        ok, fail = s.get("success", 0), s.get("fail", 0)
        self.m["ok"].setText(str(ok))
        self.m["fail"].setText(str(fail))
        self.m["rate"].setText(f"%{ok / (ok + fail) * 100:.0f}" if ok + fail else "—")
        run_button_style(self.run, running, running and w.stop_event.is_set())
        sel = d.win.preview_pid == g.pid
        self.setStyleSheet(f"QFrame#tile {{ border: 1px solid {theme.ACCENT if sel else theme.BORDER}; }}"
                           f"QFrame#tile:hover {{ border-color: {theme.ACCENT if sel else theme.BORDER_2}; }}")


class FlowGrid(QWidget):
    """Kartları genişliğe göre satırlara dizen basit ızgara."""

    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setStyleSheet(f"QWidget#root {{ background: {theme.SURFACE}; }}")
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(GAP)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.items: list[QWidget] = []
        self._cols = 0

    def set_items(self, items: list[QWidget]) -> None:
        for w in self.items:
            if w not in items:
                w.setParent(None)
                w.deleteLater()
        self.items = items
        self._cols = 0
        self._relayout()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()

    def _relayout(self) -> None:
        cols = max(1, (self.width() + GAP) // (ClientTile.W + GAP))
        if cols == self._cols and all(self.grid.indexOf(w) >= 0 for w in self.items):
            return
        self._cols = cols
        for w in self.items:
            self.grid.removeWidget(w)
        for i, w in enumerate(self.items):
            self.grid.addWidget(w, i // cols, i % cols)


def page_header(title: str, sub: QLabel) -> QVBoxLayout:
    col = QVBoxLayout()
    col.setSpacing(2)
    t = QLabel(T(title))
    t.setObjectName("h1")
    sub.setObjectName("pageSub")
    col.addWidget(t)
    col.addWidget(sub)
    return col


# ====================================================================== genel bakış
class OverviewPage(QWidget):
    def __init__(self, dash: "DashboardPage"):
        super().__init__()
        self.dash = dash
        lay = QVBoxLayout(self)
        lay.setContentsMargins(PAD, PAD, PAD, PAD)
        lay.setSpacing(GAP)

        head = QHBoxLayout()
        head.setSpacing(10)
        self.subtitle = QLabel()
        head.addLayout(page_header("Client'lar", self.subtitle))
        head.addSpacing(10)
        self.pill = StatusPill()
        head.addWidget(self.pill, 0, Qt.AlignVCenter)
        head.addStretch()
        self.btn_refresh = button("⟳  Yenile")
        self.btn_tile = button("⊞  Pencereleri diz", tip=H.get("b_tile", ""))
        self.btn_start = button("▶  Tümünü Başlat", "primary")
        self.btn_stop = button("■  Tümünü Durdur", "danger")
        for b in (self.btn_refresh, self.btn_tile, self.btn_start, self.btn_stop):
            head.addWidget(b, 0, Qt.AlignVCenter)
        lay.addLayout(head)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        lay.addWidget(self.hint)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.c_total = StatCard("Toplam tur", color=theme.ACCENT)
        self.c_ok = StatCard("İsabet", color=theme.SUCCESS)
        self.c_fail = StatCard("Iska", color=theme.DANGER)
        self.c_rate = StatCard("İsabet oranı", "—", color=theme.TEXT)
        self.c_casts = StatCard("Atılan olta", color=theme.MUTED)
        self.c_active = StatCard("Aktif bot", "0", color=theme.WARNING)
        for c, k in ((self.c_total, "s_total"), (self.c_ok, "s_ok"), (self.c_fail, "s_fail"), (self.c_rate, "s_rate"),
                     (self.c_casts, "s_casts"), (self.c_active, "s_active")):
            c.setToolTip(H.get(k, ""))
            stats.addWidget(c)
        lay.addLayout(stats)

        body = QHBoxLayout()
        body.setSpacing(GAP)
        left_card, lv = card_with_title("Oyun client'ları")
        self.empty = QLabel()
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet(f"color:{theme.MUTED}; font-size:14px; padding:40px;")
        lv.addWidget(self.empty)
        self.flow = FlowGrid()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.flow)
        scroll.setFrameShape(QFrame.NoFrame)
        lv.addWidget(scroll, 1)
        body.addWidget(left_card, 3)

        right = QVBoxLayout()
        right.setSpacing(GAP)
        self.sum_lbl = QLabel("")
        self.sum_lbl.setObjectName("faint")
        rc, rv = card_with_title("Son turlar", self.sum_lbl)
        self.rounds = RoundList()
        rv.addWidget(self.rounds, 1)
        right.addWidget(rc, 3)
        cc, cv = card_with_title("Özet", None, "summary")
        self.summary = SummaryGrid(cols=2)
        cv.addWidget(self.summary)
        right.addWidget(cc, 0)
        sc, scv = card_with_title("Tarama", None, "b_scan")
        self.scan = ScanPanel(events_only=True, on_popout=lambda: dash._open_scan(None))
        scv.addWidget(self.scan, 1)
        right.addWidget(sc, 3)
        rw = QWidget()
        rw.setLayout(right)
        rw.setMinimumWidth(380)
        body.addWidget(rw, 2)
        lay.addLayout(body, 1)

        self.btn_refresh.clicked.connect(dash.refresh)
        self.btn_tile.clicked.connect(dash.tile)
        self.btn_start.clicked.connect(dash.start_all)
        self.btn_stop.clicked.connect(dash.win.stop_all)


# ====================================================================== client detay
class ClientPage(QWidget):
    def __init__(self, dash: "DashboardPage"):
        super().__init__()
        self.dash = dash
        lay = QVBoxLayout(self)
        lay.setContentsMargins(PAD, PAD, PAD, PAD)
        lay.setSpacing(GAP)

        head = QHBoxLayout()
        head.setSpacing(12)
        back = button("←  Tüm client'lar", "ghost")
        back.clicked.connect(dash.show_overview)
        head.addWidget(back, 0, Qt.AlignVCenter)
        tcol = QVBoxLayout()
        tcol.setSpacing(2)
        trow = QHBoxLayout()
        trow.setSpacing(10)
        self.title = QLabel()
        self.title.setObjectName("h1")
        trow.addWidget(self.title)
        self.pill = StatePill()
        trow.addWidget(self.pill, 0, Qt.AlignVCenter)
        trow.addStretch()
        tcol.addLayout(trow)
        self.subtitle = QLabel()
        self.subtitle.setObjectName("pageSub")
        tcol.addWidget(self.subtitle)
        head.addLayout(tcol, 1)
        rm = button("✕  Listeden kaldır", "ghost")
        rm.clicked.connect(lambda: dash.remove_client(dash.current))
        head.addWidget(rm, 0, Qt.AlignVCenter)
        self.run = button("▶  Başlat")
        self.run.setMinimumWidth(150)
        self.run.clicked.connect(lambda: dash.toggle(dash.current))
        head.addWidget(self.run, 0, Qt.AlignVCenter)
        lay.addLayout(head)

        self.hint = QLabel()
        self.hint.setWordWrap(True)
        lay.addWidget(self.hint)

        body = QHBoxLayout()
        body.setSpacing(GAP)

        # ---- sol: canlı görüntü
        self.res_lbl = QLabel("")
        self.res_lbl.setObjectName("faint")
        live_card, lv = card_with_title("Canlı izleme", self.res_lbl, "live")
        self.live = LiveView()
        self.live.setMinimumSize(QSize(480, 300))
        self.live.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.live.setStyleSheet(f"background:{theme.LIVE_BG}; border-radius:10px; color:{theme.FAINT};")
        self.live.setText(T("Görüntü bekleniyor…"))
        lv.addWidget(self.live, 1)
        self.banner = ResultBanner(self.live)
        legend = QLabel(T("<b>Zamanlama:</b> <span style='color:#3ce63c'>■</span> kutucuk &nbsp; "
                        "<span style='color:#ff28c8'>●</span> hedef (kutucuğun tam ortası) &nbsp; "
                        "<span style='color:#ff2828'>■</span> siyah balık &nbsp; "
                        "<span style='color:#ffdc00'>●</span> tuş oyuna ulaştığında balığın yeri &nbsp; "
                        "✕ balığın durduğu yer<br>"
                        "<b>Balık beklerken:</b> <span style='color:#28a0ff'>■</span> arama alanı &nbsp; "
                        "<span style='color:#ff28c8'>+</span> kendi kafan &nbsp; "
                        "<span style='color:#3ce63c'>■</span> senin işaretin &nbsp; "
                        "<span style='color:#969696'>■</span> başka oyuncuların işareti (yok sayılır)"))
        legend.setObjectName("faint")
        legend.setWordWrap(True)
        lv.addWidget(legend)
        self.teach = QLabel()
        self.teach.setWordWrap(True)
        lv.addWidget(self.teach)
        arow = QHBoxLayout()
        arow.setSpacing(10)
        b_head = button("🎯  İşaret alanımı seç", "primary", H.get("b_head", ""))
        b_snap = button("📸  Anlık kayıt", tip=H.get("b_snap", ""))
        arow.addWidget(b_head, 2)
        arow.addWidget(b_snap, 1)
        lv.addLayout(arow)
        body.addWidget(live_card, 3)

        # ---- sağ: bilgiler (kaydırılabilir)
        side = QWidget()
        side.setObjectName("root")
        sv = QVBoxLayout(side)
        sv.setContentsMargins(0, 0, 6, 0)
        sv.setSpacing(GAP)

        chips = QGridLayout()
        chips.setSpacing(12)
        self.k_ok = StatCard("İsabet", color=theme.SUCCESS)
        self.k_fail = StatCard("Iska", color=theme.DANGER)
        self.k_rate = StatCard("Oran", "—", color=theme.TEXT)
        self.k_lat = StatCard("Tuş gecikmesi", T("— ms"), color=theme.ACCENT)
        for i, (c, k) in enumerate(((self.k_ok, "s_ok"), (self.k_fail, "s_fail"), (self.k_rate, "s_rate"),
                                    (self.k_lat, "s_lat"))):
            c.setToolTip(H.get(k, ""))
            chips.addWidget(c, i // 2, i % 2)
        sv.addLayout(chips)

        ic, iv = card_with_title("Client bilgileri")
        self.info_grid = QGridLayout()
        self.info_grid.setHorizontalSpacing(14)
        self.info_grid.setVerticalSpacing(9)
        self.info: dict[str, QLabel] = {}
        fields = [("exe", "Program"), ("res", "Çözünürlük"), ("pos", "Ekran konumu"), ("dpi", "Ölçekleme"),
                  ("input", "Giriş yöntemi"), ("area", "İşaret alanı"), ("sign", "İşaret resmi"),
                  ("last", "Son sonuç"), ("uptime", "Çalışma süresi")]
        for i, (k, label) in enumerate(fields):
            kl = help_label(label, H.get("i_" + k), muted=True)      # help_label çevirir
            vl = QLabel("—")
            vl.setObjectName("kvVal")
            vl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            vl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.info_grid.addWidget(kl, i, 0)
            self.info_grid.addWidget(vl, i, 1)
            self.info[k] = vl
        iv.addLayout(self.info_grid)
        sv.addWidget(ic)

        self.r_sum = QLabel("")
        self.r_sum.setObjectName("faint")
        rc, rv = card_with_title("Bu client'ın turları", self.r_sum)
        self.rounds = RoundList(max_items=60)
        self.rounds.setMinimumHeight(190)
        rv.addWidget(self.rounds)
        sv.addWidget(rc)

        sc, scv = card_with_title("Tarama", None, "b_scan")
        self.scan = ScanPanel(on_popout=lambda: dash._open_scan(dash.current))
        self.scan.setMinimumHeight(260)
        scv.addWidget(self.scan)
        sv.addWidget(sc)

        cc, cv = card_with_title("Özet", None, "summary")
        self.summary = SummaryGrid()
        cv.addWidget(self.summary)
        sv.addWidget(cc)
        sv.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(side)
        scroll.setMinimumWidth(400)
        body.addWidget(scroll, 2)
        lay.addLayout(body, 1)

        b_head.clicked.connect(dash._pick_head)
        b_snap.clicked.connect(dash._snapshot)

    def set_info(self, key: str, text: str, color: str | None = None) -> None:
        v = self.info.get(key)
        if v is not None:
            v.setText(text)
            v.setStyleSheet(f"color:{color};" if color else "")


# ====================================================================== panel (iki ekran)
class DashboardPage(QStackedWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.games: dict[int, GameWindow] = {}
        self.stats: dict[int, dict] = {}
        self.states: dict[int, str] = {}
        self.last_result: dict[int, str] = {}
        self.history: dict[int, list[dict]] = {}
        self.tiles: dict[int, ClientTile] = {}
        self.current: int | None = None
        self._last10: list[tuple] = []   # (pid, tur no, isabet)

        self.overview = OverviewPage(self)
        self.client = ClientPage(self)
        self.addWidget(self.overview)
        self.addWidget(self.client)
        self.live = self.client.live

        self._hint_timer = QTimer(self)
        self._hint_timer.setSingleShot(True)
        self._hint_timer.timeout.connect(self._pick_hint_default)
        self._teach_timer = QTimer(self)
        self._teach_timer.setSingleShot(True)
        self._teach_timer.timeout.connect(self._teach_default)
        self.thumb_timer = QTimer(self)
        self.thumb_timer.timeout.connect(self._update_thumbs)
        self.thumb_timer.start(2000)
        self._pick_hint_default()
        self._teach_default()

    # ------------------------------------------------------------ gezinme
    def open_client(self, pid: int) -> None:
        if pid not in self.games:
            return
        self.current = pid
        self.win.preview_pid = pid
        g = self.games[pid]
        title = g.title if len(g.title) <= 34 else g.title[:33] + "…"
        self.client.title.setText(f"{title}")
        self.client.live.clear_view(T("Görüntü bekleniyor…"))
        self.client.rounds.clear()
        self.client.scan.set_pid(pid)
        ci = client_info(g.hwnd)
        self.client.subtitle.setText(f"{g.exe}  ·  PID {g.pid}" + (f"  ·  {ci['w']}×{ci['h']}" if ci else ""))
        for r in self.history.get(pid, [])[-60:]:
            self.client.rounds.add_round(0, r, real_pid=pid)
        self.setCurrentWidget(self.client)
        self.win.go(0)
        self.tick()

    def show_overview(self) -> None:
        self.current = None
        self.win.preview_pid = None
        self.setCurrentWidget(self.overview)
        self._update_thumbs()
        self.tick()

    def detail_visible(self) -> bool:
        return self.currentWidget() is self.client and self.isVisible()


    # ------------------------------------------------------------ client listesi
    def refresh(self, check_pid: int | None = None) -> None:
        games = self.win.find_clients()
        for pid, w in self.win.workers.items():
            if w.is_alive() and pid not in {g.pid for g in games}:
                games.append(w.game)
        self.games = {g.pid: g for g in games}
        tiles = []
        for g in games:
            t = self.tiles.get(g.pid)
            if t is None or t.game.hwnd != g.hwnd:
                t = ClientTile(self, g)
                self.tiles[g.pid] = t
            tiles.append(t)
        for pid in list(self.tiles):
            if pid not in self.games:
                self.tiles.pop(pid)
        self.overview.flow.set_items(tiles)
        has = bool(games)
        self.overview.empty.setVisible(not has)
        self.overview.empty.setText(
            T('🎯\n\nHenüz client yok.\nOyunda fareyi oyun penceresinin üstüne getir ve {0} tuşuna bas.').format((self.win.cfg['pick_key'])))
        self._update_thumbs()
        if check_pid is not None and check_pid in self.games:
            self.open_client(check_pid)
        elif self.current is not None and self.current not in self.games:
            self.show_overview()
        self.tick()

    def toggle(self, pid: int | None) -> None:
        if pid is None:
            return
        w = self.win.workers.get(pid)
        if w and w.is_alive():
            self.win.stop_bot(pid)
        elif pid in self.games:
            self.win.start_bot(self.games[pid])
        self.tick()

    def remove_client(self, pid: int) -> None:
        g = self.games.get(pid)
        if g is None:
            return
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox(self)
        box.setWindowTitle(T("Client'ı kaldır"))
        box.setText(T('<b>{0}</b><br>{1}  •  PID {2}').format((g.title), (g.exe), (g.pid)))
        box.setInformativeText(T("Sadece bu pencereyi mi kaldırmak istiyorsun, yoksa bu programı hiç listelememeyi mi?"))
        only = box.addButton(T("Sadece bu pencere"), QMessageBox.AcceptRole)
        block = box.addButton(T('{0} programını engelle').format((g.exe)), QMessageBox.DestructiveRole)
        box.addButton(T("Vazgeç"), QMessageBox.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked not in (only, block):
            return
        if self.current == pid:
            self.show_overview()
        self.tiles.pop(pid, None)
        self.win.remove_client(g, block_exe=clicked is block)

    def start_all(self) -> None:
        if not self.games:
            self.flash_pick(T('Önce {0} ile bir client seç.').format((self.win.cfg['pick_key'])), ok=False)
            return
        from .main_window import MAX_CLIENTS
        games = list(self.games.values())[:MAX_CLIENTS]
        for g in games:
            self.win.start_bot(g)
        if len(self.games) > MAX_CLIENTS:
            self.flash_pick(T("Bot aynı anda en fazla {n} client çalıştırır.").format(n=MAX_CLIENTS), ok=False)
        self.tick()

    def tile(self) -> None:
        from core.winapi import tile_windows
        n = tile_windows([g.hwnd for g in list(self.games.values())[:4]])
        self.flash_pick(T("{n} pencere ekrana dizildi. Pencereler üst üste binmezse botlar daha hızlı okur.").format(n=n)
                        if n else T("Dizilecek client yok."), ok=bool(n))

    def _update_thumbs(self) -> None:
        if self.currentWidget() is not self.overview or not self.isVisible():
            return
        for pid, t in list(self.tiles.items())[:12]:
            img = WindowCapture(t.game.hwnd).grab()
            if img is not None:
                t.set_thumb(img)


    # ------------------------------------------------------------ bot olayları
    def set_state(self, pid: int, state: str) -> None:
        self.states[pid] = state

    def update_stats(self, pid: int, d: dict | None) -> None:
        if d is not None:
            self.stats[pid] = d

    def show_frame(self, pid: int, payload) -> None:
        # kareler birikmesin: sadece en sonuncusu çizilir (arayüz geride kalırsa eskiler atlanır)
        if pid != self.current or not payload or not self.detail_visible():
            return
        first = getattr(self, "_pending_frame", None) is None
        self._pending_frame = payload
        if first:
            QTimer.singleShot(0, self._apply_frame)

    def _apply_frame(self) -> None:
        payload, self._pending_frame = getattr(self, "_pending_frame", None), None
        if payload:
            self.client.live.set_payload(payload)
            img = payload.get("img")
            if img is not None:
                self.client.res_lbl.setText(f"{img.shape[1]}×{img.shape[0]}")

    def add_round(self, pid: int, r: dict) -> None:
        if r.get("fix"):
            # seri sayacı turun gerçek sonucunu bildirdi: listedeki turu düzelt
            hist = self.history.get(pid, [])
            for i in range(len(hist) - 1, max(-1, len(hist) - 30), -1):
                if hist[i].get("rid") == r.get("rid"):
                    hist[i] = {k: v for k, v in r.items() if k != "fix"}
                    break
            self.overview.rounds.add_round(pid, r)
            if pid == self.current:
                self.client.rounds.add_round(0, r, real_pid=pid)
            for j, (p_, rid_, _ok) in enumerate(self._last10):
                if p_ == pid and rid_ == r.get("rid"):
                    self._last10[j] = (p_, rid_, bool(r.get("ok")))
            self._show_last10()
            self.last_result[pid] = round_text(r)[0].replace("✓", "").replace("✗", "").strip()
            return
        self.history.setdefault(pid, []).append(r)
        self.history[pid] = self.history[pid][-200:]
        self.overview.rounds.add_round(pid, r)
        if pid == self.current:
            self.client.rounds.add_round(0, r, real_pid=pid)
            self.client.banner.show_result(r)
        self.last_result[pid] = round_text(r)[0].replace("✓", "").replace("✗", "").strip() + \
            (f" • {round_text(r)[1]}" if round_text(r)[1] else "")
        self._last10 = ([(pid, r.get("rid"), bool(r.get("ok")))] + self._last10)[:10]
        self._show_last10()

    def _show_last10(self) -> None:
        ok = sum(1 for t in self._last10 if t[2])
        self.overview.sum_lbl.setText(T('son {0}:  ✓ {1}   ✗ {2}').format((len(self._last10)), (ok), (len(self._last10) - ok)))

    # ------------------------------------------------------------ periyodik güncelleme
    def _uptime(self, pid: int, d: dict) -> float:
        w = self.win.workers.get(pid)
        if w is not None and w.is_alive():
            return time.time() - w.stats.started_at
        return float(d.get("uptime", 0) or 0)

    def _summary_rows(self, items: list[tuple[int, dict]]) -> list[tuple[str, str, str | None]]:
        """Özet: sadece botun gerçekten saydığı / ölçtüğü değerler."""
        if not items:
            return [(T("Henüz tur yok"), "", None)]
        tot = lambda k: sum(int(d.get(k, 0) or 0) for _, d in items)       # noqa: E731
        ok, fail = tot("success"), tot("fail")
        rounds = ok + fail
        n_err = sum(int(d.get("err_n", 0) or 0) for _, d in items)
        avg = sum(float(d.get("abs_err_sum", 0) or 0) for _, d in items) / n_err if n_err else None
        ups = [self._uptime(pid, d) for pid, d in items]
        per_h = sum((int(d.get("success", 0)) + int(d.get("fail", 0))) / (u / 3600)
                    for (pid, d), u in zip(items, ups) if u > 120)
        ver = tot("verified")
        rows = [
            (T("Çalışma süresi"), fmt_duration(max(ups) if ups else 0), None),
            (T("Atılan olta"), str(tot("casts")), None),
            (T("Oynanan tur"), str(rounds), None),
            (T("İsabet"), str(ok), theme.SUCCESS),
            (T("Iska"), str(fail), theme.DANGER),
            (T("İsabet oranı"), f"%{ok / rounds * 100:.1f}" if rounds else "—", None),
            (T("Seri sayacıyla doğrulanan"), f"{ver} / {rounds}" if rounds else "—", None),
            (T("Seri sayacına göre düzeltilen"), str(tot("corrected")), theme.WARNING if tot("corrected") else None),
            (T("Hedefe ortalama uzaklık"), f"{avg:.1f} px" if avg is not None else "—", None),
            (T("Saatte tur"), f"{per_h:.0f}" if per_h else "—", None),
            (T("Balık işareti gelmedi"), str(tot("timeouts")), None),
            (T("Yanlış alarm"), str(tot("false_alarms")), None),
            (T("Basılamadan kapanan pencere"), str(tot("no_press")), None),
            (T("Çözülen captcha"), str(tot("captchas")), None),
        ]
        return rows

    def tick(self) -> None:
        o = self.overview
        ok = sum(d.get("success", 0) for d in self.stats.values())
        fail = sum(d.get("fail", 0) for d in self.stats.values())
        tot = lambda k: sum(int(d.get(k, 0) or 0) for d in self.stats.values())    # noqa: E731
        n = sum(1 for w in self.win.workers.values() if w.is_alive() and not w.stop_event.is_set())
        o.c_total.set(str(ok + fail), T("{n} client").format(n=len(self.games)))
        o.c_ok.set(str(ok), T("seriyle doğrulanan {n}").format(n=tot("verified")))
        o.c_fail.set(str(fail), T("düzeltilen {n}").format(n=tot("corrected")))
        o.c_rate.set(f"%{ok / (ok + fail) * 100:.1f}" if ok + fail else "—",
                     T("son {0}: {1} isabet").format(len(self._last10), sum(1 for t in self._last10 if t[2]))
                     if self._last10 else "")
        o.c_casts.set(str(tot("casts")), T("işaret gelmedi {n}").format(n=tot("timeouts")))
        o.c_active.set(str(n), T("{n} client içinden").format(n=len(self.games)))
        o.subtitle.setText(T("{0} client  ·  {1} çalışıyor").format(len(self.games), n))
        o.pill.set_running(n)
        o.btn_stop.setEnabled(n > 0)
        o.btn_stop.setText(T('■  Tümünü Durdur ({0})').format((n)) if n else T("■  Tümünü Durdur"))
        o.btn_start.setEnabled(bool(self.games))
        o.summary.set_rows(self._summary_rows(list(self.stats.items())))
        for t in self.tiles.values():
            t.update_view()
        if self.current is not None:
            self._update_client()

    def _update_client(self) -> None:
        pid = self.current
        g = self.games.get(pid)
        c = self.client
        if g is None:
            return
        cfg = self.win.cfg
        w = self.win.workers.get(pid)
        running = bool(w and w.is_alive())
        c.pill.set_state(self.states.get(pid, "Hazır"), running)
        run_button_style(c.run, running, running and w.stop_event.is_set(), big=True)
        d = self.stats.get(pid) or {}
        okc, flc = int(d.get("success", 0)), int(d.get("fail", 0))
        c.k_ok.set(str(okc), T("seriyle doğrulanan {n}").format(n=d.get("verified", 0)))
        c.k_fail.set(str(flc), T("düzeltilen {n}").format(n=d.get("corrected", 0)))
        c.k_rate.set(f"%{okc / (okc + flc) * 100:.1f}" if okc + flc else "—",
                     T("ortalama {v} px").format(v=f"{d['avg_err']:.1f}") if d.get("avg_err") is not None else "")
        c.k_lat.set(f"{float(cfg['timing_latency_ms']):.0f} ms",
                    T("her turda öğrenilir") if cfg["timing_autolearn"] else T("sabit"))
        ci = client_info(g.hwnd)
        c.set_info("exe", T('{0}  (PID {1})').format((g.exe), (g.pid)))
        if ci:
            c.set_info("res", f"{ci['w']} × {ci['h']}")
            c.set_info("pos", f"{ci['x']}, {ci['y']}" + (T("  simge durumunda!") if ci["min"] else ""),
                       theme.WARNING if ci["min"] else None)
            aw = T({0: "oyun ölçeklemeyi bilmiyor", 1: "sistem", 2: "monitör"}.get(ci.get("aware"), "?"))
            c.set_info("dpi", f"%{ci['scale']}  ({aw})" if ci.get("scale") else "—")
        c.set_info("input", T({"karma": "Karma (önerilen)", "postmessage": "Arka plan",
                               "sendinput": "Ön plan"}.get(cfg["input_method"], "?")))
        a = cfg["bite_area"]
        c.set_info("area", T('✓ seçili  {0}×{1}').format((a['w']), (a['h'])) if isinstance(a, dict) else T("otomatik (ekranın ortası)"),
                   theme.SUCCESS if isinstance(a, dict) else theme.MUTED)
        try:
            from core.timing import SIGN_DIR
            n_sign = len(list(SIGN_DIR.glob("*.png")))
        except Exception:
            n_sign = 0
        sc = cfg["bite_scale"]
        c.set_info("sign", (T("{n} resim").format(n=n_sign) + (T(", ölçek {s}").format(s=f"{float(sc):.2f}") if sc else T(", ölçek ilk balıkta bulunur")))
                   if n_sign else T("yok (ilk balıkta öğrenilir)"), theme.SUCCESS if n_sign else theme.WARNING)
        c.set_info("last", self.last_result.get(pid, "—"))
        up = time.time() - w.stats.started_at if running else d.get("uptime", 0)
        c.set_info("uptime", fmt_duration(up))
        hist = self.history.get(pid, [])[-10:]
        okn = sum(1 for r in hist if r.get("ok"))
        c.r_sum.setText(T('son {0}:  ✓ {1}   ✗ {2}').format((len(hist)), (okn), (len(hist) - okn)) if hist else "")
        c.summary.set_rows(self._summary_rows([(pid, d)] if d else []))

    # ------------------------------------------------------------ ipuçları
    def _pick_hint_default(self) -> None:
        k, s = self.win.cfg["pick_key"], self.win.cfg["stop_key"]
        txt = T("<span style='color:{0}'><b>{1}</b></span> fare oyun penceresindeyken client seç"
                "&nbsp;&nbsp;·&nbsp;&nbsp;<b>İşaret alanımı seç</b> (yanında balık tutan oyuncu varsa)"
                "&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{2}'><b>{3}</b></span> tüm botları durdur").format(
            theme.ACCENT, k, theme.DANGER, s)
        for h in (self.overview.hint, self.client.hint):
            h.setStyleSheet(self._hint_style())
            h.setText(txt)

    def _teach_default(self) -> None:
        self.client.teach.setStyleSheet(f"color:{theme.MUTED};")
        self.client.teach.setText(T("Bot, siyah balık mor noktaya varırken Space'e basar; tuş gecikmesini her turda "
                                  "balığın durduğu yere bakarak kendisi düzeltir."))

    # ------------------------------------------------------------ eylemler
    def _data_dir(self, name: str) -> str:
        from core.config import DATA_DIR
        d = os.path.join(DATA_DIR, name)
        os.makedirs(d, exist_ok=True)
        return d

    def _snapshot(self) -> None:
        p = self.client.live._payload
        if not p:
            self.flash_teach(T("Önce canlı görüntü gelmeli."), theme.WARNING)
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        d = self._data_dir("anlik")
        ok, buf = cv2.imencode(".png", p["img"])
        if ok:
            buf.tofile(os.path.join(d, f"{stamp}_anlik.png"))
        self.flash_teach(T('✓ Kaydedildi: data\\anlik\\{0}_anlik.png').format((stamp)), theme.SUCCESS)

    def _pick_head(self) -> None:
        g = self.games.get(self.current) if self.current else None
        if g is None:
            return
        from .head_dialog import HeadAreaDialog
        HeadAreaDialog(g, self.win.cfg, self).exec()
        self.tick()

    def _hint_style(self, color: str | None = None) -> str:
        if color:
            return (f"color:white; background:{color}; border-radius:10px; padding:9px 14px; "
                    "font-weight:600;")
        return (f"color:{theme.MUTED}; background:{theme.SURFACE}; border:1px solid {theme.BORDER}; "
                "border-radius:10px; padding:9px 14px;")

    def flash_pick(self, text: str, ok: bool = True) -> None:
        for h in (self.overview.hint, self.client.hint):
            h.setStyleSheet(self._hint_style(theme.SUCCESS if ok else theme.WARNING))
            h.setText(text)
        self._hint_timer.start(4000)

    def flash_teach(self, text: str, color: str) -> None:
        self.client.teach.setStyleSheet(f"color:{color}; font-weight:600;")
        self.client.teach.setText(text)
        self._teach_timer.start(2500)

    def on_scan(self, pid: int, line: str) -> None:
        self.overview.scan.add_line(pid, line)
        if pid == self.current:
            self.client.scan.add_line(pid, line)

    def _open_scan(self, pid: int | None = None) -> None:
        from .scan_window import ScanWindow
        if getattr(self.win, "scan_win", None) is None:
            self.win.scan_win = ScanWindow(self.win)
        self.win.scan_win.set_pid(pid)
        self.win.scan_win.show()
        self.win.scan_win.raise_()
        self.win.scan_win.activateWindow()

