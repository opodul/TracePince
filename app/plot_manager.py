from typing import Iterable, Sequence

from .measurement import Measurement


class PlotManager:
    """Display selected numeric block fields on synchronized X axes."""

    def __init__(self, parent) -> None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.selected: list[str] = []
        self.axes = []

    def set_columns(self, columns: Sequence[str], selected: Sequence[str] | None = None) -> None:
        available = list(columns)
        self.selected = [name for name in (selected or available) if name in available]
        self.figure.clear()
        self.axes = []
        shared_axis = None
        for index, name in enumerate(self.selected, start=1):
            axis = self.figure.add_subplot(len(self.selected), 1, index, sharex=shared_axis)
            shared_axis = shared_axis or axis
            axis.set_ylabel(name)
            axis.grid(True, alpha=0.25)
            self.axes.append(axis)
        if self.axes:
            self.axes[-1].set_xlabel("Measurement index")
        self.canvas.draw_idle()

    def update(self, measurements: Iterable[Measurement], selected: Sequence[str] | None = None) -> None:
        points = list(measurements)
        x = list(range(len(points)))
        selected_names = list(selected if selected is not None else self.selected)
        if selected_names != self.selected:
            self.set_columns(selected_names, selected_names)
        for axis, name in zip(self.axes, self.selected):
            axis.clear()
            axis.set_ylabel(name)
            axis.grid(True, alpha=0.25)
            values = [(index, item.values.get(name)) for index, item in zip(x, points)]
            values = [(index, value) for index, value in values if value is not None]
            if values:
                axis.plot([item[0] for item in values], [item[1] for item in values], color="#d65a31")
        if self.axes:
            self.axes[-1].set_xlabel("Measurement index")
        self.canvas.draw_idle()