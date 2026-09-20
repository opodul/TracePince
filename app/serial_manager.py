import threading
from dataclasses import dataclass
from typing import Callable, Optional

import serial
from serial.tools import list_ports


@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    bytesize: int = serial.EIGHTBITS
    parity: str = serial.PARITY_NONE
    stopbits: float = serial.STOPBITS_ONE
    rtscts: bool = False


class SerialManager:
    """Read a serial port on a daemon thread and report received bytes."""

    def __init__(self, on_data: Callable[[bytes], None], on_error: Callable[[Exception], None]) -> None:
        self.on_data = on_data
        self.on_error = on_error
        self._serial: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    @staticmethod
    def list_ports() -> list[str]:
        return [port.device for port in list_ports.comports()]

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect(self, config: SerialConfig) -> None:
        self.disconnect()
        self._serial = serial.Serial(
            port=config.port,
            baudrate=config.baudrate,
            bytesize=config.bytesize,
            parity=config.parity,
            stopbits=config.stopbits,
            rtscts=config.rtscts,
            timeout=0.25,
        )
        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, name="serial-reader", daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        self._stop.set()
        if self._serial is not None:
            self._serial.close()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._serial = None

    def _read_loop(self) -> None:
        while not self._stop.is_set() and self._serial is not None:
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
                if data:
                    self.on_data(data)
            except (OSError, serial.SerialException) as error:
                if not self._stop.is_set():
                    self.on_error(error)
                break