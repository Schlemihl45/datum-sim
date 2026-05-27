import re

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from datum_sim.ui.viewport import Viewport
from datum_sim.ui.overlay.settings_panel import SettingsPanel
from datum_sim.ui.overlay.control_hub import ControlHub

from datum_sim.core.gcode_parser import GCodeParser
from datum_sim.core.sim_engine import SimEngine


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

        self._engine = SimEngine(self)
        self._engine.progress.connect(self._on_sim_progress)
        self._engine.line_changed.connect(self._on_line_changed)
        self._engine.finished.connect(self._on_sim_finished)

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
    def _on_sim_progress(self, vertex_index: int):
        self.viewport.toolpath_renderer.set_progress(vertex_index)
        self.viewport.update()

    def _on_line_changed(self, line: int):
        self.line_changed.emit(line)

    def _on_sim_finished(self):
        self.simulation_ended.emit()
        self.control_hub.set_gcode("Simulation abgeschlossen")

    def load_file(self, path: str):
        self._engine.stop()
        self._engine.wait()
        parser = GCodeParser()
        result = parser.parse_file(path)
        self._result = result
        self.viewport.load_result(result)
        if result.moves:
            self.control_hub.set_gcode(f"Geladen: {len(result.moves)} Moves")

    def load_gcode(self, gcode: str):
        parser = GCodeParser()
        result = parser.parse_string(gcode)
        self._result = result
        self.viewport.load_result(result)

    def play(self):
        if self._engine.isRunning():
            self._engine.resume()
        else:
            if self._result is not None:
                self.viewport.toolpath_renderer.reset()
                self._engine.load(
                    self._result,
                    self.viewport.toolpath_renderer  # ← neu
                )
                self._engine.start()

    def pause(self):
        self._engine.pause()

    def stop(self):
        self._engine.stop()
        self._engine.wait()
        self.viewport.toolpath_renderer.reset()
        self.viewport.update()

    def set_speed(self, factor: float):
        self._engine.set_speed(factor)

    def jump_to_line(self, line: int):
        """Simulation zu einer bestimmten G-Code-Zeile vorspulen."""
        print("jump_to_line")

    def set_current_line(self, line: int):
        """Aktuelle Zeile von außen setzen (LinuxCNC-Kopplung)."""
        self.control_hub.set_gcode(f"N{line} ...")
        print("set_current_line")