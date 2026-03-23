"""
OrbitX — Satellite Tracker
Main application controller. Delegates to:
    - DataManager: TLE data lifecycle
    - TrackingController: orbit computation & state
    - Preferences: user settings persistence
    - UI components: display & interaction
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox

from skyfield.api import Topos

from config import (THEMES, DEFAULT_THEME, UPDATE_INTERVAL_MS, STALE_DATA_HOURS,
                    LOG_FORMAT, LOG_LEVEL)
from utils.theme import T
from utils.data_manager import DataManager
from utils.tracking import TrackingController
from utils.preferences import load_preferences, save_preferences
from utils.orbit_calc import calculate_passes
from ui.map_display import MapDisplay
from ui.dashboard import Dashboard
from ui.controls import (SearchableSatelliteList, ControlPanel, LocationDialog,
                         ScheduleDialog, ModernButton)

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class SatelliteTracker:
    def __init__(self, root: tk.Tk):
        self.root = root

        # Load preferences
        self.prefs = load_preferences()
        self.theme_name = self.prefs.get('theme', DEFAULT_THEME)
        self.theme = THEMES[self.theme_name]

        # Core managers
        self.data = DataManager()
        self.tracker = TrackingController()

        # Observer from saved prefs
        self.observer = Topos(
            latitude_degrees=self.prefs.get('observer_lat', 40.7128),
            longitude_degrees=self.prefs.get('observer_lon', -74.0060),
        )
        self.current_location = self.prefs.get('observer_name',
                                                "New York, USA (40.7128 N, 74.0060 W)")

        self._setup_gui()
        self._load_data()
        logger.info("OrbitX started")

    # ============================================================
    # GUI Setup
    # ============================================================

    def _setup_gui(self):
        t = self.theme
        self.root.title("OrbitX - Satellite Tracker")
        self.root.geometry("1366x850")
        self.root.minsize(1100, 700)
        self.root.configure(bg=T(t, 'bg_deeper'))

        self.root.grid_rowconfigure(0, weight=4)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=4)
        self.root.grid_columnconfigure(1, weight=0)

        # Left: map + dashboard
        self.left_col = tk.Frame(self.root, bg=T(t, 'bg_deeper'))
        self.left_col.grid(row=0, column=0, sticky='nsew', padx=(6, 3), pady=(6, 0))
        self.left_col.grid_rowconfigure(0, weight=4)
        self.left_col.grid_rowconfigure(1, weight=1)
        self.left_col.grid_columnconfigure(0, weight=1)

        self.map_frame = tk.Frame(self.left_col, bg=T(t, 'card'),
                                  highlightbackground=T(t, 'card_border'), highlightthickness=1)
        self.map_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 3))

        self.dashboard_frame = tk.Frame(self.left_col, bg=T(t, 'bg_deeper'))
        self.dashboard_frame.grid(row=1, column=0, sticky='nsew', pady=(3, 0))

        # Right: controls + list
        self.right_col = tk.Frame(self.root, bg=T(t, 'bg_deeper'), width=280)
        self.right_col.grid(row=0, column=1, sticky='nsew', padx=(3, 6), pady=(6, 0))
        self.right_col.grid_propagate(False)
        self.right_col.grid_rowconfigure(0, weight=0)
        self.right_col.grid_rowconfigure(1, weight=1)
        self.right_col.grid_columnconfigure(0, weight=1)

        self.control_frame = tk.Frame(self.right_col, bg=T(t, 'bg_deeper'))
        self.control_frame.grid(row=0, column=0, sticky='nsew')

        self.list_frame = tk.Frame(self.right_col, bg=T(t, 'bg_deeper'))
        self.list_frame.grid(row=1, column=0, sticky='nsew', pady=(3, 0))

        # Status bar
        self.status_bar = tk.Frame(self.root, bg=T(t, 'card'), height=28)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew', padx=6, pady=(3, 6))
        self.status_bar.grid_propagate(False)
        self._create_status_bar()

        # TTK styles
        self._setup_styles()

        # Components
        self.map_display = MapDisplay(self.map_frame, self.theme)
        self.dashboard = Dashboard(self.dashboard_frame, self.theme)

        self.control_panel = ControlPanel(self.control_frame, self.theme, {
            'toggle_play': self._toggle_play,
            'update_data': self._show_fetch_dialog,
            'toggle_mode': self._on_theme_toggle,
            'show_schedule': self._show_schedule,
            'toggle_view': self._on_polar_toggle,
            'show_location': self._show_location_dialog,
            'set_propagator': self._on_propagator_changed,
        })
        self.control_panel.update_location_label(self.current_location)

        self.satellite_list = SearchableSatelliteList(
            self.list_frame, self.theme, self._on_sat_select,
            on_multi_select_callback=self._on_multi_track_changed)

        # Keyboard shortcuts
        self.root.bind('<space>', lambda e: self._toggle_play())
        self.root.bind('<Escape>', lambda e: self._stop_tracking())

    def _create_status_bar(self):
        t = self.theme
        pad = dict(padx=10, pady=4)

        self.status_count = tk.Label(self.status_bar, text="No data loaded",
                                     font=("SF Mono", 9), fg=T(t, 'fg_muted'), bg=T(t, 'card'))
        self.status_count.pack(side=tk.LEFT, **pad)

        self.status_sep1 = tk.Frame(self.status_bar, bg=T(t, 'card_border'), width=1)
        self.status_sep1.pack(side=tk.LEFT, fill=tk.Y, pady=4)

        self.status_tracking = tk.Label(self.status_bar, text="IDLE",
                                        font=("SF Mono", 9, "bold"), fg=T(t, 'fg_muted'),
                                        bg=T(t, 'card'))
        self.status_tracking.pack(side=tk.LEFT, **pad)

        self.status_sep2 = tk.Frame(self.status_bar, bg=T(t, 'card_border'), width=1)
        self.status_sep2.pack(side=tk.LEFT, fill=tk.Y, pady=4)

        self.status_age = tk.Label(self.status_bar, text="",
                                   font=("SF Mono", 9), fg=T(t, 'fg_muted'), bg=T(t, 'card'))
        self.status_age.pack(side=tk.RIGHT, **pad)

    def _setup_styles(self):
        t = self.theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox',
                        fieldbackground=T(t, 'bg_deeper'), background=T(t, 'card'),
                        foreground=T(t, 'fg'), arrowcolor=T(t, 'accent'))
        style.map('TCombobox',
                  fieldbackground=[('readonly', T(t, 'bg_deeper'))],
                  selectbackground=[('readonly', T(t, 'bg_deeper'))],
                  selectforeground=[('readonly', T(t, 'fg'))])

    # ============================================================
    # Data Loading
    # ============================================================

    def _load_data(self):
        """Load TLE data and populate the UI."""
        if self.data.load_local():
            self.satellite_list.populate_list(self.data.satellites)
            # Restore last satellite or select first
            last_sat = self.prefs.get('last_satellite')
            if last_sat and self.data.has_satellite(last_sat):
                names = sorted(self.data.satellites.keys())
                idx = names.index(last_sat) if last_sat in names else 0
                self.satellite_list.sat_list.select_set(idx)
                self._on_sat_select(last_sat)
            else:
                self.satellite_list.sat_list.select_set(0)
                self._on_sat_select(self.satellite_list.sat_list.get(0))

            # Warn if stale
            age = self.data.data_age_hours
            if age and age > STALE_DATA_HOURS:
                messagebox.showwarning("Stale Data",
                                       f"TLE data is {int(age)} hours old.\n"
                                       "Positions may be inaccurate.\n\n"
                                       "Use UPDATE DATA to refresh.")
        else:
            messagebox.showwarning("No Data", "No satellite data found. Please fetch data.")
            self._show_fetch_dialog()

        self._refresh_status()

    def _show_fetch_dialog(self):
        """Show the TLE category selection and fetch dialog."""
        from config import SATELLITE_CATEGORIES
        t = self.theme

        dialog = tk.Toplevel(self.root)
        dialog.title("Fetch Satellite Data")
        dialog.configure(bg=T(t, 'bg'))
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("380x260")
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 380) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 260) // 2
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=T(t, 'card'), highlightbackground=T(t, 'card_border'),
                        highlightthickness=1)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(main, text="SELECT CATEGORY", font=("SF Pro Display", 12, "bold"),
                 fg=T(t, 'accent'), bg=T(t, 'card')).pack(pady=(14, 4))
        tk.Frame(main, bg=T(t, 'card_border'), height=1).pack(fill=tk.X, padx=16, pady=(0, 10))

        category_var = tk.StringVar()
        combo = ttk.Combobox(main, textvariable=category_var,
                             values=list(SATELLITE_CATEGORIES.keys()),
                             state="readonly", font=("SF Pro Display", 10))
        combo.pack(padx=20, fill=tk.X)
        last_cat = self.prefs.get('last_category', list(SATELLITE_CATEGORIES.keys())[0])
        combo.set(last_cat if last_cat in SATELLITE_CATEGORIES else list(SATELLITE_CATEGORIES.keys())[0])

        status_label = tk.Label(main, text="", font=("SF Pro Display", 9),
                                fg=T(t, 'fg_muted'), bg=T(t, 'card'))
        status_label.pack(pady=6)

        btn_frame = tk.Frame(main, bg=T(t, 'card'))
        btn_frame.pack(fill=tk.X, padx=20, pady=(4, 14))

        fetch_btn = ModernButton(btn_frame, "FETCH DATA", t, accent=True, height=34)
        cancel_btn = ModernButton(btn_frame, "CANCEL", t, command=dialog.destroy, height=34)

        def _on_fetch():
            selected = category_var.get()
            if not selected:
                return

            url = SATELLITE_CATEGORIES[selected]
            status_label.config(text="Fetching data...", fg=T(t, 'warning'))
            fetch_btn._label.config(text="FETCHING...", state=tk.DISABLED)

            def _on_success():
                if dialog.winfo_exists():
                    dialog.destroy()
                self.prefs['last_category'] = selected
                save_preferences(self.prefs)
                self.satellite_list.populate_list(self.data.satellites)
                if self.data.satellite_count > 0:
                    self.satellite_list.sat_list.select_set(0)
                    self._on_sat_select(list(self.data.satellites.keys())[0])
                self._refresh_status()

            def _on_error(msg):
                if dialog.winfo_exists():
                    status_label.config(text=f"Failed: {msg}", fg=T(t, 'error'))
                    fetch_btn._label.config(text="FETCH DATA", state=tk.NORMAL)

            self.data.fetch_remote(
                url,
                on_success=lambda: self.root.after(0, _on_success),
                on_error=lambda msg: self.root.after(0, lambda: _on_error(msg)),
            )

        fetch_btn.command = _on_fetch
        fetch_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        cancel_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

    # ============================================================
    # Satellite Selection & Tracking
    # ============================================================

    def _on_sat_select(self, name: str):
        self.tracker.select_satellite(name)
        self.map_display.set_title(f"TRACKING: {name}")
        self.prefs['last_satellite'] = name
        save_preferences(self.prefs)
        self._update_display()
        self._refresh_status()

    def _on_multi_track_changed(self, tracked_list):
        self.tracker.set_tracked_list(tracked_list)
        self._refresh_status()
        if self.tracker.current_sat:
            self._update_display()

    def _on_propagator_changed(self, prop_name: str, force_preset: str):
        """Switch the active propagator."""
        from utils.orbit_calc import set_propagator, get_propagator_info
        from utils.propagators import PropagatorType, FORCE_MODEL_PRESETS

        if prop_name == "Numerical":
            fm = FORCE_MODEL_PRESETS.get(force_preset, FORCE_MODEL_PRESETS['standard'])
            set_propagator(PropagatorType.NUMERICAL, fm)
        else:
            set_propagator(PropagatorType.SGP4)

        info = get_propagator_info()
        logger.info("Propagator changed: %s", info['name'])

        # Force trajectory recalculation with new propagator
        self.tracker._trajectory_updated = None
        if self.tracker.current_sat:
            self._update_display()

    def _toggle_play(self):
        self.tracker.toggle_play()
        self.control_panel.update_play_button(self.tracker.is_playing)
        self._refresh_status()
        if self.tracker.is_playing:
            self._update_loop()

    def _stop_tracking(self):
        if self.tracker.is_playing:
            self.tracker.stop()
            self.control_panel.update_play_button(False)
            self._refresh_status()

    def _update_loop(self):
        if self.tracker.is_playing:
            self._update_display()
            self.root.after(UPDATE_INTERVAL_MS, self._update_loop)

    def _update_display(self):
        result = self.tracker.compute_update(self.data.satellites, self.observer)
        if not result:
            return
        self.dashboard.update_values(result['data'])
        self.map_display.update_display(result['data'], result['trajectory'], result['multi'])

    # ============================================================
    # Location
    # ============================================================

    def _show_location_dialog(self):
        LocationDialog(self.root, self.theme, self.current_location, self._save_location)

    def _save_location(self, location):
        self.observer = Topos(latitude_degrees=location['lat'],
                              longitude_degrees=location['lon'])
        self.current_location = location['name']
        self.control_panel.update_location_label(self.current_location)

        # Persist
        self.prefs['observer_lat'] = location['lat']
        self.prefs['observer_lon'] = location['lon']
        self.prefs['observer_name'] = location['name']
        save_preferences(self.prefs)

        if self.tracker.current_sat:
            self._update_display()

    # ============================================================
    # Schedule
    # ============================================================

    def _show_schedule(self):
        if not self.tracker.current_sat:
            messagebox.showinfo("No Satellite", "Please select a satellite first.")
            return

        def calc_passes(days):
            tle = self.data.get_tle(self.tracker.current_sat)
            if not tle:
                return []
            return calculate_passes(tle, self.observer, days)

        ScheduleDialog(self.root, self.theme, self.tracker.current_sat,
                       self.current_location, calc_passes)

    # ============================================================
    # Theme
    # ============================================================

    def _on_theme_toggle(self, is_dark: bool):
        self.theme_name = 'dark' if is_dark else 'light'
        self.theme = THEMES[self.theme_name]
        self.prefs['theme'] = self.theme_name
        save_preferences(self.prefs)
        self._apply_theme()

    def _on_polar_toggle(self, is_polar: bool):
        self.map_display.set_polar_view(is_polar)
        if self.tracker.current_sat:
            self._update_display()

    def _apply_theme(self):
        t = self.theme
        self.root.configure(bg=T(t, 'bg_deeper'))
        for frame in (self.left_col, self.right_col, self.control_frame,
                      self.list_frame, self.dashboard_frame):
            frame.configure(bg=T(t, 'bg_deeper'))
        self.map_frame.configure(bg=T(t, 'card'), highlightbackground=T(t, 'card_border'))

        # Status bar
        self.status_bar.configure(bg=T(t, 'card'))
        for w in (self.status_count, self.status_tracking, self.status_age):
            w.configure(bg=T(t, 'card'))
        for s in (self.status_sep1, self.status_sep2):
            s.configure(bg=T(t, 'card_border'))

        # TTK styles
        self._setup_styles()

        # Components
        self.control_panel.update_theme(t)
        self.satellite_list.update_theme(t)
        self.dashboard.update_theme(t)
        self.map_display.update_theme(t)
        self._refresh_status()

    # ============================================================
    # Status Bar
    # ============================================================

    def _refresh_status(self):
        t = self.theme
        self.status_count.config(text=f"{self.data.satellite_count} satellites loaded")

        if self.tracker.is_playing and self.tracker.current_sat:
            n = len(self.tracker.tracked_sats)
            extra = f" (+{n})" if n > 0 else ""
            self.status_tracking.config(
                text=f"TRACKING: {self.tracker.current_sat}{extra}", fg=T(t, 'green'))
        elif self.tracker.current_sat:
            self.status_tracking.config(
                text=f"SELECTED: {self.tracker.current_sat}", fg=T(t, 'accent'))
        else:
            self.status_tracking.config(text="IDLE", fg=T(t, 'fg_muted'))

        age = self.data.data_age_hours
        if age is not None:
            if age < 1:
                self.status_age.config(text=f"Data: {int(age * 60)}m ago", fg=T(t, 'green'))
            elif age < STALE_DATA_HOURS:
                self.status_age.config(text=f"Data: {int(age)}h ago", fg=T(t, 'fg_muted'))
            else:
                self.status_age.config(text=f"Data: {int(age)}h ago (STALE)", fg=T(t, 'warning'))
        else:
            self.status_age.config(text="No data file", fg=T(t, 'error'))
