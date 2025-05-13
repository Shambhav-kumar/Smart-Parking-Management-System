from dataclasses import dataclass
from typing import Tuple

@dataclass
class ParkingSpace:
    id: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    status: str = "free"  # can be "free", "booked", or "occupied"
    is_occupied: bool = False
    is_booked: bool = False 