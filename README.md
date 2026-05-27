# Datum Sim

G-Code Abtrags- und Werkzeugwegsimulation für LinuxCNC.  
Als eigenständiges Widget in beliebige PySide6-Projekte integrierbar.

## Installation

```bash
pip install -e .
```

## Standalone starten

```bash
datum-sim                        # leeres Fenster
datum-sim mein_programm.ngc     # Datei direkt laden
python -m datum_sim              # alternativ
```

## Integration in eigenes Projekt

```python
from datum_sim import DatumSimWidget

widget = DatumSimWidget()
widget.load_file("/pfad/zu/programm.ngc")
widget.play()

# Signals
widget.line_changed.connect(meine_funktion)
widget.position_changed.connect(lambda x, y, z: ...)
widget.simulation_ended.connect(aufraumen)
```

## Abhängigkeiten

- PySide6 >= 6.6
- moderngl >= 5.10
- numpy >= 1.26