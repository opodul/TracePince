import queue
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from .data_manager import DataManager
from .plot_manager import PlotManager
from .protocol_parser import ProtocolParser
from .serial_logger import SerialLogger
from .serial_manager import SerialConfig, SerialManager


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Chauvin Arnoux Serial Monitor")
        self.root.geometry("1200x780")
        self.events = queue.Queue()
        self.parser = ProtocolParser()
        self.data = DataManager()
        self.logger = SerialLogger(Path("logs"))
        self.serial = SerialManager(self._received, self._serial_error)
        self._build()
        self._poll_events()
        self.refresh_ports()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build(self) -> None:
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill="x")
        self.port = ttk.Combobox(controls, width=18)
        self.port.grid(row=0, column=0, padx=3)
        ttk.Button(controls, text="Refresh", command=self.refresh_ports).grid(row=0, column=1, padx=3)
        self.baud = ttk.Combobox(controls, values=("1200", "2400", "4800", "9600", "19200", "38400", "115200"), width=8)
        self.baud.set("9600")
        self.baud.grid(row=0, column=2, padx=3)
        self.parity = ttk.Combobox(controls, values=("None", "Even", "Odd", "Mark", "Space"), width=8)
        self.parity.set("None")
        self.parity.grid(row=0, column=3, padx=3)
        self.bits = ttk.Combobox(controls, values=("5", "6", "7", "8"), width=4)
        self.bits.set("8")
        self.bits.grid(row=0, column=4, padx=3)
        self.stopbits = ttk.Combobox(controls, values=("1", "1.5", "2"), width=4)
        self.stopbits.set("1")
        self.stopbits.grid(row=0, column=5, padx=3)
        self.rtscts = tk.BooleanVar(value=False)
        ttk.Checkbutton(controls, text="RTS/CTS", variable=self.rtscts).grid(row=0, column=6, padx=3)
        ttk.Button(controls, text="Connect", command=self.connect).grid(row=0, column=7, padx=3)
        ttk.Button(controls, text="Disconnect", command=self.disconnect).grid(row=0, column=8, padx=3)
        self.status = ttk.Label(controls, text="Disconnected")
        self.status.grid(row=0, column=9, padx=12)

        body = ttk.PanedWindow(self.root, orient="vertical")
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        top = ttk.Frame(body)
        bottom = ttk.Frame(body)
        body.add(top, weight=3)
        body.add(bottom, weight=2)
        columns = ("timestamp", "mode", "elapsed", "current", "voltage", "power", "frequency")
        self.table = ttk.Treeview(top, columns=columns, show="headings", height=10)
        headings = {"timestamp": "Timestamp", "mode": "Mode", "elapsed": "Elapsed", "current": "Current (A)", "voltage": "Voltage (V)", "power": "Power (W)", "frequency": "Frequency (Hz)"}
        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=115, anchor="center")
        self.table.pack(fill="both", expand=True)
        plot_frame = ttk.Frame(top)
        plot_frame.pack(fill="both", expand=True)
        self.plot = PlotManager(plot_frame)

        console_controls = ttk.Frame(bottom)
        console_controls.pack(fill="x")
        ttk.Button(console_controls, text="Clear console", command=lambda: self.console.delete("1.0", "end")).pack(side="right")
        self.power_visible = tk.BooleanVar(value=True)
        ttk.Checkbutton(console_controls, text="Show power plot", variable=self.power_visible, command=self._toggle_power).pack(side="right", padx=8)
        self.console = tk.Text(bottom, height=8, wrap="none", state="disabled")
        self.console.pack(fill="both", expand=True)

    def refresh_ports(self) -> None:
        ports = self.serial.list_ports()
        self.port["values"] = ports
        if ports and not self.port.get():
            self.port.set(ports[0])

    def connect(self) -> None:
        try:
            config = SerialConfig(self.port.get(), int(self.baud.get()), int(self.bits.get()), {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}[self.parity.get()], float(self.stopbits.get()), self.rtscts.get())
            self.parser = ProtocolParser()
            self.data.clear()
            path = self.logger.start()
            self.serial.connect(config)
            self.status.configure(text=f"Connected - {config.port} ({path.name})")
        except Exception as error:
            self.logger.close()
            messagebox.showerror("Connection error", str(error))

    def disconnect(self) -> None:
        self.serial.disconnect()
        final = self.parser.flush()
        if final is not None:
            self._show_measurement(final)
        self.logger.close()
        self.status.configure(text="Disconnected")

    def _received(self, data: bytes) -> None:
        self.logger.write(data)
        self.events.put(("data", data))

    def _serial_error(self, error: Exception) -> None:
        self.events.put(("error", error))

    def _poll_events(self) -> None:
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "data":
                    text = payload.decode("ascii", errors="replace")
                    self._append_console(text)
                    for measurement in self.parser.feed(text):
                        self._show_measurement(measurement)
                else:
                    self.status.configure(text=f"Communication error: {payload}")
                    self.disconnect()
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    def _show_measurement(self, measurement) -> None:
        self.data.add(measurement)
        values = lambda value: "-" if value is None else f"{value:g}"
        self.table.insert("", "end", values=(measurement.timestamp.strftime("%H:%M:%S.%f")[:-3], measurement.mode, measurement.elapsed_time, values(measurement.current), values(measurement.voltage), values(measurement.power), values(measurement.frequency)))
        children = self.table.get_children()
        if len(children) > 500:
            self.table.delete(children[0])
        self.plot.update(self.data.measurements)

    def _append_console(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.console.configure(state="normal")
        for line in text.splitlines():
            self.console.insert("end", f"[{stamp}] {line}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def _toggle_power(self) -> None:
        self.plot.set_power_visible(self.power_visible.get())

    def close(self) -> None:
        self.disconnect()
        self.root.destroy()