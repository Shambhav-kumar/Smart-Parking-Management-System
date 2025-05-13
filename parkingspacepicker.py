import cv2
import pickle
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Optional

@dataclass
class ParkingSpace:
    id: str
    position: Tuple[int, int]
    width: int
    height: int
    is_occupied: bool = False
    is_booked: bool = False

class ParkingSpacePicker:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.spaces: List[ParkingSpace] = []
        self.drawing = False
        self.dragging = False
        self.resizing = False
        self.selected_index = -1
        self.start_point = (-1, -1)
        self.end_point = (-1, -1)
        self.drag_start_pos = None
        self.resize_handle_size = 10
        self.template_size = None  # Store the size of the first space as template
        
        # Create sidebar image
        self.sidebar_width = 300
        self.sidebar_color = (240, 240, 240)  # Light gray
        
        # Load existing spaces
        try:
            with open('CarParkPos', 'rb') as f:
                saved_data = pickle.load(f)
                for i, (pos, size) in enumerate(saved_data):
                    self.spaces.append(ParkingSpace(
                        id=f"P{i+1:03d}",
                        position=pos,
                        width=size[0],
                        height=size[1]
                    ))
                if self.spaces:
                    self.template_size = (self.spaces[0].width, self.spaces[0].height)
        except:
            pass

    def save_spaces(self):
        """Save parking spaces to file"""
        save_data = [(space.position, (space.width, space.height)) for space in self.spaces]
        with open('CarParkPos', 'wb') as f:
            pickle.dump(save_data, f)

    def is_near_point(self, p1: Tuple[int, int], p2: Tuple[int, int], threshold: int = 10) -> bool:
        """Check if two points are near each other"""
        return abs(p1[0] - p2[0]) < threshold and abs(p1[1] - p2[1]) < threshold

    def get_space_at_point(self, point: Tuple[int, int]) -> Tuple[Optional[int], bool]:
        """Returns (space_index, is_resize_handle) or (None, False) if not found"""
        x, y = point
        if x > self.img_width:  # Ignore clicks in sidebar
            return None, False
            
        for i, space in enumerate(self.spaces):
            # Check if point is in resize handle
            handle_x = space.position[0] + space.width
            handle_y = space.position[1] + space.height
            if self.is_near_point((x, y), (handle_x, handle_y), self.resize_handle_size):
                return i, True
            
            # Check if point is inside rectangle
            if (space.position[0] <= x <= space.position[0] + space.width and 
                space.position[1] <= y <= space.position[1] + space.height):
                return i, False
        
        return None, False

    def handle_mouse_event(self, event, x, y, flags, param):
        if x > self.img_width:  # Ignore events in sidebar
            return
            
        if event == cv2.EVENT_LBUTTONDOWN:
            space_idx, is_resize = self.get_space_at_point((x, y))
            if space_idx is not None:
                self.selected_index = space_idx
                if is_resize:
                    self.resizing = True
                else:
                    self.dragging = True
                self.drag_start_pos = (x, y)
            else:
                if not self.template_size:  # First space - allow dynamic sizing
                    self.drawing = True
                    self.start_point = (x, y)
                    self.end_point = (x, y)
                else:  # Use template size for subsequent spaces
                    width, height = self.template_size
                    new_space = ParkingSpace(
                        id=f"P{len(self.spaces)+1:03d}",
                        position=(x, y),
                        width=width,
                        height=height
                    )
                    self.spaces.append(new_space)
                    self.save_spaces()

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.end_point = (x, y)
            elif self.dragging and self.selected_index != -1:
                dx = x - self.drag_start_pos[0]
                dy = y - self.drag_start_pos[1]
                space = self.spaces[self.selected_index]
                space.position = (space.position[0] + dx, space.position[1] + dy)
                self.drag_start_pos = (x, y)
            elif self.resizing and self.selected_index != -1:
                space = self.spaces[self.selected_index]
                new_width = max(30, x - space.position[0])
                new_height = max(20, y - space.position[1])
                space.width = new_width
                space.height = new_height
                if self.selected_index == 0:  # Update template if first space
                    self.template_size = (new_width, new_height)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                x1, y1 = min(self.start_point[0], self.end_point[0]), min(self.start_point[1], self.end_point[1])
                x2, y2 = max(self.start_point[0], self.end_point[0]), max(self.start_point[1], self.end_point[1])
                width = x2 - x1
                height = y2 - y1
                if width > 30 and height > 20:  # Minimum size check
                    new_space = ParkingSpace(
                        id=f"P{len(self.spaces)+1:03d}",
                        position=(x1, y1),
                        width=width,
                        height=height
                    )
                    self.spaces.append(new_space)
                    self.template_size = (width, height)  # Set as template
                self.start_point = (-1, -1)
                self.end_point = (-1, -1)
            self.dragging = False
            self.resizing = False
            self.selected_index = -1
            self.save_spaces()

        elif event == cv2.EVENT_RBUTTONDOWN:
            space_idx, _ = self.get_space_at_point((x, y))
            if space_idx is not None:
                if space_idx == 0 and len(self.spaces) > 1:
                    # If deleting first space, update template to second space
                    self.template_size = (self.spaces[1].width, self.spaces[1].height)
                self.spaces.pop(space_idx)
                # Update IDs of remaining spaces
                for i, space in enumerate(self.spaces):
                    space.id = f"P{i+1:03d}"
                self.save_spaces()

    def create_sidebar(self, img_height):
        sidebar = np.full((img_height, self.sidebar_width, 3), self.sidebar_color, dtype=np.uint8)
        
        # Add title
        cv2.putText(sidebar, "Parking Space Picker", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        # Add instructions
        instructions = [
            "Controls:",
            "",
            "- Left click & drag to draw",
            "- Left click to place space",
            "",
            "General Controls:",
            "- Drag space to move",
            "- Drag corner to resize",
            "- Right click to delete",
            "",
            f"Total spaces: {len(self.spaces)}",
            "",
            "Keyboard:",
            "- 'R': Reset all spaces",
            "- 'S': Save and exit",
            "- 'Q': Quit without saving"
        ]
        
        y = 70
        for text in instructions:
            cv2.putText(sidebar, text, (10, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            y += 25
        
        return sidebar

    def run(self):
        img = cv2.imread(self.image_path)
        if img is None:
            print(f"Error: Could not load image '{self.image_path}'. Please make sure the file exists.")
            return

        self.img_width = img.shape[1]  # Store original image width
        window_name = "Parking Space Picker"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.handle_mouse_event)

        while True:
            img_copy = img.copy()
            
            # Draw all existing spaces
            for i, space in enumerate(self.spaces):
                color = (255, 0, 255)  # Default color
                thickness = 2
                
                if i == self.selected_index:
                    color = (0, 255, 255)  # Yellow for selected
                    thickness = 3
                
                # Draw the rectangle
                cv2.rectangle(img_copy, 
                            space.position, 
                            (space.position[0] + space.width, space.position[1] + space.height), 
                            color, thickness)
                
                # Draw space ID
                cv2.putText(img_copy, space.id, 
                           (space.position[0] + 5, space.position[1] + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Draw resize handle
                handle_pos = (space.position[0] + space.width, space.position[1] + space.height)
                cv2.circle(img_copy, handle_pos, self.resize_handle_size // 2, (0, 255, 0), -1)
            
            # Draw rectangle being created
            if self.drawing and self.start_point != (-1, -1) and self.end_point != (-1, -1):
                x1, y1 = min(self.start_point[0], self.end_point[0]), min(self.start_point[1], self.end_point[1])
                x2, y2 = max(self.start_point[0], self.end_point[0]), max(self.start_point[1], self.end_point[1])
                cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Create and combine with sidebar
            sidebar = self.create_sidebar(img.shape[0])
            combined_img = np.hstack((img_copy, sidebar))
            
            cv2.imshow(window_name, combined_img)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.spaces = []
                self.template_size = None
                self.save_spaces()
            elif key == ord('s'):
                self.save_spaces()
                break

        cv2.destroyAllWindows()
        return self.spaces

if __name__ == '__main__':
    picker = ParkingSpacePicker('carParkImg.png')
    picker.run()