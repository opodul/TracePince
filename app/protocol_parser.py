"""Parser for Chauvin Arnoux Harmonic & Power Meter text frames."""

import re
from datetime import datetime
from typing import Dict, List, Optional

from .measurement import Measurement


class ProtocolParser:
    """Incrementally parse newline-delimited measurement blocks."""

    _elapsed_re = re.compile(r"^\s*ELAPSED\s+TIME\s*:\s*(\d{1,2}:\d{2})\s*$", re.I)
    _mode_re = re.compile(r"^\s*\*\s*([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*)\b", re.I)
    _value_re = r"[+-]?\s*(?:\d+(?:\.\d*)?|\.\d+)"
    _line_value_re = re.compile(r"^\s*(.*?)\s*=\s*(" + _value_re + r")\s*$", re.M)
    _ignored_modes = {"NAME", "TIME", "SCAN"}

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
            if mode_match and mode_match.group(1).upper() not in self._ignored_modes:
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
            values=values,
            **self._known_values(values),
        )

    @staticmethod
    def _normalize_label(label: str) -> str:
        label = " ".join(label.split())
        match = re.match(r"^(.*?)\s*\(\s*([^()]*)\s*\)$", label)
        if match:
            return f"{match.group(1).strip()} ({match.group(2).strip()})"
        return label.strip()

    def _parse_values(self, block: str) -> Dict[str, float]:
        values: Dict[str, float] = {}
        for match in self._line_value_re.finditer(block):
            label = self._normalize_label(match.group(1))
            if label:
                values[label] = float(match.group(2).replace(" ", ""))
        return values

    @staticmethod
    def _known_values(values: Dict[str, float]) -> dict:
        def value(pattern: str) -> Optional[float]:
            return values.get(pattern)

        return {
            "voltage_rms": value("RMS (V)"), "voltage": value("RMS (V)") or value("V (V)"),
            "voltage_peak_positive": value("Peak+ (V)"), "voltage_peak_negative": value("Peak- (V)"),
            "crest_factor": value("CF"), "voltage_dc": value("DC (V)"),
            "current": value("DC (A)") or value("A (A)"),
            "current_peak_positive": value("Peak+ (A)"), "current_peak_negative": value("Peak- (A)"),
            "ripple": value("Ripple (%)"), "power": value("P (W)"),
            "frequency": value("Freq (Hz)"),
        }


def parse_text(text: str) -> List[Measurement]:
    """Parse all complete measurement blocks in a text sample."""
    parser = ProtocolParser()
    measurements = parser.feed(text)
    final = parser.flush()
    if final is not None:
        measurements.append(final)
    return measurements