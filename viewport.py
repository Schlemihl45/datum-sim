"""
Viewport – QOpenGLWidget mit ModernGL-Context.
"""

import numpy as np
import moderngl
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QEvent, QPointF
from PySide6.QtGui import QEventPoint

from datum_sim.core.camera import ArcballCamera
from datum_sim.core.settings import AppSettings


_VERT = """
#version 330 core
in vec3 in_pos;
in vec3 in_col;
out vec3 v_col;
uniform mat4 u_mvp;
void main() {
    gl_Position = u_mvp * vec4(in_pos, 1.0);
    v_col = in_col;
}
"""

_FRAG = """
#version 330 core
in vec3 v_col;
out vec4 f_col;
void main() {
    f_col = vec4(v_col, 1.0);
}
"""


def _build_axes_grid(axis_len=60.0, grid_range=100, grid_step=10):
    verts, cols = [], []
    for end, color in [
        ([axis_len, 0, 0], [1.0, 0.2, 0.2]),
        ([0, axis_len, 0], [0.2, 1.0, 0.2]),
        ([0, 0, axis_len], [0.4, 0.6, 1.0]),
    ]:
        verts += [[0, 0, 0], end]
        cols  += [color, color]

    gc = [0.22, 0.22, 0.22]
    for i in range(-grid_range, grid_range + 1, grid_step):
        verts += [[i, 0, -grid_range], [i, 0, grid_range]]
        cols  += [gc, gc]
        verts += [[-grid_range, 0, i], [grid_range, 0, i]]
        cols  += [gc, gc]

    return np.array(verts, dtype='f4'), np.array(cols, dtype='f4')


def _dist(p1, p2):
    d = p1 - p2
    return (d.x()**2 + d.y()**2) ** 0.5


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))


class Viewport(QOpenGLWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera = ArcballCamera()
        self.toolpath_renderer = None
        self.voxel_renderer    = None
        self._mouse_last = QPointF()
        self._mouse_btn  = None

        self._rotate_accumulated = QPointF(0, 0)
        self.ROTATE_THRESHOLD = 16

        self._multi_touch_active = False

        self._bg = _hex_to_rgb(AppSettings.instance().bg_color)

        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setMinimumSize(400, 300)

        # Hintergrundfarbe live aktualisieren wenn Einstellung sich ändert
        AppSettings.instance().bg_color_changed.connect(self._on_bg_changed)

    def _on_bg_changed(self, hex_color: str):
        self._bg = _hex_to_rgb(hex_color)
        self.update()

    # ── OpenGL ────────────────────────────────────────────────────────────────

    def initializeGL(self):
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self._prog = self.ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG)
        verts, colors = _build_axes_grid()
        vbo_v = self.ctx.buffer(verts.tobytes())
        vbo_c = self.ctx.buffer(colors.tobytes())
        self._scene_vao = self.ctx.vertex_array(
            self._prog,
            [(vbo_v, '3f', 'in_pos'), (vbo_c, '3f', 'in_col')],
        )
        self._scene_vert_count = len(verts)

    def resizeGL(self, w, h):
        if hasattr(self, 'ctx'):
            self.ctx.viewport = (0, 0, w, h)

    def paintGL(self):
        fbo = self.ctx.detect_framebuffer(self.defaultFramebufferObject())
        fbo.use()
        fbo.clear(*self._bg, 1.0)
        aspect = self.width() / max(self.height(), 1)
        self._prog['u_mvp'].write(self.camera.mvp(aspect).T.tobytes())
        self._scene_vao.render(moderngl.LINES, vertices=self._scene_vert_count)
        if self.toolpath_renderer is not None:
            self.toolpath_renderer.render(self._prog)
        if self.voxel_renderer is not None:
            self.voxel_renderer.render(self._prog)

    # ── Maus ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.source() != Qt.MouseEventNotSynthesized:
            return
        self._mouse_last = e.position()
        self._mouse_btn = e.button()

    def mouseReleaseEvent(self, e):
        if e.source() != Qt.MouseEventNotSynthesized:
            return
        self._mouse_btn = None

    def mouseMoveEvent(self, e):
        if e.source() != Qt.MouseEventNotSynthesized:
            return
        if self._mouse_btn is None:
            return
        s = AppSettings.instance()
        d = e.position() - self._mouse_last
        self._mouse_last = e.position()
        if self._mouse_btn == Qt.LeftButton:
            sx = -1 if s.invert_rotate_x else 1
            sy = -1 if s.invert_rotate_y else 1
            self.camera.rotate(d.x() * s.rotate_speed * sx,
                               d.y() * s.rotate_speed * sy)
        elif self._mouse_btn == Qt.MiddleButton:
            sx = -1 if s.invert_pan_x else 1
            sy = -1 if s.invert_pan_y else 1
            self.camera.pan(d.x() * s.pan_speed * sx,
                            d.y() * s.pan_speed * sy)
        self.update()

    def wheelEvent(self, e):
        s = AppSettings.instance()
        inv = -1 if s.invert_zoom else 1
        self.camera.zoom(e.angleDelta().y() * 0.5 * s.zoom_speed * inv)
        self.update()

    # ── Touch ─────────────────────────────────────────────────────────────────

    def event(self, e):
        t = e.type()
        if t not in (QEvent.TouchBegin, QEvent.TouchUpdate, QEvent.TouchEnd):
            return super().event(e)

        all_pts = e.points()

        fingers_down = [p for p in all_pts
                        if p.state() != QEventPoint.State.Released]

        if len(fingers_down) >= 2:
            self._multi_touch_active = True

        if len(fingers_down) == 0:
            self._multi_touch_active = False
            self._rotate_accumulated = QPointF(0, 0)

        active = [p for p in all_pts
                  if p.state() in (QEventPoint.State.Pressed,
                                   QEventPoint.State.Updated,
                                   QEventPoint.State.Stationary)]

        s = AppSettings.instance()

        if len(active) == 1 and len(fingers_down) == 1 and not self._multi_touch_active:
            d = active[0].position() - active[0].lastPosition()
            self._rotate_accumulated += d

            dist = (self._rotate_accumulated.x() ** 2 +
                    self._rotate_accumulated.y() ** 2) ** 0.5

            if dist >= self.ROTATE_THRESHOLD:
                sx = -1 if s.invert_rotate_x else 1
                sy = -1 if s.invert_rotate_y else 1
                self.camera.rotate(d.x() * s.rotate_speed * sx,
                                   d.y() * s.rotate_speed * sy)

        elif len(active) >= 2:
            p1, p2 = active[0], active[1]
            self._rotate_accumulated = QPointF(0, 0)

            cur_dist  = _dist(p1.position(),     p2.position())
            last_dist = _dist(p1.lastPosition(), p2.lastPosition())
            inv = -1 if s.invert_zoom else 1
            self.camera.zoom((cur_dist - last_dist) * 0.5 * s.zoom_speed * inv)

            cur_c  = (p1.position()     + p2.position())     / 2
            last_c = (p1.lastPosition() + p2.lastPosition()) / 2
            d = cur_c - last_c
            sx = -1 if s.invert_pan_x else 1
            sy = -1 if s.invert_pan_y else 1
            self.camera.pan(d.x() * s.pan_speed * sx,
                            d.y() * s.pan_speed * sy)

        self.update()
        return True