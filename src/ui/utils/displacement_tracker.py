import tkinter as tk


class DisplacementTracker:

    def __init__(self, tk_widget: tk.Misc | None) -> None:

        self.tk_widget = tk_widget
        self.x_init = self.tk_widget.winfo_x() if self.tk_widget else 0
        self.y_init = self.tk_widget.winfo_y() if self.tk_widget else 0

        self.x = self.x_init
        self.y = self.y_init

    def get_displacement(self):
        x = self.tk_widget.winfo_x() if self.tk_widget else 0
        y = self.tk_widget.winfo_y() if self.tk_widget else 0

        x_displacement = x - self.x_init
        y_displacement = y - self.y_init

        return (x_displacement, y_displacement)

    def get_displacement_increment(self) -> tuple[float, float]:
        """ "Get the displacement since the last call"""

        x = self.tk_widget.winfo_x() if self.tk_widget else 0
        y = self.tk_widget.winfo_y() if self.tk_widget else 0

        x_displacement = x - self.x
        y_displacement = y - self.y

        self.x = x
        self.y = y
        return (x_displacement, y_displacement)
