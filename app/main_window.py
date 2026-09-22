import csv
import queue
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

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
        self.mode = None
        self.columns = []
        self.column_vars = {}
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
        self.baud.set("19200")
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
        self.rtscts = tk.BooleanVar(value=True)
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
        self.table = ttk.Treeview(top, columns=(), show="headings", height=10)
        self.table.pack(fill="both", expand=True)
        self.column_controls = ttk.Frame(top)
        self.column_controls.pack(fill="x")
        plot_frame = ttk.Frame(top)
        plot_frame.pack(fill="both", expand=True)
        self.plot = PlotManager(plot_frame)

        console_controls = ttk.Frame(bottom)
        console_controls.pack(fill="x")
        ttk.Button(console_controls, text="Clear table", command=self.clear_table).pack(side="right", padx=8)
        ttk.Button(console_controls, text="Export CSV", command=self.export_csv).pack(side="right", padx=8)
        ttk.Button(console_controls, text="Export graph PDF", command=self.export_graph).pack(side="right", padx=8)
        ttk.Button(console_controls, text="Clear console", command=lambda: self.console.delete("1.0", "end")).pack(side="right")
        ttk.Button(console_controls, text="Inject log", command=self.inject_log).pack(side="right", padx=8)
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
            self._reset_measurements(None)
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
        idle_measurement = self.parser.flush_if_idle()
        if idle_measurement is not None:
            self._show_measurement(idle_measurement)
        self.root.after(50, self._poll_events)

    def _show_measurement(self, measurement) -> None:
        if self.mode != measurement.mode:
            self._reset_measurements(measurement.mode)
        self.data.add(measurement)
        new_columns = [name for name in measurement.values if name not in self.columns]
        if new_columns:
            self.columns.extend(new_columns)
            self._configure_columns()
        self._refresh_table()
        self.plot.update(self.data.measurements, self._selected_columns())

    def _reset_measurements(self, mode: str) -> None:
        self.mode = mode
        self.columns = []
        self.data.clear()
        self.table.delete(*self.table.get_children())
        for child in self.column_controls.winfo_children():
            child.destroy()
        self.column_vars = {}
        self.plot.set_columns([])

    def clear_table(self) -> None:
        """Clear the displayed measurements and reset the dynamic schema."""
        self._reset_measurements(None)

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export table as CSV",
            defaultextension=".csv",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as output:
                writer = csv.writer(output, delimiter=";")
                columns = ("Timestamp", "Mode", "Elapsed", *self.columns)
                writer.writerow(columns)
                for item in self.data.measurements:
                    row = (item.timestamp.isoformat(timespec="milliseconds"), item.mode, item.elapsed_time)
                    writer.writerow(row + tuple(item.values.get(name, "") for name in self.columns))
            self.status.configure(text=f"CSV exported - {Path(path).name}")
        except OSError as error:
            messagebox.showerror("CSV export error", str(error))

    def export_graph(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export graph as PDF",
            defaultextension=".pdf",
            filetypes=(("PDF files", "*.pdf"), ("PNG files", "*.png"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            self.plot.save(path)
            self.status.configure(text=f"Graph exported - {Path(path).name}")
        except OSError as error:
            messagebox.showerror("Graph export error", str(error))

    def _configure_columns(self) -> None:
        old_selection = self._selected_columns()
        table_columns = ("timestamp", "mode", "elapsed", *self.columns)
        self.table.configure(columns=table_columns)
        headings = {"timestamp": "Timestamp", "mode": "Mode", "elapsed": "Elapsed"}
        for column in table_columns:
            self.table.heading(column, text=headings.get(column, column))
            self.table.column(column, width=115, anchor="center")
        for child in self.column_controls.winfo_children():
            child.destroy()
        self.column_vars = {}
        for column in self.columns:
            variable = tk.BooleanVar(value=column in old_selection or not old_selection)
            self.column_vars[column] = variable
            ttk.Checkbutton(self.column_controls, text=column, variable=variable, command=self._update_plot).pack(side="left", padx=3)
        self._update_plot()

    def _selected_columns(self):
        return [name for name, variable in self.column_vars.items() if variable.get()]

    def _refresh_table(self) -> None:
        self.table.delete(*self.table.get_children())
        format_value = lambda value: "-" if value is None else f"{value:g}"
        for item in self.data.measurements[-500:]:
            row = (item.timestamp.strftime("%H:%M:%S.%f")[:-3], item.mode, item.elapsed_time)
            self.table.insert("", "end", values=row + tuple(format_value(item.values.get(name)) for name in self.columns))

    def _update_plot(self) -> None:
        selected = self._selected_columns()
        self.plot.set_columns(self.columns, selected)
        self.plot.update(self.data.measurements, selected)

    def inject_log(self) -> None:
        path = filedialog.askopenfilename(title="Inject log", filetypes=(("Log files", "*.log *.txt"), ("All files", "*.*")))
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="ascii", errors="replace")
            self.parser = ProtocolParser()
            self._append_console(text)
            for measurement in self.parser.feed(text):
                self._show_measurement(measurement)
            final = self.parser.flush()
            if final is not None:
                self._show_measurement(final)
            self.status.configure(text=f"Injected - {Path(path).name}")
        except OSError as error:
            messagebox.showerror("Injection error", str(error))

    def _append_console(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.console.configure(state="normal")
        for line in text.splitlines():
            self.console.insert("end", f"[{stamp}] {line}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def close(self) -> None:
        self.disconnect()
        self.root.destroy()