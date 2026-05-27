"""
ArcballCamera – Orbit-Kamera um einen Fokuspunkt.

Steuerung:
  Maus links   → Drehen
  Maus mitte   → Pan
  Mausrad      → Zoom
  1 Finger     → Drehen
  2 Finger     → Pinch-Zoom + Pan
"""

import numpy as np


# ── Mathe-Hilfsfunktionen ─────────────────────────────────────────────────────

def _perspective(fov_deg: float, aspect: float,
                 near: float, far: float) -> np.ndarray:
    f = 1.0 / np.tan(np.radians(fov_deg) / 2.0)
    return np.array([
        [f / aspect, 0,  0,                           0],
        [0,          f,  0,                           0],
        [0,          0,  (far + near) / (near - far), (2 * far * near) / (near - far)],
        [0,          0, -1,                           0],
    ], dtype='f4')


def _look_at(eye: np.ndarray, target: np.ndarray,
             up: np.ndarray) -> np.ndarray:
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return np.array([
        [ r[0],  r[1],  r[2], -np.dot(r, eye)],
        [ u[0],  u[1],  u[2], -np.dot(u, eye)],
        [-f[0], -f[1], -f[2],  np.dot(f, eye)],
        [    0,      0,     0,               1],
    ], dtype='f4')


# ── Kamera ────────────────────────────────────────────────────────────────────

class ArcballCamera:

    def __init__(self):
        self.target   = np.zeros(3, dtype='f4')
        self.distance = 300.0
        self.yaw      = 45.0    # Grad
        self.pitch    = 30.0    # Grad, positiv = von oben
        self.fov      = 45.0

    # ── Eingaben ──────────────────────────────────────────────────────────────

    def rotate(self, dx: float, dy: float):
        """dx/dy in Pixel → Kamera dreht um Fokuspunkt."""
        self.yaw  -= dx * 0.4
        self.pitch = float(np.clip(self.pitch + dy * 0.4, -89.0, 89.0))

    def zoom(self, delta: float):
        """delta > 0 = heranzoomen."""
        self.distance = max(5.0, self.distance - delta * 0.8)

    def pan(self, dx: float, dy: float):
        """Fokuspunkt in Kameraebene verschieben."""
        scale = self.distance * 0.0012
        self.target -= (self._right() * dx + self._up_world() * dy) * scale

    # ── Matrizen ──────────────────────────────────────────────────────────────

    def eye(self) -> np.ndarray:
        yr = np.radians(self.yaw)
        pr = np.radians(self.pitch)
        offset = np.array([
            np.cos(pr) * np.sin(yr),
            np.sin(pr),
            np.cos(pr) * np.cos(yr),
        ], dtype='f4') * self.distance
        return self.target + offset

    def view_matrix(self) -> np.ndarray:
        return _look_at(self.eye(), self.target,
                        np.array([0, 1, 0], dtype='f4'))

    def proj_matrix(self, aspect: float) -> np.ndarray:
        return _perspective(self.fov, aspect, 0.1, 10_000.0)

    def mvp(self, aspect: float) -> np.ndarray:
        """Model-View-Projection als 4×4 float32."""
        return self.proj_matrix(aspect) @ self.view_matrix()

    # ── Hilfsvektoren ─────────────────────────────────────────────────────────

    def _right(self) -> np.ndarray:
        yr = np.radians(self.yaw)
        return np.array([np.cos(yr), 0.0, -np.sin(yr)], dtype='f4')

    def _up_world(self) -> np.ndarray:
        e  = self.eye() - self.target
        r  = self._right()
        up = np.cross(r, e)
        n  = np.linalg.norm(up)
        return up / n if n > 1e-6 else np.array([0, 1, 0], dtype='f4')

    # ── Utilities ─────────────────────────────────────────────────────────────

    def focus_on(self, center: np.ndarray, size: float):
        """Kamera auf Bounding-Box-Mitte ausrichten."""
        self.target   = center.astype('f4')
        self.distance = max(size * 2.0, 50.0)