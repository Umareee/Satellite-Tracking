import tkinter as tk
from satellite_tracker import SatelliteTracker

if __name__ == "__main__":
    root = tk.Tk()
    app = SatelliteTracker(root)
    root.mainloop()