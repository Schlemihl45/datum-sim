"""
AppSettings – zentraler Einstellungs-Singleton via QSettings.

Zugriff von überall:
    from datum_sim.core.settings import AppSettings
    s = AppSettings.instance()
    s.zoom_speed        # lesen
    s.zoom_speed = 2.0  # schreiben + automatisch speichern
"""

from PySide6.QtCore import QSettings, QObject, Signal


class AppSettings(QObject):
    """
    Singleton. Einstellungen werden sofort auf Disk geschrieben.
    Signals feuern wenn sich ein Wert ändert → UI kann reagieren.
    """

    # Signals ──────────────────────────────────────────────────────────────────
    bg_color_changed        = Signal(str)

    zoom_speed_changed      = Signal(float)
    rotate_speed_changed    = Signal(float)
    pan_speed_changed       = Signal(float)

    invert_zoom_changed     = Signal(bool)
    invert_rotate_x_changed = Signal(bool)
    invert_rotate_y_changed = Signal(bool)
    invert_pan_x_changed    = Signal(bool)
    invert_pan_y_changed    = Signal(bool)

    # Singleton ────────────────────────────────────────────────────────────────
    _instance: "AppSettings | None" = None

    @classmethod
    def instance(cls) -> "AppSettings":
        if cls._instance is None:
            cls._instance = AppSettings()
        return cls._instance

    def __init__(self):
        super().__init__()
        self._qs = QSettings("DatumSim", "DatumSim")

    # ── Hintergrundfarbe ──────────────────────────────────────────────────────

    BG_COLORS = {
        "Dark (Standard)": "#1c1c1c",
        "Black":           "#000000",
        "Dark Grey":        "#2d2d2d",
        "Grey":        "#4a4a4a",
        "Dark Blue":        "#0d1b2a",
    }

    @property
    def bg_color(self) -> str:
        return self._qs.value("camera/bg_color", "#1c1c1c", type=str)

    @bg_color.setter
    def bg_color(self, v: str):
        self._qs.setValue("camera/bg_color", v)
        self.bg_color_changed.emit(v)

    # ── Geschwindigkeiten ─────────────────────────────────────────────────────

    @property
    def zoom_speed(self) -> float:
        return self._qs.value("camera/zoom_speed", 1.0, type=float)

    @zoom_speed.setter
    def zoom_speed(self, v: float):
        self._qs.setValue("camera/zoom_speed", v)
        self.zoom_speed_changed.emit(v)

    @property
    def rotate_speed(self) -> float:
        return self._qs.value("camera/rotate_speed", 1.0, type=float)

    @rotate_speed.setter
    def rotate_speed(self, v: float):
        self._qs.setValue("camera/rotate_speed", v)
        self.rotate_speed_changed.emit(v)

    @property
    def pan_speed(self) -> float:
        return self._qs.value("camera/pan_speed", 1.0, type=float)

    @pan_speed.setter
    def pan_speed(self, v: float):
        self._qs.setValue("camera/pan_speed", v)
        self.pan_speed_changed.emit(v)

    # ── Invertierung ──────────────────────────────────────────────────────────

    @property
    def invert_zoom(self) -> bool:
        return self._qs.value("camera/invert_zoom", False, type=bool)

    @invert_zoom.setter
    def invert_zoom(self, v: bool):
        self._qs.setValue("camera/invert_zoom", v)
        self.invert_zoom_changed.emit(v)

    @property
    def invert_rotate_x(self) -> bool:
        return self._qs.value("camera/invert_rotate_x", False, type=bool)

    @invert_rotate_x.setter
    def invert_rotate_x(self, v: bool):
        self._qs.setValue("camera/invert_rotate_x", v)
        self.invert_rotate_x_changed.emit(v)

    @property
    def invert_rotate_y(self) -> bool:
        return self._qs.value("camera/invert_rotate_y", False, type=bool)

    @invert_rotate_y.setter
    def invert_rotate_y(self, v: bool):
        self._qs.setValue("camera/invert_rotate_y", v)
        self.invert_rotate_y_changed.emit(v)

    @property
    def invert_pan_x(self) -> bool:
        return self._qs.value("camera/invert_pan_x", False, type=bool)

    @invert_pan_x.setter
    def invert_pan_x(self, v: bool):
        self._qs.setValue("camera/invert_pan_x", v)
        self.invert_pan_x_changed.emit(v)

    @property
    def invert_pan_y(self) -> bool:
        return self._qs.value("camera/invert_pan_y", False, type=bool)

    @invert_pan_y.setter
    def invert_pan_y(self, v: bool):
        self._qs.setValue("camera/invert_pan_y", v)
        self.invert_pan_y_changed.emit(v)

    # ── Simulation ────────────────────────────────────────────────────────────────

    sim_mode_changed = Signal(str)
    tool_display_changed = Signal(str)
    show_rapid_changed = Signal(bool)
    show_grid_changed = Signal(bool)

    voxel_enabled_changed = Signal(bool)
    voxel_keep_on_stop_changed = Signal(bool)

    @property
    def voxel_keep_on_stop(self) -> bool:
        return self._qs.value("voxel_keep_on_stop", False, type=bool)

    @voxel_keep_on_stop.setter
    def voxel_keep_on_stop(self, v: bool):
        self._qs.setValue("voxel_keep_on_stop", v)
        self.voxel_keep_on_stop_changed.emit(v)

    @property
    def voxel_enabled(self) -> bool:
        return self._qs.value("sim/voxel_enabled", False, type=bool)

    @voxel_enabled.setter
    def voxel_enabled(self, v: bool):
        self._qs.setValue("sim/voxel_enabled", v)
        self.voxel_enabled_changed.emit(v)

    @property
    def sim_mode(self) -> str:
        return self._qs.value("sim/mode", "toolpath_full", type=str)

    @sim_mode.setter
    def sim_mode(self, v: str):
        self._qs.setValue("sim/mode", v)
        self.sim_mode_changed.emit(v)
        print(v)

    @property
    def tool_display(self) -> str:
        return self._qs.value("sim/tool_display", "point", type=str)

    @tool_display.setter
    def tool_display(self, v: str):
        self._qs.setValue("sim/tool_display", v)
        self.tool_display_changed.emit(v)

    @property
    def show_rapid(self) -> bool:
        return self._qs.value("sim/show_rapid", True, type=bool)

    @show_rapid.setter
    def show_rapid(self, v: bool):
        self._qs.setValue("sim/show_rapid", v)
        self.show_rapid_changed.emit(v)

    @property
    def show_grid(self) -> bool:
        return self._qs.value("sim/show_grid", True, type=bool)

    @show_grid.setter
    def show_grid(self, v: bool):
        self._qs.setValue("sim/show_grid", v)
        self.show_grid_changed.emit(v)