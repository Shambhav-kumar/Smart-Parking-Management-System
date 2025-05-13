import cv2
import numpy as np
from typing import List, Tuple, Optional
from PIL import Image, ImageTk
from models.parking_space import ParkingSpace

class VideoProcessor:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.current_frame = None
        self.current_dilate = None
        self.is_paused = False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from the video."""
        if self.is_paused and self.current_frame is not None:
            return True, self.current_frame.copy()
        
        success, img = self.cap.read()
        if not success:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, img = self.cap.read()
        
        if success:
            self.current_frame = img.copy()
        return success, img

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a frame for space detection."""
        imgGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 25, 16)
        imgMedian = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)
        self.current_dilate = imgDilate.copy()
        return imgDilate

    def check_space_occupancy(self, pos: Tuple[int, int], size: Tuple[int, int], 
                            processed_frame: np.ndarray) -> bool:
        """Check if a parking space is occupied."""
        x, y = pos
        width, height = size
        imgCrop = processed_frame[y:y + height, x:x + width]
        count = cv2.countNonZero(imgCrop)
        return count >= 900

    def draw_spaces(self, frame: np.ndarray, spaces: List[ParkingSpace]) -> np.ndarray:
        """Draw parking spaces on the frame."""
        img = frame.copy()
        for space in spaces:
            x, y = space.position
            width, height = space.size
            
            # Set color based on status
            if space.status == "free":
                color = (0, 255, 0)  # BGR: Green
            elif space.status == "booked":
                color = (255, 255, 0)  # BGR: Yellow
            else:  # occupied
                color = (0, 0, 255)  # BGR: Red
            
            thickness = 2
            cv2.rectangle(img, (x, y), (x + width, y + height), color, thickness)
            cv2.putText(img, space.id, (x + 5, y + height - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return img

    def get_display_image(self, frame: np.ndarray, display_width: int = 1000) -> ImageTk.PhotoImage:
        """Convert a frame to a Tkinter-compatible image."""
        aspect_ratio = frame.shape[1] / frame.shape[0]
        display_height = int(display_width / aspect_ratio)
        img_resized = cv2.resize(frame, (display_width, display_height))
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        return ImageTk.PhotoImage(image=img_pil)

    def toggle_pause(self):
        """Toggle video pause state."""
        self.is_paused = not self.is_paused

    def release(self):
        """Release the video capture."""
        self.cap.release() 