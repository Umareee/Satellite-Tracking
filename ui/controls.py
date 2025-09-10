import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
from config import LOCATIONS, DARK_BG, ACCENT_COLOR, CARD_BG, FG_COLOR


class SearchableSatelliteList:
    def __init__(self, parent_frame, on_select_callback):
        self.parent_frame = parent_frame
        self.on_select_callback = on_select_callback
        self.create_list()

    def create_list(self):
        """Create the satellite listbox with search functionality"""
        list_container = ttk.Frame(self.parent_frame, style='Card.TFrame')
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(list_container, text="ACTIVE SATELLITES", style='Title.TLabel', anchor='center').pack(
            fill=tk.X, pady=2)

        # Add search box
        search_frame = ttk.Frame(list_container, style='Card.TFrame')
        search_frame.pack(fill=tk.X, padx=2, pady=2)

        ttk.Label(search_frame, text="Search:", style='Data.TLabel').pack(side=tk.LEFT, padx=2)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_satellite_list)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.sat_list = tk.Listbox(
            list_container,
            bg=CARD_BG,
            fg=FG_COLOR,
            selectbackground=ACCENT_COLOR,
            font=('Segoe UI', 10),
            height=6
        )

        scrollbar = ttk.Scrollbar(list_container, command=self.sat_list.yview)
        self.sat_list.config(yscrollcommand=scrollbar.set)

        self.sat_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sat_list.bind('<<ListboxSelect>>', self.on_sat_select)

    def populate_list(self, satellites):
        """Populate the listbox with satellite names"""
        self.satellites = satellites
        self.sat_list.delete(0, tk.END)

        for sat in sorted(satellites.keys()):
            self.sat_list.insert(tk.END, sat)

    def filter_satellite_list(self, *args):
        """Filter the satellite list based on search term"""
        search_term = self.search_var.get().lower().strip()
        self.sat_list.delete(0, tk.END)

        for sat in sorted(self.satellites.keys()):
            if not search_term or search_term in sat.lower():
                self.sat_list.insert(tk.END, sat)

    def on_sat_select(self, event=None):
        """Handle satellite selection"""
        if selection := self.sat_list.curselection():
            selected_sat = self.sat_list.get(selection[0])
            self.on_select_callback(selected_sat)


class ControlPanel:
    def __init__(self, parent_frame, callbacks):
        self.parent_frame = parent_frame
        self.callbacks = callbacks  # Dict with callback functions
        self.create_controls()
        self.create_location_panel()
        self.setup_hover_effects()
    def setup_hover_effects(self):
        style = ttk.Style()
    # Create hover effect for Neon buttons
        style.map('Neon.TButton',
                  background=[('active', '#1A2332'), ('hover', '#0B1426')],
                  foreground=[('active', '#ffffff')],
                  relief=[('active', 'sunken')])
    # Create a new style for hover state
        style.configure('Hover.Neon.TButton', 
                        background='#0B1426',
                        foreground='#ffffff')
    def create_controls(self):
        """Create control buttons"""
        btn_container = ttk.Frame(self.parent_frame, style='Dark.TFrame')
        btn_container.grid(row=0, column=0, sticky='nsew', pady=(5, 20))

        buttons = [
            ("⏵ LIVE TRACKING", "toggle_play"),
            ("🔄 UPDATE DATA", "update_data"),
            ("🌓 LIGHT/DARK MODE", "toggle_mode"),
            ("📅 SCHEDULE", "show_schedule"),
            ("🗺️ POLAR VIEW", "toggle_view"),
        ]

        for row, (text, callback_key) in enumerate(buttons):
            btn = ttk.Button(
                btn_container,
                text=text,
                style='Neon.TButton',
                command=self.callbacks.get(callback_key)
            )
            btn.grid(row=row, column=0, padx=2, pady=2, sticky='nsew')
            
            if callback_key == "toggle_play":
                self.play_btn = btn

        btn_container.grid_columnconfigure(0, weight=1)
        for row in range(len(buttons)):
            btn_container.grid_rowconfigure(row, weight=1)

    def create_location_panel(self):
        """Create observer location controls"""
        self.location_frame = ttk.Frame(self.parent_frame, style='Card.TFrame')
        self.location_frame.grid(row=1, column=0, sticky='ew', pady=5)

        ttk.Label(self.location_frame, text="OBSERVER LOCATION", style='Title.TLabel').pack(fill=tk.X, pady=2)

        self.location_label = ttk.Label(
            self.location_frame,
            text="",
            style='Data.TLabel',
            foreground=ACCENT_COLOR,
            wraplength=250
        )
        self.location_label.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            self.location_frame,
            text="📍 SELECT LOCATION",
            style='Neon.TButton',
            command=self.callbacks.get('show_location')
        ).pack(fill=tk.X, pady=2)

    def update_play_button(self, is_playing):
        """Update play button text based on state"""
        self.play_btn.config(text="⏸ PAUSE" if is_playing else "⏵ LIVE TRACKING")

    def update_location_label(self, location_text):
        """Update the location display"""
        self.location_label.config(text=location_text)


class LocationDialog:
    """Dialog for selecting observer location"""

    def __init__(self, parent, current_location, on_save_callback):
        self.parent = parent
        self.current_location = current_location
        self.on_save_callback = on_save_callback
        self.dialog = None
        self.show_dialog()

    def show_dialog(self):
        dialog = tk.Toplevel(self.parent)
        self.dialog = dialog
        dialog.title("Select Observer Location")
        dialog.configure(bg=DARK_BG)
        dialog.resizable(False, False)

        main_frame = ttk.Frame(dialog, style='Dark.TFrame')
        main_frame.pack(padx=10, pady=10)

        ttk.Label(main_frame, text="Location:", style='Data.TLabel').grid(row=0, column=0, sticky='w')
        self.location_var = tk.StringVar()
        self.location_menu = ttk.Combobox(
            main_frame,
            textvariable=self.location_var,
            values=list(LOCATIONS.keys())
        )
        self.location_menu.grid(row=0, column=1, pady=5, sticky='ew')

        ttk.Label(main_frame, text="Custom Latitude:", style='Data.TLabel').grid(row=1, column=0, sticky='w')
        self.custom_lat_var = tk.StringVar()
        self.custom_lat_entry = ttk.Entry(main_frame, textvariable=self.custom_lat_var)
        self.custom_lat_entry.grid(row=1, column=1, pady=5, sticky='ew')

        ttk.Label(main_frame, text="Custom Longitude:", style='Data.TLabel').grid(row=2, column=0, sticky='w')
        self.custom_lon_var = tk.StringVar()
        self.custom_lon_entry = ttk.Entry(main_frame, textvariable=self.custom_lon_var)
        self.custom_lon_entry.grid(row=2, column=1, pady=5, sticky='ew')

        ttk.Button(
            main_frame,
            text="Save",
            style='Neon.TButton',
            command=self.save_location
        ).grid(row=3, column=0, columnspan=2, pady=10)

    def save_location(self):
        custom_lat = self.custom_lat_var.get().strip()
        custom_lon = self.custom_lon_var.get().strip()

        if custom_lat and custom_lon:
            try:
                lat = float(custom_lat)
                lon = float(custom_lon)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    lat_dir = 'N' if lat >= 0 else 'S'
                    lon_dir = 'E' if lon >= 0 else 'W'
                    location = {
                        'name': f"Custom Location ({abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir})",
                        'lat': lat,
                        'lon': lon
                    }
                    self.dialog.destroy()
                    self.on_save_callback(location)
                else:
                    messagebox.showerror("Invalid Input",
                                         "Latitude must be between -90 and 90, Longitude between -180 and 180.")
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for latitude and longitude.")
        else:
            selected_location = self.location_var.get()
            if selected_location:
                lat, lon = LOCATIONS[selected_location]
                lat_dir = 'N' if lat >= 0 else 'S'
                lon_dir = 'E' if lon >= 0 else 'W'
                location = {
                    'name': f"{selected_location} ({abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir})",
                    'lat': lat,
                    'lon': lon
                }
                self.dialog.destroy()
                self.on_save_callback(location)
            else:
                messagebox.showerror("No Selection", "Please select a location or enter custom coordinates.")


class ScheduleDialog:
    """Dialog for displaying satellite pass schedule"""

    def __init__(self, parent, satellite_name, location_name, calculate_passes_func):
        self.parent = parent
        self.satellite_name = satellite_name
        self.location_name = location_name
        self.calculate_passes_func = calculate_passes_func
        self.schedule_window = None
        self.show_dialog()

    def show_dialog(self):
        if not self.satellite_name:
            messagebox.showinfo("No Satellite Selected", "Please select a satellite first.")
            return

        schedule_window = tk.Toplevel(self.parent)
        self.schedule_window = schedule_window
        schedule_window.title(f"Pass Schedule for {self.satellite_name}")
        schedule_window.configure(bg=DARK_BG)
        schedule_window.geometry("800x500")

        frame = ttk.Frame(schedule_window, style='Dark.TFrame')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text=f"Pass Schedule for {self.satellite_name}", style='Title.TLabel').pack(pady=5)
        ttk.Label(frame, text=f"Observer: {self.location_name}", style='Data.TLabel').pack(pady=5)

        range_frame = ttk.Frame(frame)
        range_frame.pack(pady=5)
        ttk.Label(range_frame, text="Time Range (days):", style='Data.TLabel').pack(side=tk.LEFT)
        self.days_var = tk.StringVar(value="7")
        ttk.Combobox(range_frame, textvariable=self.days_var, values=["1", "3", "7", "14" , "30"], width=5).pack(
            side=tk.LEFT, padx=5)

        self.tree_frame = ttk.Frame(frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        self.export_btn = ttk.Button(frame, text="Export to CSV", style='Neon.TButton')
        self.export_btn.pack(pady=5)
        self.export_btn.pack_forget()

        ttk.Button(frame, text="Calculate", command=self.calculate_and_display, style='Neon.TButton').pack(pady=5)
        ttk.Button(frame, text="Close", command=schedule_window.destroy, style='Neon.TButton').pack(pady=5)

        # Calculate passes right away
        self.calculate_and_display()

    def calculate_and_display(self):
        try:
            days = float(self.days_var.get())
            if days <= 0:
                raise ValueError("Invalid input: Days must be positive.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e) or "Please enter a valid number.")
            return

        # Call the function provided to calculate passes
        passes = self.calculate_passes_func(days)

        # Clear previous results
        for widget in self.tree_frame.winfo_children():
            widget.destroy()

        if not passes:
            ttk.Label(self.tree_frame, text=f"No passes in the next {days} days.", style='Data.TLabel').pack(pady=10)
            self.export_btn.pack_forget()
        else:
            tree = ttk.Treeview(
                self.tree_frame,
                columns=('Rise Time', 'Rise Az', 'Culminate Time', 'Culm Az', 'Set Time', 'Set Az', 'Duration'),
                show='headings',
                height=10
            )

            tree.heading('Rise Time', text='Rise Time (UTC)')
            tree.heading('Rise Az', text='Az (°)')
            tree.heading('Culminate Time', text='Culminate Time (UTC)')
            tree.heading('Culm Az', text='Az (°)')
            tree.heading('Set Time', text='Set Time (UTC)')
            tree.heading('Set Az', text='Az (°)')
            tree.heading('Duration', text='Duration (min)')

            tree.column('Rise Time', width=140)
            tree.column('Rise Az', width=50)
            tree.column('Culminate Time', width=140)
            tree.column('Culm Az', width=50)
            tree.column('Set Time', width=140)
            tree.column('Set Az', width=50)
            tree.column('Duration', width=70)

            scrollbar = ttk.Scrollbar(self.tree_frame, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for pass_data in passes:
                tree.insert('', tk.END, values=(
                    pass_data['rise_time'],
                    pass_data['rise_az'],
                    pass_data['culminate_time'],
                    pass_data['culm_az'],
                    pass_data['set_time'],
                    pass_data['set_az'],
                    pass_data['duration']
                ))

            self.export_btn.config(command=lambda: self.export_schedule(passes))
            self.export_btn.pack(pady=5)

    def export_schedule(self, passes):
        try:
            filename = f"{self.satellite_name}_schedule.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Rise Time (UTC)',
                    'Rise Az',
                    'Culminate Time (UTC)',
                    'Culm Az',
                    'Set Time (UTC)',
                    'Set Az',
                    'Duration (min)'
                ])
                for p in passes:
                    writer.writerow([
                        p['rise_time'],
                        p['rise_az'],
                        p['culminate_time'],
                        p['culm_az'],
                        p['set_time'],
                        p['set_az'],
                        p['duration']
                    ])
            full_path = os.path.abspath(filename)
            messagebox.showinfo("Export", f"Schedule exported to:\n{full_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export schedule:\n{e}")