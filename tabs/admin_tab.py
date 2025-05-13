import tkinter as tk
from tkinter import ttk
from typing import List, Callable
from parkingspacepicker import ParkingSpacePicker
from models.parking_space import ParkingSpace
from database.db_manager import DatabaseManager

class AdminTab:
    def __init__(self, parent: ttk.Frame, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        # Space management buttons
        btn_frame = ttk.Frame(self.parent)
        btn_frame.pack(pady=20)
        
        self.picker_button = ttk.Button(btn_frame, text="Launch Space Picker")
        self.picker_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(btn_frame, text="Refresh Spaces")
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Space list
        list_frame = ttk.LabelFrame(self.parent, text="Parking Spaces")
        list_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        self.space_tree = ttk.Treeview(list_frame, columns=('ID', 'Status', 'Bookings'))
        self.space_tree.heading('ID', text='Space ID')
        self.space_tree.heading('Status', text='Status')
        self.space_tree.heading('Bookings', text='Total Bookings')
        
        for col in ['ID', 'Status', 'Bookings']:
            self.space_tree.column(col, width=100)
        
        self.space_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def set_picker_command(self, command: Callable):
        """Set the command for the space picker button."""
        self.picker_button.configure(command=command)

    def set_refresh_command(self, command: Callable):
        """Set the command for the refresh button."""
        self.refresh_button.configure(command=command)

    def update_space_list(self, spaces: List[ParkingSpace]):
        """Update the space list with current data."""
        # Clear current items
        for item in self.space_tree.get_children():
            self.space_tree.delete(item)
        
        # Add spaces to tree
        for space in spaces:
            # Get booking count
            booking_count = self.db_manager.get_booking_count(space.id)
            
            # Get status display text
            status_display = {
                "free": "Available",
                "booked": "Booked",
                "occupied": "Occupied"
            }.get(space.status, "Available")
            
            self.space_tree.insert('', 'end', values=(space.id, status_display, booking_count)) 