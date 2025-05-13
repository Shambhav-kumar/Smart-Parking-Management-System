import tkinter as tk
from tkinter import ttk
from typing import List, Callable
from models.parking_space import ParkingSpace

class MonitorTab:
    def __init__(self, parent: ttk.Frame):
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        # Create frame for video
        self.video_frame = ttk.Frame(self.parent)
        self.video_frame.pack(expand=True, fill=tk.BOTH)
        
        # Control buttons frame
        control_frame = ttk.Frame(self.video_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Pause/Resume button
        self.pause_button = ttk.Button(control_frame, text="Pause")
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # Video display
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Status frame
        status_frame = ttk.LabelFrame(self.parent, text="Parking Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_text = tk.Text(status_frame, height=5, width=50)
        self.status_text.pack(padx=5, pady=5)

    def update_status(self, spaces: List[ParkingSpace]):
        """Update the status text with current parking space statistics."""
        free_count = sum(1 for space in spaces if space.status == "free")
        booked_count = sum(1 for space in spaces if space.status == "booked")
        occupied_count = sum(1 for space in spaces if space.status == "occupied")
        
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, f"Free Spaces: {free_count}/{len(spaces)}\n")
        self.status_text.insert(tk.END, f"Booked Spaces: {booked_count}/{len(spaces)}\n")
        self.status_text.insert(tk.END, f"Occupied Spaces: {occupied_count}/{len(spaces)}\n")

    def set_pause_command(self, command: Callable):
        """Set the command for the pause button."""
        self.pause_button.configure(command=command)

    def update_video_display(self, image):
        """Update the video display with a new image."""
        self.video_label.configure(image=image)
        self.video_label.image = image  # Keep a reference to prevent garbage collection 