import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class SerialLogger:
    """Write each received session to a timestamped binary log file."""

    def __init__(self, directory: Path = Path("logs")) -> None:
        self.directory = Path(directory)
        self._file = None
        self.path: Optional[Path] = None

    def start(self) -> Path:
        self.close()
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        self.path = self.directory / f"serial_{stamp}.log"
        self._file = self.path.open("ab")
        return self.path

    def write(self, data: bytes) -> None:
        if self._file is None:
            self.start()
        self._file.write(data)
        self._file.flush()

    def copy_current(self, destination: Path) -> Path:
        if self.path is None:
            raise FileNotFoundError("No active log file to save.")
        destination = Path(destination)
        if destination.resolve() == self.path.resolve():
            raise ValueError("Destination must be different from the active log file.")
        if self._file is not None:
            self._file.flush()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.path, destination)
        return destination

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None