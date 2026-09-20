from typing import List

from .measurement import Measurement


class DataManager:
    def __init__(self, max_measurements: int = 5000) -> None:
        self.max_measurements = max_measurements
        self.measurements: List[Measurement] = []

    def add(self, measurement: Measurement) -> None:
        self.measurements.append(measurement)
        if len(self.measurements) > self.max_measurements:
            del self.measurements[: len(self.measurements) - self.max_measurements]

    def clear(self) -> None:
        self.measurements.clear()