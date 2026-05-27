from __future__ import annotations
import numpy as np
import moderngl
from datum_sim.core.toolpath import ParseResult, Move

_COLORS = {
    'rapid':   (0.9, 0.8, 0.1),
    'linear':  (0.2, 0.9, 0.3),
    'arc_cw':  (0.2, 0.5, 1.0),
    'arc_ccw': (0.2, 0.5, 1.0),
}


class ToolpathRenderer:

    def __init__(self, ctx: moderngl.Context):
        self.ctx             = ctx
        self._vao            = None
        self._vbo_v          = None
        self._vbo_c          = None
        self._vert_count     = 0
        self._current_vert   = 0
        self._move_vert_map  = []   # move_index → erster Vertex-Index

    # ── Daten laden ───────────────────────────────────────────────────────────

    def load(self, result: ParseResult):
        if not result.moves:
            return

        verts  = []
        colors = []
        self._move_vert_map = []

        for move in result.moves:
            self._move_vert_map.append(len(verts))
            col    = _COLORS.get(move.type, (1, 1, 1))
            points = self._discretize(move)

            for a, b in zip(points, points[1:]):
                verts  += [self._to_gl(a), self._to_gl(b)]
                colors += [col, col]

        self._move_vert_map.append(len(verts))  # Sentinel

        v = np.array(verts,  dtype='f4')
        c = np.array(colors, dtype='f4')

        self._release()
        self._vbo_v        = self.ctx.buffer(v.tobytes())
        self._vbo_c        = self.ctx.buffer(c.tobytes())
        self._vert_count   = len(v)
        self._current_vert = len(v)   # Alles zeigen bis SimEngine steuert

    def move_vertex_map(self, move_index: int) -> int:
        if not self._move_vert_map:
            return 0
        move_index = max(0, min(move_index, len(self._move_vert_map) - 1))
        return self._move_vert_map[move_index]

    # ── Diskretisierung ───────────────────────────────────────────────────────

    def _discretize(self, move: Move) -> list[np.ndarray]:
        """Alle Moves in Segmente aufteilen für flüssige Animation."""

        if move.type in ('arc_cw', 'arc_ccw') and move.arc_center is not None:
            # Bögen wie bisher
            c = move.arc_center
            r_start = move.start[:2] - c[:2]
            r_end = move.end[:2] - c[:2]
            start_angle = np.arctan2(r_start[1], r_start[0])
            end_angle = np.arctan2(r_end[1], r_end[0])

            if move.type == 'arc_cw':
                if end_angle >= start_angle:
                    end_angle -= 2 * np.pi
            else:
                if end_angle <= start_angle:
                    end_angle += 2 * np.pi

            span = abs(end_angle - start_angle)
            n = max(4, int(np.degrees(span)))
            radius = float(np.linalg.norm(r_start))
            angles = np.linspace(start_angle, end_angle, n + 1)
            z_vals = np.linspace(move.start[2], move.end[2], n + 1)

            return [
                np.array([c[0] + radius * np.cos(a),
                          c[1] + radius * np.sin(a),
                          z], dtype='f4')
                for a, z in zip(angles, z_vals)
            ]

        else:
            # Linear und Rapid: in Segmente je 1mm aufteilen
            dist = float(np.linalg.norm(move.end - move.start))
            n = max(1, int(dist))  # 1 Segment pro mm
            pts = []
            for i in range(n + 1):
                t = i / n
                pts.append(move.start + t * (move.end - move.start))
            return pts

    def _to_gl(self, p: np.ndarray) -> tuple:
        """Z-Up (G-Code) → Y-Up (OpenGL)"""
        return (float(p[0]), float(p[2]), float(p[1]))

    # ── Rendering ─────────────────────────────────────────────────────────────

    def build_vao(self, prog: moderngl.Program):
        if self._vbo_v is None:
            return
        if self._vao is not None:
            self._vao.release()
        self._vao = self.ctx.vertex_array(
            prog,
            [(self._vbo_v, '3f', 'in_pos'),
             (self._vbo_c, '3f', 'in_col')],
        )

    def render(self, prog: moderngl.Program):
        if self._vao is None and self._vbo_v is not None:
            self.build_vao(prog)
        if self._vao is None or self._current_vert == 0:
            return
        self._vao.render(moderngl.LINES, vertices=self._current_vert)

    def set_progress(self, vertex_index: int):
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