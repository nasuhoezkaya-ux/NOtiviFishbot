"""Koyu, sade ve profesyonel tema (QSS).

Renkler tek yerden gelir; bileşenler sabit renk yazmak yerine buradaki adları kullanır."""

# --- palet
BG = "#0a0e15"          # pencere zemini
SURFACE = "#10151e"     # kart
SURFACE_2 = "#161d29"   # kart içi / düğme
SURFACE_3 = "#1c2433"   # üstüne gelince
BORDER = "#212a39"
BORDER_2 = "#2c3749"
TEXT = "#e8edf4"
MUTED = "#8b97a9"
FAINT = "#5c687b"
ACCENT = "#4c8dff"      # tek vurgu rengi (mavi)
ACCENT_2 = "#7a6cff"    # degrade için ikinci ton
SUCCESS = "#2ec27e"
DANGER = "#f0525f"
WARNING = "#f5a524"
LIVE_BG = "#06090f"

FONT = '"Segoe UI Variable Text", "Segoe UI", "Inter", sans-serif'

QSS = f"""
* {{
    font-family: {FONT};
    font-size: 13px;
    color: {TEXT};
}}
QMainWindow, QDialog, QWidget#root {{ background: {BG}; }}
QWidget#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}

QLabel#h1 {{ font-size: 21px; font-weight: 600; }}
QLabel#pageSub {{ color: {MUTED}; font-size: 12px; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#faint {{ color: {FAINT}; font-size: 11px; }}
QLabel#error {{ color: {DANGER}; }}
QLabel#section {{ font-size: 14px; font-weight: 600; color: {TEXT}; }}
QLabel#eyebrow {{ color: {FAINT}; font-size: 11px; font-weight: 700; }}
QLabel#kvKey {{ color: {MUTED}; }}
QLabel#kvVal {{ font-weight: 600; }}

/* ---------- düğmeler */
QPushButton {{
    background: {SURFACE_2}; border: 1px solid {BORDER_2}; border-radius: 8px;
    padding: 7px 14px; font-weight: 600; color: {TEXT};
}}
QPushButton:hover {{ background: {SURFACE_3}; border-color: #3a475d; }}
QPushButton:pressed {{ background: {SURFACE}; }}
QPushButton:disabled {{ color: {FAINT}; border-color: {BORDER}; background: {SURFACE}; }}
QPushButton#primary {{
    background: {ACCENT}; border: 1px solid {ACCENT}; color: white;
}}
QPushButton#primary:hover {{ background: #5f9aff; border-color: #5f9aff; }}
QPushButton#primary:pressed {{ background: #3d78e0; }}
QPushButton#primary:disabled {{ background: {SURFACE_2}; border-color: {BORDER}; color: {FAINT}; }}
QPushButton#danger {{ background: transparent; border: 1px solid #5a2a31; color: {DANGER}; }}
QPushButton#danger:hover {{ background: {DANGER}; border-color: {DANGER}; color: white; }}
QPushButton#danger:disabled {{ color: {FAINT}; border-color: {BORDER}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid transparent; color: {MUTED}; padding: 5px 9px; }}
QPushButton#ghost:hover {{ background: {SURFACE_2}; color: {TEXT}; }}
QPushButton#ghost:checked {{ background: {SURFACE_3}; color: {TEXT}; border-color: {BORDER_2}; }}
QPushButton#iconBtn {{ padding: 0; border-radius: 13px; background: transparent; border: 1px solid transparent;
                       color: {FAINT}; font-size: 12px; }}
QPushButton#iconBtn:hover {{ background: {SURFACE_3}; color: {TEXT}; }}

/* ---------- giriş alanları */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
    background: {SURFACE_2}; border: 1px solid {BORDER_2}; border-radius: 8px; padding: 7px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{ border-color: #3a475d; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QLineEdit#big {{ padding: 11px 13px; font-size: 14px; border-radius: 9px; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; border: 1px solid {BORDER_2}; outline: 0;
                               selection-background-color: {SURFACE_3}; padding: 4px; }}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0; }}

/* ---------- kartlar */
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#tile {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#tile:hover {{ border-color: {BORDER_2}; background: #121823; }}
QFrame#divider {{ background: {BORDER}; max-height: 1px; min-height: 1px; border: none; }}
QLabel#cardTitle {{ color: {MUTED}; font-size: 11px; font-weight: 700; }}
QLabel#cardValue {{ font-size: 24px; font-weight: 600; }}
QLabel#cardCaption {{ color: {FAINT}; font-size: 11px; }}

/* ---------- listeler */
QListWidget {{ background: transparent; border: none; padding: 0; outline: 0; }}
QListWidget::item {{ padding: 7px 10px; border-radius: 7px; margin: 1px 0; }}
QListWidget::item:selected {{ background: {SURFACE_3}; }}
QTableWidget {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; gridline-color: transparent; }}
QHeaderView::section {{ background: {SURFACE}; color: {MUTED}; border: none; border-bottom: 1px solid {BORDER};
                        padding: 8px; font-weight: 600; font-size: 11px; }}
QPlainTextEdit#console {{
    background: {LIVE_BG}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px 8px;
    font-family: "Cascadia Mono", Consolas, monospace; font-size: 11px; color: #c9d3e0;
}}

/* ---------- seçim kutuları */
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: 16px; height: 16px; }}
QCheckBox::indicator {{ border: 1px solid {BORDER_2}; border-radius: 4px; background: {SURFACE_2}; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QRadioButton::indicator {{ border: 1px solid {BORDER_2}; border-radius: 8px; background: {SURFACE_2}; }}
QRadioButton::indicator:checked {{ background: {ACCENT}; border: 3px solid {SURFACE_2}; }}

QSlider::groove:horizontal {{ height: 4px; background: {SURFACE_3}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: white; width: 14px; margin: -5px 0; border-radius: 7px; }}

/* ---------- kaydırma çubukları */
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {BORDER_2}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #3a475d; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {BORDER_2}; border-radius: 4px; min-width: 30px; }}
QScrollArea {{ border: none; background: transparent; }}

QToolTip {{ background: {SURFACE_2}; color: {TEXT}; border: 1px solid {BORDER_2}; border-radius: 6px; padding: 8px; }}
QLabel#helpIcon {{
    background: transparent; color: {FAINT}; border: 1px solid {BORDER_2}; border-radius: 8px;
    font-size: 10px; font-weight: 700;
}}
QLabel#helpIcon:hover {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QLabel#sectionDesc {{ color: {MUTED}; font-size: 12px; }}
QFrame#sectionIcon {{ background: {SURFACE_2}; border-radius: 10px; }}
QMessageBox {{ background: {SURFACE}; }}
"""

STATE_COLORS = {
    "Olta atılıyor": ACCENT,
    "Balık bekleniyor": ACCENT,
    "Zamanlama penceresi bekleniyor": WARNING,
    "Zamanlama": SUCCESS,
    "Ödül çarkı dönüyor": SUCCESS,
    "Molada": MUTED,
    "CAPTCHA": DANGER,
    "CAPTCHA — elle çözülmesi bekleniyor": DANGER,
    "Hazır": MUTED,
    "Durdu": MUTED,
    "Hata": DANGER,
}
