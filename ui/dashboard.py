import tkinter as tk
from typing import Dict, Any

from utils.theme import T


class Dashboard:
    def __init__(self, parent_frame, theme: dict):
        self.parent_frame = parent_frame
        self.theme = theme
        self.labels = {}
        self.all_widgets = []  # For theme updates
        self.create_dashboard()

    def create_dashboard(self):
        t = self.theme
        self.container = tk.Frame(self.parent_frame, bg=T(t, 'card'),
                                  highlightbackground=T(t, 'card_border'), highlightthickness=1)
        self.container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.header = tk.Frame(self.container, bg=T(t, 'card'))
        self.header.pack(fill=tk.X, padx=12, pady=(10, 4))
        self.header_label = tk.Label(self.header, text="SATELLITE TELEMETRY",
                                     font=("SF Pro Display", 11, "bold"),
                                     fg=T(t, 'accent'), bg=T(t, 'card'))
        self.header_label.pack(side=tk.LEFT)

        self.sep = tk.Frame(self.container, bg=T(t, 'card_border'), height=1)
        self.sep.pack(fill=tk.X, padx=12, pady=(2, 6))

        self.data_frame = tk.Frame(self.container, bg=T(t, 'card'))
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        parameters = [
            ("SATELLITE", "name", None),
            ("LATITUDE", "lat", "deg"),
            ("LONGITUDE", "lon", "deg"),
            ("ALTITUDE", "alt", "km"),
            ("VELOCITY", "vel", "km/s"),
            ("AZIMUTH", "az", "deg"),
            ("ELEVATION", "el", "deg"),
            ("TIME UTC", "time", None),
        ]

        cols = 4
        self.param_labels = []
        self.unit_labels = []

        for idx, (label, key, unit) in enumerate(parameters):
            row = idx // cols
            col = idx % cols

            cell = tk.Frame(self.data_frame, bg=T(t, 'card'))
            cell.grid(row=row, column=col, padx=6, pady=4, sticky='nsew')

            lbl = tk.Label(cell, text=label, font=("SF Pro Display", 8),
                           fg=T(t, 'fg_muted'), bg=T(t, 'card'))
            lbl.pack(anchor='w')
            self.param_labels.append(lbl)

            value_frame = tk.Frame(cell, bg=T(t, 'card'))
            value_frame.pack(anchor='w')

            val_label = tk.Label(value_frame, text="---", font=("SF Mono", 13, "bold"),
                                 fg=T(t, 'fg'), bg=T(t, 'card'))
            val_label.pack(side=tk.LEFT)

            if unit:
                ulbl = tk.Label(value_frame, text=f" {unit}", font=("SF Pro Display", 9),
                                fg=T(t, 'fg_muted'), bg=T(t, 'card'))
                ulbl.pack(side=tk.LEFT, pady=(2, 0))
                self.unit_labels.append(ulbl)

            self.labels[key] = val_label

        for c in range(cols):
            self.data_frame.columnconfigure(c, weight=1)

    def update_values(self, data: Dict[str, Any]):
        if not data:
            return

        t = self.theme
        formatters = {
            'name': lambda v: str(v),
            'lat': lambda v: f"{v:+.4f}",
            'lon': lambda v: f"{v:+.4f}",
            'alt': lambda v: f"{v:,.1f}",
            'vel': lambda v: f"{v:.3f}",
            'az': lambda v: f"{v:.1f}",
            'el': lambda v: f"{v:.1f}",
            'time': lambda v: str(v).replace(' UTC', ''),
        }

        for key, label in self.labels.items():
            if key in data:
                formatter = formatters.get(key, str)
                label.config(text=formatter(data[key]))

                if key == 'el':
                    el_val = data[key]
                    if el_val > 10:
                        label.config(fg=T(t, 'green'))
                    elif el_val > 0:
                        label.config(fg=T(t, 'warning'))
                    else:
                        label.config(fg=T(t, 'fg'))
            else:
                label.config(text="---")

    def update_theme(self, theme: dict):
        self.theme = theme
        t = theme
        self.container.config(bg=T(t, 'card'), highlightbackground=T(t, 'card_border'))
        self.header.config(bg=T(t, 'card'))
        self.header_label.config(fg=T(t, 'accent'), bg=T(t, 'card'))
        self.sep.config(bg=T(t, 'card_border'))
        self.data_frame.config(bg=T(t, 'card'))

        for lbl in self.param_labels:
            lbl.config(fg=T(t, 'fg_muted'), bg=T(t, 'card'))
            lbl.master.config(bg=T(t, 'card'))
            # Also update the value_frame parent
            for child in lbl.master.winfo_children():
                child.config(bg=T(t, 'card'))
                for grandchild in child.winfo_children():
                    try:
                        grandchild.config(bg=T(t, 'card'))
                    except tk.TclError:
                        pass

        for ulbl in self.unit_labels:
            ulbl.config(fg=T(t, 'fg_muted'), bg=T(t, 'card'))

        for key, label in self.labels.items():
            if key != 'el':  # el has special coloring
                label.config(fg=T(t, 'fg'), bg=T(t, 'card'))
            else:
                label.config(bg=T(t, 'card'))
