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

    def _parse_lines(self, lines: list[str]) -> ParseResult:
        result   = ParseResult()
        pos      = np.zeros(3, dtype='f4')
        feedrate = 0.0
        motion   = 'rapid'
        absolute = True
        unit_mm  = True

        for lineno, raw in enumerate(lines, 1):
            line = self._strip_comments(raw).strip().upper()
            if not line:
                continue

            words = self._tokenize(line)
            if not words:
                continue

            # Modal G-Codes
            for letter, value in words:
                if letter == 'G':
                    g = round(value, 1)
                    if   g == 0:  motion   = 'rapid'
                    elif g == 1:  motion   = 'linear'
                    elif g == 2:  motion   = 'arc_cw'
                    elif g == 3:  motion   = 'arc_ccw'
                    elif g == 20: unit_mm  = False
                    elif g == 21: unit_mm  = True
                    elif g == 90: absolute = True
                    elif g == 91: absolute = False
                elif letter == 'F':
                    feedrate = value

            scale   = 1.0 if unit_mm else 25.4
            axes    = {l: v for l, v in words if l in ('X','Y','Z')}
            offsets = {l: v for l, v in words if l in ('I','J','K')}

            if not axes and not offsets:
                continue

            # Zielposition
            target = pos.copy()
            for axis, idx in (('X',0),('Y',1),('Z',2)):
                if axis in axes:
                    v = axes[axis] * scale
                    target[idx] = v if absolute else pos[idx] + v

            if np.allclose(pos, target):
                continue

            # Bogenmittelpunkt
            arc_center = None
            if motion in ('arc_cw', 'arc_ccw') and offsets:
                arc_center = pos.copy()
                arc_center[0] += offsets.get('I', 0) * scale
                arc_center[1] += offsets.get('J', 0) * scale
                arc_center[2] += offsets.get('K', 0) * scale

            result.moves.append(Move(
                type        = motion,
                start       = pos.copy(),
                end         = target.copy(),
                feedrate    = feedrate,
                line_number = lineno,
                arc_center  = arc_center,
            ))

            pos = target

        # Bounding Box
        if result.moves:
            pts = np.array([m.start for m in result.moves] +
                           [m.end   for m in result.moves])
            result.bbox_min = pts.min(axis=0)
            result.bbox_max = pts.max(axis=0)

        return result

    def _strip_comments(self, line: str) -> str:
        line = re.sub(r'\(.*?\)', '', line)
        line = re.sub(r';.*$',    '', line)
        return line

    def _tokenize(self, line: str) -> list[tuple[str, float]]:
        words = []
        for m in re.finditer(r'([A-Z])\s*([-+]?\d*\.?\d+)', line):
            try:
                words.append((m.group(1), float(m.group(2))))
            except ValueError:
                pass
        return words