from __future__ import annotations
import numpy as np
from datum_sim.core.toolpath import Move

def interpolate_move(move: Move, t:float) -> np.ndarray:
    """
    X,Y,Z position for t \in [0,1]
    """
    t = float(np.clip(t, 0.0, 1.0))

    if move.type in ("arc_cw", "arc_ccw") and move.arc_center is not None:
        c       = move.arc_center
        r_start = move.start[:2] - c[:2]
        r_end   = move.end[:2] - c[:2]

        start_angle = np.arctan2(r_start[1], r_start[0])
        end_angle = np.arctan2(r_end[1], r_end[0])

        if move.type == "arc_cw":
            if end_angle >= start_angle:
                end_angle -= 2 * np.pi
        else:
            if end_angle <= start_angle:
                end_angle += 2 * np.pi

        angle   = start_angle + t * (end_angle - start_angle)
        radius  = float(np.linalg.norm(r_start))
        z       = move.start[2] + t * (move.end[2] - move.start[2])

        return np.array([
            c[0] + radius * np.cos(angle),
            c[1] + radius * np.sin(angle),
            z
        ], dtype = np.float32)

    return (move.start + t * (move.end - move.start)).astype(np.float32)

def arc_length(move: Move) -> float:
    """
    Length of a move in mm
    Arcs: helix-length
    Lines: euclidean distance
    """
    if move.type in ('arc_cw', 'arc_ccw') and move.arc_center is not None:
        r_start = move.start[:2] - move.arc_center[:2]
        r_end = move.end[:2] - move.arc_center[:2]
        start_angle = np.arctan2(r_start[1], r_start[0])
        end_angle = np.arctan2(r_end[1], r_end[0])

        if move.type == 'arc_cw':
            if end_angle >= start_angle:
                end_angle -= 2 * np.pi
        else:
            if end_angle <= start_angle:
                end_angle += 2 * np.pi

        span = abs(end_angle - start_angle)
        radius = float(np.linalg.norm(r_start))
        z_dist = abs(move.end[2] - move.start[2])
        return float(np.hypot(radius * span, z_dist))

    return float(np.linalg.norm(move.end - move.start))