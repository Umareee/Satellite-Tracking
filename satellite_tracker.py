import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timezone
from skyfield.api import Loader, Topos

# Import custom modules
from config import DARK_BG, FG_COLOR, ACCENT_COLOR, CARD_BG
from utils.satellite_data import load_tle_data, fetch_tle_data, save_tle_data
from utils.orbit_calc import get_satellite_position, calculate_trajectory, calculate_passes
from ui.map_display import MapDisplay
from ui.dashboard import Dashboard
from ui.controls import SearchableSatelliteList, ControlPanel, LocationDialog, ScheduleDialog


class SatelliteTracker:
    def __init__(self, root):
        self.root = root
        self.satellites = {}
        self.current_sat = None
        self.is_playing = False

        # Observer settings
        self.observer = Topos(latitude_degrees=40.7128, longitude_degrees=-74.0060)
        self.current_location = "New York, USA (40.7128°N, 74.0060°W)"

        # Tracking data
        self.last_trajectory_update = None
        self.cached_trajectory = []
        self.update_interval = 500  # milliseconds

        # Set up the UI components
        self.setup_gui()
        self.initialize_data()

    def setup_gui(self):
        """Set up the main GUI structure and styles"""
        self.root.title("OrbitX - Satellite Tracker")
        self.root.geometry("1280x800")
        self.root.configure(bg=DARK_BG)

        # Configure grid layout
        self.root.grid_rowconfigure(0, weight=3)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)

        # Create main frames
        self.map_frame = ttk.Frame(self.root, style='Dark.TFrame')
        self.map_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.control_frame = ttk.Frame(self.root, style='Dark.TFrame')
        self.control_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

        self.dashboard_frame = ttk.Frame(self.root, style='Dark.TFrame')
        self.dashboard_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        self.list_frame = ttk.Frame(self.root, style='Dark.TFrame')
        self.list_frame.grid(row=1, column=1, sticky='nsew', padx=10, pady=10)

        # Set up styles
        self.setup_styles()

        # Initialize UI components
        self.map_display = MapDisplay(self.map_frame)
        self.dashboard = Dashboard(self.dashboard_frame)

        # Control panel callbacks
        control_callbacks = {
            'toggle_play': self.toggle_play,
            'update_data': self.threaded_update_tle,
            'toggle_mode': self.toggle_mode,
            'show_schedule': self.show_schedule,
            'toggle_view': self.toggle_polar_view,
            'show_location': self.show_location_dialog
        }
        self.control_panel = ControlPanel(self.control_frame, control_callbacks)
        self.control_panel.update_location_label(self.current_location)

        # Satellite list with selection callback
        self.satellite_list = SearchableSatelliteList(self.list_frame, self.on_sat_select)

    def setup_styles(self):
        """Set up ttk styles for the application"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Dark.TFrame', background=DARK_BG)
        self.style.configure('Card.TFrame', background=CARD_BG, borderwidth=2, relief='flat')
        self.style.configure('Neon.TButton',
                             font=('Segoe UI', 10, 'bold'),
                             width=12,
                             anchor='center',
                             padding=5)
        self.style.map('Neon.TButton',
                       background=[('active', ACCENT_COLOR)],
                       foreground=[('active', DARK_BG)])
        self.style.configure('Title.TLabel',
                             font=('Segoe UI', 12, 'bold'),
                             foreground=ACCENT_COLOR,
                             background=DARK_BG)
        self.style.configure('Data.TLabel',
                             font=('Segoe UI', 10),
                             foreground=FG_COLOR,
                             background=CARD_BG,
                             padding=2)

    def initialize_data(self):
        """Load initial satellite data"""
        try:
            self.satellites = load_tle_data()
            if self.satellites:
                self.satellite_list.populate_list(self.satellites)
                # Select the first satellite
                self.satellite_list.sat_list.select_set(0)
                self.on_sat_select(self.satellite_list.sat_list.get(0))
            else:
                messagebox.showwarning("No Data", "TLE file is empty or invalid. Please update data.")
        except Exception as e:
            print(f"Error loading local TLE file: {e}")
            self.threaded_update_tle()

    def threaded_update_tle(self):
        """Update TLE data via category dialog"""
        from config import SATELLITE_CATEGORIES

        dialog = tk.Toplevel(self.root)
        dialog.title("Select Satellite Category")
        dialog.configure(bg=DARK_BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, style='Dark.TFrame')
        main_frame.pack(padx=20, pady=20)

        ttk.Label(main_frame, text="Choose a Satellite Category:", style='Title.TLabel').pack(pady=(0, 10))

        category_var = tk.StringVar()
        category_menu = ttk.Combobox(main_frame, textvariable=category_var,
                                     values=list(SATELLITE_CATEGORIES.keys()), state="readonly")
        category_menu.pack(pady=5)
        category_menu.set(list(SATELLITE_CATEGORIES.keys())[0])

        loading_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        loading_frame.pack(pady=5)
        loading_label = ttk.Label(loading_frame, text="", style='Data.TLabel', foreground="green")

        def fetch_selected_category():
            """Fetch selected category of satellites"""
            selected_category = category_var.get()
            if not selected_category:
                messagebox.showwarning("No Selection", "Please select a category.")
                return

            url = SATELLITE_CATEGORIES[selected_category]
            loading_label.pack()
            dialog.update()

            def fetch_and_update():
                try:
                    tle_text = fetch_tle_data(url)
                    self.satellites = save_tle_data(tle_text)
                    self.root.after(0, lambda: self._update_complete(dialog))
                except Exception as e:
                    print(f"Error fetching TLE data: {e}")
                    self.root.after(0, lambda: messagebox.showerror(
                        "Update Failed", f"Failed to update satellite data:\n{e}"))
                    dialog.destroy()

            threading.Thread(target=fetch_and_update, daemon=True).start()

        ttk.Button(main_frame, text="Fetch Data", style='Neon.TButton',
                   command=fetch_selected_category).pack(pady=10)
        ttk.Button(main_frame, text="Cancel", style='Neon.TButton',
                   command=dialog.destroy).pack(pady=5)

    def _update_complete(self, dialog):
        """Handle successful TLE update"""
        dialog.destroy()
        messagebox.showinfo("Update Complete", "Satellite data has been updated successfully.")
        self.satellite_list.populate_list(self.satellites)

        # Select first satellite
        if self.satellites:
            self.satellite_list.sat_list.select_set(0)
            self.on_sat_select(list(self.satellites.keys())[0])

    def on_sat_select(self, satellite_name):
        """Handle satellite selection"""
        self.current_sat = satellite_name
        self.last_trajectory_update = None  # Force trajectory recalculation
        self.map_display.set_title(f"TRACKING: {self.current_sat}")
        self.update_display()

    def toggle_play(self):
        """Toggle live tracking"""
        self.is_playing = not self.is_playing
        self.control_panel.update_play_button(self.is_playing)
        if self.is_playing:
            self.update_loop()

    def toggle_mode(self):
        """Toggle between light and dark mode"""
        self.map_display.toggle_mode()

    def toggle_polar_view(self):
        """Toggle between regular and polar view"""
        self.map_display.toggle_polar_view()
        if self.current_sat:
            self.update_display()

    def show_location_dialog(self):
        """Show dialog to select observer location"""
        LocationDialog(self.root, self.current_location, self.save_location)

    def save_location(self, location):
        """Save the selected observer location"""
        self.observer = Topos(latitude_degrees=location['lat'], longitude_degrees=location['lon'])
        self.current_location = location['name']
        self.control_panel.update_location_label(self.current_location)
        if self.current_sat:
            self.update_display()

    def show_schedule(self):
        """Show satellite pass schedule"""
        if not self.current_sat:
            messagebox.showinfo("No Satellite Selected", "Please select a satellite first.")
            return

        def calc_passes(days):
            if self.current_sat not in self.satellites:
                return []

            tle = self.satellites[self.current_sat]
            return calculate_passes(tle, self.observer, days)

        ScheduleDialog(self.root, self.current_sat, self.current_location, calc_passes)

    def update_loop(self):
        """Loop for continuous updates when live tracking is enabled"""
        if self.is_playing:
            self.update_display()
            self.root.after(self.update_interval, self.update_loop)

    def update_display(self):
        """Update the satellite display with current data"""
        if not self.current_sat or self.current_sat not in self.satellites:
            return

        # Update trajectory data periodically
        current_time = datetime.now(timezone.utc)
        if self.last_trajectory_update is None or (current_time - self.last_trajectory_update).total_seconds() > 10:
            self.cached_trajectory = calculate_trajectory(self.satellites[self.current_sat])
            self.last_trajectory_update = current_time

        # Get current position
        data = get_satellite_position(self.satellites[self.current_sat], self.observer)
        if not data:
            return

        # Add satellite name for dashboard
        data['name'] = self.current_sat

        # Update UI components
        self.dashboard.update_values(data)
        self.map_display.update_display(data, self.cached_trajectory)