import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import pickle
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from PIL import Image, ImageTk
import threading
import time
import os
from parkingspacepicker import ParkingSpace, ParkingSpacePicker
from models.parking_space import ParkingSpace
from database.db_manager import DatabaseManager
from video.video_processor import VideoProcessor
from tabs.monitor_tab import MonitorTab
from tabs.booking_tab import BookingTab
from tabs.admin_tab import AdminTab

class ParkingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Parking System")
        self.root.state('zoomed')  # Maximize window
        
        # Check if video file exists
        if not os.path.exists('carPark.mp4'):
            messagebox.showerror("Error", "Video file 'carPark.mp4' not found!")
            self.root.destroy()
            return

        # Initialize components
        self.db_manager = DatabaseManager()
        self.video_processor = VideoProcessor('carPark.mp4')
        self.spaces = []
        
        # Load parking spaces
        self.load_spaces()
        
        # Create main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_container)
        
        # Initialize tab modules
        self.monitor_tab = MonitorTab(ttk.Frame(self.tab_control))
        self.booking_tab = BookingTab(ttk.Frame(self.tab_control), self.db_manager)
        self.admin_tab = AdminTab(ttk.Frame(self.tab_control), self.db_manager)
        
        # Add tabs to notebook
        self.tab_control.add(self.monitor_tab.parent, text='Monitor')
        self.tab_control.add(self.booking_tab.parent, text='Book Space')
        self.tab_control.add(self.admin_tab.parent, text='Admin')
        self.tab_control.pack(expand=True, fill=tk.BOTH)
        
        # Set up event handlers
        self.setup_event_handlers()
        
        # Start update timers
        self.update_bookings()
        self.update_video()
        
        # Bind cleanup to window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_database(self):
        self.conn = sqlite3.connect('parking.db')
        c = self.conn.cursor()
        
        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS parking_spaces
                    (id INTEGER PRIMARY KEY, space_id TEXT, position_x INTEGER, position_y INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS bookings
                    (id INTEGER PRIMARY KEY,
                     space_id INTEGER,
                     user_name TEXT,
                     user_email TEXT,
                     license_plate TEXT,
                     start_time TIMESTAMP,
                     end_time TIMESTAMP,
                     is_active BOOLEAN,
                     FOREIGN KEY (space_id) REFERENCES parking_spaces (id))''')
        
        self.conn.commit()

    def load_spaces(self):
        """Load parking spaces from file."""
        try:
            with open('CarParkPos', 'rb') as f:
                data = pickle.load(f)
                self.spaces = []
                for i, (pos, size) in enumerate(data):
                    self.spaces.append(ParkingSpace(
                        id=f"P{i+1:03d}",
                        position=pos,
                        size=size
                    ))
        except:
            self.spaces = []

    def setup_event_handlers(self):
        """Set up event handlers for all components."""
        # Monitor tab
        self.monitor_tab.set_pause_command(self.toggle_pause)
        
        # Booking tab
        self.booking_tab.set_book_command(self.book_space)
        self.booking_tab.set_cancel_command(self.cancel_booking)
        self.booking_tab.set_refresh_commands(self.refresh_bookings)
        
        # Admin tab
        self.admin_tab.set_picker_command(self.launch_space_picker)
        self.admin_tab.set_refresh_command(self.refresh_spaces)

    def toggle_pause(self):
        """Toggle video pause state."""
        self.video_processor.toggle_pause()
        text = "Resume" if self.video_processor.is_paused else "Pause"
        self.monitor_tab.pause_button.configure(text=text)

    def book_space(self):
        """Handle booking form submission."""
        form_data = self.booking_tab.get_form_data()
        
        # Validate
        if not all([form_data['space_id'], form_data['name'], 
                   form_data['email'], form_data['license_plate']]):
            messagebox.showerror("Error", "All fields are required")
            return
            
        if form_data['hours'] == 0 and form_data['minutes'] == 0:
            messagebox.showerror("Error", "Duration must be greater than 0")
            return
        
        # Create booking
        start_time = datetime.now()
        end_time = start_time + timedelta(
            hours=form_data['hours'], 
            minutes=form_data['minutes']
        )
        
        success = self.db_manager.create_booking(
            form_data['space_id'],
            form_data['name'],
            form_data['email'],
            form_data['license_plate'],
            start_time,
            end_time
        )
        
        if success:
            self.booking_tab.clear_form()
            messagebox.showinfo(
                "Success", 
                f"Space {form_data['space_id']} booked until {end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            self.refresh_spaces()
        else:
            messagebox.showerror("Error", "Failed to create booking")

    def cancel_booking(self):
        """Cancel the selected booking."""
        selection = self.booking_tab.booking_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a booking to cancel")
            return
        
        item = self.booking_tab.booking_tree.item(selection[0])
        booking_id = item['values'][0]  # First column should be booking ID
        
        if self.db_manager.cancel_booking(booking_id):
            self.refresh_spaces()
            messagebox.showinfo("Success", "Booking cancelled successfully")
        else:
            messagebox.showerror("Error", "Failed to cancel booking")

    def launch_space_picker(self):
        """Launch the space picker tool."""
        self.root.iconify()  # Minimize main window
        picker = ParkingSpacePicker('carParkImg.png')
        picker.run()
        self.root.deiconify()  # Restore main window
        self.refresh_spaces()

    def refresh_spaces(self):
        """Refresh the parking space data."""
        # Reload spaces
        self.load_spaces()
        
        # Update space statuses
        success, frame = self.video_processor.read_frame()
        if success:
            processed_frame = self.video_processor.process_frame(frame)
            for space in self.spaces:
                # Check physical occupancy
                is_occupied = self.video_processor.check_space_occupancy(
                    space.position, space.size, processed_frame
                )
                # Check booking status
                is_booked = self.db_manager.is_space_booked(space.id, datetime.now())
                
                # Set status
                if is_occupied:
                    space.status = "occupied"
                elif is_booked:
                    space.status = "booked"
                else:
                    space.status = "free"

        # Update displays
        self.admin_tab.update_space_list(self.spaces)
        self.update_booking_spaces()

    def update_booking_spaces(self):
        """Update available spaces in booking tab."""
        available_spaces = [space.id for space in self.spaces if space.status == "free"]
        self.booking_tab.update_available_spaces(available_spaces)

    def update_bookings(self):
        """Update booking displays."""
        if not self.root.winfo_exists():
            return
        
        self.booking_tab.update_bookings()
        self.root.after(30000, self.update_bookings)  # Update every 30 seconds

    def update_video(self):
        """Update video display."""
        if not self.root.winfo_exists():
            return

        success, frame = self.video_processor.read_frame()
        if success:
            processed_frame = self.video_processor.process_frame(frame)
            
            # Update space statuses
            for space in self.spaces:
                # Check physical occupancy
                is_occupied = self.video_processor.check_space_occupancy(
                    space.position, space.size, processed_frame
                )
                # Check booking status
                is_booked = self.db_manager.is_space_booked(space.id, datetime.now())
                
                # Set status
                if is_occupied:
                    space.status = "occupied"
                elif is_booked:
                    space.status = "booked"
                else:
                    space.status = "free"
            
            # Draw spaces and update display
            frame_with_spaces = self.video_processor.draw_spaces(frame, self.spaces)
            display_image = self.video_processor.get_display_image(frame_with_spaces)
            
            self.monitor_tab.update_video_display(display_image)
            self.monitor_tab.update_status(self.spaces)
            
            # Update booking spaces
            self.update_booking_spaces()
        
        self.root.after(100, self.update_video)  # Update every 100ms

    def refresh_bookings(self):
        """Manually refresh the booking displays."""
        self.booking_tab.update_bookings()
        self.refresh_spaces()  # Also refresh spaces to update their status

    def on_closing(self):
        """Clean up resources before closing."""
        self.video_processor.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ParkingSystem(root)
    root.mainloop() 