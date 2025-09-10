import tkinter as tk
from tkinter import ttk
from config import CARD_BG, FG_COLOR, ACCENT_COLOR


class Dashboard:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.create_dashboard()

    def create_dashboard(self):
        """Create the satellite details dashboard"""
        dashboard = ttk.Frame(self.parent_frame, style='Card.TFrame')
        dashboard.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(dashboard, text="SATELLITE DETAILS", style='Title.TLabel', anchor='center').pack(fill=tk.X, pady=2)

        data_table = ttk.Frame(dashboard, style='Card.TFrame')
        data_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        parameters = [
            ("Name", "name"),
            ("Lat", "lat"),
            ("Lon", "lon"),
            ("Alt (km)", "alt"),
            ("Vel (km/s)", "vel"),
            ("Az (°)", "az"),
            ("El (°)", "el"),
            ("Time (UTC)", "time")
        ]

        for row, (label, key) in enumerate(parameters, start=1):
            ttk.Label(data_table, text=label, style='Data.TLabel').grid(
                row=row, column=0, padx=2, pady=1, sticky='w')

            setattr(self, f'detail_{key}',
                    ttk.Label(data_table, text="-", style='Data.TLabel', foreground=ACCENT_COLOR))

            getattr(self, f'detail_{key}').grid(
                row=row, column=1, padx=2, pady=1, sticky='e')

        data_table.columnconfigure((0, 1), weight=1)

    def update_values(self, data):
        """Update dashboard with satellite data"""
        if not data:
            return

        self.detail_name.config(text=data['name'] if 'name' in data else '-')
        self.detail_lat.config(text=f"{data['lat']:.4f}" if 'lat' in data else '-')
        self.detail_lon.config(text=f"{data['lon']:.4f}" if 'lon' in data else '-')
        self.detail_alt.config(text=f"{data['alt']:.1f}" if 'alt' in data else '-')
        self.detail_vel.config(text=f"{data['vel']:.2f}" if 'vel' in data else '-')
        self.detail_az.config(text=f"{data['az']:.1f}" if 'az' in data else '-')
        self.detail_el.config(text=f"{data['el']:.1f}" if 'el' in data else '-')
        self.detail_time.config(text=f"{data['time']}" if 'time' in data else '-')