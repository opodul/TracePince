from typing import Iterable

from .measurement import Measurement


class PlotManager:
    """Own the three live matplotlib axes embedded in the Tk window."""

    def __init__(self, parent) -> None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.axes = {
            "current": self.figure.add_subplot(311),
            "voltage": self.figure.add_subplot(312),
            "power": self.figure.add_subplot(313),
        }
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.power_visible = True
        self._style_axes()

    def _style_axes(self) -> None:
        labels = {"current": "Current (A)", "voltage": "Voltage (V)", "power": "Power (W)"}
        for name, axis in self.axes.items():
            axis.set_ylabel(labels[name])
            axis.grid(True, alpha=0.25)
        self.axes["power"].set_xlabel("Elapsed time")

    def set_power_visible(self, visible: bool) -> None:
        self.power_visible = visible
        self.axes["power"].set_visible(visible)
        self.canvas.draw_idle()

    def update(self, measurements: Iterable[Measurement]) -> None:
        points = list(measurements)
        x = list(range(len(points)))
        series = {
            "current": [item.current for item in points],
            "voltage": [item.voltage for item in points],
            "power": [item.power for item in points],
        }
        for name, axis in self.axes.items():
            axis.clear()
            axis.set_ylabel({"current": "Current (A)", "voltage": "Voltage (V)", "power": "Power (W)"}[name])
            axis.grid(True, alpha=0.25)
            values = [(index, value) for index, value in zip(x, series[name]) if value is not None]
            if values:
                axis.plot([item[0] for item in values], [item[1] for item in values], color="#d65a31")
        self.axes["power"].set_visible(self.power_visible)
        self.canvas.draw_idle()