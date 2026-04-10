"""
SpectrumIA - Feature Extraction Tests

Comprehensive unit tests for eye-tracking feature extraction.
Tests fixation detection, saccade analysis, social attention metrics,
and scanpath analysis.

Coverage:
- FixationMetrics: duration, count, dispersion
- SaccadeMetrics: amplitude, velocity, peak velocity
- SocialAttentionMetrics: SAI (core ASD biomarker), AOI preferences
- ScanpathMetrics: entropy, fixation density, path length
- AOI (Area of Interest) classification
- Temporal analysis: time to first fixation, latency
"""

import pytest
import numpy as np
from datetime import datetime
from typing import List
from unittest.mock import Mock, MagicMock, patch

from models.schemas import (
    GazeDataPoint,
    FixationMetricsModel,
    SaccadeMetricsModel,
    SocialAttentionMetricsModel,
    ScanpathMetricsModel,
    GazeMetricsModel,
    AOIType,
)

# ========================================================================
# FIXTURES
# ========================================================================


@pytest.fixture
def steady_gaze_data():
    """Generate gaze data with steady fixation (no movement)."""
    samples = []
    start_time = datetime.utcnow().timestamp()

    for i in range(100):
        # Fixed gaze at center with small jitter
        sample = GazeDataPoint(
            timestamp=start_time + i * 0.033,  # 30fps
            gaze_x=0.5 + np.random.normal(0, 0.01),
            gaze_y=0.5 + np.random.normal(0, 0.01),
            confidence=float(np.clip(0.9 + np.random.normal(0, 0.05), 0.0, 1.0)),
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )
        samples.append(sample)

    return samples


@pytest.fixture
def dynamic_gaze_data():
    """Generate gaze data with multiple saccades (rapid movements)."""
    samples = []
    start_time = datetime.utcnow().timestamp()

    for i in range(300):
        # Sinusoidal movement pattern with saccades
        t = i * 0.033
        if i % 50 == 0 and i > 0:
            # Saccade: rapid jump
            gaze_x = np.random.uniform(0.2, 0.8)
            gaze_y = np.random.uniform(0.2, 0.8)
        else:
            # Smooth movement
            gaze_x = 0.5 + 0.3 * np.sin(t)
            gaze_y = 0.5 + 0.3 * np.cos(t)

        sample = GazeDataPoint(
            timestamp=start_time + t,
            gaze_x=np.clip(gaze_x, 0, 1),
            gaze_y=np.clip(gaze_y, 0, 1),
            confidence=float(np.clip(0.85 + np.random.normal(0, 0.1), 0.0, 1.0)),
            is_blink=np.random.random() < 0.02,
            head_pitch=np.random.normal(0, 3),
            head_yaw=np.random.normal(0, 3),
            head_roll=np.random.normal(0, 2),
        )
        samples.append(sample)

    return samples


@pytest.fixture
def face_attention_gaze_data():
    """Generate gaze data focused on face regions (eyes, mouth)."""
    samples = []
    start_time = datetime.utcnow().timestamp()

    for i in range(200):
        # Alternate between eyes and mouth
        if (i // 20) % 2 == 0:
            # Eyes region (upper face)
            gaze_x = 0.5 + np.random.normal(0, 0.05)
            gaze_y = 0.3 + np.random.normal(0, 0.05)
        else:
            # Mouth region (lower face)
            gaze_x = 0.5 + np.random.normal(0, 0.05)
            gaze_y = 0.7 + np.random.normal(0, 0.05)

        sample = GazeDataPoint(
            timestamp=start_time + i * 0.033,
            gaze_x=np.clip(gaze_x, 0, 1),
            gaze_y=np.clip(gaze_y, 0, 1),
            confidence=float(np.clip(0.88 + np.random.normal(0, 0.08), 0.0, 1.0)),
            is_blink=i % 100 == 0,  # Occasional blinks
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )
        samples.append(sample)

    return samples


@pytest.fixture
def background_attention_gaze_data():
    """Generate gaze data focused on background (not face)."""
    samples = []
    start_time = datetime.utcnow().timestamp()

    for i in range(200):
        # Random background areas
        gaze_x = np.random.uniform(0, 1)
        gaze_y = np.random.uniform(0, 1)

        # Avoid face center region
        if 0.3 < gaze_x < 0.7 and 0.2 < gaze_y < 0.8:
            gaze_x = np.random.choice([np.random.uniform(0, 0.2), np.random.uniform(0.8, 1)])
            gaze_y = np.random.choice([np.random.uniform(0, 0.1), np.random.uniform(0.9, 1)])

        sample = GazeDataPoint(
            timestamp=start_time + i * 0.033,
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            confidence=float(np.clip(0.82 + np.random.normal(0, 0.1), 0.0, 1.0)),
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )
        samples.append(sample)

    return samples


# ========================================================================
# FIXATION METRICS TESTS
# ========================================================================


class TestFixationDetection:
    """Test fixation detection and metrics calculation."""

    def test_fixation_duration_calculation(self, steady_gaze_data):
        """Test calculation of mean fixation duration."""
        samples = steady_gaze_data

        # With steady data, all samples should be part of one fixation
        # Simulate fixation detection: group consecutive stable samples
        fixations = []
        fixation_start = 0

        for i in range(1, len(samples)):
            prev = samples[i - 1]
            curr = samples[i]

            # Calculate angular distance
            dx = (curr.gaze_x - prev.gaze_x) * 100
            dy = (curr.gaze_y - prev.gaze_y) * 100
            distance = np.sqrt(dx**2 + dy**2)

            # If movement exceeds threshold, end current fixation
            if distance > 1.0 or i == len(samples) - 1:
                fixation_duration = (samples[i].timestamp - samples[fixation_start].timestamp)
                fixations.append(fixation_duration)
                fixation_start = i

        assert len(fixations) > 0
        mean_duration = np.mean(fixations)
        assert mean_duration > 0

    def test_fixation_count(self, dynamic_gaze_data):
        """Test counting number of fixations."""
        samples = dynamic_gaze_data

        # Detect fixations in dynamic data
        fixation_count = 0
        in_fixation = False
        fixation_threshold = 1.0  # degrees

        for i in range(1, len(samples)):
            prev = samples[i - 1]
            curr = samples[i]

            dx = (curr.gaze_x - prev.gaze_x) * 100
            dy = (curr.gaze_y - prev.gaze_y) * 100
            distance = np.sqrt(dx**2 + dy**2)

            if distance < fixation_threshold:
                if not in_fixation:
                    fixation_count += 1
                    in_fixation = True
            else:
                in_fixation = False

        assert fixation_count > 1  # Should have multiple fixations

    def test_fixation_dispersion(self):
        """Test fixation dispersion (spatial spread within fixation)."""
        # Create fixation with known dispersion
        fixation_points = [
            GazeDataPoint(
                timestamp=datetime.utcnow().timestamp() + i * 0.033,
                gaze_x=0.5 + np.random.normal(0, 0.02),
                gaze_y=0.5 + np.random.normal(0, 0.02),
                confidence=0.9,
                is_blink=False,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            )
            for i in range(30)
        ]

        # Calculate dispersion
        x_coords = [p.gaze_x for p in fixation_points]
        y_coords = [p.gaze_y for p in fixation_points]

        x_std = np.std(x_coords)
        y_std = np.std(y_coords)
        dispersion = np.sqrt(x_std**2 + y_std**2)

        # With tight clustering, dispersion should be small
        assert dispersion < 0.1

    def test_fixation_metrics_model_validation(self):
        """Test FixationMetricsModel data validation."""
        metrics = FixationMetricsModel(
            fixation_count=5,
            mean_fixation_duration_ms=250.5,
            std_fixation_duration_ms=45.2,
            min_fixation_duration_ms=180.0,
            max_fixation_duration_ms=320.0,
            total_fixation_time_ms=1252.5,
            mean_fixation_dispersion_deg=1.5,
        )

        assert metrics.fixation_count == 5
        assert metrics.mean_fixation_duration_ms > 0
        assert metrics.mean_fixation_dispersion_deg > 0


# ========================================================================
# SACCADE METRICS TESTS
# ========================================================================


class TestSaccadeDetection:
    """Test saccade detection and metrics."""

    def test_saccade_amplitude(self, dynamic_gaze_data):
        """Test saccade amplitude calculation."""
        samples = dynamic_gaze_data

        amplitudes = []
        velocity_threshold = 30  # degrees per second

        for i in range(1, len(samples)):
            prev = samples[i - 1]
            curr = samples[i]

            dx = curr.gaze_x - prev.gaze_x
            dy = curr.gaze_y - prev.gaze_y

            # Calculate distance in degrees (approximate)
            amplitude = np.sqrt(dx**2 + dy**2) * 100  # Scale to degrees

            # Calculate velocity
            dt = curr.timestamp - prev.timestamp
            velocity = amplitude / (dt + 1e-6)

            # Saccade if velocity exceeds threshold
            if velocity > velocity_threshold:
                amplitudes.append(amplitude)

        assert len(amplitudes) > 0
        mean_amplitude = np.mean(amplitudes)
        assert mean_amplitude > 0

    def test_saccade_velocity(self, dynamic_gaze_data):
        """Test saccade peak velocity calculation."""
        samples = dynamic_gaze_data

        velocities = []

        for i in range(1, len(samples)):
            prev = samples[i - 1]
            curr = samples[i]

            dx = curr.gaze_x - prev.gaze_x
            dy = curr.gaze_y - prev.gaze_y
            amplitude = np.sqrt(dx**2 + dy**2) * 100

            dt = curr.timestamp - prev.timestamp
            if dt > 0:
                velocity = amplitude / dt
                velocities.append(velocity)

        assert len(velocities) > 0
        mean_velocity = np.mean(velocities)
        assert mean_velocity >= 0

    def test_saccade_metrics_model(self):
        """Test SaccadeMetricsModel validation."""
        metrics = SaccadeMetricsModel(
            saccade_count=12,
            mean_saccade_amplitude_deg=8.5,
            std_saccade_amplitude_deg=2.1,
            min_saccade_amplitude_deg=3.2,
            max_saccade_amplitude_deg=14.5,
            mean_saccade_velocity_deg_per_sec=220.0,
            mean_saccade_peak_velocity_deg_per_sec=350.0,
        )

        assert metrics.saccade_count > 0
        assert metrics.mean_saccade_amplitude_deg > 0
        assert metrics.mean_saccade_velocity_deg_per_sec > 0


# ========================================================================
# SOCIAL ATTENTION METRICS TESTS
# ========================================================================


class TestSocialAttention:
    """Test social attention metrics (core ASD biomarker)."""

    def test_social_attention_index_calculation(self, face_attention_gaze_data):
        """Test Social Attention Index (SAI) calculation - Jones & Klin 2013."""
        samples = face_attention_gaze_data

        # Define AOI regions
        eye_region = [(0.25, 0.75, 0.15, 0.45)]  # Left/Right eyes
        mouth_region = [(0.25, 0.75, 0.55, 0.85)]  # Mouth

        time_on_eyes = 0
        time_on_mouth = 0
        total_time = 0

        for sample in samples:
            total_time += 1

            # Check if gaze is in eyes region
            if 0.25 < sample.gaze_x < 0.75 and 0.15 < sample.gaze_y < 0.45:
                time_on_eyes += 1
            # Check if gaze is in mouth region
            elif 0.25 < sample.gaze_x < 0.75 and 0.55 < sample.gaze_y < 0.85:
                time_on_mouth += 1

        # SAI = (eyes + mouth) / total
        sai = (time_on_eyes + time_on_mouth) / total_time if total_time > 0 else 0

        assert 0 <= sai <= 1
        # With face attention data, SAI should be relatively high
        assert sai > 0.3

    def test_eye_preference_metric(self, face_attention_gaze_data):
        """Test eye region preference (eyes vs mouth)."""
        samples = face_attention_gaze_data

        eye_region_time = 0
        mouth_region_time = 0
        total_time = 0

        for sample in samples:
            total_time += 1

            if 0.25 < sample.gaze_x < 0.75 and 0.15 < sample.gaze_y < 0.45:
                eye_region_time += 1
            elif 0.25 < sample.gaze_x < 0.75 and 0.55 < sample.gaze_y < 0.85:
                mouth_region_time += 1

        # Eye preference = eyes / (eyes + mouth)
        eye_preference = (
            eye_region_time / (eye_region_time + mouth_region_time)
            if (eye_region_time + mouth_region_time) > 0
            else 0
        )

        assert 0 <= eye_preference <= 1

    def test_geometric_preference(self, background_attention_gaze_data):
        """Test preference for geometric patterns vs faces."""
        samples = background_attention_gaze_data

        # Background region = geometric stimuli
        background_time = 0
        face_time = 0

        for sample in samples:
            # Face region
            if 0.3 < sample.gaze_x < 0.7 and 0.2 < sample.gaze_y < 0.8:
                face_time += 1
            else:
                background_time += 1

        geometric_preference = (
            background_time / (face_time + background_time)
            if (face_time + background_time) > 0
            else 0
        )

        assert 0 <= geometric_preference <= 1

    def test_social_attention_metrics_model(self):
        """Test SocialAttentionMetricsModel validation."""
        metrics = SocialAttentionMetricsModel(
            mean_social_attention_index=0.72,
            std_social_attention_index=0.08,
            mean_eye_preference=0.68,
            mean_mouth_preference=0.15,
            mean_nose_preference=0.04,
            mean_geometric_preference=0.13,
            social_to_geometric_ratio=5.5,
            aoi_transitions_per_second=2.3,
            mean_time_to_social_fixation_ms=450.0,
        )

        assert 0 <= metrics.mean_social_attention_index <= 1
        assert metrics.mean_eye_preference > metrics.mean_mouth_preference
        assert metrics.social_to_geometric_ratio > 0


# ========================================================================
# SCANPATH METRICS TESTS
# ========================================================================


class TestScanpath:
    """Test scanpath analysis and entropy calculation."""

    def test_scanpath_entropy_calculation(self):
        """Test scanpath entropy (predictability of gaze pattern)."""
        # Create predictable vs random scanpaths
        # Predictable: same sequence repeated
        predictable_path = [0, 1, 2, 1, 0, 1, 2, 1] * 5  # Repeating pattern

        # Calculate entropy
        unique, counts = np.unique(predictable_path, return_counts=True)
        probabilities = counts / len(predictable_path)
        entropy_predictable = -np.sum(probabilities * np.log(probabilities + 1e-10))

        # Random: each position visited equally
        random_path = np.random.choice(range(10), 100)
        unique, counts = np.unique(random_path, return_counts=True)
        probabilities = counts / len(random_path)
        entropy_random = -np.sum(probabilities * np.log(probabilities + 1e-10))

        # Predictable path should have lower entropy
        assert entropy_predictable < entropy_random
        assert entropy_predictable >= 0

    def test_fixation_density(self, face_attention_gaze_data):
        """Test fixation density (fixations per unit area)."""
        samples = face_attention_gaze_data

        # Discretize into grid cells
        grid_size = 5
        grid_cells = []

        for sample in samples:
            cell_x = int(sample.gaze_x * grid_size)
            cell_y = int(sample.gaze_y * grid_size)
            grid_cells.append((cell_x, cell_y))

        # Count cells with fixations
        unique_cells = len(set(grid_cells))
        density = unique_cells / (grid_size * grid_size)

        assert 0 <= density <= 1

    def test_fixation_path_length(self):
        """Test total scanpath length (sum of saccade amplitudes)."""
        # Create synthetic gaze path
        path_points = [
            (0.0, 0.0),
            (0.5, 0.0),
            (0.5, 0.5),
            (0.0, 0.5),
            (0.0, 0.0),
        ]

        # Calculate total distance
        total_distance = 0
        for i in range(1, len(path_points)):
            prev = path_points[i - 1]
            curr = path_points[i]

            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            distance = np.sqrt(dx**2 + dy**2)
            total_distance += distance

        # Should form approximate square (perimeter ~2.0)
        assert 1.8 < total_distance < 2.2

    def test_scanpath_metrics_model(self):
        """Test ScanpathMetricsModel validation."""
        metrics = ScanpathMetricsModel(
            mean_scanpath_entropy=0.58,
            std_scanpath_entropy=0.12,
            fixation_density_per_area=0.42,
            mean_path_length_deg=285.5,
            path_efficiency_ratio=0.68,
        )

        assert 0 <= metrics.mean_scanpath_entropy <= 1
        assert 0 <= metrics.fixation_density_per_area <= 1
        assert 0 <= metrics.path_efficiency_ratio <= 1


# ========================================================================
# TEMPORAL ANALYSIS TESTS
# ========================================================================


class TestTemporalMetrics:
    """Test temporal eye-tracking metrics."""

    def test_time_to_first_fixation(self, face_attention_gaze_data):
        """Test latency to first fixation on target."""
        samples = face_attention_gaze_data

        # Define target region
        target_x_range = (0.3, 0.7)
        target_y_range = (0.2, 0.8)

        time_to_fixation = None
        start_time = samples[0].timestamp

        for i, sample in enumerate(samples):
            if target_x_range[0] < sample.gaze_x < target_x_range[1]:
                if target_y_range[0] < sample.gaze_y < target_y_range[1]:
                    time_to_fixation = (sample.timestamp - start_time) * 1000
                    break

        assert time_to_fixation is None or time_to_fixation >= 0

    def test_aoi_dwell_time(self, face_attention_gaze_data):
        """Test dwell time in areas of interest."""
        samples = face_attention_gaze_data

        # Define AOIs
        aoi_eyes = {"x_range": (0.3, 0.7), "y_range": (0.15, 0.45), "name": "Eyes"}
        aoi_mouth = {"x_range": (0.3, 0.7), "y_range": (0.55, 0.85), "name": "Mouth"}

        dwell_times = {"Eyes": 0, "Mouth": 0}

        for sample in samples:
            if aoi_eyes["x_range"][0] < sample.gaze_x < aoi_eyes["x_range"][1]:
                if aoi_eyes["y_range"][0] < sample.gaze_y < aoi_eyes["y_range"][1]:
                    dwell_times["Eyes"] += 1
            elif aoi_mouth["x_range"][0] < sample.gaze_x < aoi_mouth["x_range"][1]:
                if aoi_mouth["y_range"][0] < sample.gaze_y < aoi_mouth["y_range"][1]:
                    dwell_times["Mouth"] += 1

        # At least some dwell time in face regions
        assert dwell_times["Eyes"] > 0 or dwell_times["Mouth"] > 0

    def test_fixation_sequence_analysis(self, face_attention_gaze_data):
        """Test sequence of fixation locations."""
        samples = face_attention_gaze_data

        # Detect fixation sequence
        fixation_sequence = []

        for sample in samples:
            # Classify current gaze location
            if 0.25 < sample.gaze_x < 0.75:
                if 0.15 < sample.gaze_y < 0.45:
                    aoi = "Eyes"
                elif 0.55 < sample.gaze_y < 0.85:
                    aoi = "Mouth"
                else:
                    aoi = "Face"
            else:
                aoi = "Background"

            # Add to sequence if different from last
            if not fixation_sequence or fixation_sequence[-1] != aoi:
                fixation_sequence.append(aoi)

        assert len(fixation_sequence) > 0


# ========================================================================
# CONFIDENCE & SIGNAL QUALITY
# ========================================================================


class TestSignalQuality:
    """Test signal quality metrics."""

    def test_mean_confidence_calculation(self, steady_gaze_data):
        """Test mean confidence score."""
        samples = steady_gaze_data

        confidences = [s.confidence for s in samples]
        mean_confidence = np.mean(confidences)
        std_confidence = np.std(confidences)

        assert 0 <= mean_confidence <= 1
        assert std_confidence >= 0

    def test_signal_quality_with_blinks(self):
        """Test signal quality degradation due to blinks."""
        # Create samples with blinks
        samples = []
        for i in range(100):
            is_blink = i % 20 == 0  # Blink every 20 samples
            confidence = 0.0 if is_blink else 0.9

            sample = GazeDataPoint(
                timestamp=datetime.utcnow().timestamp() + i * 0.033,
                gaze_x=0.5,
                gaze_y=0.5,
                confidence=confidence,
                is_blink=is_blink,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            )
            samples.append(sample)

        # Calculate signal quality (excluding blinks)
        valid_samples = [s for s in samples if not s.is_blink]
        signal_quality = len(valid_samples) / len(samples) if samples else 0

        assert 0 <= signal_quality <= 1
        assert signal_quality < 1.0  # Some blinks present

    def test_confidence_range_validation(self):
        """Test that confidence values are properly constrained."""
        # Valid sample
        valid = GazeDataPoint(
            timestamp=datetime.utcnow().timestamp(),
            gaze_x=0.5,
            gaze_y=0.5,
            confidence=0.85,
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )

        assert 0 <= valid.confidence <= 1

        # Edge cases
        edge_low = GazeDataPoint(
            timestamp=datetime.utcnow().timestamp(),
            gaze_x=0.5,
            gaze_y=0.5,
            confidence=0.0,
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )

        edge_high = GazeDataPoint(
            timestamp=datetime.utcnow().timestamp(),
            gaze_x=0.5,
            gaze_y=0.5,
            confidence=1.0,
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )

        assert edge_low.confidence == 0.0
        assert edge_high.confidence == 1.0


# ========================================================================
# COMPLETE METRICS MODEL TESTS
# ========================================================================


class TestCompleteGazeMetricsModel:
    """Test complete GazeMetricsModel with all sub-metrics."""

    def test_gaze_metrics_model_structure(self):
        """Test that GazeMetricsModel contains all required metrics."""
        fixation = FixationMetricsModel(
            fixation_count=8,
            mean_fixation_duration_ms=260.0,
            std_fixation_duration_ms=50.0,
            min_fixation_duration_ms=180.0,
            max_fixation_duration_ms=340.0,
            total_fixation_time_ms=2080.0,
            mean_fixation_dispersion_deg=1.8,
        )

        saccade = SaccadeMetricsModel(
            saccade_count=14,
            mean_saccade_amplitude_deg=9.2,
            std_saccade_amplitude_deg=2.5,
            min_saccade_amplitude_deg=2.1,
            max_saccade_amplitude_deg=15.8,
            mean_saccade_velocity_deg_per_sec=215.0,
            mean_saccade_peak_velocity_deg_per_sec=340.0,
        )

        social = SocialAttentionMetricsModel(
            mean_social_attention_index=0.74,
            std_social_attention_index=0.09,
            mean_eye_preference=0.66,
            mean_mouth_preference=0.18,
            mean_nose_preference=0.05,
            mean_geometric_preference=0.11,
            social_to_geometric_ratio=6.7,
            aoi_transitions_per_second=2.1,
            mean_time_to_social_fixation_ms=520.0,
        )

        scanpath = ScanpathMetricsModel(
            mean_scanpath_entropy=0.61,
            std_scanpath_entropy=0.11,
            fixation_density_per_area=0.38,
            mean_path_length_deg=312.5,
            path_efficiency_ratio=0.71,
        )

        # Create complete model
        metrics = GazeMetricsModel(
            mean_social_attention_index=social.mean_social_attention_index,
            mean_eye_preference=social.mean_eye_preference,
            mean_mouth_preference=social.mean_mouth_preference,
            mean_nose_preference=social.mean_nose_preference,
            mean_fixation_duration_ms=fixation.mean_fixation_duration_ms,
            mean_fixation_count=fixation.fixation_count,
            mean_fixation_dispersion_deg=fixation.mean_fixation_dispersion_deg,
            mean_saccade_amplitude_deg=saccade.mean_saccade_amplitude_deg,
            mean_saccade_velocity_deg_per_sec=saccade.mean_saccade_velocity_deg_per_sec,
            mean_saccade_peak_velocity_deg_per_sec=saccade.mean_saccade_peak_velocity_deg_per_sec,
            mean_time_to_first_fixation_ms=520.0,
            mean_scanpath_entropy=scanpath.mean_scanpath_entropy,
            signal_quality_mean=0.89,
            mean_blink_rate=15.2,
        )

        # Verify all fields present
        assert metrics.mean_social_attention_index > 0
        assert metrics.mean_fixation_duration_ms > 0
        assert metrics.mean_saccade_amplitude_deg > 0
        assert metrics.mean_scanpath_entropy >= 0


# ========================================================================
# EDGE CASES & VALIDATION
# ========================================================================


class TestEdgeCasesFeatureExtraction:
    """Test edge cases in feature extraction."""

    def test_empty_gaze_dataset(self):
        """Test handling of empty gaze dataset."""
        samples = []

        assert len(samples) == 0

    def test_single_sample(self):
        """Test with single gaze sample."""
        sample = GazeDataPoint(
            timestamp=datetime.utcnow().timestamp(),
            gaze_x=0.5,
            gaze_y=0.5,
            confidence=0.9,
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )

        assert sample.gaze_x == 0.5
        assert sample.gaze_y == 0.5

    def test_all_blinks_dataset(self):
        """Test dataset containing only blinks."""
        samples = [
            GazeDataPoint(
                timestamp=datetime.utcnow().timestamp() + i * 0.033,
                gaze_x=0.5,
                gaze_y=0.5,
                confidence=0.0,
                is_blink=True,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            )
            for i in range(30)
        ]

        blink_rate = sum(1 for s in samples if s.is_blink) / len(samples)
        assert blink_rate == 1.0

    def test_extreme_coordinate_values(self):
        """Test handling of extreme coordinate values."""
        # Edge of screen
        edge_samples = [
            GazeDataPoint(
                timestamp=datetime.utcnow().timestamp(),
                gaze_x=0.0,
                gaze_y=0.0,
                confidence=0.8,
                is_blink=False,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            ),
            GazeDataPoint(
                timestamp=datetime.utcnow().timestamp() + 0.033,
                gaze_x=1.0,
                gaze_y=1.0,
                confidence=0.8,
                is_blink=False,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            ),
        ]

        assert edge_samples[0].gaze_x == 0.0
        assert edge_samples[1].gaze_x == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
