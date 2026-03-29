"""
Eye-Tracking Feature Extraction

Extracts scientifically validated eye-tracking metrics from gaze data.
Based on research from Harvard/MGH, Duke, and meta-analysis studies.

References:
- Klin et al. (2002) - Visual fixation patterns
- Jones & Klin (2013) - Attention to eyes
- Frazier et al. (2018) - Gaze meta-analysis
- Carpenter et al. (2021) - Digital behavioral phenotyping
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

from .utils import calculate_euclidean_distance

logger = logging.getLogger(__name__)


class AOIType(Enum):
    """Area of Interest types."""

    EYES = "eyes"
    MOUTH = "mouth"
    NOSE = "nose"
    FACE_OVAL = "face_oval"
    BACKGROUND = "background"


@dataclass
class FixationMetrics:
    """Fixation analysis metrics."""

    count: int = 0
    mean_duration_ms: float = 0.0
    median_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    std_duration_ms: float = 0.0


@dataclass
class SaccadeMetrics:
    """Saccade analysis metrics."""

    count: int = 0
    mean_amplitude_deg: float = 0.0
    mean_velocity_deg_per_sec: float = 0.0
    median_velocity_deg_per_sec: float = 0.0
    mean_peak_velocity_deg_per_sec: float = 0.0
    latency_ms: float = 0.0


@dataclass
class SocialAttentionMetrics:
    """Social attention metrics."""

    social_attention_index: float = 0.0  # (eyes + mouth) / total
    eye_preference: float = 0.0  # eyes / (eyes + mouth)
    mouth_preference: float = 0.0  # mouth / (eyes + mouth)
    time_on_eyes_ms: float = 0.0
    time_on_mouth_ms: float = 0.0
    time_on_face_ms: float = 0.0
    attention_shifts: int = 0  # Transitions between ROIs


@dataclass
class ScanpathMetrics:
    """Scanpath and temporal metrics."""

    entropy: float = 0.0  # Predictability of scan pattern
    time_to_first_fixation_ms: float = 0.0
    fixation_density: float = 0.0  # Fixations per second
    transition_count: int = 0
    path_length_deg: float = 0.0  # Total distance traveled
    mean_gaze_position: Tuple[float, float] = (0.0, 0.0)


@dataclass
class GazeMetrics:
    """Comprehensive eye-tracking metrics."""

    timestamp: float = 0.0
    stimulus_id: Optional[str] = None

    # Detailed metrics
    fixations: FixationMetrics = field(default_factory=FixationMetrics)
    saccades: SaccadeMetrics = field(default_factory=SaccadeMetrics)
    social_attention: SocialAttentionMetrics = field(default_factory=SocialAttentionMetrics)
    scanpath: ScanpathMetrics = field(default_factory=ScanpathMetrics)

    # Per-AOI metrics
    aoi_metrics: Dict[str, Dict] = field(default_factory=dict)

    # Global metrics
    blink_count: int = 0
    blink_rate: float = 0.0  # Blinks per minute
    gaze_confidence_mean: float = 0.0
    signal_quality: float = 0.0  # 0-1, 1 = excellent


class FeatureExtractor:
    """
    Extract eye-tracking features from gaze data streams.

    This class processes raw gaze points and facial landmarks to compute
    validated metrics for ASD screening based on scientific literature.
    """

    # Fixation thresholds
    FIXATION_DURATION_MIN_MS = 100
    FIXATION_DURATION_MAX_MS = 1000
    FIXATION_DISPERSION_THRESHOLD_DEG = 1.0

    # Saccade thresholds
    SACCADE_VELOCITY_MIN_DEG_PER_SEC = 30
    SACCADE_VELOCITY_MAX_DEG_PER_SEC = 700

    # AOI definitions (normalized 0-1)
    AOI_DEFINITIONS = {
        AOIType.EYES: (0.3, 0.2, 0.7, 0.4),  # x_min, y_min, x_max, y_max
        AOIType.MOUTH: (0.35, 0.6, 0.65, 0.85),
        AOIType.NOSE: (0.4, 0.35, 0.6, 0.6),
        AOIType.FACE_OVAL: (0.2, 0.1, 0.8, 0.95),
        AOIType.BACKGROUND: (0.0, 0.0, 1.0, 1.0),
    }

    def __init__(
        self,
        ppd: float = 60.0,  # Pixels per degree (depends on monitor/distance)
        sampling_rate_hz: float = 30.0,
    ):
        """
        Initialize Feature Extractor.

        Args:
            ppd: Pixels per degree of visual angle
            sampling_rate_hz: Gaze sampling rate in Hz
        """
        self.ppd = ppd
        self.sampling_rate_hz = sampling_rate_hz
        self.frame_duration_ms = 1000 / sampling_rate_hz

        # Gaze history
        self.gaze_history: List[Tuple[float, float, float]] = []  # (x, y, timestamp)
        self.face_landmarks_history = []
        self.blink_history: List[Tuple[float, bool]] = []  # (timestamp, is_blink)
        self.confidence_history: List[float] = []

        # Processing buffers
        self.current_fixation_start = None
        self.current_fixation_points = []
        self.fixations = []
        self.saccades = []

    def add_gaze_sample(
        self,
        gaze_x: float,
        gaze_y: float,
        timestamp: float,
        confidence: float = 1.0,
        is_blink: bool = False,
    ) -> None:
        """
        Add a gaze sample to the processing buffer.

        Args:
            gaze_x: Gaze x coordinate (normalized 0-1)
            gaze_y: Gaze y coordinate (normalized 0-1)
            timestamp: Timestamp in seconds
            confidence: Confidence score 0-1
            is_blink: Whether a blink was detected
        """
        self.gaze_history.append((gaze_x, gaze_y, timestamp))
        self.confidence_history.append(confidence)
        self.blink_history.append((timestamp, is_blink))

        # Detect fixations and saccades
        if len(self.gaze_history) > 1:
            self._update_fixation_detection()

    def extract_features(self, stimulus_id: Optional[str] = None) -> GazeMetrics:
        """
        Extract all features from collected gaze data.

        Args:
            stimulus_id: Optional identifier for stimulus

        Returns:
            GazeMetrics object with all computed metrics
        """
        if not self.gaze_history:
            logger.warning("No gaze data available for feature extraction")
            return GazeMetrics()

        # Compute individual metrics
        fixation_metrics = self._compute_fixation_metrics()
        saccade_metrics = self._compute_saccade_metrics()
        social_attention = self._compute_social_attention()
        scanpath_metrics = self._compute_scanpath_metrics()
        aoi_metrics = self._compute_aoi_metrics()

        # Blink metrics
        blink_count, blink_rate = self._compute_blink_metrics()

        # Quality metrics
        confidence_mean = float(np.mean(self.confidence_history)) if self.confidence_history else 0.0
        signal_quality = self._compute_signal_quality()

        metrics = GazeMetrics(
            timestamp=self.gaze_history[-1][2],
            stimulus_id=stimulus_id,
            fixations=fixation_metrics,
            saccades=saccade_metrics,
            social_attention=social_attention,
            scanpath=scanpath_metrics,
            aoi_metrics=aoi_metrics,
            blink_count=blink_count,
            blink_rate=blink_rate,
            gaze_confidence_mean=confidence_mean,
            signal_quality=signal_quality,
        )

        return metrics

    def _update_fixation_detection(self) -> None:
        """Update fixation and saccade detection with current gaze sample."""
        if len(self.gaze_history) < 2:
            return

        current_x, current_y, current_time = self.gaze_history[-1]
        prev_x, prev_y, prev_time = self.gaze_history[-2]

        # Calculate distance (in degrees)
        distance_pixels = calculate_euclidean_distance((current_x, current_y), (prev_x, prev_y))
        distance_deg = distance_pixels / self.ppd

        # Detect fixation vs saccade
        if distance_deg < self.FIXATION_DISPERSION_THRESHOLD_DEG:
            # Likely part of fixation
            if self.current_fixation_start is None:
                self.current_fixation_start = current_time
            self.current_fixation_points.append((current_x, current_y, current_time))
        else:
            # Saccade detected - end current fixation
            if self.current_fixation_start is not None and len(self.current_fixation_points) > 2:
                fixation_duration = current_time - self.current_fixation_start
                if self.FIXATION_DURATION_MIN_MS / 1000 <= fixation_duration <= self.FIXATION_DURATION_MAX_MS / 1000:
                    self.fixations.append({
                        "start_time": self.current_fixation_start,
                        "end_time": current_time,
                        "duration": fixation_duration * 1000,
                        "points": self.current_fixation_points,
                        "center": (
                            np.mean([p[0] for p in self.current_fixation_points]),
                            np.mean([p[1] for p in self.current_fixation_points]),
                        ),
                    })

            # Record saccade
            duration = current_time - prev_time
            if duration > 0:
                velocity = distance_deg / duration
                if self.SACCADE_VELOCITY_MIN_DEG_PER_SEC <= velocity <= self.SACCADE_VELOCITY_MAX_DEG_PER_SEC:
                    self.saccades.append({
                        "start_time": prev_time,
                        "end_time": current_time,
                        "amplitude_deg": distance_deg,
                        "velocity_deg_per_sec": velocity,
                    })

            # Reset fixation buffer
            self.current_fixation_start = None
            self.current_fixation_points = []

    def _compute_fixation_metrics(self) -> FixationMetrics:
        """Compute fixation-related metrics."""
        if not self.fixations:
            return FixationMetrics()

        durations = [f["duration"] for f in self.fixations]

        return FixationMetrics(
            count=len(self.fixations),
            mean_duration_ms=float(np.mean(durations)),
            median_duration_ms=float(np.median(durations)),
            min_duration_ms=float(np.min(durations)),
            max_duration_ms=float(np.max(durations)),
            total_duration_ms=float(np.sum(durations)),
            std_duration_ms=float(np.std(durations)),
        )

    def _compute_saccade_metrics(self) -> SaccadeMetrics:
        """Compute saccade-related metrics."""
        if not self.saccades:
            return SaccadeMetrics()

        amplitudes = [s["amplitude_deg"] for s in self.saccades]
        velocities = [s["velocity_deg_per_sec"] for s in self.saccades]

        return SaccadeMetrics(
            count=len(self.saccades),
            mean_amplitude_deg=float(np.mean(amplitudes)),
            mean_velocity_deg_per_sec=float(np.mean(velocities)),
            median_velocity_deg_per_sec=float(np.median(velocities)),
            mean_peak_velocity_deg_per_sec=float(np.max(velocities)) if velocities else 0.0,
        )

    def _compute_social_attention(self) -> SocialAttentionMetrics:
        """Compute social attention metrics (core ASD screening metric)."""
        # Determine which fixations fall in eyes and mouth AOIs
        eyes_time = 0.0
        mouth_time = 0.0
        face_time = 0.0

        for fixation in self.fixations:
            center_x, center_y = fixation["center"]
            duration = fixation["duration"]

            # Check AOI membership
            if self._point_in_aoi((center_x, center_y), AOIType.EYES):
                eyes_time += duration
            if self._point_in_aoi((center_x, center_y), AOIType.MOUTH):
                mouth_time += duration
            if self._point_in_aoi((center_x, center_y), AOIType.FACE_OVAL):
                face_time += duration

        # Calculate SAI (Social Attention Index)
        social_time = eyes_time + mouth_time
        sai = social_time / face_time if face_time > 0 else 0.0

        # Calculate preferences
        total_social = social_time
        eye_pref = eyes_time / total_social if total_social > 0 else 0.0
        mouth_pref = mouth_time / total_social if total_social > 0 else 0.0

        # Count attention shifts
        attention_shifts = 0
        prev_aoi = None
        for fixation in self.fixations:
            center_x, center_y = fixation["center"]
            current_aoi = None

            if self._point_in_aoi((center_x, center_y), AOIType.EYES):
                current_aoi = AOIType.EYES
            elif self._point_in_aoi((center_x, center_y), AOIType.MOUTH):
                current_aoi = AOIType.MOUTH

            if prev_aoi and current_aoi and prev_aoi != current_aoi:
                attention_shifts += 1

            prev_aoi = current_aoi

        return SocialAttentionMetrics(
            social_attention_index=float(sai),
            eye_preference=float(eye_pref),
            mouth_preference=float(mouth_pref),
            time_on_eyes_ms=float(eyes_time),
            time_on_mouth_ms=float(mouth_time),
            time_on_face_ms=float(face_time),
            attention_shifts=attention_shifts,
        )

    def _compute_scanpath_metrics(self) -> ScanpathMetrics:
        """Compute scanpath and temporal metrics."""
        if not self.gaze_history:
            return ScanpathMetrics()

        # Entropy calculation (Shannon entropy of fixation distributions)
        entropy = self._calculate_scanpath_entropy()

        # Time to first fixation
        ttff = 0.0
        if self.fixations:
            ttff = (self.fixations[0]["start_time"] - self.gaze_history[0][2]) * 1000

        # Fixation density
        total_time = (self.gaze_history[-1][2] - self.gaze_history[0][2])
        fixation_density = len(self.fixations) / total_time if total_time > 0 else 0.0

        # Path length (total distance traveled)
        path_length = 0.0
        for i in range(1, len(self.gaze_history)):
            dist = calculate_euclidean_distance(
                (self.gaze_history[i][0], self.gaze_history[i][1]),
                (self.gaze_history[i-1][0], self.gaze_history[i-1][1]),
            )
            path_length += dist / self.ppd  # Convert to degrees

        # Mean gaze position
        mean_x = np.mean([g[0] for g in self.gaze_history])
        mean_y = np.mean([g[1] for g in self.gaze_history])

        return ScanpathMetrics(
            entropy=entropy,
            time_to_first_fixation_ms=ttff,
            fixation_density=float(fixation_density),
            transition_count=len(self.saccades),
            path_length_deg=float(path_length),
            mean_gaze_position=(float(mean_x), float(mean_y)),
        )

    def _compute_aoi_metrics(self) -> Dict[str, Dict]:
        """Compute per-AOI metrics."""
        aoi_metrics = {}

        for aoi_type in AOIType:
            fixations_in_aoi = []
            total_time = 0.0

            for fixation in self.fixations:
                center = fixation["center"]
                if self._point_in_aoi(center, aoi_type):
                    fixations_in_aoi.append(fixation)
                    total_time += fixation["duration"]

            aoi_metrics[aoi_type.value] = {
                "fixation_count": len(fixations_in_aoi),
                "total_dwell_time_ms": float(total_time),
                "mean_fixation_duration_ms": float(np.mean([f["duration"] for f in fixations_in_aoi]))
                    if fixations_in_aoi else 0.0,
            }

        return aoi_metrics

    def _compute_blink_metrics(self) -> Tuple[int, float]:
        """Compute blink-related metrics."""
        blinks = sum(1 for _, is_blink in self.blink_history if is_blink)

        if not self.gaze_history:
            return blinks, 0.0

        total_time_sec = self.gaze_history[-1][2] - self.gaze_history[0][2]
        blink_rate = (blinks / total_time_sec * 60) if total_time_sec > 0 else 0.0

        return int(blinks), float(blink_rate)

    def _compute_signal_quality(self) -> float:
        """Compute overall signal quality (0-1)."""
        if not self.confidence_history:
            return 0.0

        # Quality based on mean confidence and consistency
        mean_conf = np.mean(self.confidence_history)
        std_conf = np.std(self.confidence_history)

        # Penalize high variance
        consistency = 1.0 - (std_conf / 2.0)
        quality = (mean_conf + consistency) / 2.0

        return float(np.clip(quality, 0.0, 1.0))

    def _calculate_scanpath_entropy(self) -> float:
        """Calculate Shannon entropy of fixation scanpath."""
        if len(self.fixations) < 2:
            return 0.0

        # Discretize gaze into grid
        grid_size = 3
        grid_visits = defaultdict(int)

        for fixation in self.fixations:
            center_x, center_y = fixation["center"]
            grid_x = int(center_x * grid_size)
            grid_y = int(center_y * grid_size)
            grid_x = np.clip(grid_x, 0, grid_size - 1)
            grid_y = np.clip(grid_y, 0, grid_size - 1)

            grid_visits[(grid_x, grid_y)] += 1

        # Calculate entropy
        total_visits = len(self.fixations)
        entropy = 0.0
        for count in grid_visits.values():
            p = count / total_visits
            if p > 0:
                entropy -= p * np.log2(p)

        return float(entropy)

    @staticmethod
    def _point_in_aoi(point: Tuple[float, float], aoi_type: AOIType) -> bool:
        """Check if point is in AOI."""
        x, y = point
        x_min, y_min, x_max, y_max = FeatureExtractor.AOI_DEFINITIONS[aoi_type]

        return x_min <= x <= x_max and y_min <= y <= y_max

    def reset(self) -> None:
        """Reset all buffers for new stimulus."""
        self.gaze_history = []
        self.face_landmarks_history = []
        self.blink_history = []
        self.confidence_history = []
        self.current_fixation_start = None
        self.current_fixation_points = []
        self.fixations = []
        self.saccades = []


if __name__ == "__main__":
    # Test feature extraction
    logging.basicConfig(level=logging.INFO)

    extractor = FeatureExtractor(ppd=60.0, sampling_rate_hz=30.0)

    # Simulate gaze data with fixations
    timestamp = 0.0
    for i in range(100):
        # Fixation on eyes area (0.5, 0.3)
        gaze_x = 0.5 + np.random.normal(0, 0.02)
        gaze_y = 0.3 + np.random.normal(0, 0.02)
        extractor.add_gaze_sample(gaze_x, gaze_y, timestamp, confidence=0.95)
        timestamp += 1 / 30

    # Saccade to mouth area
    for i in range(20):
        gaze_x = 0.5 + i * 0.02
        gaze_y = 0.3 + i * 0.025
        extractor.add_gaze_sample(gaze_x, gaze_y, timestamp, confidence=0.85)
        timestamp += 1 / 30

    # Fixation on mouth area (0.5, 0.7)
    for i in range(80):
        gaze_x = 0.5 + np.random.normal(0, 0.02)
        gaze_y = 0.7 + np.random.normal(0, 0.02)
        extractor.add_gaze_sample(gaze_x, gaze_y, timestamp, confidence=0.95)
        timestamp += 1 / 30

    # Extract features
    metrics = extractor.extract_features(stimulus_id="test_stimulus")

    print("📊 Feature Extraction Results")
    print("=" * 70)
    print(f"Social Attention Index (SAI): {metrics.social_attention.social_attention_index:.3f}")
    print(f"Eye Preference: {metrics.social_attention.eye_preference:.3f}")
    print(f"Mouth Preference: {metrics.social_attention.mouth_preference:.3f}")
    print(f"Fixation Count: {metrics.fixations.count}")
    print(f"Mean Fixation Duration: {metrics.fixations.mean_duration_ms:.1f} ms")
    print(f"Saccade Count: {metrics.saccades.count}")
    print(f"Blink Rate: {metrics.blink_rate:.1f} blinks/min")
    print(f"Signal Quality: {metrics.signal_quality:.3f}")
    print(f"Scanpath Entropy: {metrics.scanpath.entropy:.3f}")
    print("=" * 70)
    print("\n✓ Feature extraction test completed")
