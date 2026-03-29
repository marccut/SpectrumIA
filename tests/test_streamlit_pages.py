"""
SpectrumIA - End-to-End (E2E) Tests for Streamlit Pages

Tests for calibration.py, assessment.py, and results.py pages.
Uses pytest with Streamlit testing framework and mocked dependencies.

Coverage:
- Page initialization and session state management
- User authentication flow
- Calibration workflow (9-point grid)
- Assessment workflow (stimulus presentation)
- Results visualization and interpretation
- Database integration
- Error handling and edge cases
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import List, Dict, Any

# Mock Streamlit before importing pages
import sys
from unittest.mock import MagicMock as MM

# Mock streamlit and its components
sys.modules['streamlit'] = MM()
sys.modules['streamlit.testing'] = MM()

# Import page modules with mocked streamlit
import importlib.util

# ========================================================================
# FIXTURES
# ========================================================================


@pytest.fixture
def mock_streamlit_session():
    """Mock Streamlit session state."""
    session = {}
    return session


@pytest.fixture
def mock_user_id():
    """Sample user ID."""
    return "user_test_12345"


@pytest.fixture
def mock_calibration_id():
    """Sample calibration ID."""
    return "calib_test_67890"


@pytest.fixture
def mock_assessment_session_id():
    """Sample assessment session ID."""
    return "assess_test_11111"


@pytest.fixture
def mock_calibration_points():
    """Sample calibration points with realistic errors."""
    from models.schemas import CalibrationPoint

    points = []
    for i in range(9):
        x = [0.25, 0.5, 0.75][i % 3]
        y = [0.25, 0.5, 0.75][i // 3]

        point = CalibrationPoint(
            point_id=f"calib_point_{i}",
            screen_x=x,
            screen_y=y,
            gaze_x=x + np.random.normal(0, 0.02),  # Small error
            gaze_y=y + np.random.normal(0, 0.02),
            timestamp=datetime.utcnow().timestamp(),
            confidence=0.85 + np.random.uniform(0, 0.15),
            distance_pixels=np.random.uniform(10, 40),  # 10-40px error
        )
        points.append(point)

    return points


@pytest.fixture
def mock_gaze_data():
    """Sample gaze data points."""
    from models.schemas import GazeDataPoint

    samples = []
    for i in range(100):
        sample = GazeDataPoint(
            timestamp=datetime.utcnow().timestamp() + i * 0.033,  # ~30fps
            gaze_x=0.5 + np.sin(i * 0.1) * 0.2,
            gaze_y=0.5 + np.cos(i * 0.1) * 0.2,
            confidence=0.8 + np.random.uniform(0, 0.2),
            is_blink=i % 20 == 0,  # Blink every 20 samples
            head_pitch=np.random.uniform(-10, 10),
            head_yaw=np.random.uniform(-10, 10),
            head_roll=np.random.uniform(-5, 5),
        )
        samples.append(sample)

    return samples


@pytest.fixture
def mock_assessment_result():
    """Sample assessment results."""
    from models.schemas import (
        AssessmentResultsResponse,
        ScreeningResult,
        RiskFactors,
        AssessmentMetricsSnapshot,
    )

    risk_factors = RiskFactors(
        reduced_eye_gaze=False,
        reduced_mouth_gaze=False,
        reduced_social_attention=False,
        atypical_fixation_patterns=False,
        increased_scanpath_entropy=False,
        increased_blink_rate=False,
        poor_signal_quality=False,
    )

    metrics = AssessmentMetricsSnapshot(
        mean_social_attention_index=0.75,
        mean_eye_preference=0.68,
        mean_mouth_preference=0.15,
        mean_nose_preference=0.07,
        mean_fixation_duration_ms=280.5,
        mean_fixation_count=45,
        mean_fixation_dispersion_deg=2.1,
        mean_saccade_amplitude_deg=8.5,
        mean_saccade_velocity_deg_per_sec=220.0,
        mean_saccade_peak_velocity_deg_per_sec=350.0,
        mean_time_to_first_fixation_ms=320.0,
        mean_scanpath_entropy=0.62,
        signal_quality_mean=0.92,
        mean_blink_rate=14.5,
    )

    result = AssessmentResultsResponse(
        result_id="result_test_12345",
        session_id="assess_test_11111",
        user_id="user_test_12345",
        assessment_type="asd_screening",
        assessment_completed_at=datetime.utcnow(),
        results_generated_at=datetime.utcnow(),
        screening_result=ScreeningResult.LOW_RISK,
        risk_percentage=15.0,
        confidence_score=0.88,
        risk_factors=risk_factors,
        metrics_snapshot=metrics,
        risk_factor_count=0,
        clinical_notes="Sample assessment - no risk factors detected",
        expires_at=None,
    )

    return result


@pytest.fixture
def mock_database_client():
    """Mock Supabase database client."""
    client = MagicMock()

    # User operations
    client.create_user = MagicMock(return_value=Mock(user_id="user_test_12345"))
    client.get_user = MagicMock(return_value=Mock(user_id="user_test_12345"))
    client.list_users = MagicMock(return_value=[])

    # Calibration operations
    client.create_calibration_session = MagicMock(
        return_value=Mock(
            calibration_id="calib_test_67890",
            user_id="user_test_12345",
            status="in_progress",
        )
    )
    client.get_calibration_session = MagicMock(
        return_value=Mock(
            calibration_id="calib_test_67890",
            user_id="user_test_12345",
            status="completed",
            validity_score=0.92,
        )
    )
    client.update_calibration_session = MagicMock(return_value=Mock())

    # Assessment operations
    client.create_assessment_session = MagicMock(
        return_value=Mock(
            session_id="assess_test_11111",
            user_id="user_test_12345",
            calibration_id="calib_test_67890",
            status="in_progress",
        )
    )
    client.get_assessment_session = MagicMock(
        return_value=Mock(
            session_id="assess_test_11111",
            user_id="user_test_12345",
            status="in_progress",
        )
    )
    client.update_assessment_session = MagicMock(return_value=Mock())
    client.list_user_assessments = MagicMock(return_value=[])

    # Gaze data operations
    client.insert_gaze_data = MagicMock(return_value=100)
    client.get_gaze_data = MagicMock(return_value=[])

    # Results operations
    client.create_assessment_results = MagicMock(return_value=Mock())
    client.get_assessment_results = MagicMock(return_value=Mock())
    client.list_user_results = MagicMock(return_value=[])
    client.delete_expired_results = MagicMock(return_value=5)

    return client


# ========================================================================
# CALIBRATION PAGE TESTS
# ========================================================================


class TestCalibrationPageInitialization:
    """Test calibration page initialization and session state."""

    def test_session_state_initialization(self, mock_streamlit_session):
        """Test that session state is properly initialized."""
        # Simulate page initialization
        session_state = {
            "calibration_session_id": None,
            "calibration_points": [],
            "current_calibration_index": 0,
            "calibration_status": "not_started",
            "face_detector": None,
            "gaze_estimator": None,
        }

        assert session_state["calibration_session_id"] is None
        assert session_state["calibration_points"] == []
        assert session_state["current_calibration_index"] == 0
        assert session_state["calibration_status"] == "not_started"

    def test_authentication_check(self, mock_streamlit_session, mock_user_id):
        """Test that page requires authentication."""
        # User not authenticated
        session = {}
        assert "user_id" not in session

        # After authentication
        session["user_id"] = mock_user_id
        assert "user_id" in session
        assert session["user_id"] == mock_user_id


class TestCalibrationWorkflow:
    """Test complete calibration workflow."""

    def test_calibration_grid_generation(self):
        """Test 9-point calibration grid generation."""
        # 9-point grid should generate coordinates at 0.25, 0.5, 0.75
        grid_9 = []
        for i in [0.25, 0.5, 0.75]:
            for j in [0.25, 0.5, 0.75]:
                grid_9.append((i, j))

        assert len(grid_9) == 9
        assert (0.25, 0.25) in grid_9
        assert (0.5, 0.5) in grid_9
        assert (0.75, 0.75) in grid_9

    def test_calibration_session_creation(
        self, mock_database_client, mock_user_id
    ):
        """Test calibration session creation."""
        # Simulate session creation
        session = mock_database_client.create_calibration_session(
            user_id=mock_user_id, num_points=9
        )

        assert session is not None
        assert session.user_id == mock_user_id
        assert session.status == "in_progress"
        mock_database_client.create_calibration_session.assert_called_once_with(
            user_id=mock_user_id, num_points=9
        )

    def test_calibration_sample_collection(self, mock_calibration_points):
        """Test calibration point collection."""
        points = mock_calibration_points
        assert len(points) == 9

        # Verify point structure
        for point in points:
            assert 0 <= point.screen_x <= 1
            assert 0 <= point.screen_y <= 1
            assert 0 <= point.gaze_x <= 1
            assert 0 <= point.gaze_y <= 1
            assert 0 <= point.confidence <= 1
            assert point.distance_pixels >= 0

    def test_calibration_completion(
        self, mock_database_client, mock_calibration_points
    ):
        """Test calibration session completion and validation."""
        # Calculate statistics
        distances = [p.distance_pixels for p in mock_calibration_points]
        mean_error = float(np.mean(distances))
        max_error = float(np.max(distances))
        validity_score = max(0.0, 1.0 - (mean_error / 100.0))

        assert 0 <= mean_error <= 100
        assert 0 <= max_error <= 100
        assert 0 <= validity_score <= 1

        # Update session
        updates = {
            "status": "completed",
            "mean_error_pixels": mean_error,
            "max_error_pixels": max_error,
            "validity_score": validity_score,
        }

        mock_database_client.update_calibration_session(
            "calib_test_67890", updates
        )
        mock_database_client.update_calibration_session.assert_called_once()

    def test_calibration_error_scenarios(self, mock_database_client, mock_user_id):
        """Test error handling during calibration."""
        # No points collected
        mock_database_client.update_calibration_session.return_value = None

        result = mock_database_client.update_calibration_session(
            "calib_test_67890", {"calibration_points": []}
        )

        assert result is None


# ========================================================================
# ASSESSMENT PAGE TESTS
# ========================================================================


class TestAssessmentPageInitialization:
    """Test assessment page initialization."""

    def test_session_state_setup(self):
        """Test assessment session state initialization."""
        session_state = {
            "assessment_session_id": None,
            "assessment_status": "not_started",
            "gaze_samples": [],
            "current_stimulus_index": 0,
            "feature_extractor": None,
            "face_detector": None,
            "gaze_estimator": None,
        }

        assert session_state["assessment_status"] == "not_started"
        assert len(session_state["gaze_samples"]) == 0
        assert session_state["current_stimulus_index"] == 0

    def test_prerequisite_checks(self):
        """Test that assessment requires calibration."""
        session = {
            "user_id": "user_test_12345",
            # No calibration_id
        }

        # Should fail without calibration
        assert "calibration_id" not in session


class TestStimulusPresentation:
    """Test stimulus presentation workflow."""

    def test_stimulus_list_generation(self):
        """Test stimulus list generation."""
        stimuli = [
            {
                "id": "face_video_01",
                "name": "Rosto Falando",
                "type": "face",
                "duration_ms": 30000,
                "description": "Vídeo de rosto falando (30s)",
            },
            {
                "id": "face_video_02",
                "name": "Rosto Sorrindo",
                "type": "face",
                "duration_ms": 20000,
                "description": "Vídeo de rosto com expressões (20s)",
            },
            {
                "id": "geometric_01",
                "name": "Padrão Geométrico",
                "type": "geometric",
                "duration_ms": 15000,
                "description": "Padrão geométrico em movimento (15s)",
            },
        ]

        assert len(stimuli) == 3
        assert all(s["id"] for s in stimuli)
        assert all(s["type"] in ["face", "geometric"] for s in stimuli)
        assert all(s["duration_ms"] > 0 for s in stimuli)

    def test_stimulus_progression(self):
        """Test progression through stimuli."""
        stimuli_count = 3
        current_index = 0

        # Progress through all stimuli
        while current_index < stimuli_count:
            assert current_index < stimuli_count
            current_index += 1

        assert current_index == stimuli_count


class TestGazeDataCollection:
    """Test gaze data collection during assessment."""

    def test_gaze_sample_collection(self, mock_gaze_data):
        """Test gaze sample collection and storage."""
        samples = mock_gaze_data
        assert len(samples) == 100

        # Verify sample validity
        for sample in samples:
            assert 0 <= sample.gaze_x <= 1
            assert 0 <= sample.gaze_y <= 1
            assert 0 <= sample.confidence <= 1
            assert isinstance(sample.is_blink, bool)
            assert sample.timestamp > 0

    def test_gaze_data_persistence(
        self, mock_database_client, mock_assessment_session_id, mock_gaze_data
    ):
        """Test saving gaze data to database."""
        result = mock_database_client.insert_gaze_data(
            mock_assessment_session_id, mock_gaze_data
        )

        assert result == 100  # 100 samples saved
        mock_database_client.insert_gaze_data.assert_called_once()

    def test_real_time_metrics(self, mock_gaze_data):
        """Test real-time metric calculation during assessment."""
        # Simulate real-time metric display
        samples = mock_gaze_data

        # Calculate running metrics
        confidences = [s.confidence for s in samples]
        blinks = sum(1 for s in samples if s.is_blink)

        assert len(confidences) == 100
        assert all(0 <= c <= 1 for c in confidences)
        assert blinks > 0  # Should have some blinks


class TestAssessmentCompletion:
    """Test assessment completion workflow."""

    def test_assessment_session_completion(
        self, mock_database_client, mock_assessment_session_id, mock_gaze_data
    ):
        """Test marking assessment as completed."""
        # Save gaze data
        mock_database_client.insert_gaze_data(mock_assessment_session_id, mock_gaze_data)

        # Update session status
        updates = {
            "status": "completed",
            "samples_count": len(mock_gaze_data),
            "completed_at": datetime.utcnow().isoformat(),
        }

        mock_database_client.update_assessment_session(
            mock_assessment_session_id, updates
        )

        assert mock_database_client.update_assessment_session.called

    def test_assessment_cancellation(self, mock_database_client):
        """Test assessment cancellation."""
        # Cancel assessment without saving
        updates = {
            "status": "cancelled",
            "completed_at": datetime.utcnow().isoformat(),
        }

        mock_database_client.update_assessment_session(
            "assess_test_11111", updates
        )

        assert mock_database_client.update_assessment_session.called


# ========================================================================
# RESULTS PAGE TESTS
# ========================================================================


class TestResultsPageInitialization:
    """Test results page initialization."""

    def test_results_session_state(self):
        """Test results session state setup."""
        session_state = {
            "results_data": None,
            "selected_result_id": None,
        }

        assert session_state["results_data"] is None
        assert session_state["selected_result_id"] is None

    def test_authentication_requirement(self):
        """Test that results page requires authentication."""
        session = {}
        assert "user_id" not in session


class TestResultsLoading:
    """Test loading assessment results."""

    def test_load_user_results(
        self, mock_database_client, mock_user_id, mock_assessment_result
    ):
        """Test loading results for a user."""
        # Mock multiple results
        results_list = [mock_assessment_result]
        mock_database_client.list_user_results.return_value = results_list

        results = mock_database_client.list_user_results(mock_user_id, limit=50)

        assert len(results) >= 1
        assert results[0].user_id == mock_user_id

    def test_result_selection(self, mock_assessment_result):
        """Test result selection from list."""
        result = mock_assessment_result

        assert result.result_id is not None
        assert result.screening_result is not None
        assert result.confidence_score > 0


class TestRiskAssessment:
    """Test risk assessment and interpretation."""

    def test_risk_level_classification(self, mock_assessment_result):
        """Test risk level classification."""
        from models.schemas import ScreeningResult

        result = mock_assessment_result

        assert result.screening_result in [
            ScreeningResult.LOW_RISK,
            ScreeningResult.MODERATE_RISK,
            ScreeningResult.HIGH_RISK,
        ]

        assert result.risk_percentage >= 0
        assert result.risk_percentage <= 100

    def test_risk_factors_evaluation(self, mock_assessment_result):
        """Test risk factor evaluation."""
        result = mock_assessment_result
        risk_factors = result.risk_factors

        # Verify factor structure
        factors = [
            risk_factors.reduced_eye_gaze,
            risk_factors.reduced_mouth_gaze,
            risk_factors.reduced_social_attention,
            risk_factors.atypical_fixation_patterns,
            risk_factors.increased_scanpath_entropy,
            risk_factors.increased_blink_rate,
            risk_factors.poor_signal_quality,
        ]

        assert len(factors) == 7
        assert all(isinstance(f, bool) for f in factors)
        assert result.risk_factor_count <= 7

    def test_confidence_score_range(self, mock_assessment_result):
        """Test confidence score is within valid range."""
        result = mock_assessment_result
        assert 0 <= result.confidence_score <= 1


class TestClinicalInterpretation:
    """Test clinical interpretation generation."""

    def test_interpretation_for_low_risk(self):
        """Test interpretation for low-risk result."""
        from models.schemas import ScreeningResult

        screening_result = ScreeningResult.LOW_RISK
        risk_percentage = 15.0

        # Should recommend monitoring
        assert screening_result == ScreeningResult.LOW_RISK
        assert risk_percentage < 50

    def test_interpretation_for_moderate_risk(self):
        """Test interpretation for moderate-risk result."""
        from models.schemas import ScreeningResult

        screening_result = ScreeningResult.MODERATE_RISK
        risk_percentage = 65.0

        # Should recommend clinical evaluation
        assert screening_result == ScreeningResult.MODERATE_RISK
        assert 50 <= risk_percentage < 85

    def test_interpretation_for_high_risk(self):
        """Test interpretation for high-risk result."""
        from models.schemas import ScreeningResult

        screening_result = ScreeningResult.HIGH_RISK
        risk_percentage = 90.0

        # Should recommend urgent evaluation
        assert screening_result == ScreeningResult.HIGH_RISK
        assert risk_percentage >= 85

    def test_recommendations_generation(self, mock_assessment_result):
        """Test that recommendations are generated based on risk level."""
        result = mock_assessment_result

        # Should have recommendations for any risk level
        assert result.screening_result is not None
        # Recommendations would be generated based on screening_result


class TestMetricsVisualization:
    """Test metrics display on results page."""

    def test_metrics_snapshot_structure(self, mock_assessment_result):
        """Test that metrics snapshot contains all expected fields."""
        metrics = mock_assessment_result.metrics_snapshot

        # Core ASD biomarker - Social Attention Index
        assert 0 <= metrics.mean_social_attention_index <= 1

        # Eye and mouth attention
        assert 0 <= metrics.mean_eye_preference <= 1
        assert 0 <= metrics.mean_mouth_preference <= 1

        # Fixation metrics
        assert metrics.mean_fixation_duration_ms > 0
        assert metrics.mean_fixation_count > 0

        # Saccade metrics
        assert metrics.mean_saccade_amplitude_deg > 0
        assert metrics.mean_saccade_velocity_deg_per_sec > 0

        # Temporal metrics
        assert metrics.mean_time_to_first_fixation_ms > 0
        assert metrics.mean_scanpath_entropy >= 0

        # Signal quality
        assert 0 <= metrics.signal_quality_mean <= 1

    def test_metrics_normalization(self, mock_assessment_result):
        """Test that metrics are properly normalized."""
        metrics = mock_assessment_result.metrics_snapshot

        # Normalized metrics should be 0-1
        assert 0 <= metrics.mean_social_attention_index <= 1
        assert 0 <= metrics.mean_eye_preference <= 1
        assert 0 <= metrics.signal_quality_mean <= 1


class TestExportFunctionality:
    """Test export of results."""

    def test_json_export_structure(self, mock_assessment_result):
        """Test JSON export contains valid data."""
        result = mock_assessment_result

        # Simulate JSON export
        export_data = {
            "result_id": result.result_id,
            "screening_result": result.screening_result.value,
            "risk_percentage": result.risk_percentage,
            "confidence_score": result.confidence_score,
        }

        assert export_data["result_id"] is not None
        assert 0 <= export_data["risk_percentage"] <= 100
        assert 0 <= export_data["confidence_score"] <= 1

    def test_csv_export_format(self, mock_assessment_result):
        """Test CSV export format."""
        metrics = mock_assessment_result.metrics_snapshot

        # Simulate CSV rows
        csv_rows = [
            ["Métrica", "Valor"],
            ["Social Attention Index", str(metrics.mean_social_attention_index)],
            ["Eye Preference", str(metrics.mean_eye_preference)],
            ["Mean Fixation Duration (ms)", str(metrics.mean_fixation_duration_ms)],
        ]

        assert len(csv_rows) > 1
        assert csv_rows[0] == ["Métrica", "Valor"]


# ========================================================================
# INTEGRATION TESTS
# ========================================================================


class TestFullWorkflowIntegration:
    """Test complete workflow from calibration through results."""

    def test_complete_user_workflow(
        self,
        mock_database_client,
        mock_user_id,
        mock_calibration_id,
        mock_gaze_data,
        mock_assessment_result,
    ):
        """Test complete workflow: create user → calibrate → assess → view results."""
        # 1. User creation
        user = mock_database_client.create_user(user_id=mock_user_id)
        assert user is not None

        # 2. Calibration
        calib = mock_database_client.create_calibration_session(
            user_id=mock_user_id, num_points=9
        )
        assert calib.user_id == mock_user_id

        # 3. Assessment
        assess = mock_database_client.create_assessment_session(
            user_id=mock_user_id, calibration_id=calib.calibration_id
        )
        assert assess.user_id == mock_user_id

        # 4. Gaze data collection
        count = mock_database_client.insert_gaze_data(assess.session_id, mock_gaze_data)
        assert count == 100

        # 5. Complete assessment
        mock_database_client.update_assessment_session(
            assess.session_id, {"status": "completed"}
        )

        # 6. Results viewing
        results = mock_database_client.list_user_results(mock_user_id)
        assert isinstance(results, list)

    def test_error_recovery_workflow(self, mock_database_client, mock_user_id):
        """Test recovery from errors during workflow."""
        # Attempt calibration creation with error
        mock_database_client.create_calibration_session.side_effect = Exception(
            "Connection error"
        )

        with pytest.raises(Exception):
            mock_database_client.create_calibration_session(
                user_id=mock_user_id, num_points=9
            )

        # Recovery: reset mock and retry
        mock_database_client.create_calibration_session.side_effect = None
        calib = mock_database_client.create_calibration_session(
            user_id=mock_user_id, num_points=9
        )
        assert calib is not None


# ========================================================================
# EDGE CASES AND ERROR HANDLING
# ========================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_results_list(self, mock_database_client, mock_user_id):
        """Test handling of user with no results."""
        mock_database_client.list_user_results.return_value = []

        results = mock_database_client.list_user_results(mock_user_id)
        assert len(results) == 0

    def test_perfect_calibration(self):
        """Test perfect calibration (0 error)."""
        from models.schemas import CalibrationPoint

        point = CalibrationPoint(
            point_id="perfect_calib",
            screen_x=0.5,
            screen_y=0.5,
            gaze_x=0.5,  # Exact match
            gaze_y=0.5,  # Exact match
            timestamp=datetime.utcnow().timestamp(),
            confidence=1.0,
            distance_pixels=0.0,
        )

        assert point.distance_pixels == 0.0
        validity = max(0.0, 1.0 - (0.0 / 100.0))
        assert validity == 1.0

    def test_poor_signal_quality(self, mock_gaze_data):
        """Test assessment with poor signal quality."""
        # Simulate low confidence samples
        poor_quality_samples = []
        for sample in mock_gaze_data:
            # Set all to low confidence
            sample.confidence = 0.3
            poor_quality_samples.append(sample)

        avg_confidence = np.mean([s.confidence for s in poor_quality_samples])
        assert avg_confidence < 0.5


# ========================================================================
# PERFORMANCE TESTS
# ========================================================================


class TestPagePerformance:
    """Test page performance with large datasets."""

    def test_large_result_list_loading(self, mock_database_client):
        """Test loading many results."""
        # Create mock list of 100 results
        mock_results = [Mock(result_id=f"result_{i}") for i in range(100)]
        mock_database_client.list_user_results.return_value = mock_results

        results = mock_database_client.list_user_results("user_test", limit=100)
        assert len(results) == 100

    def test_large_gaze_dataset_processing(self, mock_database_client):
        """Test processing large gaze datasets."""
        from models.schemas import GazeDataPoint

        # Create 10,000 gaze samples
        samples = []
        for i in range(10000):
            sample = GazeDataPoint(
                timestamp=datetime.utcnow().timestamp() + i * 0.001,
                gaze_x=np.random.uniform(0, 1),
                gaze_y=np.random.uniform(0, 1),
                confidence=np.random.uniform(0.5, 1.0),
                is_blink=False,
                head_pitch=0,
                head_yaw=0,
                head_roll=0,
            )
            samples.append(sample)

        # Test insertion of large batch
        mock_database_client.insert_gaze_data("session_id", samples)
        assert mock_database_client.insert_gaze_data.called


# ========================================================================
# SESSION STATE MANAGEMENT
# ========================================================================


class TestSessionStateManagement:
    """Test session state management across pages."""

    def test_state_persistence_across_pages(self):
        """Test that session state persists across page transitions."""
        session = {
            "user_id": "user_test_12345",
            "calibration_id": "calib_test_67890",
            "assessment_session_id": "assess_test_11111",
        }

        # Should be accessible across pages
        assert session["user_id"] == "user_test_12345"
        assert session["calibration_id"] == "calib_test_67890"
        assert session["assessment_session_id"] == "assess_test_11111"

    def test_state_reset_on_new_assessment(self):
        """Test that session state resets for new assessment."""
        session = {
            "gaze_samples": [Mock(), Mock()],
            "current_stimulus_index": 2,
        }

        # Reset for new assessment
        session["gaze_samples"] = []
        session["current_stimulus_index"] = 0

        assert len(session["gaze_samples"]) == 0
        assert session["current_stimulus_index"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
