import re

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from PySide6.QtCore import QTimer

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

        self._result = None
        self._engine = SimEngine(self)
        self._engine.line_changed.connect(self._on_line_changed)
        self._engine.finished.connect(self._on_finished)

        self._render_timer = QTimer(self)
        self._render_timer.setInterval(16)  # ~60fps
        self._render_timer.timeout.connect(self.viewport.update)
        self._render_timer.start()

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

    def _on_progress(self, vertex_index: int):
        self.viewport.toolpath_renderer.set_progress(vertex_index)

    def _on_line_changed(self, line: int):
        self.line_changed.emit(line)

    def _on_finished(self):
        self.simulation_ended.emit()
        self.viewport.toolpath_renderer.show_all()
        self.viewport.update()

    # Öffentliche API:
    def load_file(self, path: str):
        self._engine.stop()
        self._engine.wait()
        result = GCodeParser().parse_file(path)
        self._result = result
        self.viewport.load_result(result)

    def load_gcode(self, gcode: str):
        self._engine.stop()
        self._engine.wait()
        result = GCodeParser().parse_string(gcode)
        self._result = result
        self.viewport.load_result(result)

    def play(self):
        print(f"play() aufgerufen")
        print(f"  result: {self._result}")
        print(f"  engine läuft: {self._engine.isRunning()}")
        if self._result is None:
            print("  ABBRUCH: kein result")
            return
        if self._engine.isRunning():
            print("  resume")
            self._engine.resume()
        else:
            print("  starte engine")
            self._engine.load(self._result,
                              self.viewport.toolpath_renderer)
            print(f"  renderer: {self.viewport.toolpath_renderer}")
            print(f"  renderer moves: {len(self._result.moves)}")
            self._engine.start()
            print(f"  engine gestartet: {self._engine.isRunning()}")

    def stop(self):
        self._engine.stop()
        self._engine.wait()
        # Jetzt erst zurücksetzen – Engine ist sicher gestoppt
        self.viewport.toolpath_renderer.reset()
        self.viewport.update()

    def pause(self):
        self._engine.pause()


    def set_speed(self, factor: float):
        self._engine.set_speed(factor)

    def jump_to_line(self, line: int):
        """Simulation zu einer bestimmten G-Code-Zeile vorspulen."""
        print("jump_to_line")

    def set_current_line(self, line: int):
        """Aktuelle Zeile von außen setzen (LinuxCNC-Kopplung)."""
        self.control_hub.set_gcode(f"N{line} ...")
        print("set_current_line")