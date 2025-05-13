import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Callable
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager

class BookingTab:
    def __init__(self, parent: ttk.Frame, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        # Booking form
        form_frame = ttk.LabelFrame(self.parent, text="Book a Parking Space")
        form_frame.pack(padx=20, pady=20, fill=tk.X)
        
        # Space selection
        ttk.Label(form_frame, text="Select Space:").grid(row=0, column=0, padx=5, pady=5)
        self.space_var = tk.StringVar()
        self.space_combo = ttk.Combobox(form_frame, textvariable=self.space_var)
        self.space_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # User details
        ttk.Label(form_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(form_frame)
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=2, column=0, padx=5, pady=5)
        self.email_entry = ttk.Entry(form_frame)
        self.email_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="License Plate:").grid(row=3, column=0, padx=5, pady=5)
        self.license_entry = ttk.Entry(form_frame)
        self.license_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Duration frame
        duration_frame = ttk.Frame(form_frame)
        duration_frame.grid(row=4, column=0, columnspan=2, pady=5)
        
        ttk.Label(duration_frame, text="Duration:").pack(side=tk.LEFT, padx=5)
        
        # Hours
        self.hours_var = tk.IntVar(value=0)
        ttk.Spinbox(duration_frame, from_=0, to=23, width=3, textvariable=self.hours_var).pack(side=tk.LEFT)
        ttk.Label(duration_frame, text="hours").pack(side=tk.LEFT, padx=2)
        
        # Minutes
        self.minutes_var = tk.IntVar(value=30)
        ttk.Spinbox(duration_frame, from_=0, to=59, width=3, textvariable=self.minutes_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(duration_frame, text="minutes").pack(side=tk.LEFT, padx=2)
        
        # Book button
        self.book_button = ttk.Button(form_frame, text="Book Space")
        self.book_button.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Create notebook for active and expired bookings
        bookings_notebook = ttk.Notebook(self.parent)
        bookings_notebook.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Active bookings frame
        active_frame = ttk.Frame(bookings_notebook)
        bookings_notebook.add(active_frame, text='Active Bookings')
        
        # Button frame for active bookings
        active_btn_frame = ttk.Frame(active_frame)
        active_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.refresh_active_button = ttk.Button(active_btn_frame, text="Refresh")
        self.refresh_active_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(active_btn_frame, text="Cancel Selected Booking")
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Active bookings tree
        self.booking_tree = ttk.Treeview(active_frame, 
            columns=('ID', 'Space', 'Name', 'License', 'Start', 'End', 'Status', 'Time Left'),
            show='headings')
        
        # Configure columns
        columns = [
            ('ID', 50),
            ('Space', 80),
            ('Name', 150),
            ('License', 100),
            ('Start', 150),
            ('End', 150),
            ('Status', 80),
            ('Time Left', 100)
        ]
        
        for col, width in columns:
            self.booking_tree.heading(col, text=col)
            self.booking_tree.column(col, width=width)
        
        self.booking_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Expired bookings frame
        expired_frame = ttk.Frame(bookings_notebook)
        bookings_notebook.add(expired_frame, text='Expired Bookings')
        
        # Button frame for expired bookings
        expired_btn_frame = ttk.Frame(expired_frame)
        expired_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.refresh_expired_button = ttk.Button(expired_btn_frame, text="Refresh")
        self.refresh_expired_button.pack(side=tk.LEFT, padx=5)
        
        # Expired bookings tree
        self.expired_tree = ttk.Treeview(expired_frame, 
            columns=('ID', 'Space', 'Name', 'License', 'Start', 'End'),
            show='headings')
        
        # Configure columns
        columns = [
            ('ID', 50),
            ('Space', 80),
            ('Name', 150),
            ('License', 100),
            ('Start', 150),
            ('End', 150)
        ]
        
        for col, width in columns:
            self.expired_tree.heading(col, text=col)
            self.expired_tree.column(col, width=width)
        
        self.expired_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def update_available_spaces(self, space_ids: List[str]):
        """Update the available spaces in the combobox."""
        self.space_combo['values'] = space_ids
        if not self.space_var.get() and space_ids:
            self.space_var.set(space_ids[0])

    def clear_form(self):
        """Clear the booking form."""
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.license_entry.delete(0, tk.END)
        self.hours_var.set(0)
        self.minutes_var.set(30)

    def set_book_command(self, command: Callable):
        """Set the command for the book button."""
        self.book_button.configure(command=command)

    def set_cancel_command(self, command: Callable):
        """Set the command for the cancel button."""
        self.cancel_button.configure(command=command)

    def get_form_data(self) -> Dict:
        """Get the form data as a dictionary."""
        return {
            'space_id': self.space_var.get(),
            'name': self.name_entry.get(),
            'email': self.email_entry.get(),
            'license_plate': self.license_entry.get(),
            'hours': self.hours_var.get(),
            'minutes': self.minutes_var.get()
        }

    def update_bookings(self):
        """Update the booking trees with current data."""
        # Clear current items
        for tree in [self.booking_tree, self.expired_tree]:
            for item in tree.get_children():
                tree.delete(item)

        # Get bookings from database
        active_bookings = self.db_manager.get_active_bookings()
        expired_bookings = self.db_manager.get_expired_bookings()
        current_time = datetime.now()

        # Update active bookings
        for booking in active_bookings:
            try:
                # Parse end time, handling potential microseconds
                end_time_str = booking['end_time'].split('.')[0]
                end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
                start_time = datetime.strptime(booking['start_time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                
                time_left = end_time - current_time
                
                # If booking has expired, move it to expired bookings
                if time_left.total_seconds() <= 0:
                    self.db_manager.cancel_booking(booking['id'])
                    self.expired_tree.insert('', 'end', values=(
                        booking['id'],
                        booking['space_id'],
                        booking['user_name'],
                        booking['license_plate'],
                        start_time.strftime('%Y-%m-%d %H:%M'),
                        end_time.strftime('%Y-%m-%d %H:%M')
                    ))
                else:
                    # Calculate time left
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60
                    time_left_str = f"{hours}h {minutes}m"
                    
                    self.booking_tree.insert('', 'end', values=(
                        booking['id'],
                        booking['space_id'],
                        booking['user_name'],
                        booking['license_plate'],
                        start_time.strftime('%Y-%m-%d %H:%M'),
                        end_time.strftime('%Y-%m-%d %H:%M'),
                        'Active',
                        time_left_str
                    ))
            except (ValueError, IndexError) as e:
                print(f"Error processing booking {booking['id']}: {e}")
                continue

        # Update expired bookings
        for booking in expired_bookings:
            try:
                start_time = datetime.strptime(booking['start_time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(booking['end_time'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                
                self.expired_tree.insert('', 'end', values=(
                    booking['id'],
                    booking['space_id'],
                    booking['user_name'],
                    booking['license_plate'],
                    start_time.strftime('%Y-%m-%d %H:%M'),
                    end_time.strftime('%Y-%m-%d %H:%M')
                ))
            except (ValueError, IndexError) as e:
                print(f"Error processing expired booking {booking['id']}: {e}")
                continue

    def set_refresh_commands(self, command: Callable):
        """Set the command for both refresh buttons."""
        self.refresh_active_button.configure(command=command)
        self.refresh_expired_button.configure(command=command) 