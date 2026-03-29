#!/usr/bin/env python3
"""
Validation script for Core Processing Modules

Simple validation without pytest dependency.
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.face_detection import FaceDetector, FaceLandmarks
from core.gaze_estimation import GazeEstimator, GazePoint
from core.utils import (
    normalize_coordinates,
    denormalize_coordinates,
    smooth_gaze_points,
    calculate_euclidean_distance,
    is_point_in_roi,
)


def test_face_detector():
    """Test FaceDetector initialization."""
    print("Testing FaceDetector...", end=" ")
    detector = FaceDetector()
    assert detector.frame_width is None
    assert detector.frame_height is None
    assert len(detector.LEFT_EYE_INDICES) == 6
    assert len(detector.RIGHT_EYE_INDICES) == 6
    print("✓")


def test_face_landmarks():
    """Test FaceLandmarks dataclass."""
    print("Testing FaceLandmarks...", end=" ")
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
    print("✓")


def test_gaze_estimator():
    """Test GazeEstimator initialization."""
    print("Testing GazeEstimator...", end=" ")
    estimator = GazeEstimator(screen_width=1920, screen_height=1080)
    assert estimator.screen_width == 1920
    assert estimator.screen_height == 1080
    assert estimator.get_calibration_samples_count() == 0
    print("✓")


def test_gaze_point():
    """Test GazePoint dataclass."""
    print("Testing GazePoint...", end=" ")
    gaze = GazePoint(
        gaze_x=0.5,
        gaze_y=0.5,
        gaze_confidence=0.95,
        eye_open=True,
    )

    assert gaze.gaze_x == 0.5
    assert gaze.gaze_y == 0.5
    assert gaze.gaze_confidence == 0.95
    print("✓")


def test_normalize_coordinates():
    """Test coordinate normalization."""
    print("Testing normalize_coordinates...", end=" ")
    norm = normalize_coordinates((100, 200), 640, 480)
    assert abs(norm[0] - 0.15625) < 0.01
    assert abs(norm[1] - 0.41667) < 0.01
    print("✓")


def test_denormalize_coordinates():
    """Test coordinate denormalization."""
    print("Testing denormalize_coordinates...", end=" ")
    denorm = denormalize_coordinates((0.5, 0.5), 640, 480)
    assert denorm == (320, 240)
    print("✓")


def test_roundtrip_coordinates():
    """Test normalize-denormalize roundtrip."""
    print("Testing roundtrip coordinates...", end=" ")
    original = (100, 200)
    norm = normalize_coordinates(original, 640, 480)
    denorm = denormalize_coordinates(norm, 640, 480)
    assert denorm[0] == original[0]
    assert denorm[1] == original[1]
    print("✓")


def test_smooth_gaze_points():
    """Test gaze point smoothing."""
    print("Testing smooth_gaze_points...", end=" ")
    points = [(0, 0), (10, 10), (20, 20), (30, 30)]
    smoothed = smooth_gaze_points(points, alpha=0.7)

    assert len(smoothed) == len(points)
    assert smoothed[0] == points[0]
    assert all(0 <= p[0] <= 30 for p in smoothed)
    assert all(0 <= p[1] <= 30 for p in smoothed)
    print("✓")


def test_euclidean_distance():
    """Test Euclidean distance calculation."""
    print("Testing euclidean_distance...", end=" ")
    dist = calculate_euclidean_distance((0, 0), (3, 4))
    assert abs(dist - 5.0) < 0.01
    print("✓")


def test_point_in_roi():
    """Test point-in-ROI check."""
    print("Testing is_point_in_roi...", end=" ")
    assert is_point_in_roi((0.5, 0.5), (0.3, 0.3, 0.7, 0.7)) is True
    assert is_point_in_roi((0.1, 0.1), (0.3, 0.3, 0.7, 0.7)) is False
    print("✓")


def test_eye_aspect_ratio():
    """Test eye aspect ratio calculation."""
    print("Testing eye_aspect_ratio...", end=" ")
    eye_landmarks = np.array([
        [0, 0],
        [1, 1],
        [1, 0],
        [2, 0],
        [1, -1],
        [1, -1],
    ], dtype=np.float32)

    ear = GazeEstimator._calculate_eye_aspect_ratio(eye_landmarks)
    assert 0 <= ear <= 10
    print("✓")


def test_invalid_face_gaze_estimation():
    """Test gaze estimation with invalid face."""
    print("Testing gaze estimation with invalid face...", end=" ")
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
    print("✓")


def test_gaze_point_bounds():
    """Test that gaze points are bounded 0-1."""
    print("Testing gaze point bounds...", end=" ")
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
    print("✓")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("VALIDATING CORE PROCESSING MODULES")
    print("=" * 70 + "\n")

    tests = [
        test_face_detector,
        test_face_landmarks,
        test_gaze_estimator,
        test_gaze_point,
        test_normalize_coordinates,
        test_denormalize_coordinates,
        test_roundtrip_coordinates,
        test_smooth_gaze_points,
        test_euclidean_distance,
        test_point_in_roi,
        test_eye_aspect_ratio,
        test_invalid_face_gaze_estimation,
        test_gaze_point_bounds,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    if failed == 0:
        print("✓ All validations passed!")
        return 0
    else:
        print("✗ Some validations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
