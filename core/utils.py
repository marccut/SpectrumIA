"""
SpectrumIA Utility Functions

Common helper functions used throughout the application.
"""

import logging
from typing import Tuple, List
import numpy as np
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def normalize_coordinates(
    point: Tuple[float, float],
    width: int,
    height: int,
) -> Tuple[float, float]:
    """
    Normalize coordinates to [0, 1] range.

    Args:
        point: (x, y) coordinates
        width: Image/screen width
        height: Image/screen height

    Returns:
        Normalized (x, y) coordinates
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid dimensions: width={width}, height={height}")

    x, y = point
    return (x / width, y / height)


def denormalize_coordinates(
    point: Tuple[float, float],
    width: int,
    height: int,
) -> Tuple[float, float]:
    """
    Denormalize coordinates from [0, 1] range to pixel coordinates.

    Args:
        point: Normalized (x, y) coordinates
        width: Image/screen width
        height: Image/screen height

    Returns:
        Pixel (x, y) coordinates
    """
    x, y = point
    return (int(x * width), int(y * height))


def smooth_gaze_points(
    points: List[Tuple[float, float]],
    alpha: float = 0.7,
) -> List[Tuple[float, float]]:
    """
    Apply exponential smoothing to gaze points.

    Args:
        points: List of (x, y) gaze coordinates
        alpha: Smoothing factor (0-1). Higher = more smoothing

    Returns:
        Smoothed points
    """
    if not points:
        return []

    if alpha < 0 or alpha > 1:
        raise ValueError(f"alpha must be between 0 and 1, got {alpha}")

    smoothed = [points[0]]
    for i in range(1, len(points)):
        x = alpha * smoothed[i - 1][0] + (1 - alpha) * points[i][0]
        y = alpha * smoothed[i - 1][1] + (1 - alpha) * points[i][1]
        smoothed.append((x, y))

    return smoothed


def calculate_euclidean_distance(
    point1: Tuple[float, float],
    point2: Tuple[float, float],
) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        point1: (x, y) coordinates
        point2: (x, y) coordinates

    Returns:
        Distance
    """
    x1, y1 = point1
    x2, y2 = point2
    return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def is_point_in_roi(
    point: Tuple[float, float],
    roi: Tuple[float, float, float, float],
) -> bool:
    """
    Check if point is within Region of Interest (ROI).

    Args:
        point: (x, y) coordinates
        roi: (x_min, y_min, x_max, y_max) ROI bounds

    Returns:
        True if point is in ROI
    """
    x, y = point
    x_min, y_min, x_max, y_max = roi

    return x_min <= x <= x_max and y_min <= y <= y_max


def calculate_time_duration(start_time: datetime, end_time: datetime) -> float:
    """
    Calculate duration between two timestamps in milliseconds.

    Args:
        start_time: Start timestamp
        end_time: End timestamp

    Returns:
        Duration in milliseconds
    """
    delta = end_time - start_time
    return delta.total_seconds() * 1000


def format_duration(milliseconds: float) -> str:
    """
    Format milliseconds to human-readable string.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted string (e.g., "1m 23s", "500ms")
    """
    total_seconds = int(milliseconds / 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    ms = int(milliseconds % 1000)

    if minutes > 0:
        return f"{minutes}m {seconds}s"
    elif seconds > 0:
        return f"{seconds}s {ms}ms"
    else:
        return f"{ms}ms"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max.

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


if __name__ == "__main__":
    # Test utilities
    setup_logging("DEBUG")

    # Test coordinate normalization
    norm = normalize_coordinates((100, 200), 640, 480)
    print(f"Normalized: {norm}")

    denorm = denormalize_coordinates(norm, 640, 480)
    print(f"Denormalized: {denorm}")

    # Test smoothing
    points = [(0, 0), (10, 10), (15, 20), (25, 25)]
    smoothed = smooth_gaze_points(points, alpha=0.7)
    print(f"Smoothed: {smoothed}")

    # Test distance
    dist = calculate_euclidean_distance((0, 0), (3, 4))
    print(f"Distance: {dist}")  # Should be 5

    # Test ROI
    in_roi = is_point_in_roi((0.5, 0.5), (0.3, 0.3, 0.7, 0.7))
    print(f"In ROI: {in_roi}")  # Should be True

    print("\n✓ Utilities validated successfully")
