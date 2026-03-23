import tkinter as tk
from satellite_tracker import SatelliteTracker

if __name__ == "__main__":
    root = tk.Tk()

    # Set app icon if available
    try:
        from utils.resource_utils import resource_path
        root.iconbitmap(resource_path('assets/satellite-logo.ico'))
    except Exception:
        pass

    app = SatelliteTracker(root)
    root.mainloop()
