"""
ToolpathRenderer – zeichnet Werkzeugwege als Linien im Viewport.

Farben:
  Eilgang (G0)   → gelb,  gestrichelt (kurze Segmente)
  Vorschub (G1)  → grün
  Bogen (G2/G3)  → blau  (kommt später)
"""

from __future__ import annotations
import numpy as np
import moderngl
from datum_sim.core.toolpath import ParseResult, Move


# Farben pro Move-Typ  (RGB float)
_COLORS = {
    'rapid':  (0.9, 0.8, 0.1),
    'linear': (0.2, 0.9, 0.3),
    'arc':    (0.2, 0.5, 1.0),
}


class ToolpathRenderer:

    def __init__(self, ctx: moderngl.Context):
        self.ctx        = ctx
        self._vao       = None
        self._vbo_v     = None
        self._vbo_c     = None
        self._vert_count = 0
        self._current_vert = 0   # Bis wohin gezeichnet wird

    # ── Daten laden ───────────────────────────────────────────────────────────

    def load(self, result: ParseResult):
        if not result.moves:
            return

        verts = []
        colors = []
        # Mapping: Move-Index → erster Vertex-Index (für SimEngine)
        self._move_vertex_map = []

        for move in result.moves:
            col = _COLORS.get(move.type.split('_')[0]
                              if '_' in move.type else move.type,
                              (1, 1, 1))
            points = self._discretize_move(move)
            self._move_vertex_map.append(len(verts))

            for a, b in zip(points, points[1:]):
                verts += [self._swap(a), self._swap(b)]
                colors += [col, col]

        self._move_vertex_map.append(len(verts))  # Sentinel

        v = np.array(verts, dtype='f4')
        c = np.array(colors, dtype='f4')
        self._release()
        self._vbo_v = self.ctx.buffer(v.tobytes())
        self._vbo_c = self.ctx.buffer(c.tobytes())
        self._vert_count = len(v)
        self._current_vert = len(v)
        self._all_points = verts  # für Interpolation

    def _swap(self, p: np.ndarray) -> tuple:
        """Z-Up (G-Code) → Y-Up (OpenGL)"""
        return (float(p[0]), float(p[2]), float(p[1]))

    # ── Rendering ─────────────────────────────────────────────────────────────

    def build_vao(self, prog: moderngl.Program):
        """VAO mit bestehendem Shader-Programm aufbauen."""
        if self._vbo_v is None:
            return
        self._vao = self.ctx.vertex_array(
            prog,
            [(self._vbo_v, '3f', 'in_pos'),
             (self._vbo_c, '3f', 'in_col')],
        )

    def render(self, prog: moderngl.Program):
        """Wird von Viewport.paintGL() aufgerufen."""
        if self._vao is None and self._vbo_v is not None:
            self.build_vao(prog)
        if self._vao is None or self._current_vert == 0:
            return
        self._vao.render(moderngl.LINES,
                         vertices=self._current_vert)

    def set_progress(self, vertex_index: int):
        """SimEngine setzt wie weit gezeichnet wird (0 – vert_count)."""
        self._current_vert = max(0, min(vertex_index, self._vert_count))

    def reset(self):
        self._current_vert = 0

    def show_all(self):
        self._current_vert = self._vert_count

    def _release(self):
        for obj in (self._vao, self._vbo_v, self._vbo_c):
            if obj is not None:
                obj.release()
        self._vao = self._vbo_v = self._vbo_c = None

    def _discretize_move(self, move: Move) -> list[np.ndarray]:
        """
        Gibt Liste von Punkten zurück die diesen Move beschreiben.
        Linear/Rapid → [start, end]
        Bogen → viele Zwischenpunkte
        """
        if move.type in ('rapid', 'linear'):
            return [move.start, move.end]

        if move.arc_center is None:
            return [move.start, move.end]

        # Bogen in der XY-Ebene (G17 Standard)
        c = move.arc_center
        r_vec_start = move.start - c
        r_vec_end = move.end - c

        start_angle = np.arctan2(r_vec_start[1], r_vec_start[0])
        end_angle = np.arctan2(r_vec_end[1], r_vec_end[0])

        # Richtung
        if move.type == 'arc_cw':
            if end_angle >= start_angle:
                end_angle -= 2 * np.pi
        else:  # arc_ccw
            if end_angle <= start_angle:
                end_angle += 2 * np.pi

        # Anzahl Segmente: 1 pro Grad, mindestens 4
        angle_span = abs(end_angle - start_angle)
        n_segments = max(4, int(np.degrees(angle_span)))

        radius = np.linalg.norm(r_vec_start[:2])
        angles = np.linspace(start_angle, end_angle, n_segments + 1)

        # Z linear interpolieren
        z_vals = np.linspace(move.start[2], move.end[2], n_segments + 1)

        points = []
        for i, (a, z) in enumerate(zip(angles, z_vals)):
            p = np.array([
                c[0] + radius * np.cos(a),
                c[1] + radius * np.sin(a),
                z
            ], dtype='f4')
            points.append(p)

        return points

    def move_vertex_map(self, move_index: int) -> int:
        if not hasattr(self, '_move_vertex_map'):
            return 0
        return self._move_vertex_map[move_index]