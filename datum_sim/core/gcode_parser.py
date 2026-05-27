"""
RS274/NGC Parser – G0, G1, G2, G3, G20/G21, G90/G91, G54-G59.
Gibt ParseResult mit Move-Liste und Bounding Box zurück.
"""

from __future__ import annotations
import re
import numpy as np
from datum_sim.core.toolpath import Move, ParseResult


class GCodeParser:

    def parse_file(self, path: str) -> ParseResult:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return self._parse_lines(lines)

    def parse_string(self, gcode: str) -> ParseResult:
        return self._parse_lines(gcode.splitlines())

    # ── Interner Parser ───────────────────────────────────────────────────────

    def _parse_lines(self, lines: list[str]) -> ParseResult:
        result   = ParseResult()
        pos      = np.zeros(3, dtype='f4')   # Aktuelle Position XYZ
        feedrate = 0.0
        motion   = 'rapid'                   # G0 = rapid, G1 = linear
        absolute = True                      # G90 = absolut, G91 = relativ
        unit_mm  = True                      # G21 = mm, G20 = inch

        for lineno, raw in enumerate(lines, 1):
            line = self._strip_comments(raw).strip().upper()
            if not line:
                continue

            words = self._tokenize(line)
            if not words:
                continue

            # ── Modal G-Codes ─────────────────────────────────────────────────
            for letter, value in words:
                if letter == 'G':
                    g = round(value, 1)
                    if g == 0:   motion   = 'rapid'
                    elif g == 1: motion   = 'linear'
                    elif g == 2: motion = 'arc_cw'
                    elif g == 3: motion = 'arc_ccw'
                    elif g == 20: unit_mm = False
                    elif g == 21: unit_mm = True
                    elif g == 90: absolute = True
                    elif g == 91: absolute = False
                elif letter == 'F':
                    feedrate = value

            # ── Zielposition extrahieren ──────────────────────────────────────
            offsets = {l: v for l, v in words if l in ('I', 'J', 'K')}
            axes = {l: v for l, v in words if l in ('X', 'Y', 'Z')}
            if not axes:
                continue

            scale = 1.0 if unit_mm else 25.4
            target = pos.copy()
            for axis, idx in (('X', 0), ('Y', 1), ('Z', 2)):
                if axis in axes:
                    v = axes[axis] * scale
                    target[idx] = v if absolute else pos[idx] + v

            # ── Move erzeugen ─────────────────────────────────────────────────
            if motion in ('arc_cw', 'arc_ccw') and offsets:
                center = pos.copy()
                center[0] += offsets.get('I', 0) * scale
                center[1] += offsets.get('J', 0) * scale
                center[2] += offsets.get('K', 0) * scale
                move = Move(
                    type=motion,
                    start=pos.copy(),
                    end=target.copy(),
                    feedrate=feedrate,
                    line_number=lineno,
                    arc_center=center,
                )
            else:
                move = Move(
                    type=motion if motion in ('rapid', 'linear') else 'linear',
                    start=pos.copy(),
                    end=target.copy(),
                    feedrate=feedrate,
                    line_number=lineno,
                )
            pos = target

        # ── Bounding Box ──────────────────────────────────────────────────────
        if result.moves:
            all_pts = np.array(
                [m.start for m in result.moves] +
                [m.end   for m in result.moves]
            )
            result.bbox_min = all_pts.min(axis=0)
            result.bbox_max = all_pts.max(axis=0)

        return result

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    def _strip_comments(self, line: str) -> str:
        """Entfernt (Kommentare) und ; bis Zeilenende."""
        line = re.sub(r'\(.*?\)', '', line)
        line = re.sub(r';.*$',    '', line)
        return line

    def _tokenize(self, line: str) -> list[tuple[str, float]]:
        """Zerlegt 'G0 X10.5 Y-3' → [('G',0), ('X',10.5), ('Y',-3)]"""
        words = []
        for m in re.finditer(r'([A-Z])\s*([-+]?\d*\.?\d+)', line):
            try:
                words.append((m.group(1), float(m.group(2))))
            except ValueError:
                pass
        return words