import logging
from typing import Dict, List, Tuple, Optional, Any

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patheffects as patheffects
from matplotlib.patches import Circle
from matplotlib.path import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature
import tkinter as tk

from utils.resource_utils import resource_path
from utils.theme import T

logger = logging.getLogger(__name__)


class MapDisplay:
    def __init__(self, parent_frame, theme: dict):
        self.parent_frame = parent_frame
        self.theme = theme
        self.is_polar_view = False
        self.canvas = None
        self.fig = None
        self.ax = None
        self.satellite_marker = None
        self.satellite_img = None
        self.satellite_box = None
        self._bg_img_cache = None
        self._multi_lines = []
        self._multi_markers = []
        self.setup_map()

    def setup_map(self):
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if hasattr(self, 'toolbar_frame') and self.toolbar_frame:
            self.toolbar_frame.destroy()
            self.toolbar_frame = None
        if hasattr(self, 'fig') and self.fig:
            plt.close(self.fig)

        self.satellite_marker = None
        self._multi_lines = []
        self._multi_markers = []

        t = self.theme
        self.fig = plt.Figure(figsize=(10, 6), dpi=100, facecolor=T(t, 'map_face'))
        self.fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)

        if self.is_polar_view:
            self._setup_polar_view()
        else:
            self._setup_regular_view()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.configure(highlightthickness=0)

        self.toolbar_frame = tk.Frame(self.parent_frame, bg=T(t, 'map_face'))
        self.toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        try:
            self.toolbar.config(background=T(t, 'map_face'))
            for child in self.toolbar.winfo_children():
                try:
                    child.configure(bg=T(t, 'map_face'))
                except tk.TclError:
                    pass
        except tk.TclError:
            pass
        self.toolbar.update()

        self._load_satellite_image()

    def _get_background_image(self):
        if self._bg_img_cache is None:
            self._bg_img_cache = plt.imread(resource_path('assets/nasa_light.jpg'))
        return self._bg_img_cache

    def _setup_regular_view(self):
        t = self.theme
        self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
        self.ax.set_global()

        bg_img = self._get_background_image()
        self.bg_img = self.ax.imshow(bg_img, extent=[-180, 180, -90, 90],
                                     transform=ccrs.PlateCarree())

        self.ax.coastlines(color=T(t, 'map_coast'), linewidth=0.6)
        self.ax.add_feature(cartopy.feature.BORDERS, edgecolor=T(t, 'map_border'), linewidth=0.4)

        gl = self.ax.gridlines(draw_labels=True, linewidth=0.3,
                               color=T(t, 'map_grid'), alpha=0.4, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 8, 'color': T(t, 'fg_muted')}
        gl.ylabel_style = {'size': 8, 'color': T(t, 'fg_muted')}

        self.title = self.ax.set_title("ORBITAL TRACKING DISPLAY",
                                       color=T(t, 'fg'), pad=12,
                                       fontsize=11, fontweight='bold', fontfamily='sans-serif')

        self.time_text = self.ax.text(
            0.01, 0.98, '', color=T(t, 'accent'), fontsize=9, fontweight='bold',
            fontfamily='monospace', transform=self.ax.transAxes, va='top',
            bbox=dict(facecolor=T(t, 'bg'), edgecolor=T(t, 'border'),
                      alpha=0.85, boxstyle='round,pad=0.4'))

        self._setup_common_elements()

    def _setup_polar_view(self):
        t = self.theme
        self.ax = self.fig.add_subplot(111, projection=ccrs.NorthPolarStereo())
        self.ax.set_extent([-180, 180, 30, 90], ccrs.PlateCarree())

        theta = np.linspace(0, 2 * np.pi, 100)
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T * 0.5 + [0.5, 0.5]
        self.ax.set_boundary(Path(verts), transform=self.ax.transAxes)

        for lat in [40, 50, 60, 70, 80]:
            self.ax.add_patch(plt.Circle((0, 0), radius=(90 - lat) / 60,
                                         transform=ccrs.PlateCarree(), facecolor='none',
                                         edgecolor=T(t, 'card_border'), linestyle='--', linewidth=0.4))

        label_style = dict(transform=self.ax.transAxes, color=T(t, 'fg_muted'),
                           fontsize=11, fontweight='bold', fontfamily='sans-serif')
        self.ax.text(0.5, 0.97, 'N', ha='center', va='bottom', **label_style)
        self.ax.text(0.5, 0.03, 'S', ha='center', va='top', **label_style)
        self.ax.text(0.97, 0.5, 'E', ha='left', va='center', **label_style)
        self.ax.text(0.03, 0.5, 'W', ha='right', va='center', **label_style)

        bg_img = self._get_background_image()
        self.bg_img = self.ax.imshow(bg_img, extent=[-180, 180, -90, 90],
                                     transform=ccrs.PlateCarree())

        self.ax.coastlines(color=T(t, 'map_coast'), linewidth=0.6)
        self.ax.add_feature(cartopy.feature.BORDERS, edgecolor=T(t, 'map_border'), linewidth=0.4)
        self.ax.gridlines(linewidth=0.3, color=T(t, 'map_grid'), alpha=0.3, linestyle='--')

        self.title = self.ax.set_title("POLAR ORBITAL DISPLAY",
                                       color=T(t, 'fg'), pad=12,
                                       fontsize=11, fontweight='bold', fontfamily='sans-serif')

        self.time_text = self.ax.text(
            0.05, 0.95, '', color=T(t, 'accent'), fontsize=9,
            transform=self.ax.transAxes, va='top',
            bbox=dict(facecolor=T(t, 'bg'), edgecolor=T(t, 'border'), alpha=0.85,
                      boxstyle='round,pad=0.4'))
        self.time_text.set_visible(False)

        self._setup_common_elements()

    def _setup_common_elements(self):
        t = self.theme
        self.trajectory_line, = self.ax.plot(
            [], [], color=T(t, 'trajectory'), linewidth=2.0, alpha=0.8,
            transform=ccrs.PlateCarree(),
            path_effects=[patheffects.withStroke(linewidth=3.5, foreground='#0e7490', alpha=0.3)])

        self.marker, = self.ax.plot(
            [], [], 'o', color=T(t, 'accent'), markersize=8,
            markeredgecolor='white', markeredgewidth=1.5,
            transform=ccrs.PlateCarree(), zorder=8)

        self.footprint = Circle(
            (0, 0), radius=0, facecolor=T(t, 'footprint'), alpha=0.08,
            edgecolor=T(t, 'footprint'), linewidth=1.5, linestyle='--',
            transform=ccrs.PlateCarree())
        self.ax.add_patch(self.footprint)

        self.position_text = self.ax.text(
            0, 0, '', color=T(t, 'fg'), fontsize=8, fontfamily='monospace',
            transform=ccrs.PlateCarree(),
            bbox=dict(facecolor=T(t, 'bg'), edgecolor=T(t, 'border'),
                      alpha=0.8, boxstyle='round,pad=0.3'))

    def _load_satellite_image(self):
        try:
            self.satellite_img = mpimg.imread(resource_path('assets/satellite.webp'))
            self.satellite_box = OffsetImage(self.satellite_img, zoom=0.1)
            self.satellite_marker = None
        except FileNotFoundError:
            logger.warning("satellite.webp not found, using circle marker")
            self.satellite_img = None

    def set_polar_view(self, is_polar: bool):
        if self.is_polar_view != is_polar:
            self.is_polar_view = is_polar
            self.setup_map()

    def update_theme(self, theme: dict):
        self.theme = theme
        self.setup_map()

    def update_display(self, data: Dict[str, Any], trajectory: List[Tuple[float, float]],
                       multi_data: Optional[List[Dict[str, Any]]] = None):
        if not data:
            return

        # Time
        if not self.is_polar_view:
            self.time_text.set_text(data['time'])

        # Primary trajectory
        if trajectory and len(trajectory) > 0:
            if self.is_polar_view:
                filtered = [(lon, lat) for lon, lat in trajectory if lat >= 30]
                if filtered:
                    lons, lats = zip(*filtered)
                    self.trajectory_line.set_data(lons, lats)
                else:
                    self.trajectory_line.set_data([], [])
            else:
                lons, lats = zip(*trajectory)
                self.trajectory_line.set_data(lons, lats)
        else:
            self.trajectory_line.set_data([], [])

        # Primary satellite marker
        if not self.is_polar_view or data['lat'] >= 30:
            self.footprint.set_center((data['lon'], data['lat']))
            self.footprint.set_radius(data['footprint_radius'])
            self.position_text.set_text(f"AZ {data['az']:.1f}   EL {data['el']:.1f}")
            self.position_text.set_position((data['lon'] + 5, data['lat']))

            if self.is_polar_view:
                self.marker.set_data([data['lon']], [data['lat']])
                self.marker.set_visible(True)
                if self.satellite_marker is not None:
                    self.satellite_marker.remove()
                    self.satellite_marker = None
            else:
                if self.satellite_img is not None:
                    if self.satellite_marker is not None:
                        self.satellite_marker.xybox = (data['lon'], data['lat'])
                        self.satellite_marker.xy = (data['lon'], data['lat'])
                    else:
                        self.satellite_marker = AnnotationBbox(
                            self.satellite_box, (data['lon'], data['lat']),
                            frameon=False, pad=0, zorder=10, transform=ccrs.PlateCarree())
                        self.ax.add_artist(self.satellite_marker)
                    self.marker.set_visible(False)
                else:
                    self.marker.set_data([data['lon']], [data['lat']])
                    self.marker.set_visible(True)
        else:
            self.marker.set_visible(False)
            if self.satellite_marker is not None:
                self.satellite_marker.remove()
                self.satellite_marker = None
            self.footprint.set_center((0, 0))
            self.footprint.set_radius(0)
            self.position_text.set_text("")

        # --- Multi-satellite overlays ---
        # Remove old multi-track artists
        for line in self._multi_lines:
            try:
                line.remove()
            except ValueError:
                pass
        for mkr in self._multi_markers:
            try:
                mkr.remove()
            except ValueError:
                pass
        self._multi_lines.clear()
        self._multi_markers.clear()

        if multi_data:
            for sat_info in multi_data:
                color = sat_info.get('color', '#ffffff')
                traj = sat_info.get('trajectory', [])
                lat = sat_info['lat']
                lon = sat_info['lon']

                # Skip if in polar view and below threshold
                if self.is_polar_view and lat < 30:
                    continue

                # Trajectory line
                if traj:
                    if self.is_polar_view:
                        traj = [(lo, la) for lo, la in traj if la >= 30]
                    if traj:
                        tlons, tlats = zip(*traj)
                        line, = self.ax.plot(tlons, tlats, color=color, linewidth=1.5,
                                             alpha=0.6, transform=ccrs.PlateCarree(),
                                             linestyle='--')
                        self._multi_lines.append(line)

                # Marker
                mkr, = self.ax.plot([lon], [lat], 'D', color=color, markersize=6,
                                     markeredgecolor='white', markeredgewidth=1,
                                     transform=ccrs.PlateCarree(), zorder=7)
                self._multi_markers.append(mkr)

                # Label
                label = self.ax.text(lon + 3, lat + 2,
                                     sat_info['name'][:20],
                                     color=color, fontsize=7, fontfamily='monospace',
                                     transform=ccrs.PlateCarree(),
                                     bbox=dict(facecolor=T(self.theme, 'bg'), alpha=0.7,
                                               edgecolor='none', boxstyle='round,pad=0.2'))
                self._multi_markers.append(label)

        self._safe_draw()

    def _safe_draw(self):
        """Draw canvas with error protection."""
        try:
            if self.canvas:
                self.canvas.draw_idle()
        except Exception as e:
            logger.debug("Canvas draw skipped: %s", e)

    def set_title(self, title_text: str):
        self.title.set_text(title_text)
        self._safe_draw()
