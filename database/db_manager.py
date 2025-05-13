import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = 'parking.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database and create necessary tables."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
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
            
            conn.commit()

    def create_booking(self, space_id: str, user_name: str, user_email: str, 
                      license_plate: str, start_time: datetime, end_time: datetime) -> bool:
        """Create a new booking in the database."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            try:
                c.execute("""
                    INSERT INTO bookings 
                    (space_id, user_name, user_email, license_plate, start_time, end_time, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (space_id, user_name, user_email, license_plate, start_time, end_time, True))
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def get_active_bookings(self) -> List[Dict]:
        """Get all active bookings."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, space_id, user_name, user_email, license_plate, 
                       start_time, end_time, is_active
                FROM bookings
                WHERE is_active = 1
                ORDER BY start_time DESC
            """)
            columns = ['id', 'space_id', 'user_name', 'user_email', 'license_plate', 
                      'start_time', 'end_time', 'is_active']
            return [dict(zip(columns, row)) for row in c.fetchall()]

    def get_expired_bookings(self) -> List[Dict]:
        """Get all expired bookings."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, space_id, user_name, user_email, license_plate, 
                       start_time, end_time, is_active
                FROM bookings
                WHERE is_active = 0
                ORDER BY end_time DESC
            """)
            columns = ['id', 'space_id', 'user_name', 'user_email', 'license_plate', 
                      'start_time', 'end_time', 'is_active']
            return [dict(zip(columns, row)) for row in c.fetchall()]

    def cancel_booking(self, booking_id: int) -> bool:
        """Cancel a booking by setting is_active to False."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            try:
                c.execute("UPDATE bookings SET is_active = 0 WHERE id = ?", (booking_id,))
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def is_space_booked(self, space_id: str, current_time: datetime) -> bool:
        """Check if a space is currently booked."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT 1 FROM bookings 
                WHERE space_id = ? AND is_active = 1 
                AND ? BETWEEN datetime(start_time) AND datetime(end_time)
            """, (space_id, current_time.strftime('%Y-%m-%d %H:%M:%S')))
            return c.fetchone() is not None

    def get_booking_count(self, space_id: str) -> int:
        """Get the total number of bookings for a space."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM bookings WHERE space_id = ?", (space_id,))
            return c.fetchone()[0] 