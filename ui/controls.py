import logging
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import csv
from typing import Callable, Dict, List, Optional

from config import (LOCATIONS, THEMES, MULTI_TRACK_COLORS)
from utils.theme import T

logger = logging.getLogger(__name__)


class ToggleSwitch(tk.Canvas):
    """A modern toggle switch widget."""

    def __init__(self, parent, theme: dict, command: Optional[Callable] = None,
                 initial: bool = False, width: int = 44, height: int = 22):
        super().__init__(parent, width=width, height=height,
                         bg=T(theme, 'card'), highlightthickness=0, cursor="hand2")
        self.theme = theme
        self.command = command
        self.state = initial
        self.w = width
        self.h = height
        self._draw()
        self.bind("<Button-1>", self._toggle)

    def _draw(self):
        self.delete("all")
        w, h = self.w, self.h
        r = h // 2
        if self.state:
            bg = T(self.theme, 'accent')
            knob_x = w - r
        else:
            bg = T(self.theme, 'border')
            knob_x = r
        # Track
        self.create_oval(0, 0, h, h, fill=bg, outline="")
        self.create_oval(w - h, 0, w, h, fill=bg, outline="")
        self.create_rectangle(r, 0, w - r, h, fill=bg, outline="")
        # Knob
        pad = 3
        self.create_oval(knob_x - r + pad, pad, knob_x + r - pad, h - pad,
                         fill="#ffffff", outline="")

    def _toggle(self, event=None):
        self.state = not self.state
        self._draw()
        if self.command:
            self.command(self.state)

    def set_state(self, state: bool):
        self.state = state
        self._draw()

    def update_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=T(theme, 'card'))
        self._draw()


class ModernButton(tk.Frame):
    """A modern styled button that fills its parent width."""

    def __init__(self, parent, text: str, theme: dict,
                 command: Optional[Callable] = None,
                 accent: bool = False, height: int = 38):
        super().__init__(parent, bg=T(theme, 'card'), height=height)
        self.pack_propagate(False)

        self.command = command
        self.text_str = text
        self.accent = accent
        self.theme = theme

        self._normal_bg = T(theme, 'accent') if accent else T(theme, 'card_hover')
        self._hover_bg = T(theme, 'accent_hover') if accent else T(theme, 'border')
        self._fg = T(theme, 'bg') if accent else T(theme, 'fg')

        self._label = tk.Label(
            self, text=text,
            font=("SF Pro Display", 10, "bold"),
            fg=self._fg, bg=self._normal_bg,
            cursor="hand2", pady=6,
        )
        self._label.pack(fill=tk.BOTH, expand=True)

        for widget in (self, self._label):
            widget.bind("<Enter>", lambda e: self._label.config(bg=self._hover_bg))
            widget.bind("<Leave>", lambda e: self._label.config(bg=self._normal_bg))
            widget.bind("<Button-1>", self._on_click)

    def _on_click(self, event):
        if self.command:
            self.command()

    def set_text(self, text: str):
        self.text_str = text
        self._label.config(text=text)

    def update_theme(self, theme: dict):
        self.theme = theme
        self._normal_bg = T(theme, 'accent') if self.accent else T(theme, 'card_hover')
        self._hover_bg = T(theme, 'accent_hover') if self.accent else T(theme, 'border')
        self._fg = T(theme, 'bg') if self.accent else T(theme, 'fg')
        self.configure(bg=T(theme, 'card'))
        self._label.config(fg=self._fg, bg=self._normal_bg)


class SearchableSatelliteList:
    def __init__(self, parent_frame, theme: dict, on_select_callback: Callable,
                 on_multi_select_callback: Optional[Callable] = None):
        self.parent_frame = parent_frame
        self.theme = theme
        self.on_select_callback = on_select_callback
        self.on_multi_select_callback = on_multi_select_callback
        self.satellites: Dict = {}
        self._search_after_id = None
        self._tracked_sats: List[str] = []
        self.create_list()

    def create_list(self):
        """Create satellite list with search and multi-track buttons."""
        t = self.theme
        self.container = tk.Frame(self.parent_frame, bg=T(t, 'card'),
                                  highlightbackground=T(t, 'card_border'),
                                  highlightthickness=1)
        self.container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Header
        header = tk.Frame(self.container, bg=T(t, 'card'))
        header.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(header, text="SATELLITES", font=("SF Pro Display", 11, "bold"),
                 fg=T(t, 'accent'), bg=T(t, 'card')).pack(side=tk.LEFT)
        self.count_label = tk.Label(header, text="0", font=("SF Pro Display", 9),
                                    fg=T(t, 'fg_muted'), bg=T(t, 'card'))
        self.count_label.pack(side=tk.RIGHT)

        # Search bar
        search_frame = tk.Frame(self.container, bg=T(t, 'card'))
        search_frame.pack(fill=tk.X, padx=10, pady=(4, 6))

        self._placeholder = "Search satellites..."
        self._placeholder_active = True
        self.search_entry = tk.Entry(search_frame, bg=T(t, 'bg_deeper'),
                                     fg=T(t, 'fg_muted'),
                                     insertbackground=T(t, 'accent'),
                                     font=("SF Pro Display", 10), relief=tk.FLAT,
                                     highlightbackground=T(t, 'card_border'),
                                     highlightthickness=1)
        self.search_entry.insert(0, self._placeholder)
        self.search_entry.pack(fill=tk.X, ipady=6)

        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        tk.Frame(self.container, bg=T(t, 'card_border'), height=1).pack(fill=tk.X, padx=10)

        # Tracked satellites display
        self.tracked_frame = tk.Frame(self.container, bg=T(t, 'card'))
        self.tracked_frame.pack(fill=tk.X, padx=10, pady=(4, 0))

        # Listbox
        list_frame = tk.Frame(self.container, bg=T(t, 'card'))
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 10))

        self.sat_list = tk.Listbox(
            list_frame, bg=T(t, 'bg_deeper'), fg=T(t, 'fg'),
            selectbackground=T(t, 'accent'), selectforeground=T(t, 'bg'),
            activestyle='none', font=("SF Mono", 10), relief=tk.FLAT,
            highlightthickness=0, borderwidth=0,
        )

        scrollbar = tk.Scrollbar(list_frame, command=self.sat_list.yview,
                                 bg=T(t, 'card'), troughcolor=T(t, 'bg_deeper'))
        self.sat_list.config(yscrollcommand=scrollbar.set)
        self.sat_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sat_list.bind('<<ListboxSelect>>', self._on_sat_select)
        self.sat_list.bind('<Double-Button-1>', self._on_double_click)

    def populate_list(self, satellites: Dict):
        self.satellites = satellites
        self._tracked_sats.clear()
        self._update_tracked_display()
        self._update_listbox()

    def _on_search_focus_in(self, event=None):
        if self._placeholder_active:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=T(self.theme, 'fg'))
            self._placeholder_active = False

    def _on_search_focus_out(self, event=None):
        if not self.search_entry.get():
            self._placeholder_active = True
            self.search_entry.insert(0, self._placeholder)
            self.search_entry.config(fg=T(self.theme, 'fg_muted'))

    def _on_search_changed(self, *args):
        if self._placeholder_active:
            return
        if self._search_after_id:
            self.parent_frame.after_cancel(self._search_after_id)
        self._search_after_id = self.parent_frame.after(200, self._update_listbox)

    def _update_listbox(self):
        if self._placeholder_active:
            search_term = ""
        else:
            search_term = self.search_entry.get().lower().strip()
        self.sat_list.delete(0, tk.END)
        filtered = sorted(
            name for name in self.satellites.keys()
            if not search_term or search_term in name.lower()
        )
        for sat in filtered:
            self.sat_list.insert(tk.END, sat)
        self.count_label.config(text=f"{len(filtered)} / {len(self.satellites)}")

    def _on_sat_select(self, event=None):
        if selection := self.sat_list.curselection():
            selected_sat = self.sat_list.get(selection[0])
            self.on_select_callback(selected_sat)

    def _on_double_click(self, event=None):
        """Double-click to add/remove from multi-track list."""
        if not self.on_multi_select_callback:
            return
        if selection := self.sat_list.curselection():
            sat_name = self.sat_list.get(selection[0])
            if sat_name in self._tracked_sats:
                self._tracked_sats.remove(sat_name)
            elif len(self._tracked_sats) < 5:
                self._tracked_sats.append(sat_name)
            self._update_tracked_display()
            self.on_multi_select_callback(self._tracked_sats)

    def _update_tracked_display(self):
        for w in self.tracked_frame.winfo_children():
            w.destroy()

        if not self._tracked_sats:
            tk.Label(self.tracked_frame, text="Double-click to add/remove tracking",
                     font=("SF Pro Display", 8), fg=T(self.theme, 'fg_muted'),
                     bg=T(self.theme, 'card')).pack(anchor='w')
            return

        for i, name in enumerate(self._tracked_sats):
            color = MULTI_TRACK_COLORS[i % len(MULTI_TRACK_COLORS)]
            row = tk.Frame(self.tracked_frame, bg=T(self.theme, 'card'))
            row.pack(fill=tk.X, pady=1)
            # Color dot
            dot = tk.Canvas(row, width=10, height=10, bg=T(self.theme, 'card'),
                            highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=color, outline="")
            dot.pack(side=tk.LEFT, padx=(0, 4))
            # Name (truncated)
            display_name = name[:25] + "..." if len(name) > 25 else name
            tk.Label(row, text=display_name, font=("SF Mono", 8),
                     fg=color, bg=T(self.theme, 'card')).pack(side=tk.LEFT)
            # Remove button
            rm = tk.Label(row, text="x", font=("SF Pro Display", 8, "bold"),
                          fg=T(self.theme, 'fg_muted'), bg=T(self.theme, 'card'),
                          cursor="hand2")
            rm.pack(side=tk.RIGHT)
            rm.bind("<Button-1>", lambda e, n=name: self._remove_tracked(n))

    def _remove_tracked(self, name: str):
        if name in self._tracked_sats:
            self._tracked_sats.remove(name)
            self._update_tracked_display()
            if self.on_multi_select_callback:
                self.on_multi_select_callback(self._tracked_sats)

    def get_tracked(self) -> List[str]:
        return self._tracked_sats.copy()

    def update_theme(self, theme: dict):
        self.theme = theme
        self.container.config(bg=T(theme, 'card'), highlightbackground=T(theme, 'card_border'))
        self.search_entry.config(bg=T(theme, 'bg_deeper'), fg=T(theme, 'fg'),
                                 insertbackground=T(theme, 'accent'),
                                 highlightbackground=T(theme, 'card_border'))
        self.sat_list.config(bg=T(theme, 'bg_deeper'), fg=T(theme, 'fg'),
                             selectbackground=T(theme, 'accent'), selectforeground=T(theme, 'bg'))
        self.count_label.config(fg=T(theme, 'fg_muted'), bg=T(theme, 'card'))
        # Update all child frames and labels inside container
        self._theme_children(self.container, theme)
        self._update_tracked_display()

    def _theme_children(self, parent, theme: dict):
        """Recursively update bg color of inner frames/labels."""
        for child in parent.winfo_children():
            if child in (self.search_entry, self.sat_list):
                continue  # Already handled
            try:
                if isinstance(child, tk.Frame):
                    # Separators are 1px height frames — use border color
                    if child.winfo_reqheight() <= 2:
                        child.config(bg=T(theme, 'card_border'))
                    else:
                        child.config(bg=T(theme, 'card'))
                elif isinstance(child, tk.Label):
                    child.config(bg=T(theme, 'card'))
                elif isinstance(child, tk.Scrollbar):
                    child.config(bg=T(theme, 'card'), troughcolor=T(theme, 'bg_deeper'))
            except tk.TclError:
                pass
            self._theme_children(child, theme)


class ControlPanel:
    def __init__(self, parent_frame, theme: dict, callbacks: Dict[str, Callable]):
        self.parent_frame = parent_frame
        self.theme = theme
        self.callbacks = callbacks
        self.widgets = []  # Track widgets for theme updates
        self.create_controls()
        self.create_location_panel()

    def create_controls(self):
        t = self.theme

        # ---- Play/Pause section ----
        play_container = tk.Frame(self.parent_frame, bg=T(t, 'card'),
                                  highlightbackground=T(t, 'card_border'), highlightthickness=1)
        play_container.pack(fill=tk.X, padx=4, pady=(4, 2))
        self.widgets.append(('card_container', play_container))

        self.play_btn = ModernButton(play_container, "START LIVE TRACKING", t,
                                     command=self.callbacks.get('toggle_play'), accent=True)
        self.play_btn.pack(fill=tk.X, padx=10, pady=10)
        self.widgets.append(('button', self.play_btn))

        # ---- Settings section ----
        settings_container = tk.Frame(self.parent_frame, bg=T(t, 'card'),
                                      highlightbackground=T(t, 'card_border'), highlightthickness=1)
        settings_container.pack(fill=tk.X, padx=4, pady=2)
        self.widgets.append(('card_container', settings_container))

        # Dark/Light toggle row
        self.theme_row = tk.Frame(settings_container, bg=T(t, 'card'))
        self.theme_row.pack(fill=tk.X, padx=10, pady=(10, 4))
        self.widgets.append(('inner_frame', self.theme_row))
        self.theme_label = tk.Label(self.theme_row, text="Dark Mode", font=("SF Pro Display", 10),
                                    fg=T(t, 'fg'), bg=T(t, 'card'))
        self.theme_label.pack(side=tk.LEFT)
        self.theme_toggle = ToggleSwitch(self.theme_row, t,
                                         command=self.callbacks.get('toggle_mode'),
                                         initial=True)
        self.theme_toggle.pack(side=tk.RIGHT)

        # Polar view toggle row
        self.polar_row = tk.Frame(settings_container, bg=T(t, 'card'))
        self.polar_row.pack(fill=tk.X, padx=10, pady=4)
        self.widgets.append(('inner_frame', self.polar_row))
        self.polar_label = tk.Label(self.polar_row, text="Polar View", font=("SF Pro Display", 10),
                                    fg=T(t, 'fg'), bg=T(t, 'card'))
        self.polar_label.pack(side=tk.LEFT)
        self.polar_toggle = ToggleSwitch(self.polar_row, t,
                                         command=self.callbacks.get('toggle_view'),
                                         initial=False)
        self.polar_toggle.pack(side=tk.RIGHT)

        # Propagator selector
        self.prop_sep = tk.Frame(settings_container, bg=T(t, 'card_border'), height=1)
        self.prop_sep.pack(fill=tk.X, padx=10, pady=4)

        self.prop_row = tk.Frame(settings_container, bg=T(t, 'card'))
        self.prop_row.pack(fill=tk.X, padx=10, pady=4)
        self.widgets.append(('inner_frame', self.prop_row))

        self.prop_label = tk.Label(self.prop_row, text="Propagator", font=("SF Pro Display", 10),
                                   fg=T(t, 'fg'), bg=T(t, 'card'))
        self.prop_label.pack(side=tk.LEFT)

        self.prop_var = tk.StringVar(value="SGP4")
        self.prop_combo = ttk.Combobox(self.prop_row, textvariable=self.prop_var,
                                       values=["SGP4", "Numerical"], state="readonly",
                                       width=10, font=("SF Pro Display", 9))
        self.prop_combo.pack(side=tk.RIGHT)
        self.prop_combo.bind("<<ComboboxSelected>>", self._on_propagator_changed)

        # Force model selector (shown only when Numerical selected)
        self.force_row = tk.Frame(settings_container, bg=T(t, 'card'))
        self.widgets.append(('inner_frame', self.force_row))

        self.force_label = tk.Label(self.force_row, text="Force Model", font=("SF Pro Display", 10),
                                    fg=T(t, 'fg'), bg=T(t, 'card'))
        self.force_label.pack(side=tk.LEFT)

        self.force_var = tk.StringVar(value="standard")
        self.force_combo = ttk.Combobox(self.force_row, textvariable=self.force_var,
                                        values=["basic", "standard", "high_fidelity"],
                                        state="readonly", width=12, font=("SF Pro Display", 9))
        self.force_combo.pack(side=tk.RIGHT)
        self.force_combo.bind("<<ComboboxSelected>>", self._on_propagator_changed)
        # Hidden by default (SGP4 doesn't need force model)

        # Force model description
        self.force_desc = tk.Label(settings_container, text="",
                                   font=("SF Pro Display", 8), fg=T(t, 'fg_muted'),
                                   bg=T(t, 'card'), wraplength=230, justify=tk.LEFT)
        self.widgets.append(('inner_frame', self.force_desc.master))

        self.settings_sep = tk.Frame(settings_container, bg=T(t, 'card_border'), height=1)
        self.settings_sep.pack(fill=tk.X, padx=10, pady=4)

        # Action buttons
        self.btn_frame = tk.Frame(settings_container, bg=T(t, 'card'))
        self.btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.widgets.append(('inner_frame', self.btn_frame))

        self.schedule_btn = ModernButton(self.btn_frame, "PASS SCHEDULE", t,
                                         command=self.callbacks.get('show_schedule'))
        self.schedule_btn.pack(fill=tk.X, pady=2)
        self.widgets.append(('button', self.schedule_btn))

        self.update_btn = ModernButton(self.btn_frame, "UPDATE DATA", t,
                                       command=self.callbacks.get('update_data'))
        self.update_btn.pack(fill=tk.X, pady=2)
        self.widgets.append(('button', self.update_btn))

    def create_location_panel(self):
        t = self.theme
        container = tk.Frame(self.parent_frame, bg=T(t, 'card'),
                             highlightbackground=T(t, 'card_border'), highlightthickness=1)
        container.pack(fill=tk.X, padx=4, pady=(2, 4))
        self.widgets.append(('card_container', container))

        self.loc_header = tk.Frame(container, bg=T(t, 'card'))
        self.loc_header.pack(fill=tk.X, padx=10, pady=(10, 4))
        self.widgets.append(('inner_frame', self.loc_header))
        self.obs_label = tk.Label(self.loc_header, text="OBSERVER",
                                  font=("SF Pro Display", 11, "bold"),
                                  fg=T(t, 'accent'), bg=T(t, 'card'))
        self.obs_label.pack(side=tk.LEFT)

        self.loc_sep = tk.Frame(container, bg=T(t, 'card_border'), height=1)
        self.loc_sep.pack(fill=tk.X, padx=10)

        self.loc_body = tk.Frame(container, bg=T(t, 'card'))
        self.loc_body.pack(fill=tk.X, padx=10, pady=8)
        self.widgets.append(('inner_frame', self.loc_body))

        self.location_label = tk.Label(self.loc_body, text="", font=("SF Pro Display", 9),
                                       fg=T(t, 'fg'), bg=T(t, 'card'), wraplength=220,
                                       justify=tk.LEFT)
        self.location_label.pack(fill=tk.X, pady=(0, 6))

        self.loc_btn = ModernButton(self.loc_body, "SELECT LOCATION", t,
                                    command=self.callbacks.get('show_location'))
        self.loc_btn.pack(fill=tk.X, pady=2)
        self.widgets.append(('button', self.loc_btn))

    def _on_propagator_changed(self, event=None):
        """Handle propagator or force model selection change."""
        prop_name = self.prop_var.get()
        force_name = self.force_var.get()

        PRESET_INFO = {
            'basic': "J2 gravity + atmospheric drag\nFast, ~1-5 km accuracy",
            'standard': "J2, J3 gravity + atmospheric drag\nGood balance of speed and accuracy",
            'high_fidelity': "J2-J6 gravity, drag, solar radiation,\nMoon & Sun perturbations (~10-100m accuracy)",
        }

        if prop_name == "Numerical":
            self.force_row.pack(fill=tk.X, padx=10, pady=2)
            self.force_desc.config(text=PRESET_INFO.get(force_name, ""))
            self.force_desc.pack(fill=tk.X, padx=10, pady=(0, 4))
        else:
            self.force_row.pack_forget()
            self.force_desc.pack_forget()
            self.force_desc.config(text="")

        if self.callbacks.get('set_propagator'):
            self.callbacks['set_propagator'](prop_name, force_name)

    def update_play_button(self, is_playing: bool):
        self.play_btn.set_text("PAUSE TRACKING" if is_playing else "START LIVE TRACKING")

    def update_location_label(self, location_text: str):
        self.location_label.config(text=location_text)

    def update_theme(self, theme: dict):
        self.theme = theme
        for kind, widget in self.widgets:
            if kind == 'card_container':
                widget.config(bg=T(theme, 'card'), highlightbackground=T(theme, 'card_border'))
            elif kind == 'inner_frame':
                widget.config(bg=T(theme, 'card'))
            elif kind == 'button':
                widget.update_theme(theme)
        # Separators
        for sep in (self.settings_sep, self.loc_sep, self.prop_sep):
            sep.config(bg=T(theme, 'card_border'))
        # Labels
        for label in (self.theme_label, self.polar_label, self.location_label,
                      self.prop_label, self.force_label, self.force_desc):
            label.config(fg=T(theme, 'fg'), bg=T(theme, 'card'))
        self.obs_label.config(fg=T(theme, 'accent'), bg=T(theme, 'card'))
        self.force_desc.config(fg=T(theme, 'fg_muted'))
        # Toggles
        self.theme_toggle.update_theme(theme)
        self.polar_toggle.update_theme(theme)


class LocationDialog:
    """Dialog for selecting observer location."""

    def __init__(self, parent, theme: dict, current_location: str, on_save_callback: Callable):
        self.parent = parent
        self.theme = theme
        self.on_save_callback = on_save_callback
        self.show_dialog()

    def show_dialog(self):
        t = self.theme
        dialog = tk.Toplevel(self.parent)
        self.dialog = dialog
        dialog.title("Select Observer Location")
        dialog.configure(bg=T(t, 'bg'))
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        dialog.geometry("400x320")
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 400) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 320) // 2
        dialog.geometry(f"+{x}+{y}")

        main = tk.Frame(dialog, bg=T(t, 'card'), highlightbackground=T(t, 'card_border'),
                        highlightthickness=1)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(main, text="OBSERVER LOCATION", font=("SF Pro Display", 12, "bold"),
                 fg=T(t, 'accent'), bg=T(t, 'card')).pack(pady=(12, 4))
        tk.Frame(main, bg=T(t, 'card_border'), height=1).pack(fill=tk.X, padx=16, pady=(0, 10))

        form = tk.Frame(main, bg=T(t, 'card'))
        form.pack(fill=tk.X, padx=16)

        tk.Label(form, text="Preset Location", font=("SF Pro Display", 9),
                 fg=T(t, 'fg_muted'), bg=T(t, 'card')).pack(anchor='w')
        self.location_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.location_var,
                     values=sorted(LOCATIONS.keys()), state="readonly",
                     font=("SF Pro Display", 10)).pack(fill=tk.X, pady=(2, 10))

        tk.Label(form, text="- OR ENTER CUSTOM -", font=("SF Pro Display", 8),
                 fg=T(t, 'fg_muted'), bg=T(t, 'card')).pack(pady=(0, 6))

        coord_frame = tk.Frame(form, bg=T(t, 'card'))
        coord_frame.pack(fill=tk.X)

        lat_frame = tk.Frame(coord_frame, bg=T(t, 'card'))
        lat_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        tk.Label(lat_frame, text="Latitude (-90 to 90)", font=("SF Pro Display", 9),
                 fg=T(t, 'fg_muted'), bg=T(t, 'card')).pack(anchor='w')
        self.custom_lat_var = tk.StringVar()
        tk.Entry(lat_frame, textvariable=self.custom_lat_var, bg=T(t, 'bg_deeper'),
                 fg=T(t, 'fg'), insertbackground=T(t, 'accent'), relief=tk.FLAT,
                 font=("SF Mono", 10), highlightbackground=T(t, 'card_border'),
                 highlightthickness=1).pack(fill=tk.X, ipady=4)

        lon_frame = tk.Frame(coord_frame, bg=T(t, 'card'))
        lon_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))
        tk.Label(lon_frame, text="Longitude (-180 to 180)", font=("SF Pro Display", 9),
                 fg=T(t, 'fg_muted'), bg=T(t, 'card')).pack(anchor='w')
        self.custom_lon_var = tk.StringVar()
        tk.Entry(lon_frame, textvariable=self.custom_lon_var, bg=T(t, 'bg_deeper'),
                 fg=T(t, 'fg'), insertbackground=T(t, 'accent'), relief=tk.FLAT,
                 font=("SF Mono", 10), highlightbackground=T(t, 'card_border'),
                 highlightthickness=1).pack(fill=tk.X, ipady=4)

        btn_frame = tk.Frame(main, bg=T(t, 'card'))
        btn_frame.pack(fill=tk.X, padx=16, pady=(14, 12))

        ModernButton(btn_frame, "CONFIRM", t, command=self.save_location,
                     accent=True, height=34).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ModernButton(btn_frame, "CANCEL", t, command=dialog.destroy,
                     height=34).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

    def _format_location(self, lat: float, lon: float) -> str:
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'
        return f"{abs(lat):.4f} {lat_dir}, {abs(lon):.4f} {lon_dir}"

    def save_location(self):
        custom_lat = self.custom_lat_var.get().strip()
        custom_lon = self.custom_lon_var.get().strip()

        if custom_lat and custom_lon:
            try:
                lat, lon = float(custom_lat), float(custom_lon)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    messagebox.showerror("Invalid Range",
                                         "Latitude: -90 to 90\nLongitude: -180 to 180",
                                         parent=self.dialog)
                    return
                location = {
                    'name': f"Custom ({self._format_location(lat, lon)})",
                    'lat': lat, 'lon': lon,
                }
                self.dialog.destroy()
                self.on_save_callback(location)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers.",
                                     parent=self.dialog)
        else:
            selected = self.location_var.get()
            if selected and selected in LOCATIONS:
                lat, lon = LOCATIONS[selected]
                location = {
                    'name': f"{selected} ({self._format_location(lat, lon)})",
                    'lat': lat, 'lon': lon,
                }
                self.dialog.destroy()
                self.on_save_callback(location)
            else:
                messagebox.showwarning("No Selection", "Select a location or enter coordinates.",
                                       parent=self.dialog)


class ScheduleDialog:
    """Dialog for satellite pass schedule."""

    def __init__(self, parent, theme: dict, satellite_name: str, location_name: str,
                 calculate_passes_func: Callable):
        self.parent = parent
        self.theme = theme
        self.satellite_name = satellite_name
        self.location_name = location_name
        self.calculate_passes_func = calculate_passes_func
        self.show_dialog()

    def show_dialog(self):
        if not self.satellite_name:
            messagebox.showinfo("No Satellite", "Please select a satellite first.")
            return

        t = self.theme
        win = tk.Toplevel(self.parent)
        self.win = win
        win.title(f"Pass Schedule - {self.satellite_name}")
        win.configure(bg=T(t, 'bg'))
        win.geometry("900x550")
        win.transient(self.parent)

        main = tk.Frame(win, bg=T(t, 'card'), highlightbackground=T(t, 'card_border'),
                        highlightthickness=1)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header = tk.Frame(main, bg=T(t, 'card'))
        header.pack(fill=tk.X, padx=14, pady=(12, 4))
        tk.Label(header, text="PASS SCHEDULE", font=("SF Pro Display", 13, "bold"),
                 fg=T(t, 'accent'), bg=T(t, 'card')).pack(side=tk.LEFT)

        info = tk.Frame(main, bg=T(t, 'card'))
        info.pack(fill=tk.X, padx=14)
        tk.Label(info, text=f"Satellite: {self.satellite_name}   |   Observer: {self.location_name}",
                 font=("SF Pro Display", 9), fg=T(t, 'fg_muted'), bg=T(t, 'card')).pack(side=tk.LEFT)

        tk.Frame(main, bg=T(t, 'card_border'), height=1).pack(fill=tk.X, padx=14, pady=(6, 0))

        ctrl = tk.Frame(main, bg=T(t, 'card'))
        ctrl.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(ctrl, text="Days:", font=("SF Pro Display", 10),
                 fg=T(t, 'fg'), bg=T(t, 'card')).pack(side=tk.LEFT)
        self.days_var = tk.StringVar(value="7")
        ttk.Combobox(ctrl, textvariable=self.days_var, values=["1", "3", "7", "14", "30"],
                     width=5, state="readonly", font=("SF Pro Display", 10)).pack(side=tk.LEFT, padx=6)

        calc_btn = ModernButton(ctrl, "CALCULATE", t, command=self._threaded_calculate,
                               accent=True, height=30)
        calc_btn.configure(width=120)
        calc_btn.pack(side=tk.LEFT, padx=6)

        self.export_btn = ModernButton(ctrl, "EXPORT CSV", t, command=None, height=30)
        self.export_btn.configure(width=120)

        self.status_label = tk.Label(ctrl, text="", font=("SF Pro Display", 9),
                                     fg=T(t, 'fg_muted'), bg=T(t, 'card'))
        self.status_label.pack(side=tk.RIGHT)

        self.tree_frame = tk.Frame(main, bg=T(t, 'card'))
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 12))

        self._threaded_calculate()

    def _threaded_calculate(self):
        try:
            days = float(self.days_var.get())
            if days <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid", "Enter a positive number of days.", parent=self.win)
            return

        self.status_label.config(text="Calculating...", fg=T(self.theme, 'warning'))
        self.win.update_idletasks()

        def _calc():
            passes = self.calculate_passes_func(days)
            self.win.after(0, lambda: self._display_results(passes, days))

        threading.Thread(target=_calc, daemon=True).start()

    def _display_results(self, passes: List, days: float):
        t = self.theme
        self.status_label.config(text="")

        for widget in self.tree_frame.winfo_children():
            widget.destroy()

        if not passes:
            tk.Label(self.tree_frame, text=f"No visible passes found in the next {int(days)} days.",
                     font=("SF Pro Display", 11), fg=T(t, 'fg_muted'), bg=T(t, 'card')).pack(pady=30)
            self.export_btn.pack_forget()
            return

        self.status_label.config(text=f"{len(passes)} passes found", fg=T(t, 'green'))

        style = ttk.Style()
        style.configure("Schedule.Treeview",
                        background=T(t, 'bg_deeper'), foreground=T(t, 'fg'),
                        fieldbackground=T(t, 'bg_deeper'), font=("SF Mono", 9), rowheight=26)
        style.configure("Schedule.Treeview.Heading",
                        background=T(t, 'card'), foreground=T(t, 'accent'),
                        font=("SF Pro Display", 9, "bold"))
        style.map("Schedule.Treeview",
                  background=[("selected", T(t, 'accent'))],
                  foreground=[("selected", T(t, 'bg'))])

        columns = ('Rise Time', 'Rise Az', 'Max El', 'Culminate', 'Culm Az',
                   'Set Time', 'Set Az', 'Duration')
        tree = ttk.Treeview(self.tree_frame, columns=columns, show='headings',
                            height=14, style="Schedule.Treeview")

        headings = {
            'Rise Time': ('Rise Time (UTC)', 145), 'Rise Az': ('Az', 50),
            'Max El': ('Max El', 55), 'Culminate': ('Culminate (UTC)', 145),
            'Culm Az': ('Az', 50), 'Set Time': ('Set Time (UTC)', 145),
            'Set Az': ('Az', 50), 'Duration': ('Dur (min)', 65),
        }

        for col, (heading, width) in headings.items():
            tree.heading(col, text=heading)
            tree.column(col, width=width, minwidth=40)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for p in passes:
            tree.insert('', tk.END, values=(
                p['rise_time'], f"{p['rise_az']}", f"{p.get('culm_alt', '-')}",
                p['culminate_time'], f"{p['culm_az']}",
                p['set_time'], f"{p['set_az']}", p['duration'],
            ))

        self.export_btn.command = lambda: self._export(passes)
        self.export_btn.pack(side=tk.RIGHT, padx=6)

    def _export(self, passes: List):
        safe_name = re.sub(r'[^\w\s\-.]', '', self.satellite_name).strip() or "satellite"
        filename = f"{safe_name}_schedule.csv"
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Rise Time (UTC)', 'Rise Az', 'Max Elevation',
                                 'Culminate Time (UTC)', 'Culm Az',
                                 'Set Time (UTC)', 'Set Az', 'Duration (min)'])
                for p in passes:
                    writer.writerow([p['rise_time'], p['rise_az'], p.get('culm_alt', ''),
                                     p['culminate_time'], p['culm_az'],
                                     p['set_time'], p['set_az'], p['duration']])
            messagebox.showinfo("Exported", f"Saved to:\n{os.path.abspath(filename)}", parent=self.win)
        except OSError as e:
            messagebox.showerror("Export Failed", f"Could not save file:\n{e}", parent=self.win)
