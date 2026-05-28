from __future__ import annotations
import time
import numpy as np
from abc import ABC, abstractmethod
from datum_sim.core.toolpath import Move
from datum_sim.core.toolstate import ToolState
from datum_sim.core.toolpath_math import interpolate_move, arc_length

RESOLUTION_MM = 0.01

def _steps_for(dist: float) -> int:
    """
    Steps based on move length and resolution.
    At least 1.
    """
    return max(1, int(dist / RESOLUTION_MM))

class MachineBackend(ABC):
    @abstractmethod
    def on_start(self): ...

    @abstractmethod
    def step(self, move:Move, move_index:int):
        """Generator: creates ToolState objects for a move"""

    @abstractmethod
    def on_stop(self): ...

# Free Simulation
class FreeRunBackend(MachineBackend):
    """
    Time-based. Every step represents RESOLUTION_MM in physical millimeter.
    The sleep-time per step comes directly from the feedrate:

        seg_duration = RESOLUTION_MM / (feedrate / 60) [s]

    The feedrate is uneffected by the move-length
    """

    FRAME_TIME = 1 / 60 #Target FPS

    def __init__(self):
        self._speed         = 1.0
        self._frame_start   = 0.0

    def set_speed(self, s: float):
        self._speed = max(0.01, s)

    def on_start(self):
        self._frame_start = time.perf_counter()

    def step(self, move:Move, move_index:int):
        dist = arc_length(move)
        steps = _steps_for(dist)

        # Seconds per step (= RESOLUTION_MM / feedrate)
        if move.feedrate > 0 and move.type != "rapid":
            seg_duration = (RESOLUTION_MM / (move.feedrate / 60)) / self._speed
        else:
            seg_duration = 0.0

        segs_per_frame = max(1, int(self.FRAME_TIME / seg_duration)) if seg_duration > 0 else steps

        for step in range(1, steps + 1):
            t = step / steps
            pos = interpolate_move(move, t)

            yield ToolState(
                move_index=move_index,
                position=pos,
                t=t,
                feedrate=move.feedrate,
                move_type=move.type,
                line_number=move.line_number,
            )

            if step % segs_per_frame == 0:
                elapsed = time.perf_counter() - self._frame_start
                sleep_t = self.FRAME_TIME - elapsed
                if sleep_t > 0:
                    time.sleep(sleep_t)
                self._frame_start = time.perf_counter()

    def on_stop(self):
        pass

def _project_on_move(move: Move, machine_pos = np.ndarray) -> float:
    """
    Projects X,Y,Z of the machine to a move .> t in [0,1]
    Lines: analytical projections
    Arcs: Angle
    """
    if move.type in ('arc_cw', 'arc_ccw') and move.arc_center is not None:
        c = move.arc_center
        r_machine = machine_pos[:2] - c[:2]
        r_start = move.start[:2] - c[:2]
        r_end = move.end[:2] - c[:2]
        start_angle = np.arctan2(r_start[1], r_start[0])
        end_angle = np.arctan2(r_end[1], r_end[0])
        angle_m = np.arctan2(r_machine[1], r_machine[0])

        if move.type == 'arc_cw':
            if end_angle >= start_angle:
                end_angle -= 2 * np.pi
        else:
            if end_angle <= start_angle:
                end_angle += 2 * np.pi

        span = end_angle - start_angle
        if abs(span) < 1e-9:
            return 0.0
        return float(np.clip((angle_m - start_angle) / span, 0.0, 1.0))


    ab = move.end - move.start
    ap = machine_pos - move.start
    denom = float(np.dot(ab, ab))
    if denom < 1e-9:
        return 0.0
    return float(np.clip(np.dot(ap, ab) / denom, 0.0, 1.0))

