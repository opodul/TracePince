"""Parser for Chauvin Arnoux Harmonic & Power Meter text frames."""

import re
from datetime import datetime
from typing import List, Optional

from .measurement import Measurement


class ProtocolParser:
    """Incrementally parse newline-delimited measurement blocks."""

    _elapsed_re = re.compile(r"^\s*ELAPSED\s+TIME\s*:\s*(\d{1,2}:\d{2})\s*$", re.I)
    _mode_re = re.compile(r"^\s*\*\s*(VOLTAGE|CURRENT|POWER-1PH)\b", re.I)
    _value_re = r"[+-]?\s*(?:\d+(?:\.\d*)?|\.\d+)"

    def __init__(self) -> None:
        self._mode = "UNKNOWN"
        self._current_lines: List[str] = []
        self._current_elapsed: Optional[str] = None
        self._line_buffer = ""

    @property
    def mode(self) -> str:
        return self._mode

    def feed(self, data: str) -> List[Measurement]:
        """Consume text and return only complete blocks found in ``data``."""
        measurements: List[Measurement] = []
        self._line_buffer += data
        lines = self._line_buffer.splitlines(keepends=True)
        self._line_buffer = ""
        if lines and not lines[-1].endswith(("\n", "\r")):
            self._line_buffer = lines.pop()
        for line in lines:
            elapsed_match = self._elapsed_re.match(line.rstrip("\r\n"))
            if elapsed_match:
                measurement = self._finish_block()
                if measurement is not None:
                    measurements.append(measurement)
                self._current_elapsed = elapsed_match.group(1)
                self._current_lines = [line]
                continue

            mode_match = self._mode_re.match(line.rstrip("\r\n"))
            if mode_match:
                self._mode = mode_match.group(1).upper()

            if self._current_elapsed is not None:
                self._current_lines.append(line)
        return measurements

    def flush(self) -> Optional[Measurement]:
        """Finish the currently buffered block, if it has one."""
        return self._finish_block()

    def _finish_block(self) -> Optional[Measurement]:
        if self._current_elapsed is None:
            return None

        raw_block = "".join(self._current_lines)
        elapsed_time = self._current_elapsed
        self._current_elapsed = None
        self._current_lines = []
        values = self._parse_values(raw_block)
        return Measurement(
            timestamp=datetime.now(),
            elapsed_time=elapsed_time,
            mode=self._mode,
            raw_block=raw_block,
            **values,
        )

    def _parse_values(self, block: str) -> dict:
        def value(pattern: str) -> Optional[float]:
            match = re.search(pattern, block, re.I | re.M)
            if not match:
                return None
            return float(match.group(1).replace(" ", ""))

        if self._mode == "VOLTAGE":
            return {
                "voltage_rms": value(r"^\s*RMS\s*\(\s*V\s*\)\s*=\s*(" + self._value_re + r")"),
                "voltage": value(r"^\s*RMS\s*\(\s*V\s*\)\s*=\s*(" + self._value_re + r")"),
                "voltage_peak_positive": value(r"^\s*Peak\+\s*\(\s*V\s*\)\s*=\s*(" + self._value_re + r")"),
                "voltage_peak_negative": value(r"^\s*Peak-\s*\(\s*V\s*\)\s*=\s*(" + self._value_re + r")"),
                "crest_factor": value(r"^\s*CF\s*=\s*(" + self._value_re + r")"),
                "voltage_dc": value(r"^\s*DC\s*\(\s*V\s*\)\s*=\s*(" + self._value_re + r")"),
                "frequency": value(r"^\s*Freq\s*\(\s*Hz\s*\)\s*=\s*(" + self._value_re + r")"),
            }
        if self._mode == "CURRENT":
            return {
                "current": value(r"^\s*DC\s*\(\s*A\s*\)\s*=\s*(" + self._value_re + r")"),
                "current_peak_positive": value(r"^\s*Peak\+\s*\(\s*A\s*\)\s*=\s*(" + self._value_re + r")"),
                "current_peak_negative": value(r"^\s*Peak-\s*\(\s*A\s*\)\s*=\s*(" + self._value_re + r")"),
                "ripple": value(r"^\s*Ripple\s*\(\s*%\s*\)\s*=\s*(" + self._value_re + r")"),
                "frequency": value(r"^\s*Freq\s*\(\s*Hz\s*\)\s*=\s*(" + self._value_re + r")"),
            }
        if self._mode == "POWER-1PH":
            return {
                "power": value(r"^\s*P\s*\(\s*W\s*\)\s*=\s*(" + self._value_re + r")"),
                "current": value(r"^\s*A\s*\(\s*A\s*\)\s*=\s*(" + self._value_re + r")"),
                "voltage": value(r"^\s*V\s*\(\s*V\s*\)\s*=\s*(" + self._value_re + r")"),
                "frequency": value(r"^\s*Freq\s*\(\s*Hz\s*\)\s*=\s*(" + self._value_re + r")"),
            }
        return {}


def parse_text(text: str) -> List[Measurement]:
    """Parse all complete measurement blocks in a text sample."""
    parser = ProtocolParser()
    measurements = parser.feed(text)
    final = parser.flush()
    if final is not None:
        measurements.append(final)
    return measurements