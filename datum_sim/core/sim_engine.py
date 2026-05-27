"""
SimEngine – animiert den Werkzeugweg Linie für Linie.

Läuft in einem QThread damit die UI nicht blockiert.
Kommuniziert über Signals mit dem Viewport.
"""

from __future__ import annotations
import time
from PySide6.QtCore import QThread, Signal
from datum_sim.core.toolpath import ParseResult


class SimEngine(QThread):

    # Signals → werden von DatumSimWidget empfangen
    progress   = Signal(int)    # Aktueller Vertex-Index → ToolpathRenderer
    line_changed = Signal(int)  # Aktuelle G-Code-Zeile → ControlHub
    finished   = Signal()       # Simulation abgeschlossen

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result:  ParseResult | None = None
        self._speed:   float = 1.0
        self._paused:  bool  = False
        self._stopped: bool  = False

    # ── Steuerung ─────────────────────────────────────────────────────────────

    def load(self, result: ParseResult, renderer=None):
        self._result = result
        self._renderer = renderer

    def set_speed(self, factor: float):
        self._speed = max(0.01, factor)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._stopped = True
        self._paused  = False

    # ── Thread ────────────────────────────────────────────────────────────────

    def run(self):
        if self._result is None or not self._result.moves:
            return

        self._stopped = False
        self._paused = False

        STEPS_PER_MM = 5  # Interpolationsschritte pro mm
        UPDATE_HZ = 60  # Maximale Framerate

        for i, move in enumerate(self._result.moves):
            if self._stopped:
                break

            import numpy as np
            dist = float(np.linalg.norm(move.end - move.start))
            steps = max(1, int(dist * STEPS_PER_MM))

            # Wie lange dauert dieser Move in Sekunden?
            if move.feedrate > 0 and move.type != 'rapid':
                duration = (dist / move.feedrate * 60) / self._speed
            else:
                duration = dist * 0.0002 / self._speed  # Eilgang: schnell

            dt = duration / steps

            for step in range(1, steps + 1):
                while self._paused and not self._stopped:
                    time.sleep(0.05)
                if self._stopped:
                    return

                # Vertex-Index für diesen Teilschritt
                # move_vertex_map[i] = erster Vertex dieses Moves
                # move_vertex_map[i+1] = erster Vertex des nächsten Moves
                v_start = self._renderer.move_vertex_map(i)
                v_end = self._renderer.move_vertex_map(i + 1)
                v_range = v_end - v_start
                v_now = v_start + int(v_range * step / steps)

                self.progress.emit(v_now)
                self.line_changed.emit(move.line_number)

                time.sleep(max(dt, 1 / UPDATE_HZ))

        if not self._stopped:
            self.finished.emit()