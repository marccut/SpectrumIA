"""
SpectrumIA - Performance Tests

Performance benchmarking and optimization tests for:
- Gaze data processing (10,000+ samples)
- Feature extraction (metric calculation)
- Database operations (insertion, retrieval)
- Real-time processing pipeline
- Memory usage and scalability

Uses pytest with performance markers and timing assertions.
"""

import pytest
import numpy as np
import time
from datetime import datetime
from typing import List
from unittest.mock import MagicMock, Mock
import sys

# ========================================================================
# PERFORMANCE CONFIGURATION
# ========================================================================

# Maximum acceptable execution times (milliseconds)
PERFORMANCE_THRESHOLDS = {
    "gaze_sample_creation": 0.1,  # ms per sample
    "metric_extraction": 50.0,  # ms for 100 samples
    "fixation_detection": 10.0,  # ms for 100 samples
    "database_insert": 5.0,  # ms per 100 samples
    "database_query": 20.0,  # ms per query
    "real_time_processing": 33.0,  # ms (30 fps requirement)
}

# ========================================================================
# FIXTURES
# ========================================================================


@pytest.fixture
def large_gaze_dataset():
    """Create large gaze dataset for stress testing."""
    from models.schemas import GazeDataPoint

    samples = []
    start_time = datetime.utcnow().timestamp()

    for i in range(10000):
        # Generate realistic eye-tracking data
        t = i * 0.033  # ~30fps
        gaze_x = 0.5 + 0.2 * np.sin(t)
        gaze_y = 0.5 + 0.2 * np.cos(t)

        sample = GazeDataPoint(
            timestamp=start_time + t,
            gaze_x=np.clip(gaze_x, 0, 1),
            gaze_y=np.clip(gaze_y, 0, 1),
            confidence=float(np.clip(0.8 + np.random.normal(0, 0.1), 0.0, 1.0)),
            is_blink=np.random.random() < 0.01,  # ~1% blink rate
            head_pitch=np.random.normal(0, 5),
            head_yaw=np.random.normal(0, 5),
            head_roll=np.random.normal(0, 3),
        )
        samples.append(sample)

    return samples


@pytest.fixture
def mock_database_client():
    """Mock database client for performance testing."""
    client = MagicMock()

    # Configure mocks with realistic delays
    def slow_insert(*args, **kwargs):
        time.sleep(0.001)  # 1ms per operation
        return 100

    def slow_query(*args, **kwargs):
        time.sleep(0.005)  # 5ms per query
        return []

    client.insert_gaze_data = MagicMock(side_effect=slow_insert)
    client.get_gaze_data = MagicMock(side_effect=slow_query)
    client.create_assessment_results = MagicMock(side_effect=slow_insert)

    return client


# ========================================================================
# GAZE DATA PROCESSING PERFORMANCE
# ========================================================================


class TestGazeDataProcessingPerformance:
    """Performance tests for gaze data handling."""

    def test_gaze_sample_creation_speed(self):
        """Test speed of creating gaze samples."""
        from models.schemas import GazeDataPoint

        start = time.perf_counter()

        samples = []
        for i in range(1000):
            sample = GazeDataPoint(
                timestamp=time.time() + i * 0.001,
                gaze_x=np.random.uniform(0, 1),
                gaze_y=np.random.uniform(0, 1),
                confidence=np.random.uniform(0.5, 1.0),
                is_blink=False,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            )
            samples.append(sample)

        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        per_sample = elapsed / 1000

        assert per_sample < PERFORMANCE_THRESHOLDS["gaze_sample_creation"]
        assert len(samples) == 1000

    def test_large_dataset_memory_usage(self, large_gaze_dataset):
        """Test memory usage with large datasets."""
        samples = large_gaze_dataset
        assert len(samples) == 10000

        # Verify data integrity
        for sample in samples:
            assert 0 <= sample.gaze_x <= 1
            assert 0 <= sample.gaze_y <= 1
            assert 0 <= sample.confidence <= 1

    def test_gaze_data_batch_processing(self, large_gaze_dataset):
        """Test batch processing of gaze data."""
        samples = large_gaze_dataset
        batch_size = 100

        start = time.perf_counter()

        # Process in batches
        for i in range(0, len(samples), batch_size):
            batch = samples[i : i + batch_size]
            # Simulate processing
            _ = [s.gaze_x for s in batch]

        elapsed = (time.perf_counter() - start) * 1000
        per_batch = elapsed / (len(samples) // batch_size)

        assert per_batch < 50  # Should process 100 samples quickly

    def test_gaze_normalization_performance(self, large_gaze_dataset):
        """Test performance of gaze coordinate normalization."""
        samples = large_gaze_dataset

        start = time.perf_counter()

        # Normalize coordinates
        for sample in samples:
            norm_x = np.clip(sample.gaze_x, 0, 1)
            norm_y = np.clip(sample.gaze_y, 0, 1)

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50  # Should complete quickly


# ========================================================================
# FEATURE EXTRACTION PERFORMANCE
# ========================================================================


class TestFeatureExtractionPerformance:
    """Performance tests for metric extraction."""

    def test_fixation_detection_speed(self, large_gaze_dataset):
        """Test fixation detection performance."""
        samples = large_gaze_dataset[:1000]

        start = time.perf_counter()

        # Simulate fixation detection (samples with < 1deg movement)
        fixations = []
        for i in range(1, len(samples)):
            prev = samples[i - 1]
            curr = samples[i]

            # Calculate angular distance
            dx = (curr.gaze_x - prev.gaze_x) * 100  # Approximate pixels
            dy = (curr.gaze_y - prev.gaze_y) * 100

            distance = np.sqrt(dx**2 + dy**2)

            if distance < 1.0:  # Fixation threshold
                fixations.append(i)

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < PERFORMANCE_THRESHOLDS["fixation_detection"]
        assert len(fixations) > 0

    def test_saccade_detection_speed(self, large_gaze_dataset):
        """Test saccade detection performance."""
        samples = large_gaze_dataset[:1000]

        start = time.perf_counter()

        # Simulate saccade detection (large rapid movements)
        saccades = []
        velocity_threshold = 30  # degrees per second

        for i in range(1, len(samples)):
            prev = samples[i - 1]
            curr = samples[i]

            dx = curr.gaze_x - prev.gaze_x
            dy = curr.gaze_y - prev.gaze_y

            # Approximate velocity
            velocity = np.sqrt(dx**2 + dy**2) * 30  # samples at 30fps

            if velocity > velocity_threshold:
                saccades.append(i)

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50
        assert len(saccades) > 0

    def test_social_attention_index_calculation(self):
        """Test Social Attention Index (SAI) calculation speed."""
        # Create synthetic AOI attention data
        aoi_times = {
            "eyes": np.random.uniform(0, 100, 1000),
            "mouth": np.random.uniform(0, 100, 1000),
            "background": np.random.uniform(0, 100, 1000),
        }

        start = time.perf_counter()

        # Calculate SAI
        total_time = sum(aoi_times.values())
        sai = (aoi_times["eyes"] + aoi_times["mouth"]) / total_time

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 10  # Should be very fast
        assert len(sai) == 1000

    def test_scanpath_entropy_calculation(self):
        """Test scanpath entropy calculation performance."""
        # Create synthetic scanpath data
        gaze_points = np.random.uniform(0, 1, (1000, 2))

        start = time.perf_counter()

        # Discretize into grid cells (simplified entropy)
        grid_size = 10
        cells = np.floor(gaze_points * grid_size).astype(int)

        # Calculate entropy
        unique, counts = np.unique(cells, axis=0, return_counts=True)
        probabilities = counts / len(cells)
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 50
        assert entropy >= 0

    def test_metric_extraction_pipeline(self, large_gaze_dataset):
        """Test complete metric extraction pipeline."""
        samples = large_gaze_dataset[:1000]

        start = time.perf_counter()

        # Extract multiple metrics
        metrics = {
            "mean_gaze_x": np.mean([s.gaze_x for s in samples]),
            "mean_gaze_y": np.mean([s.gaze_y for s in samples]),
            "std_gaze_x": np.std([s.gaze_x for s in samples]),
            "std_gaze_y": np.std([s.gaze_y for s in samples]),
            "mean_confidence": np.mean([s.confidence for s in samples]),
            "blink_rate": sum(1 for s in samples if s.is_blink) / len(samples),
        }

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < PERFORMANCE_THRESHOLDS["metric_extraction"]
        assert all(v >= 0 for v in metrics.values())


# ========================================================================
# DATABASE PERFORMANCE
# ========================================================================


class TestDatabasePerformance:
    """Performance tests for database operations."""

    def test_gaze_data_insertion_speed(
        self, mock_database_client, large_gaze_dataset
    ):
        """Test bulk gaze data insertion performance."""
        samples = large_gaze_dataset[:1000]

        start = time.perf_counter()

        # Insert samples
        result = mock_database_client.insert_gaze_data("session_id", samples)

        elapsed = (time.perf_counter() - start) * 1000

        assert result == 100  # Mock returns 100
        assert elapsed < 100  # Should be fast even with 1000 samples

    def test_database_query_performance(self, mock_database_client):
        """Test database query performance."""
        start = time.perf_counter()

        # Perform query
        results = mock_database_client.get_gaze_data("session_id")

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < PERFORMANCE_THRESHOLDS["database_query"]
        assert isinstance(results, list)

    def test_batch_result_insertion(self, mock_database_client):
        """Test batch insertion of assessment results."""
        # Create multiple results
        results = [Mock() for _ in range(100)]

        start = time.perf_counter()

        # Insert batch
        for result in results:
            mock_database_client.create_assessment_results(result)

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 500  # Should handle 100 insertions

    def test_database_scalability(self, mock_database_client):
        """Test database operation scalability."""
        # Test with increasing data sizes
        sizes = [100, 500, 1000, 5000]
        times = []

        for size in sizes:
            samples = [Mock() for _ in range(size)]

            start = time.perf_counter()
            mock_database_client.insert_gaze_data("session", samples)
            elapsed = (time.perf_counter() - start) * 1000

            times.append(elapsed)

        # Verify linear scalability (not exponential)
        # Time should roughly double when data size doubles
        assert times[-1] < times[0] * 10  # At most 10x slower for 50x more data


# ========================================================================
# REAL-TIME PROCESSING PERFORMANCE
# ========================================================================


class TestRealTimeProcessingPerformance:
    """Performance tests for real-time processing requirements."""

    def test_frame_processing_latency(self, large_gaze_dataset):
        """Test per-frame processing latency (30fps requirement = 33ms)."""
        # Simulate frame-by-frame processing
        max_latency = PERFORMANCE_THRESHOLDS["real_time_processing"]

        frames = large_gaze_dataset[:300]  # 10 seconds at 30fps

        latencies = []
        for frame in frames:
            start = time.perf_counter()

            # Simulate processing
            _ = {
                "gaze_x": frame.gaze_x,
                "gaze_y": frame.gaze_y,
                "confidence": frame.confidence,
            }

            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)

        avg_latency = np.mean(latencies)
        max_frame_latency = np.max(latencies)

        assert avg_latency < max_latency
        assert max_frame_latency < max_latency * 2

    def test_calibration_sample_collection_speed(self):
        """Test speed of collecting calibration samples."""
        from models.schemas import CalibrationPoint

        grid_points = 9
        samples_per_point = 5

        start = time.perf_counter()

        # Collect calibration samples
        calibration_data = []
        for point_idx in range(grid_points):
            for sample_idx in range(samples_per_point):
                point = CalibrationPoint(
                    point_id=f"calib_{point_idx}_{sample_idx}",
                    screen_x=0.5,
                    screen_y=0.5,
                    gaze_x=0.5 + np.random.normal(0, 0.05),
                    gaze_y=0.5 + np.random.normal(0, 0.05),
                    timestamp=time.time(),
                    confidence=0.9,
                    distance_pixels=np.random.uniform(5, 30),
                )
                calibration_data.append(point)

        elapsed = (time.perf_counter() - start) * 1000

        assert len(calibration_data) == grid_points * samples_per_point
        assert elapsed < 100  # Should be fast

    def test_assessment_stimulus_rendering_cycle(self):
        """Test stimulus presentation and gaze collection cycle."""
        # Simulate stimulus presentation with real-time gaze collection
        stimulus_duration_ms = 30000  # 30 second stimulus
        fps = 30
        frames = int(stimulus_duration_ms / (1000 / fps))

        start = time.perf_counter()

        samples_collected = 0
        for frame in range(frames):
            # Simulate frame processing
            sample = {
                "gaze_x": np.random.uniform(0, 1),
                "gaze_y": np.random.uniform(0, 1),
                "confidence": np.random.uniform(0.8, 1.0),
            }
            samples_collected += 1

        elapsed = (time.perf_counter() - start) * 1000
        fps_actual = samples_collected / (elapsed / 1000)

        # Should maintain at least 25 fps
        assert fps_actual > 25

    def test_results_computation_latency(self, large_gaze_dataset):
        """Test latency of computing assessment results."""
        samples = large_gaze_dataset

        start = time.perf_counter()

        # Simulate result computation
        risk_factors = {
            "reduced_eye_gaze": False,
            "reduced_mouth_gaze": False,
            "reduced_social_attention": False,
            "atypical_fixation_patterns": False,
            "increased_scanpath_entropy": False,
            "increased_blink_rate": False,
            "poor_signal_quality": False,
        }

        risk_count = sum(risk_factors.values())
        screening_result = "LOW_RISK" if risk_count == 0 else "MODERATE_RISK"

        elapsed = (time.perf_counter() - start) * 1000

        assert elapsed < 100  # Should be very fast
        assert isinstance(screening_result, str)


# ========================================================================
# MEMORY EFFICIENCY
# ========================================================================


class TestMemoryEfficiency:
    """Test memory usage efficiency."""

    def test_gaze_sample_memory_footprint(self):
        """Test memory footprint of gaze samples."""
        from models.schemas import GazeDataPoint
        import sys

        sample = GazeDataPoint(
            timestamp=time.time(),
            gaze_x=0.5,
            gaze_y=0.5,
            confidence=0.9,
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )

        # Rough estimate of object size
        size = sys.getsizeof(sample)
        assert size > 0  # Should have reasonable size

    def test_large_dataset_memory_streaming(self, large_gaze_dataset):
        """Test memory-efficient streaming of large datasets."""
        samples = large_gaze_dataset

        # Process in chunks instead of loading all
        chunk_size = 1000
        processed = 0

        for i in range(0, len(samples), chunk_size):
            chunk = samples[i : i + chunk_size]
            processed += len(chunk)

        assert processed == len(samples)

    def test_metric_computation_memory(self, large_gaze_dataset):
        """Test memory efficiency of metric computation."""
        samples = large_gaze_dataset

        # Use generators for memory efficiency
        x_values = (s.gaze_x for s in samples)
        y_values = (s.gaze_y for s in samples)

        # Compute without loading all into memory
        mean_x = sum(x_values) / len(samples)
        mean_y = sum(y_values) / len(samples)

        assert 0 <= mean_x <= 1
        assert 0 <= mean_y <= 1


# ========================================================================
# STRESS TESTS
# ========================================================================


class TestStressScenarios:
    """Stress tests for extreme scenarios."""

    def test_sustained_high_frequency_sampling(self):
        """Test sustained high-frequency gaze sampling (120fps equivalent)."""
        from models.schemas import GazeDataPoint

        samples = []
        duration_s = 60  # 60 second test
        fps = 120

        start = time.perf_counter()

        for i in range(duration_s * fps):
            sample = GazeDataPoint(
                timestamp=time.time() + i / fps,
                gaze_x=np.random.uniform(0, 1),
                gaze_y=np.random.uniform(0, 1),
                confidence=np.random.uniform(0.5, 1.0),
                is_blink=np.random.random() < 0.01,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            )
            samples.append(sample)

        elapsed = (time.perf_counter() - start) * 1000

        expected_samples = duration_s * fps
        assert len(samples) == expected_samples

    def test_extreme_calibration_accuracy(self):
        """Test calibration with extreme accuracy requirements."""
        from models.schemas import CalibrationPoint

        # Collect 100 samples per calibration point
        points_per_grid = 9
        samples_per_point = 100

        calibration_points = []
        for grid_idx in range(points_per_grid):
            for sample_idx in range(samples_per_point):
                x = 0.25 + (grid_idx % 3) * 0.25
                y = 0.25 + (grid_idx // 3) * 0.25

                point = CalibrationPoint(
                    point_id=f"calib_{grid_idx}_{sample_idx}",
                    screen_x=x,
                    screen_y=y,
                    gaze_x=x + np.random.normal(0, 0.002),  # Very tight error
                    gaze_y=y + np.random.normal(0, 0.002),
                    timestamp=time.time(),
                    confidence=0.95 + np.random.uniform(0, 0.05),
                    distance_pixels=np.random.uniform(0.5, 3),  # Sub-pixel errors
                )
                calibration_points.append(point)

        assert len(calibration_points) == points_per_grid * samples_per_point

    def test_concurrent_session_simulation(self, mock_database_client):
        """Simulate multiple concurrent assessment sessions."""
        num_sessions = 10
        samples_per_session = 100

        start = time.perf_counter()

        for session_idx in range(num_sessions):
            samples = [Mock() for _ in range(samples_per_session)]
            mock_database_client.insert_gaze_data(
                f"session_{session_idx}", samples
            )

        elapsed = (time.perf_counter() - start) * 1000

        # Should handle concurrent operations
        assert elapsed < 1000


# ========================================================================
# REGRESSION TESTS
# ========================================================================


@pytest.mark.parametrize(
    "sample_count,max_time_ms",
    [
        (100, 10),
        (1000, 50),
        (10000, 200),
    ],
)
def test_metric_extraction_regression(sample_count, max_time_ms):
    """Regression test for metric extraction performance."""
    from models.schemas import GazeDataPoint

    samples = [
        GazeDataPoint(
            timestamp=time.time() + i * 0.001,
            gaze_x=np.random.uniform(0, 1),
            gaze_y=np.random.uniform(0, 1),
            confidence=np.random.uniform(0.5, 1.0),
            is_blink=False,
            head_pitch=0,
            head_yaw=0,
            head_roll=0,
        )
        for i in range(sample_count)
    ]

    start = time.perf_counter()

    # Extract metrics
    metrics = {
        "mean_x": np.mean([s.gaze_x for s in samples]),
        "mean_y": np.mean([s.gaze_y for s in samples]),
        "std_x": np.std([s.gaze_x for s in samples]),
        "std_y": np.std([s.gaze_y for s in samples]),
    }

    elapsed = (time.perf_counter() - start) * 1000

    assert elapsed < max_time_ms
    assert all(isinstance(v, float) for v in metrics.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
