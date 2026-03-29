"""
Tests for Core Processing Modules

Tests for face detection and gaze estimation modules.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.face_detection import FaceDetector, FaceLandmarks, visualize_landmarks
from core.gaze_estimation import GazeEstimator, GazePoint
from core.utils import (
    normalize_coordinates,
    denormalize_coordinates,
    smooth_gaze_points,
    calculate_euclidean_distance,
    is_point_in_roi,
)


class TestFaceDetector:
    """Test FaceDetector class."""

    def test_face_detector_initialization(self):
        """Test face detector initialization."""
        detector = FaceDetector()
        assert detector.frame_width is None
        assert detector.frame_height is None
        assert detector.face_detected_last_frame is False

    def test_detect_invalid_frame(self):
        """Test detection with invalid frame."""
        detector = FaceDetector()
        result = detector.detect(None)
        assert result == []

    def test_eye_landmark_indices(self):
        """Test that eye landmark indices are defined."""
        assert len(FaceDetector.LEFT_EYE_INDICES) == 6
        assert len(FaceDetector.RIGHT_EYE_INDICES) == 6
        assert FaceDetector.LEFT_IRIS_INDEX == 468
        assert FaceDetector.RIGHT_IRIS_INDEX == 473

    def test_face_landmarks_dataclass(self):
        """Test FaceLandmarks dataclass."""
        landmarks_3d = np.random.rand(478, 3)
        landmarks_2d = np.random.rand(478, 2).astype(np.int32)

        face_lm = FaceLandmarks(
            face_detected=True,
            landmarks_3d=landmarks_3d,
            landmarks_2d=landmarks_2d,
            face_confidence=0.95,
        )

        assert face_lm.face_detected is True
        assert face_lm.face_confidence == 0.95
        assert face_lm.landmarks_3d.shape == (478, 3)


class TestGazeEstimator:
    """Test GazeEstimator class."""

    def test_gaze_estimator_initialization(self):
        """Test gaze estimator initialization."""
        estimator = GazeEstimator(screen_width=1920, screen_height=1080)
        assert estimator.screen_width == 1920
        assert estimator.screen_height == 1080

    def test_gaze_point_dataclass(self):
        """Test GazePoint dataclass."""
        gaze = GazePoint(
            gaze_x=0.5,
            gaze_y=0.5,
            gaze_confidence=0.95,
            eye_open=True,
        )

        assert gaze.gaze_x == 0.5
        assert gaze.gaze_y == 0.5
        assert gaze.gaze_confidence == 0.95
        assert gaze.eye_open is True

    def test_estimate_gaze_invalid_face(self):
        """Test gaze estimation with invalid face."""
        estimator = GazeEstimator()

        face_lm = FaceLandmarks(
            face_detected=False,
            landmarks_3d=np.array([]),
            landmarks_2d=np.array([]),
            face_confidence=0.0,
        )

        gaze = estimator.estimate_gaze(face_lm)
        assert gaze.gaze_confidence == 0.0
        assert gaze.eye_open is False

    def test_eye_aspect_ratio(self):
        """Test eye aspect ratio calculation."""
        # Create artificial eye landmarks
        eye_landmarks = np.array([
            [0, 0],      # p1
            [1, 1],      # p2
            [1, 0],      # p3
            [2, 0],      # p4
            [1, -1],     # p5
            [1, -1],     # p6
        ], dtype=np.float32)

        ear = GazeEstimator._calculate_eye_aspect_ratio(eye_landmarks)
        assert 0 <= ear <= 1

    def test_gaze_point_clipping(self):
        """Test that gaze points are clipped to 0-1 range."""
        estimator = GazeEstimator()

        face_lm = FaceLandmarks(
            face_detected=True,
            landmarks_3d=np.random.rand(478, 3),
            landmarks_2d=np.random.rand(478, 2).astype(np.int32) * 1000,
            face_confidence=0.95,
        )

        gaze = estimator.estimate_gaze(face_lm)
        assert 0.0 <= gaze.gaze_x <= 1.0
        assert 0.0 <= gaze.gaze_y <= 1.0

    def test_calibration_samples(self):
        """Test calibration sample collection."""
        estimator = GazeEstimator()
        assert estimator.get_calibration_samples_count() == 0

        # Add sample
        face_lm = FaceLandmarks(
            face_detected=True,
            landmarks_3d=np.random.rand(478, 3),
            landmarks_2d=np.random.rand(478, 2).astype(np.int32) * 1000,
            face_confidence=0.95,
        )

        estimator.add_calibration_sample((0.5, 0.5), face_lm)
        assert estimator.get_calibration_samples_count() == 1

        # Clear
        estimator.clear_calibration()
        assert estimator.get_calibration_samples_count() == 0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_normalize_coordinates(self):
        """Test coordinate normalization."""
        norm = normalize_coordinates((100, 200), 640, 480)
        assert abs(norm[0] - 0.15625) < 0.01
        assert abs(norm[1] - 0.41667) < 0.01

    def test_denormalize_coordinates(self):
        """Test coordinate denormalization."""
        denorm = denormalize_coordinates((0.5, 0.5), 640, 480)
        assert denorm[0] == 320
        assert denorm[1] == 240

    def test_normalize_denormalize_roundtrip(self):
        """Test normalize-denormalize roundtrip."""
        original = (100, 200)
        norm = normalize_coordinates(original, 640, 480)
        denorm = denormalize_coordinates(norm, 640, 480)
        assert denorm[0] == original[0]
        assert denorm[1] == original[1]

    def test_smooth_gaze_points(self):
        """Test gaze point smoothing."""
        points = [(0, 0), (10, 10), (20, 20), (30, 30)]
        smoothed = smooth_gaze_points(points, alpha=0.7)

        assert len(smoothed) == len(points)
        # First point should be same
        assert smoothed[0] == points[0]
        # Smoothed points should be between extremes
        assert all(0 <= p[0] <= 30 for p in smoothed)
        assert all(0 <= p[1] <= 30 for p in smoothed)

    def test_euclidean_distance(self):
        """Test Euclidean distance calculation."""
        dist = calculate_euclidean_distance((0, 0), (3, 4))
        assert abs(dist - 5.0) < 0.01

    def test_point_in_roi(self):
        """Test point-in-ROI check."""
        # Point inside ROI
        assert is_point_in_roi((0.5, 0.5), (0.3, 0.3, 0.7, 0.7)) is True
        # Point outside ROI
        assert is_point_in_roi((0.1, 0.1), (0.3, 0.3, 0.7, 0.7)) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
