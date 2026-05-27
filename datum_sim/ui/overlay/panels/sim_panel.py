"""
SimPanel – Simulationseinstellungen.

Sektionen:
  1. Modus        → Werkzeugweg / Animiert / Voxel
  2. Werkzeug     → Punkt / Zylinder / Werkzeugform
  3. Darstellung  → Eilgang anzeigen, Linienbreite
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QFrame
)
from PySide6.QtCore import Qt
from datum_sim.core.settings import AppSettings


LABEL_STYLE   = "color: rgba(255,255,255,180); font-size: 11px;"
SECTION_STYLE = "color: white; font-size: 12px; font-weight: bold; padding-top: 8px; padding-bottom: 4px;"

def _section_label(text):
    l = QLabel(text)
    l.setStyleSheet(SECTION_STYLE)
    return l

def _row_label(text):
    l = QLabel(text)
    l.setStyleSheet(LABEL_STYLE)
    l.setFixedWidth(110)
    return l

def _separator():
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("color: rgba(255,255,255,40); margin: 6px 0;")
    return sep

COMBO_STYLE = """
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
"""


class SimPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._s = AppSettings.instance()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(2)
        root.setAlignment(Qt.AlignTop)

        self._build_mode(root)
        root.addWidget(_separator())
        self._build_tool(root)
        root.addWidget(_separator())
        self._build_display(root)
        root.addStretch()

    # ── 1. Modus ──────────────────────────────────────────────────────────────

    def _build_mode(self, root):
        root.addWidget(_section_label("Simulationsmodus"))

        row = QHBoxLayout()
        row.addWidget(_row_label("Modus"))
        self._mode_box = QComboBox()
        self._mode_box.setStyleSheet(COMBO_STYLE)
        self._mode_box.addItem("Werkzeugweg komplett",  "toolpath_full")
        self._mode_box.addItem("Werkzeugweg animiert",  "toolpath_anim")
        self._mode_box.addItem("Voxel animiert",        "voxel_anim")
        self._mode_box.addItem("Werkzeugweg + Voxel",   "both")

        saved = self._s.sim_mode
        for i in range(self._mode_box.count()):
            if self._mode_box.itemData(i) == saved:
                self._mode_box.setCurrentIndex(i)

        self._mode_box.currentIndexChanged.connect(
            lambda _: setattr(self._s, 'sim_mode',
                               self._mode_box.currentData()))
        row.addWidget(self._mode_box)
        root.addLayout(row)

    # ── 2. Werkzeug ───────────────────────────────────────────────────────────

    def _build_tool(self, root):
        root.addWidget(_section_label("Werkzeugdarstellung"))

        row = QHBoxLayout()
        row.addWidget(_row_label("Form"))
        self._tool_box = QComboBox()
        self._tool_box.setStyleSheet(COMBO_STYLE)
        self._tool_box.addItem("Keins",           "none")
        self._tool_box.addItem("Punkt",            "point")
        self._tool_box.addItem("Zylinder",         "cylinder")
        self._tool_box.addItem("Schaftfräser",     "endmill")

        saved = self._s.tool_display
        for i in range(self._tool_box.count()):
            if self._tool_box.itemData(i) == saved:
                self._tool_box.setCurrentIndex(i)

        self._tool_box.currentIndexChanged.connect(
            lambda _: setattr(self._s, 'tool_display',
                               self._tool_box.currentData()))
        row.addWidget(self._tool_box)
        root.addLayout(row)

    # ── 3. Darstellung ────────────────────────────────────────────────────────

    def _build_display(self, root):
        root.addWidget(_section_label("Darstellung"))

        for label, attr in [
            ("Eilgang anzeigen",  "show_rapid"),
            ("Grid anzeigen",     "show_grid"),
        ]:
            row = QHBoxLayout()
            row.addWidget(_row_label(label))
            cb = QCheckBox()
            cb.setChecked(getattr(self._s, attr))
            cb.setStyleSheet("QCheckBox::indicator { width: 20px; height: 20px; }")
            cb.toggled.connect(lambda v, a=attr: setattr(self._s, a, v))
            row.addWidget(cb)
            row.addStretch()
            root.addLayout(row)