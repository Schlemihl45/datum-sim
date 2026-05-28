from __future__ import annotations
import time
from PySide6.QtCore import QThread, Signal
from datum_sim.core.toolpath import ParseResult
from datum_sim.core.toolstate import ToolState
from datum_sim.core.machine_backend import FreeRunBackend, MachineBackend


class SimEngine(QThread):

    tool_moved      = Signal(object)
    line_changed    = Signal(int)
    finished        = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._result: ParseResult | None = None
        self._renderer                   = None
        self._backend: MachineBackend    = FreeRunBackend()
        self._paused = False
        self._stopped = False

    def load(self, result: ParseResult, renderer):
        self._result = result
        self._renderer = renderer

    def set_backend(self, backend: MachineBackend):
        self._backend = backend

    def set_speed(self, factor: float):
        if isinstance(self._backend, FreeRunBackend):
            self._backend.set_speed(factor)

    def pause(self): self._paused = True
    def resume(self): self._paused = False
    def stop(self):
        self._stopped = True
        self._paused = False

    def _wait_if_paused(self) -> bool:
        while self._paused and not self._stopped:
            time.sleep(0.05)
        return self._stopped

    def run(self):
        if self._result is None or self._renderer is None:
            return

        self._stopped = False
        self._paused = False
        self._renderer.reset()
        self._backend.on_start()

        for move_index, move in enumerate(self._result.moves):
            if self._stopped or self._wait_if_paused():
                break

            for state in self._backend.step(move, move_index):
                if self._stopped or self._wait_if_paused():
                    self._backend.on_stop()
                    return

                # Vertex progress for ToolpathRenderer
                v_start = self._renderer.move_vertex_map(move_index)
                v_end = self._renderer.move_vertex_map(move_index + 1)
                self._renderer.set_progress(
                    int(v_start + state.t * (v_end - v_start))
                )

                self.tool_moved.emit(state)
                self.line_changed.emit(state.line_number)

        self._backend.on_stop()
        if not self._stopped:
            self.finished.emit()