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

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None