"""
Face Detection and Landmarks Extraction using MediaPipe

Detects faces and extracts facial landmarks for gaze estimation.
Based on MediaPipe Face Mesh (478 landmarks).
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FaceLandmarks:
    """Container for face landmarks and detection results."""

    face_detected: bool
    landmarks_3d: np.ndarray  # (478, 3) - x, y, z coordinates
    landmarks_2d: np.ndarray  # (478, 2) - x, y screen coordinates
    face_confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)
    face_id: int = -1


class FaceDetector:
    """
    Face detection and landmark extraction using MediaPipe Face Mesh.

    MediaPipe provides 478 facial landmarks with real-time performance.
    Key landmark indices for eye-tracking:
    - Left eye: 33, 160, 158, 133, 153, 144
    - Right eye: 263, 387, 385, 362, 381, 373
    - Iris center: 468 (left), 473 (right)
    """

    # Key landmark indices
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [263, 387, 385, 362, 381, 373]
    LEFT_IRIS_INDEX = 468
    RIGHT_IRIS_INDEX = 473

    FACE_OVAL_INDICES = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]

    NOSE_INDICES = [1, 2, 3, 4, 5, 6, 98, 327, 331]
    MOUTH_INDICES = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95, 185, 40, 39, 37, 0, 267, 269, 270, 409, 415, 310, 311, 312, 13, 82, 81, 80, 16, 61, 191, 78, 80, 81, 82, 13, 312, 311, 310, 415, 407, 213, 147, 123, 50, 187, 192, 211, 212, 32, 38, 128, 245, 244, 233, 232, 213, 427, 428, 429, 430, 431, 432, 433, 434]

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Initialize Face Detector.

        Args:
            static_image_mode: Static image or video mode
            max_num_faces: Maximum number of faces to detect
            refine_landmarks: Refine iris landmarks
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
        """
        self.mp_face_mesh = mp.solutions.face_mesh

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.frame_width = None
        self.frame_height = None
        self.face_detected_last_frame = False

    def detect(self, frame: np.ndarray) -> List[FaceLandmarks]:
        """
        Detect faces and landmarks in frame.

        Args:
            frame: Input frame (BGR format, HxWx3)

        Returns:
            List of FaceLandmarks objects
        """
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame provided to FaceDetector.detect()")
            return []

        # Get frame dimensions
        self.frame_height, self.frame_width = frame.shape[:2]

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect landmarks
        results = self.face_mesh.process(rgb_frame)

        faces = []

        if results.multi_face_landmarks:
            for face_id, face_landmarks in enumerate(results.multi_face_landmarks):
                landmarks_3d = np.array(
                    [[lm.x, lm.y, lm.z] for lm in face_landmarks.landmark],
                    dtype=np.float32,
                )

                # Convert to pixel coordinates
                landmarks_2d = landmarks_3d[:, :2].copy()
                landmarks_2d[:, 0] *= self.frame_width
                landmarks_2d[:, 1] *= self.frame_height

                # Calculate face confidence
                face_confidence = float(np.mean([lm.z for lm in face_landmarks.landmark]))

                # Calculate bounding box
                bbox = self._calculate_bbox(landmarks_2d)

                faces.append(
                    FaceLandmarks(
                        face_detected=True,
                        landmarks_3d=landmarks_3d,
                        landmarks_2d=landmarks_2d.astype(np.int32),
                        face_confidence=face_confidence,
                        bbox=bbox,
                        face_id=face_id,
                    )
                )

            self.face_detected_last_frame = True
        else:
            self.face_detected_last_frame = False
            logger.debug("No faces detected in frame")

        return faces

    def get_eye_landmarks(self, face_landmarks: FaceLandmarks) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract eye landmarks from face landmarks.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Tuple of (left_eye_landmarks, right_eye_landmarks)
        """
        left_eye = face_landmarks.landmarks_2d[self.LEFT_EYE_INDICES]
        right_eye = face_landmarks.landmarks_2d[self.RIGHT_EYE_INDICES]

        return left_eye, right_eye

    def get_iris_center(self, face_landmarks: FaceLandmarks) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get iris center points.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Tuple of (left_iris_center, right_iris_center) as (x, y)
        """
        left_iris = face_landmarks.landmarks_2d[self.LEFT_IRIS_INDEX]
        right_iris = face_landmarks.landmarks_2d[self.RIGHT_IRIS_INDEX]

        return left_iris, right_iris

    def get_mouth_landmarks(self, face_landmarks: FaceLandmarks) -> np.ndarray:
        """
        Extract mouth landmarks.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Mouth landmarks (48, 2)
        """
        return face_landmarks.landmarks_2d[self.MOUTH_INDICES]

    def get_nose_landmarks(self, face_landmarks: FaceLandmarks) -> np.ndarray:
        """
        Extract nose landmarks.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Nose landmarks (9, 2)
        """
        return face_landmarks.landmarks_2d[self.NOSE_INDICES]

    def get_face_oval(self, face_landmarks: FaceLandmarks) -> np.ndarray:
        """
        Get face oval contour.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Face oval landmarks
        """
        return face_landmarks.landmarks_2d[self.FACE_OVAL_INDICES]

    def calculate_head_pose(
        self, face_landmarks: FaceLandmarks
    ) -> Tuple[float, float, float]:
        """
        Calculate head pose (pitch, yaw, roll) in degrees.

        Args:
            face_landmarks: FaceLandmarks object

        Returns:
            Tuple of (pitch, yaw, roll) in degrees
        """
        # Use 3D landmarks for head pose estimation
        landmarks_3d = face_landmarks.landmarks_3d

        # Key points for head pose
        nose = landmarks_3d[1]  # Nose tip
        left_eye = landmarks_3d[33]  # Left eye
        right_eye = landmarks_3d[263]  # Right eye
        chin = landmarks_3d[152]  # Chin

        # Calculate vectors
        face_center = np.mean(landmarks_3d, axis=0)

        # Simple head pose estimation based on facial landmarks
        eye_vector = right_eye - left_eye
        nose_vector = nose - face_center
        chin_vector = chin - face_center

        # Calculate angles (simplified)
        yaw = np.arctan2(eye_vector[0], eye_vector[2]) * 180 / np.pi
        pitch = np.arctan2(nose_vector[1], nose_vector[2]) * 180 / np.pi
        roll = np.arctan2(chin_vector[0], chin_vector[1]) * 180 / np.pi

        return pitch, yaw, roll

    @staticmethod
    def _calculate_bbox(landmarks_2d: np.ndarray) -> Tuple[int, int, int, int]:
        """
        Calculate bounding box from landmarks.

        Args:
            landmarks_2d: 2D landmarks array

        Returns:
            Tuple of (x, y, width, height)
        """
        x_min = int(np.min(landmarks_2d[:, 0]))
        x_max = int(np.max(landmarks_2d[:, 0]))
        y_min = int(np.min(landmarks_2d[:, 1]))
        y_max = int(np.max(landmarks_2d[:, 1]))

        x = x_min
        y = y_min
        w = x_max - x_min
        h = y_max - y_min

        return x, y, w, h

    def release(self):
        """Release MediaPipe resources."""
        try:
            if hasattr(self, 'face_mesh') and self.face_mesh is not None:
                self.face_mesh.close()
        except Exception as e:
            logger.warning(f"Error releasing FaceDetector resources: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.release()
        except Exception as e:
            logger.warning(f"Error in FaceDetector cleanup: {e}")


def visualize_landmarks(
    frame: np.ndarray,
    face_landmarks: FaceLandmarks,
    draw_eye_only: bool = False,
    draw_iris: bool = True,
) -> np.ndarray:
    """
    Visualize face landmarks on frame.

    Args:
        frame: Input frame
        face_landmarks: FaceLandmarks object
        draw_eye_only: Draw only eye landmarks
        draw_iris: Draw iris center

    Returns:
        Frame with drawn landmarks
    """
    frame_copy = frame.copy()

    if not face_landmarks.face_detected:
        return frame_copy

    landmarks = face_landmarks.landmarks_2d

    if draw_eye_only:
        # Draw eye landmarks
        left_eye_indices = FaceDetector.LEFT_EYE_INDICES
        right_eye_indices = FaceDetector.RIGHT_EYE_INDICES

        for idx in left_eye_indices:
            pt = landmarks[idx]
            cv2.circle(frame_copy, tuple(pt), 2, (0, 255, 0), -1)

        for idx in right_eye_indices:
            pt = landmarks[idx]
            cv2.circle(frame_copy, tuple(pt), 2, (0, 255, 0), -1)
    else:
        # Draw all landmarks
        for pt in landmarks:
            cv2.circle(frame_copy, tuple(pt), 1, (0, 255, 0), -1)

    # Draw iris centers
    if draw_iris:
        left_iris = landmarks[FaceDetector.LEFT_IRIS_INDEX]
        right_iris = landmarks[FaceDetector.RIGHT_IRIS_INDEX]

        cv2.circle(frame_copy, tuple(left_iris), 3, (255, 0, 0), -1)
        cv2.circle(frame_copy, tuple(right_iris), 3, (255, 0, 0), -1)

    # Draw face bounding box
    if face_landmarks.bbox:
        x, y, w, h = face_landmarks.bbox
        cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (255, 0, 0), 2)

    return frame_copy


if __name__ == "__main__":
    # Test face detection
    import sys

    logging.basicConfig(level=logging.INFO)

    detector = FaceDetector()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open webcam")
        sys.exit(1)

    print("Face Detection Test - Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detector.detect(frame)

        if faces:
            face = faces[0]
            frame = visualize_landmarks(frame, face, draw_iris=True)
            print(f"Face detected - Confidence: {face.face_confidence:.2f}")

        cv2.imshow("Face Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.release()

    print("✓ Face detection test completed")
