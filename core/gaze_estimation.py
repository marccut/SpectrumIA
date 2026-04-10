"""
Gaze Estimation from Eye Landmarks

Estimates gaze point (2D screen coordinates) from facial landmarks.
Uses 3D face model and eye contour for accurate gaze prediction.
"""

import numpy as np
import cv2
from typing import Tuple, Optional, List
from dataclasses import dataclass
import logging

from .face_detection import FaceLandmarks, FaceDetector

logger = logging.getLogger(__name__)


@dataclass
class GazePoint:
    """Container for gaze estimation results."""

    gaze_x: float  # Normalized 0-1
    gaze_y: float  # Normalized 0-1
    gaze_confidence: float
    eye_open: bool
    blink_detected: bool = False
    timestamp: Optional[float] = None


class GazeEstimator:
    """
    Gaze estimation using facial landmarks.

    This implementation uses eye aspect ratio and iris position
    to estimate where on screen the user is looking.
    """

    # Eye aspect ratio threshold for blink detection
    EYE_ASPECT_RATIO_THRESHOLD = 0.2
    BLINK_CONSECUTIVE_FRAMES = 3

    def __init__(
        self,
        screen_width: int = 1920,
        screen_height: int = 1080,
        calibration_points: List[Tuple[float, float]] = None,
    ):
        """
        Initialize Gaze Estimator.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            calibration_points: Calibration points for personalized estimation
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.calibration_points = calibration_points or []
        self.calibration_samples = {}

        # Smoothing buffer
        self.gaze_history = []
        self.max_history = 5

        # Blink detection
        self.blink_counter = 0
        self.previous_eye_aspect_ratio = 0.5

        # Lazy-initialized shared FaceDetector instance
        self._face_detector: Optional["FaceDetector"] = None

    @property
    def face_detector(self) -> "FaceDetector":
        """Lazily-initialized shared FaceDetector instance."""
        if self._face_detector is None:
            self._face_detector = FaceDetector()
        return self._face_detector

    def estimate_gaze(
        self,
        face_landmarks: FaceLandmarks,
        screen_width: Optional[int] = None,
        screen_height: Optional[int] = None,
    ) -> GazePoint:
        """
        Estimate gaze point from face landmarks.

        Args:
            face_landmarks: FaceLandmarks object
            screen_width: Override default screen width
            screen_height: Override default screen height

        Returns:
            GazePoint object
        """
        if not face_landmarks.face_detected:
            return GazePoint(0.5, 0.5, 0.0, False)

        if screen_width:
            self.screen_width = screen_width
        if screen_height:
            self.screen_height = screen_height

        # Get eye landmarks
        left_eye, right_eye = self.face_detector.get_eye_landmarks(face_landmarks)
        iris_left, iris_right = self.face_detector.get_iris_center(face_landmarks)

        # Calculate eye aspect ratios
        left_ear = self._calculate_eye_aspect_ratio(left_eye)
        right_ear = self._calculate_eye_aspect_ratio(right_eye)

        # Detect blink
        avg_ear = (left_ear + right_ear) / 2
        blink_detected = False

        if avg_ear < self.EYE_ASPECT_RATIO_THRESHOLD:
            self.blink_counter += 1
        else:
            if self.blink_counter >= self.BLINK_CONSECUTIVE_FRAMES:
                blink_detected = True
            self.blink_counter = 0

        # Calculate gaze point
        gaze_x, gaze_y = self._estimate_gaze_point(
            left_eye, right_eye, iris_left, iris_right, face_landmarks
        )

        # Validate gaze point
        gaze_x = np.clip(gaze_x, 0.0, 1.0)
        gaze_y = np.clip(gaze_y, 0.0, 1.0)

        # Calculate confidence
        confidence = self._calculate_gaze_confidence(
            left_ear, right_ear, face_landmarks
        )

        # Apply smoothing
        smoothed_x, smoothed_y = self._apply_smoothing(gaze_x, gaze_y)

        eye_open = avg_ear > self.EYE_ASPECT_RATIO_THRESHOLD

        return GazePoint(
            gaze_x=smoothed_x,
            gaze_y=smoothed_y,
            gaze_confidence=confidence,
            eye_open=eye_open,
            blink_detected=blink_detected,
        )

    @staticmethod
    def _calculate_eye_aspect_ratio(eye_landmarks: np.ndarray) -> float:
        """
        Calculate eye aspect ratio (EAR) for blink detection.

        Formula: EAR = (||p2-p6|| + ||p3-p5||) / (2*||p1-p4||)

        Args:
            eye_landmarks: Eye contour landmarks (6 points)

        Returns:
            Eye aspect ratio
        """
        if len(eye_landmarks) < 6:
            return 0.5

        # Calculate distances
        a = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])  # p2-p6
        b = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])  # p3-p5
        c = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])  # p1-p4

        if c == 0:
            return 0.5

        ear = (a + b) / (2.0 * c)
        return ear

    def _estimate_gaze_point(
        self,
        left_eye: np.ndarray,
        right_eye: np.ndarray,
        iris_left: np.ndarray,
        iris_right: np.ndarray,
        face_landmarks: FaceLandmarks,
    ) -> Tuple[float, float]:
        """
        Estimate gaze point on screen.

        Uses iris position relative to eye contour to estimate gaze.

        Args:
            left_eye: Left eye contour landmarks
            right_eye: Right eye contour landmarks
            iris_left: Left iris center
            iris_right: Right iris center
            face_landmarks: Face landmarks for head pose

        Returns:
            Tuple of (normalized_x, normalized_y)
        """
        # Calculate eye centers
        left_eye_center = np.mean(left_eye, axis=0)
        right_eye_center = np.mean(right_eye, axis=0)

        # Calculate iris position relative to eye
        left_iris_relative = (iris_left - left_eye_center) / (
            np.std(left_eye, axis=0) + 1e-6
        )
        right_iris_relative = (iris_right - right_eye_center) / (
            np.std(right_eye, axis=0) + 1e-6
        )

        # Average iris position
        iris_avg_relative = (left_iris_relative + right_iris_relative) / 2

        # Convert to gaze point (simple linear mapping)
        # This is a basic model; in production, would use more sophisticated methods
        gaze_x = 0.5 + iris_avg_relative[0] * 0.1
        gaze_y = 0.5 + iris_avg_relative[1] * 0.1

        return float(gaze_x), float(gaze_y)

    def _calculate_gaze_confidence(
        self, left_ear: float, right_ear: float, face_landmarks: FaceLandmarks
    ) -> float:
        """
        Calculate confidence of gaze estimation.

        Args:
            left_ear: Left eye aspect ratio
            right_ear: Right eye aspect ratio
            face_landmarks: Face landmarks

        Returns:
            Confidence score 0-1
        """
        # Confidence based on eye opening
        ear_confidence = min(
            (left_ear + right_ear) / 2 / self.EYE_ASPECT_RATIO_THRESHOLD,
            1.0,
        )

        # Confidence based on face detection confidence
        face_confidence = face_landmarks.face_confidence

        # Combined confidence
        confidence = (ear_confidence + face_confidence) / 2

        return float(confidence)

    def _apply_smoothing(self, gaze_x: float, gaze_y: float) -> Tuple[float, float]:
        """
        Apply temporal smoothing to gaze points.

        Args:
            gaze_x: Current gaze x
            gaze_y: Current gaze y

        Returns:
            Smoothed (gaze_x, gaze_y)
        """
        self.gaze_history.append((gaze_x, gaze_y))

        if len(self.gaze_history) > self.max_history:
            self.gaze_history.pop(0)

        # Simple moving average
        avg_x = np.mean([g[0] for g in self.gaze_history])
        avg_y = np.mean([g[1] for g in self.gaze_history])

        return avg_x, avg_y

    def add_calibration_sample(
        self, screen_point: Tuple[float, float], face_landmarks: FaceLandmarks
    ) -> None:
        """
        Add calibration sample for personalized gaze estimation.

        Args:
            screen_point: Expected gaze point on screen (normalized 0-1)
            face_landmarks: Corresponding face landmarks
        """
        if not face_landmarks.face_detected:
            return

        key = f"{screen_point[0]:.1f}_{screen_point[1]:.1f}"

        if key not in self.calibration_samples:
            self.calibration_samples[key] = []

        # Store iris positions and screen point
        iris_left, iris_right = self.face_detector.get_iris_center(face_landmarks)
        self.calibration_samples[key].append(
            {
                "screen_point": screen_point,
                "iris_left": iris_left,
                "iris_right": iris_right,
                "landmarks": face_landmarks.landmarks_3d,
            }
        )

    def clear_calibration(self) -> None:
        """Clear calibration data."""
        self.calibration_samples = {}

    def get_head_pose(self, face_landmarks: "FaceLandmarks") -> Tuple[float, float, float]:
        """
        Get head pose (pitch, yaw, roll) from face landmarks.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Tuple of (pitch, yaw, roll) in degrees
        """
        return self.face_detector.calculate_head_pose(face_landmarks)

    def get_calibration_samples_count(self) -> int:
        """Get number of calibration samples collected."""
        return sum(len(v) for v in self.calibration_samples.values())


def visualize_gaze(
    frame: np.ndarray,
    gaze_point: GazePoint,
    face_landmarks: FaceLandmarks,
    draw_gaze_ray: bool = True,
) -> np.ndarray:
    """
    Visualize gaze point on frame.

    Args:
        frame: Input frame
        gaze_point: GazePoint object
        face_landmarks: FaceLandmarks object
        draw_gaze_ray: Draw ray from iris to gaze point

    Returns:
        Frame with gaze visualization
    """
    frame_copy = frame.copy()
    h, w = frame.shape[:2]

    # Convert normalized gaze to pixel coordinates
    gaze_pixel_x = int(gaze_point.gaze_x * w)
    gaze_pixel_y = int(gaze_point.gaze_y * h)

    # Draw gaze point
    color = (0, 255, 0) if gaze_point.eye_open else (0, 0, 255)
    cv2.circle(frame_copy, (gaze_pixel_x, gaze_pixel_y), 10, color, 2)

    # Draw iris center and ray
    if face_landmarks.face_detected and draw_gaze_ray:
        _detector = FaceDetector()
        iris_left, iris_right = _detector.get_iris_center(face_landmarks)
        iris_center = (iris_left + iris_right) / 2
        iris_pixel = tuple(iris_center.astype(int))

        # Draw ray from iris to gaze point
        cv2.line(
            frame_copy,
            iris_pixel,
            (gaze_pixel_x, gaze_pixel_y),
            (255, 0, 255),
            2,
        )

    # Draw confidence text
    confidence_text = f"Gaze Confidence: {gaze_point.gaze_confidence:.2f}"
    cv2.putText(
        frame_copy,
        confidence_text,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )

    # Draw blink indicator
    if gaze_point.blink_detected:
        cv2.putText(
            frame_copy,
            "BLINK DETECTED",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    return frame_copy


if __name__ == "__main__":
    # Test gaze estimation
    import sys
    from .face_detection import FaceDetector

    logging.basicConfig(level=logging.INFO)

    detector = FaceDetector()
    estimator = GazeEstimator(screen_width=1920, screen_height=1080)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open webcam")
        sys.exit(1)

    print("Gaze Estimation Test - Press 'q' to quit")
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detector.detect(frame)

        if faces:
            face = faces[0]
            gaze_point = estimator.estimate_gaze(face, 1920, 1080)
            frame = visualize_gaze(frame, gaze_point, face)

            if frame_count % 30 == 0:
                print(
                    f"Gaze: ({gaze_point.gaze_x:.2f}, {gaze_point.gaze_y:.2f}) "
                    f"Confidence: {gaze_point.gaze_confidence:.2f}"
                )

        cv2.imshow("Gaze Estimation", frame)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.release()

    print("✓ Gaze estimation test completed")
