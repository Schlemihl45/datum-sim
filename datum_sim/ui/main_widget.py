import re

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from datum_sim.ui.viewport import Viewport
from datum_sim.ui.overlay.settings_panel import SettingsPanel
from datum_sim.ui.overlay.control_hub import ControlHub


class DatumSimWidget(QWidget):

    # ── Signals ───────────────────────────────────────────────────────────────
    line_changed     = Signal(int)
    position_changed = Signal(float, float, float)
    simulation_ended = Signal()
    error_occurred   = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Subwidgets (Kinder von self, nicht von viewport!) ─────────────────
        self.viewport = Viewport(self)
        self.settings = SettingsPanel(self)

        self.control_hub = ControlHub(self)
        self.control_hub.play_clicked.connect(self.play)
        self.control_hub.pause_clicked.connect(self.pause)
        self.control_hub.stop_clicked.connect(self.stop)
        self.control_hub.speed_changed.connect(self.set_speed)


        self._layout_overlays()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _layout_overlays(self):
        """Viewport füllt alles, Overlays werden manuell positioniert."""
        self.viewport.setGeometry(self.rect())
        # Strip immer rechts bündig – Breite variiert je nach Panel-Zustand
        w = self.settings.width()
        self.settings.setGeometry(
            self.width() - w,
            0,
            w,
            self.height(),
        )

        if hasattr(self, 'control_hub'):
            margin = 20
            hub_w = self.control_hub.width()
            hub_h = self.control_hub.height()  # Holt sich die dynamische Höhe!

            x = (self.width() - hub_w) // 2
            y = self.height() - hub_h - margin

            self.control_hub.setGeometry(x, y, hub_w, hub_h)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._layout_overlays()

    # ── Öffentliche API ───────────────────────────────────────────────────────
    def load_file(self, path: str):
        print("load file")

    def load_gcode(self, gcode: str):
        print("loading gcode")
    def play(self):
        print("play")

    def pause(self):
        print("pause")

    def stop(self):
        print("stop")

    def set_speed(self, factor: float):
        print("set speed")

    def jump_to_line(self, line: int):
        """Simulation zu einer bestimmten G-Code-Zeile vorspulen."""
        print("jump_to_line")

    def set_current_line(self, line: int):
        """Aktuelle Zeile von außen setzen (LinuxCNC-Kopplung)."""
        self.control_hub.set_gcode(f"N{line} ...")
        print("set_current_line")