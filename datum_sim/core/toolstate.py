from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import numpy as np

@dataclass
class ToolState:
    move_index:     int         # Which movement
    position:       np.ndarray  # XYZ relative to the datum
    t:              float
    feedrate:       float       # mm/min
    move_type:      str         # "rapid", "linear", "arc_cw", "arc_ccw"
    line_number:    int         # G-Code linealso n
