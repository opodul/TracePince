from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Measurement:
    """One parsed measurement block from the instrument."""

    timestamp: datetime
    elapsed_time: str
    mode: str
    current: Optional[float] = None
    voltage: Optional[float] = None
    power: Optional[float] = None
    frequency: Optional[float] = None
    voltage_rms: Optional[float] = None
    voltage_peak_positive: Optional[float] = None
    voltage_peak_negative: Optional[float] = None
    crest_factor: Optional[float] = None
    voltage_dc: Optional[float] = None
    current_peak_positive: Optional[float] = None
    current_peak_negative: Optional[float] = None
    ripple: Optional[float] = None
    raw_block: str = ""