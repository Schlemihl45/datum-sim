# Datum Sim

Code simulation and planning for LinuxCNC. Based on PySide6.

## Installation

```bash
pip install -e .
```

## Starting the standalone

```bash
datum-sim                        # leeres Fenster
datum-sim mein_programm.ngc     # Datei direkt laden
python -m datum_sim              # alternativ
```

## Integration in your own project

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

## Dependencies

- PySide6 >= 6.6
- moderngl >= 5.10
- numpy >= 1.26
