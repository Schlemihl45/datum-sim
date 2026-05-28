from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import numpy as np

@dataclass
class Move:
    type:        Literal['rapid', 'linear', 'arc_cw', 'arc_ccw']
    start:       np.ndarray        # XYZ in mm
    end:         np.ndarray        # XYZ in mm
    feedrate:    float             # mm/min, 0 = Eilgang
    line_number: int               # Original G-Code Zeile
    arc_center:  np.ndarray | None = None  # Nur für G2/G3


@dataclass
class ParseResult:
    moves:    list[Move] = field(default_factory=list)
    warnings: list[str]  = field(default_factory=list)
    bbox_min: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype='f4'))
    bbox_max: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype='f4'))