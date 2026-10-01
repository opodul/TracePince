import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class SerialLogger:
    """Write each received session to a timestamped binary log file."""

    _block_start = re.compile(rb"^\s*ELAPSED\s+TIME\s*:", re.IGNORECASE | re.M)

    def __init__(self, directory: Path = Path("logs")) -> None:
        self.directory = Path(directory)
        self._file = None
        self._pending = bytearray()
        self.path: Optional[Path] = None
        self._recording = False

    def start(self) -> Path:
        self.close()
        self.directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        self.path = self.directory / f"serial_{stamp}.log"
        self._pending.clear()
        self._recording = True
        return self.path

    def write(self, data: bytes) -> None:
        if not self._recording:
            self.start()
        if self._file is None:
            self._pending.extend(data)
            if len(self._block_start.findall(self._pending)) > 1:
                if self.path is None:
                    return
                self._file = self.path.open("ab")
                self._file.write(self._pending)
                self._file.flush()
                self._pending.clear()
            return
        self._file.write(data)
        self._file.flush()

    def copy_current(self, destination: Path) -> Path:
        if self.path is None or not self.path.is_file():
            raise FileNotFoundError("No active measurement file to save.")
        destination = Path(destination)
        if destination.resolve() == self.path.resolve():
            raise ValueError("Destination must be different from the active measurement file.")
        if self._file is not None:
            self._file.flush()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.path, destination)
        return destination

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
        self._pending.clear()
        self._recording = False