import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patheffects as patheffects
from matplotlib.patches import Circle
from matplotlib.path import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import numpy as np
import cartopy.crs as ccrs
import tkinter as tk
import cartopy.feature
from config import (DARK_BG, FG_COLOR, ACCENT_COLOR, TRAJECTORY_COLOR,
                    BORDER_COLOR, GROUND_CIRCLE, CARD_BG)
from utils.resource_utils import resource_path



class MapDisplay:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.is_polar_view = False
        self.dark_mode = True
        self.canvas = None
        self.fig = None
        self.ax = None
        self.satellite_marker = None
        self.satellite_img = None
        self.setup_map()

    def setup_map(self):
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()

        if hasattr(self, 'toolbar_frame') and self.toolbar_frame:
            self.toolbar_frame.destroy()

        self.fig = plt.Figure(figsize=(10, 6), dpi=100, facecolor=DARK_BG)

        if self.is_polar_view:
            self._setup_polar_view()
        else:
            self._setup_regular_view()

        # Create canvas with navigation toolbar for zooming/panning
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Add toolbar for zooming and panning
        self.toolbar_frame = tk.Frame(self.parent_frame)
        self.toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.config(background=DARK_BG)
        self.toolbar.update()

        # Connect events
        self.canvas.mpl_connect('draw_event', self.on_draw)

        # Load satellite image
        self._load_satellite_image()

    def _setup_regular_view(self):
        """Set up regular (non-polar) map view"""
        self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
        self.ax.set_global()

        # Add background image
        self.dark_img = plt.imread(resource_path('assets/nasa_light.jpg'))
        self.bg_img = self.ax.imshow(self.dark_img,
                                     extent=[-180, 180, -90, 90],
                                     transform=ccrs.PlateCarree())

        # Add borders and coastlines
        self.ax.coastlines(color=BORDER_COLOR, linewidth=0.8)

        # Add country borders
        self.ax.add_feature(cartopy.feature.BORDERS, edgecolor=BORDER_COLOR, linewidth=0.6)

        # Add grid lines with custom styling
        gl = self.ax.gridlines(draw_labels=True, linewidth=0.5, color=BORDER_COLOR, alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False

        self.title = self.ax.set_title("ORBITAL TRACKING DISPLAY", color=FG_COLOR, pad=20)

        self.time_text = self.ax.text(0.05, 0.95, '',
                                      color=FG_COLOR,
                                      fontsize=10,
                                      transform=self.ax.transAxes,
                                      va='top',
                                      bbox=dict(facecolor=DARK_BG, edgecolor=BORDER_COLOR, alpha=0.7))

        self._setup_common_elements()

    def _setup_polar_view(self):
        """Set up polar projection view"""
        self.ax = self.fig.add_subplot(111, projection=ccrs.NorthPolarStereo())
        self.ax.set_extent([-180, 180, 30, 90], ccrs.PlateCarree())

        # Set circular boundary
        theta = np.linspace(0, 2 * np.pi, 100)
        center = [0.5, 0.5]
        radius = 0.5
        verts = np.vstack([np.sin(theta), np.cos(theta)]).T * radius + center
        boundary_path = Path(verts)
        self.ax.set_boundary(boundary_path, transform=self.ax.transAxes)

        # Add circular gridlines (latitude circles)
        for lat in [40, 50, 60, 70, 80]:
            circle = plt.Circle((0, 0), radius=(90 - lat) / 60, transform=ccrs.PlateCarree(),
                                facecolor='none', edgecolor=CARD_BG, linestyle='--', linewidth=0.5)
            self.ax.add_patch(circle)

        # Add fixed NSEW labels
        self.ax.text(0.5, 0.98, 'N', transform=self.ax.transAxes, ha='center', va='bottom',
                     color=FG_COLOR, fontsize=12, fontweight='bold')
        self.ax.text(0.5, 0.02, 'S', transform=self.ax.transAxes, ha='center', va='top',
                     color=FG_COLOR, fontsize=12, fontweight='bold')
        self.ax.text(0.98, 0.5, 'E', transform=self.ax.transAxes, ha='left', va='center',
                     color=FG_COLOR, fontsize=12, fontweight='bold')
        self.ax.text(0.02, 0.5, 'W', transform=self.ax.transAxes, ha='right', va='center',
                     color=FG_COLOR, fontsize=12, fontweight='bold')

        # Set up background and other features
        self.dark_img = plt.imread(resource_path('assets/nasa_light.jpg'))
        self.bg_img = self.ax.imshow(self.dark_img,
                                     extent=[-180, 180, -90, 90],
                                     transform=ccrs.PlateCarree())

        # Add coastlines and borders
        self.ax.coastlines(color=BORDER_COLOR, linewidth=0.8)
        self.ax.add_feature(cartopy.feature.BORDERS, edgecolor=BORDER_COLOR, linewidth=0.6)

        # Add gridlines
        gl = self.ax.gridlines(linewidth=0.5, color=BORDER_COLOR, alpha=0.3, linestyle='--')

        self.title = self.ax.set_title("POLAR ORBITAL DISPLAY", color=FG_COLOR, pad=20)

        self.time_text = self.ax.text(0.05, 0.95, '', color=FG_COLOR, fontsize=10,
                                      transform=self.ax.transAxes, va='top',
                                      bbox=dict(facecolor=DARK_BG, edgecolor=BORDER_COLOR, alpha=0.7))
        self.time_text.set_visible(False)

        self._setup_common_elements()

    def _setup_common_elements(self):
        # Set up trajectory line
        self.trajectory_line, = self.ax.plot([], [],
                                             color=TRAJECTORY_COLOR,
                                             linewidth=2.5,
                                             alpha=0.9,
                                             transform=ccrs.PlateCarree(),
                                             path_effects=[patheffects.withStroke(linewidth=4,
                                                                                  foreground=BORDER_COLOR,
                                                                                  alpha=0.3)])

        # Create marker
        self.marker, = self.ax.plot([], [],
                                    'o',
                                    color=ACCENT_COLOR,
                                    markersize=8,
                                    markeredgecolor='white',
                                    transform=ccrs.PlateCarree())

        # Create footprint circle
        self.footprint = Circle((0, 0),
                                radius=0,
                                facecolor='none',
                                edgecolor=GROUND_CIRCLE,
                                linewidth=2,
                                alpha=0.5,
                                transform=ccrs.PlateCarree())
        self.ax.add_patch(self.footprint)

        # Create position text
        self.position_text = self.ax.text(0, 0, '',
                                          color=FG_COLOR,
                                          fontsize=9,
                                          transform=ccrs.PlateCarree(),
                                          bbox=dict(facecolor=DARK_BG, edgecolor=BORDER_COLOR, alpha=0.7))

    def _load_satellite_image(self):
        try:
            self.satellite_img = mpimg.imread(resource_path('assets/satellite.webp'))
            self.satellite_box = OffsetImage(self.satellite_img, zoom=0.1)
            self.satellite_marker = None
        except FileNotFoundError:
            print("Warning: 'satellite.webp' image not found. Using circle marker instead.")
            self.satellite_img = None

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        self.bg_img.set_data(self.dark_img if self.dark_mode else plt.imread(resource_path('assets/nasa_light.jpg')))
        self.fig.set_facecolor(DARK_BG if self.dark_mode else "#f0f0f0")
        self.title.set_color(FG_COLOR if self.dark_mode else 'black')
        self.position_text.set_color('#f0f0f0')
        self.time_text.set_color('#f0f0f0')
        self.canvas.draw()

    def toggle_polar_view(self):
        self.is_polar_view = not self.is_polar_view
        self.setup_map()

    def update_display(self, data, trajectory):
        """Update the map display with satellite data"""
        if not data:
            return

        # Update time display
        if not self.is_polar_view:
            self.time_text.set_text(data['time'])

        # Update trajectory
        if trajectory:
            if self.is_polar_view:
                # Only show trajectory points above 30° latitude in polar view
                filtered_trajectory = [(lon, lat) for lon, lat in trajectory if lat >= 30]
                if filtered_trajectory:
                    lons, lats = zip(*filtered_trajectory)
                    self.trajectory_line.set_data(lons, lats)
                else:
                    self.trajectory_line.set_data([], [])
            else:
                lons, lats = zip(*trajectory)
                self.trajectory_line.set_data(lons, lats)
        else:
            self.trajectory_line.set_data([], [])

        # Update satellite marker and footprint
        if not self.is_polar_view or (self.is_polar_view and data['lat'] >= 30):
            self.footprint.set_center((data['lon'], data['lat']))
            self.footprint.set_radius(data['footprint_radius'])
            self.position_text.set_text(f"Az: {data['az']:.2f}°\nEl: {data['el']:.2f}°")
            self.position_text.set_position((data['lon'] + 5, data['lat']))

            if self.is_polar_view:
                # Use the circle marker in polar view
                self.marker.set_data([data['lon']], [data['lat']])
                self.marker.set_visible(True)

                # Remove the satellite image if it exists
                if self.satellite_marker is not None:
                    self.satellite_marker.remove()
                    self.satellite_marker = None
            else:
                # Use the satellite image in regular view if available
                if self.satellite_img is not None:
                    # Remove the old annotation box if it exists
                    if self.satellite_marker is not None:
                        self.satellite_marker.remove()

                    # Create a new annotation box at the correct position
                    self.satellite_marker = AnnotationBbox(
                        self.satellite_box,
                        (data['lon'], data['lat']),
                        frameon=False,
                        pad=0,
                        zorder=10,
                        transform=ccrs.PlateCarree()
                    )
                    self.ax.add_artist(self.satellite_marker)
                    self.marker.set_visible(False)
                else:
                    # Fallback to circle if image not available
                    self.marker.set_data([data['lon']], [data['lat']])
                    self.marker.set_visible(True)
        else:
            # Hide both markers when the satellite is below 30° in polar view
            self.marker.set_visible(False)
            if self.satellite_marker is not None:
                self.satellite_marker.remove()
                self.satellite_marker = None
            self.footprint.set_center((0, 0))
            self.footprint.set_radius(0)
            self.position_text.set_text("")

        # Use draw_idle to preserve zoom level during updates
        self.canvas.draw_idle()

    def on_draw(self, event):
        """Handle redrawing after zoom or pan operations"""
        # This method can be expanded to adjust elements based on current view
        pass

    def set_title(self, title_text):
        """Update map title"""
        self.title.set_text(title_text)
        self.canvas.draw_idle()