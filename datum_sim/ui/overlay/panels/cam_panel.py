"""
CamPanel – Kamera-Einstellungen.

Sektionen:
  1. Anzeige      → Hintergrundfarbe
  2. Steuerung    → Zoom / Rotation / Pan Geschwindigkeit
  3. Invertierung → Richtungsumkehr für alle Achsen
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QCheckBox, QComboBox, QFrame, QPushButton
)
from PySide6.QtCore import Qt

from datum_sim.core.settings import AppSettings


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

LABEL_STYLE = "color: rgba(255,255,255,180); font-size: 11px;"
SECTION_STYLE = """
    QFrame {
        border: none;
        border-top: 1px solid rgba(255,255,255,40);
        margin-top: 4px;
    }
"""

def _section_label(text: str) -> QLabel:
    """Überschrift für eine Sektion."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: white; font-size: 12px; font-weight: bold;"
        "padding-top: 8px; padding-bottom: 4px;"
    )
    return lbl


def _row_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(LABEL_STYLE)
    lbl.setFixedWidth(110)
    return lbl


def _separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("color: rgba(255,255,255,40); margin: 6px 0;")
    return sep


def _speed_slider(setting_name: str, s: AppSettings) -> QSlider:
    """Slider 0.1× – 5.0×, gespeicherter Wert als Startpunkt."""
    slider = QSlider(Qt.Horizontal)
    slider.setRange(1, 50)       # intern ×10, also 0.1 – 5.0
    slider.setSingleStep(1)
    slider.setPageStep(5)
    current = getattr(s, setting_name)
    slider.setValue(int(current * 10))
    return slider


# ── CamPanel ──────────────────────────────────────────────────────────────────

class CamPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._s = AppSettings.instance()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(2)
        root.setAlignment(Qt.AlignTop)

        self._build_display(root)
        root.addWidget(_separator())
        self._build_speed(root)
        root.addWidget(_separator())
        self._build_invert(root)
        root.addStretch()

    # ── 1. Anzeige ────────────────────────────────────────────────────────────

    def _build_display(self, root: QVBoxLayout):
        root.addWidget(_section_label("View"))

        row = QHBoxLayout()
        row.addWidget(_row_label("Background Color"))

        self._color_box = QComboBox()
        self._color_box.setStyleSheet("""
            QComboBox {
                color: white;
                background: rgba(255,255,255,20);
                border: 1px solid rgba(255,255,255,40);
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                color: white;
                selection-background-color: rgba(255,255,255,40);
            }
        """)

        current = self._s.bg_color
        for name, hex_val in AppSettings.BG_COLORS.items():
            self._color_box.addItem(name, hex_val)
            if hex_val == current:
                self._color_box.setCurrentText(name)

        self._color_box.currentIndexChanged.connect(self._on_color_changed)
        row.addWidget(self._color_box)
        root.addLayout(row)

    def _on_color_changed(self, _):
        self._s.bg_color = self._color_box.currentData()

    # ── 2. Steuerung ──────────────────────────────────────────────────────────

    def _build_speed(self, root: QVBoxLayout):
        root.addWidget(_section_label("Camera"))

        for label, attr in [
            ("Zoom",     "zoom_speed"),
            ("Rotation", "rotate_speed"),
            ("Pan",      "pan_speed"),
        ]:
            row   = QHBoxLayout()
            lbl   = _row_label(label)
            val   = QLabel(f"{getattr(self._s, attr):.1f}×")
            val.setStyleSheet(LABEL_STYLE)
            val.setFixedWidth(32)

            slider = _speed_slider(attr, self._s)

            # Closure über attr und val
            def _changed(v, a=attr, display=val):
                speed = v / 10.0
                setattr(self._s, a, speed)
                display.setText(f"{speed:.1f}×")

            slider.valueChanged.connect(_changed)

            row.addWidget(lbl)
            row.addWidget(slider)
            row.addWidget(val)
            root.addLayout(row)

    # ── 3. Invertierung ───────────────────────────────────────────────────────

    def _build_invert(self, root: QVBoxLayout):
        root.addWidget(_section_label("Inverting"))

        for label, attr in [
            ("Zoom",       "invert_zoom"),
            ("Rotation X", "invert_rotate_x"),
            ("Rotation Y", "invert_rotate_y"),
            ("Pan X",      "invert_pan_x"),
            ("Pan Y",      "invert_pan_y"),
        ]:
            row = QHBoxLayout()
            row.addWidget(_row_label(label))

            cb = QCheckBox()
            cb.setChecked(getattr(self._s, attr))
            cb.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")

            def _toggled(checked, a=attr):
                setattr(self._s, a, checked)

            cb.toggled.connect(_toggled)
            row.addWidget(cb)
            row.addStretch()
            root.addLayout(row)