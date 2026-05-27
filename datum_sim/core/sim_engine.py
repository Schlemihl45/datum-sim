from __future__ import annotations
import time
import numpy as np
from PySide6.QtCore import QThread, Signal
from datum_sim.core.toolpath import ParseResult, Move


class SimSession:
    """
    Hält den kompletten Zustand einer laufenden Simulation.
    Wird bei Reset neu erstellt, bei Pause eingefroren.
    """
    def __init__(self, result: ParseResult):
        self.result       = result
        self.move_index   = 0
        self.vertex_index = 0
        self.voxel_cache  = None


class SimEngine(QThread):

    progress     = Signal(int)
    line_changed = Signal(int)
    finished     = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session:  SimSession | None = None
        self._renderer = None
        self._speed: float = 1.0
        self._paused: bool = False
        self._stopped: bool = False

    def load(self, result: ParseResult, renderer):
        """Creates a new session"""
        self._session = SimSession(result)
        self._renderer = renderer

    def set_speed(self, factor: float):
        self._speed = max(0.01, factor)

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._stopped = True
        self._paused = False

    def run(self):
        print("run() wird ausgeführt")
        if self._session is None or self._renderer is None:
            print(f"  ABBRUCH: session={self._session}, renderer={self._renderer}")
            return

        self._stopped = False
        self._paused = False
        self._renderer.reset()
        self.progress.emit(0)
        print("progress(0) emitted")

        session = self._session
        STEPS_PER_MM = 5
        MIN_SLEEP = 1 / 30

        FRAME_TIME = 1 / 60  # 60fps Ziel

        for i, move in enumerate(session.result.moves):
            if self._stopped:
                break
            while self._paused and not self._stopped:
                time.sleep(0.05)

            session.move_index = i

            dist = float(np.linalg.norm(move.end - move.start))
            v_start = self._renderer.move_vertex_map(i)
            v_end = self._renderer.move_vertex_map(i + 1)
            v_range = v_end - v_start
            steps = max(1, v_range // 2)

            # Wie lange dauert ein Segment in Sekunden?
            if move.feedrate > 0 and move.type not in ('rapid', 'arc_cw', 'arc_ccw'):
                seg_duration = (dist / move.feedrate * 60) / self._speed / steps
            else:
                seg_duration = 0.0001 / self._speed

            # Wie viele Segmente passen in einen Frame?
            segs_per_frame = max(1, int(FRAME_TIME / seg_duration))

            frame_start = time.perf_counter()

            for step in range(1, steps + 1):
                while self._paused and not self._stopped:
                    time.sleep(0.05)
                if self._stopped:
                    return

                v_now = v_start + step * 2
                session.vertex_index = v_now
                self.progress.emit(v_now)
                self.line_changed.emit(move.line_number)

                # Nur schlafen wenn genug Segmente in diesem Frame verarbeitet
                if step % segs_per_frame == 0:
                    elapsed = time.perf_counter() - frame_start
                    sleep_t = FRAME_TIME - elapsed
                    if sleep_t > 0:
                        time.sleep(sleep_t)
                    frame_start = time.perf_counter()

        if not self._stopped:
            self.finished.emit()