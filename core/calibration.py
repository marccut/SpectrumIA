"""
Gaze Calibration Module

Implements 9-point gaze calibration for eye-tracking systems.
Collects gaze data at known screen positions to calibrate gaze estimation.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CalibrationPoint:
    """Single calibration data point."""
    point_id: int  # 0-8 for 9-point calibration
    screen_x: float  # Normalized screen position (0-1)
    screen_y: float  # Normalized screen position (0-1)
    gaze_x: float  # Estimated gaze position
    gaze_y: float  # Estimated gaze position
    face_detected: bool
    face_confidence: float
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CalibrationData:
    """Complete calibration dataset."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    points: List[CalibrationPoint] = field(default_factory=list)
    screen_width: int = 1920
    screen_height: int = 1080
    calibration_quality: float = 0.0  # 0-100 based on face detection consistency
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_point(self, point: CalibrationPoint):
        """Add a calibration point to the dataset."""
        self.points.append(point)

    def get_accuracy(self) -> float:
        """Calculate calibration accuracy based on collected points."""
        if not self.points:
            return 0.0

        detected_count = sum(1 for p in self.points if p.face_detected)
        return (detected_count / len(self.points)) * 100

    def is_complete(self) -> bool:
        """Check if calibration has all 9 points."""
        return len(self.points) >= 9

    def is_valid(self) -> bool:
        """Check if calibration meets quality standards."""
        # Require at least 80% face detection rate
        return self.get_accuracy() >= 80


class CalibrationManager:
    """Manages the 9-point gaze calibration process."""

    # 9-point grid positions (3x3)
    CALIBRATION_POINTS_GRID = [
        # Row 1
        (0.1, 0.1),   # Top-left
        (0.5, 0.1),   # Top-center
        (0.9, 0.1),   # Top-right
        # Row 2
        (0.1, 0.5),   # Middle-left
        (0.5, 0.5),   # Center
        (0.9, 0.5),   # Middle-right
        # Row 3
        (0.1, 0.9),   # Bottom-left
        (0.5, 0.9),   # Bottom-center
        (0.9, 0.9),   # Bottom-right
    ]

    # Circle radius for calibration points (percentage of screen)
    POINT_RADIUS_PCT = 0.02

    def __init__(self):
        """Initialize calibration manager."""
        self.current_point_index = 0
        self.calibration_data = CalibrationData()

    def get_next_point(self) -> Optional[Tuple[float, float]]:
        """Get the next calibration point coordinates."""
        if self.current_point_index >= len(self.CALIBRATION_POINTS_GRID):
            return None

        return self.CALIBRATION_POINTS_GRID[self.current_point_index]

    def get_current_point_number(self) -> int:
        """Get current calibration point number (1-9)."""
        return self.current_point_index + 1

    def is_complete(self) -> bool:
        """Check if calibration is complete."""
        return self.current_point_index >= len(self.CALIBRATION_POINTS_GRID)

    def add_gaze_data(
        self,
        gaze_x: float,
        gaze_y: float,
        face_detected: bool,
        face_confidence: float
    ):
        """Add gaze data for the current calibration point."""
        if self.is_complete():
            logger.warning("Calibration already complete, cannot add more data")
            return

        point = CalibrationPoint(
            point_id=self.current_point_index,
            screen_x=self.CALIBRATION_POINTS_GRID[self.current_point_index][0],
            screen_y=self.CALIBRATION_POINTS_GRID[self.current_point_index][1],
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            face_detected=face_detected,
            face_confidence=face_confidence
        )

        self.calibration_data.add_point(point)
        self.current_point_index += 1

        logger.info(
            f"Calibration point {self.get_current_point_number()-1}/9 collected. "
            f"Face detected: {face_detected}, Confidence: {face_confidence:.2f}"
        )

    def get_progress(self) -> float:
        """Get calibration progress (0-100%)."""
        return (self.current_point_index / len(self.CALIBRATION_POINTS_GRID)) * 100

    def get_accuracy(self) -> float:
        """Get current calibration accuracy based on face detection."""
        return self.calibration_data.get_accuracy()

    def reset(self):
        """Reset calibration to start over."""
        self.current_point_index = 0
        self.calibration_data = CalibrationData()
        logger.info("Calibration reset")

    def finalize(self) -> CalibrationData:
        """Finalize calibration and return the data."""
        self.calibration_data.calibration_quality = self.get_accuracy()
        logger.info(f"Calibration finalized with quality: {self.calibration_data.calibration_quality:.1f}%")
        return self.calibration_data


class CalibrationVisualizer:
    """Helper class to generate calibration point coordinates for display."""

    @staticmethod
    def get_point_screen_position(
        normalized_x: float,
        normalized_y: float,
        screen_width: int = 1920,
        screen_height: int = 1080
    ) -> Tuple[int, int]:
        """Convert normalized coordinates to screen pixel coordinates."""
        screen_x = int(normalized_x * screen_width)
        screen_y = int(normalized_y * screen_height)
        return screen_x, screen_y

    @staticmethod
    def calculate_distance(
        gaze_x: float,
        gaze_y: float,
        target_x: float,
        target_y: float
    ) -> float:
        """Calculate Euclidean distance between gaze and target in normalized space."""
        return np.sqrt((gaze_x - target_x)**2 + (gaze_y - target_y)**2)
