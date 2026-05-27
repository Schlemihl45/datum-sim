"""
Einstiegspunkt für:
  python -m datum_sim
  datum-sim                   (nach pip install)
  datum-sim datei.ngc         (Datei direkt öffnen)
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat


def _configure_opengl():
    """OpenGL 3.3 Core Profile – Pflicht für ModernGL."""
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setDepthBufferSize(24)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)


def main():
    _configure_opengl()
    app = QApplication(sys.argv)

    from datum_sim.ui.main_widget import DatumSimWidget
    win = DatumSimWidget()
    win.setWindowTitle("Datum Sim")
    win.resize(1280, 800)

    # Optionales Argument: datum-sim mein_programm.ngc
    if len(sys.argv) > 1:
        win.load_file(sys.argv[1])
    if len(sys.argv) > 1:
        win.load_file(sys.argv[1])
    else:
        # Test-G-Code wenn keine Datei übergeben
        win.load_gcode("""
    G21 G90
    G0 X0 Y0 Z5
    G1 Z-1 F100
    G1 X50 F300
    G1 Y50
    G1 X0
    G1 Y0
    G0 Z5
    G1 X25 Y25
    G1 Z-2 F100
    G1 X35
    G1 Y35
    G1 X15
    G1 Y15
    G1 X25
    G0 Z10
    """)

    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()