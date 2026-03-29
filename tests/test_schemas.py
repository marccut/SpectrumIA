"""
SpectrumIA Unit Tests - Pydantic Schemas

Testa validação de modelos Pydantic, ranges, enums, e constraints.

Referências:
- Pydantic v2 validation
- Scientific constraints (ranges 0-1 para scores)
- Enum validation
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.schemas import (
    Gender,
    AgeGroup,
    AssessmentStatus,
    ScreeningResult,
    AOIType,
    UserBase,
    UserCreate,
    UserResponse,
    CalibrationPoint,
    CalibrationSessionCreate,
    CalibrationSessionResponse,
    GazeDataPoint,
    FixationMetricsModel,
    SaccadeMetricsModel,
    SocialAttentionMetricsModel,
    ScanpathMetricsModel,
    GazeMetricsModel,
    AssessmentSessionCreate,
    AssessmentSessionResponse,
    AssessmentMetricsSnapshot,
    RiskFactors,
    AssessmentResultsResponse,
    create_assessment_results,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Test enum values and constraints."""

    def test_gender_enum_values(self):
        """Test all Gender enum values."""
        assert Gender.MALE.value == "male"
        assert Gender.FEMALE.value == "female"
        assert Gender.OTHER.value == "other"
        assert Gender.NOT_SPECIFIED.value == "not_specified"

    def test_age_group_enum_values(self):
        """Test all AgeGroup enum values."""
        assert AgeGroup.TODDLER.value == "toddler"
        assert AgeGroup.PRESCHOOL.value == "preschool"
        assert AgeGroup.SCHOOL.value == "school"
        assert AgeGroup.ADOLESCENT.value == "adolescent"
        assert AgeGroup.ADULT.value == "adult"
        assert AgeGroup.OLDER_ADULT.value == "older_adult"

    def test_assessment_status_enum(self):
        """Test AssessmentStatus enum."""
        statuses = [
            AssessmentStatus.PENDING,
            AssessmentStatus.IN_PROGRESS,
            AssessmentStatus.COMPLETED,
            AssessmentStatus.CANCELLED,
            AssessmentStatus.FAILED,
        ]
        assert len(statuses) == 5

    def test_screening_result_enum(self):
        """Test ScreeningResult enum."""
        results = [
            ScreeningResult.LOW_RISK,
            ScreeningResult.MODERATE_RISK,
            ScreeningResult.HIGH_RISK,
            ScreeningResult.INCONCLUSIVE,
        ]
        assert len(results) == 4


# ============================================================================
# USER MODEL TESTS
# ============================================================================

class TestUserModels:
    """Test User-related models."""

    def test_user_base_valid(self):
        """Test valid UserBase creation."""
        user = UserBase(
            email="test@example.com",
            age=25,
            gender=Gender.FEMALE,
            age_group=AgeGroup.ADULT,
        )
        assert user.email == "test@example.com"
        assert user.age == 25
        assert user.gender == Gender.FEMALE

    def test_user_base_invalid_age_negative(self):
        """Test UserBase with negative age."""
        with pytest.raises(ValidationError):
            UserBase(
                email="test@example.com",
                age=-5,
                gender=Gender.MALE,
                age_group=AgeGroup.ADULT,
            )

    def test_user_base_invalid_age_over_120(self):
        """Test UserBase with age > 120."""
        with pytest.raises(ValidationError):
            UserBase(
                email="test@example.com",
                age=150,
                gender=Gender.MALE,
                age_group=AgeGroup.ADULT,
            )

    def test_user_base_invalid_email(self):
        """Test UserBase with invalid email."""
        with pytest.raises(ValidationError):
            UserBase(
                email="invalid-email",
                age=25,
                gender=Gender.MALE,
                age_group=AgeGroup.ADULT,
            )

    def test_user_create_with_password(self):
        """Test UserCreate with password."""
        user = UserCreate(
            email="test@example.com",
            age=30,
            gender=Gender.MALE,
            age_group=AgeGroup.ADULT,
            password="secure_password",
            first_name="João",
            last_name="Silva",
        )
        assert user.password == "secure_password"
        assert user.first_name == "João"

    def test_user_response_creation(self):
        """Test UserResponse creation."""
        now = datetime.utcnow()
        user = UserResponse(
            user_id="uuid-123",
            email="test@example.com",
            age=25,
            gender=Gender.FEMALE,
            age_group=AgeGroup.ADULT,
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        assert user.user_id == "uuid-123"
        assert user.is_active is True


# ============================================================================
# CALIBRATION MODEL TESTS
# ============================================================================

class TestCalibrationModels:
    """Test Calibration-related models."""

    def test_calibration_point_valid(self):
        """Test valid CalibrationPoint."""
        point = CalibrationPoint(
            screen_x=0.5,
            screen_y=0.5,
            gaze_x=0.48,
            gaze_y=0.52,
            timestamp=1234567890.0,
            confidence=0.95,
            distance_pixels=10.5,
        )
        assert point.screen_x == 0.5
        assert point.confidence == 0.95

    def test_calibration_point_invalid_gaze_x_negative(self):
        """Test CalibrationPoint with invalid gaze_x."""
        with pytest.raises(ValidationError):
            CalibrationPoint(
                screen_x=0.5,
                screen_y=0.5,
                gaze_x=-0.1,  # Invalid: < 0.0
                gaze_y=0.5,
                timestamp=1234567890.0,
                confidence=0.9,
            )

    def test_calibration_point_invalid_gaze_x_over_1(self):
        """Test CalibrationPoint with gaze_x > 1.0."""
        with pytest.raises(ValidationError):
            CalibrationPoint(
                screen_x=0.5,
                screen_y=0.5,
                gaze_x=1.5,  # Invalid: > 1.0
                gaze_y=0.5,
                timestamp=1234567890.0,
                confidence=0.9,
            )

    def test_calibration_point_invalid_confidence(self):
        """Test CalibrationPoint with invalid confidence."""
        with pytest.raises(ValidationError):
            CalibrationPoint(
                screen_x=0.5,
                screen_y=0.5,
                gaze_x=0.5,
                gaze_y=0.5,
                timestamp=1234567890.0,
                confidence=1.5,  # Invalid: > 1.0
            )

    def test_calibration_session_create_valid(self):
        """Test valid CalibrationSessionCreate."""
        session = CalibrationSessionCreate(
            user_id="user-123",
            num_points=9,
            calibration_distance_cm=50.0,
        )
        assert session.num_points == 9

    def test_calibration_session_create_invalid_num_points(self):
        """Test CalibrationSessionCreate with invalid num_points."""
        with pytest.raises(ValidationError):
            CalibrationSessionCreate(
                user_id="user-123",
                num_points=2,  # Invalid: < 4
            )


# ============================================================================
# GAZE DATA TESTS
# ============================================================================

class TestGazeDataModels:
    """Test Gaze-related models."""

    def test_gaze_data_point_valid(self):
        """Test valid GazeDataPoint."""
        point = GazeDataPoint(
            timestamp=1234567890.0,
            gaze_x=0.5,
            gaze_y=0.5,
            confidence=0.9,
            is_blink=False,
            head_pitch=0.0,
            head_yaw=0.0,
            head_roll=0.0,
        )
        assert point.gaze_x == 0.5
        assert point.is_blink is False

    def test_gaze_data_point_invalid_confidence(self):
        """Test GazeDataPoint with invalid confidence."""
        with pytest.raises(ValidationError):
            GazeDataPoint(
                timestamp=1234567890.0,
                gaze_x=0.5,
                gaze_y=0.5,
                confidence=-0.1,  # Invalid
            )

    def test_fixation_metrics_valid(self):
        """Test valid FixationMetricsModel."""
        metrics = FixationMetricsModel(
            count=10,
            mean_duration_ms=250.0,
            median_duration_ms=240.0,
            min_duration_ms=100.0,
            max_duration_ms=500.0,
            total_duration_ms=2500.0,
            std_duration_ms=50.0,
        )
        assert metrics.count == 10
        assert metrics.mean_duration_ms == 250.0

    def test_saccade_metrics_valid(self):
        """Test valid SaccadeMetricsModel."""
        metrics = SaccadeMetricsModel(
            count=15,
            mean_amplitude_deg=5.0,
            mean_velocity_deg_per_sec=150.0,
            median_velocity_deg_per_sec=140.0,
            mean_peak_velocity_deg_per_sec=200.0,
            latency_ms=50.0,
        )
        assert metrics.count == 15


# ============================================================================
# SOCIAL ATTENTION TESTS (CORE ASD METRIC)
# ============================================================================

class TestSocialAttentionMetrics:
    """Test Social Attention metrics - CORE ASD biomarker."""

    def test_social_attention_index_valid(self):
        """Test valid SocialAttentionMetricsModel."""
        metrics = SocialAttentionMetricsModel(
            social_attention_index=0.45,  # Jones & Klin 2013
            eye_preference=0.65,
            mouth_preference=0.35,
            time_on_eyes_ms=5000.0,
            time_on_mouth_ms=2000.0,
            time_on_face_ms=7000.0,
            attention_shifts=20,
        )
        assert metrics.social_attention_index == 0.45
        assert metrics.eye_preference + metrics.mouth_preference == 1.0

    def test_social_attention_index_invalid_range(self):
        """Test SocialAttentionMetricsModel with invalid SAI."""
        with pytest.raises(ValidationError):
            SocialAttentionMetricsModel(
                social_attention_index=1.5,  # Invalid: > 1.0
            )

    def test_social_attention_index_zero(self):
        """Test SocialAttentionMetricsModel with zero SAI (extreme case)."""
        metrics = SocialAttentionMetricsModel(
            social_attention_index=0.0,  # No social attention
        )
        assert metrics.social_attention_index == 0.0


# ============================================================================
# GAZE METRICS (COMPREHENSIVE)
# ============================================================================

class TestGazeMetricsModel:
    """Test comprehensive GazeMetricsModel."""

    def test_gaze_metrics_valid(self):
        """Test valid GazeMetricsModel with all fields."""
        fixations = FixationMetricsModel(count=10, mean_duration_ms=250.0)
        saccades = SaccadeMetricsModel(count=15, mean_amplitude_deg=5.0)
        social_att = SocialAttentionMetricsModel(social_attention_index=0.45)
        scanpath = ScanpathMetricsModel(entropy=0.5)

        metrics = GazeMetricsModel(
            timestamp=1234567890.0,
            stimulus_id="face_video_01",
            fixations=fixations,
            saccades=saccades,
            social_attention=social_att,
            scanpath=scanpath,
            blink_count=3,
            blink_rate=12.0,
            gaze_confidence_mean=0.92,
            signal_quality=0.95,
        )

        assert metrics.timestamp == 1234567890.0
        assert metrics.fixations.count == 10
        assert metrics.social_attention.social_attention_index == 0.45

    def test_gaze_metrics_signal_quality_range(self):
        """Test signal quality range validation."""
        with pytest.raises(ValidationError):
            GazeMetricsModel(
                timestamp=1234567890.0,
                signal_quality=1.5,  # Invalid: > 1.0
                fixations=FixationMetricsModel(),
                saccades=SaccadeMetricsModel(),
                social_attention=SocialAttentionMetricsModel(),
                scanpath=ScanpathMetricsModel(),
            )


# ============================================================================
# ASSESSMENT TESTS
# ============================================================================

class TestAssessmentModels:
    """Test Assessment-related models."""

    def test_assessment_session_create_valid(self):
        """Test valid AssessmentSessionCreate."""
        session = AssessmentSessionCreate(
            user_id="user-123",
            calibration_id="calib-123",
            assessment_type="asd_screening",
        )
        assert session.assessment_type == "asd_screening"

    def test_assessment_session_response_valid(self):
        """Test valid AssessmentSessionResponse."""
        now = datetime.utcnow()
        session = AssessmentSessionResponse(
            session_id="sess-123",
            user_id="user-123",
            calibration_id="calib-123",
            status=AssessmentStatus.COMPLETED,
            assessment_type="asd_screening",
            total_duration_ms=120000,
            samples_count=3600,
            signal_quality_mean=0.90,
            created_at=now,
        )
        assert session.samples_count == 3600


# ============================================================================
# RESULTS TESTS
# ============================================================================

class TestAssessmentResults:
    """Test Assessment Results and Risk Assessment."""

    def test_risk_factors_all_false(self):
        """Test RiskFactors with no risk factors (low risk)."""
        factors = RiskFactors(
            reduced_eye_gaze=False,
            reduced_mouth_gaze=False,
            atypical_fixation_patterns=False,
            reduced_social_attention=False,
            increased_scanpath_entropy=False,
            increased_blink_rate=False,
            poor_signal_quality=False,
        )
        assert sum([
            factors.reduced_eye_gaze,
            factors.reduced_mouth_gaze,
            factors.atypical_fixation_patterns,
            factors.reduced_social_attention,
            factors.increased_scanpath_entropy,
            factors.increased_blink_rate,
            factors.poor_signal_quality,
        ]) == 0

    def test_risk_factors_all_true(self):
        """Test RiskFactors with all risk factors (high risk)."""
        factors = RiskFactors(
            reduced_eye_gaze=True,
            reduced_mouth_gaze=True,
            atypical_fixation_patterns=True,
            reduced_social_attention=True,
            increased_scanpath_entropy=True,
            increased_blink_rate=True,
            poor_signal_quality=True,
        )
        assert sum([
            factors.reduced_eye_gaze,
            factors.reduced_mouth_gaze,
            factors.atypical_fixation_patterns,
            factors.reduced_social_attention,
            factors.increased_scanpath_entropy,
            factors.increased_blink_rate,
            factors.poor_signal_quality,
        ]) == 7

    def test_assessment_metrics_snapshot_valid(self):
        """Test valid AssessmentMetricsSnapshot."""
        metrics = AssessmentMetricsSnapshot(
            mean_social_attention_index=0.35,  # Reduced (ASD-like)
            sai_std=0.08,
            mean_eye_preference=0.50,
            mean_fixation_duration_ms=200.0,
            mean_fixation_count=50,
            mean_saccade_amplitude_deg=4.5,
            signal_quality_mean=0.92,
            valid_stimuli_count=3,
            total_stimuli_count=3,
        )
        assert metrics.mean_social_attention_index == 0.35

    def test_create_assessment_results_low_risk(self):
        """Test create_assessment_results for low risk."""
        metrics = AssessmentMetricsSnapshot(
            mean_social_attention_index=0.60,  # High SAI = low risk
        )
        risk_factors = RiskFactors()  # No risk factors

        result = create_assessment_results(
            session_id="sess-123",
            user_id="user-123",
            metrics_snapshot=metrics,
            risk_factors=risk_factors
        )

        assert result.screening_result == ScreeningResult.LOW_RISK
        assert result.risk_factor_count == 0

    def test_create_assessment_results_high_risk(self):
        """Test create_assessment_results for high risk."""
        metrics = AssessmentMetricsSnapshot(
            mean_social_attention_index=0.20,  # Low SAI = high risk
        )
        risk_factors = RiskFactors(
            reduced_eye_gaze=True,
            reduced_social_attention=True,
            atypical_fixation_patterns=True,
            increased_scanpath_entropy=True,
            increased_blink_rate=True,
        )

        result = create_assessment_results(
            session_id="sess-123",
            user_id="user-123",
            metrics_snapshot=metrics,
            risk_factors=risk_factors
        )

        assert result.screening_result == ScreeningResult.HIGH_RISK
        assert result.risk_factor_count == 5
        assert result.recommend_clinical_evaluation is True

    def test_assessment_results_confidence_score_range(self):
        """Test that confidence scores are within valid range."""
        metrics = AssessmentMetricsSnapshot(
            mean_social_attention_index=0.45,
        )
        risk_factors = RiskFactors()

        result = create_assessment_results(
            session_id="sess-123",
            user_id="user-123",
            metrics_snapshot=metrics,
            risk_factors=risk_factors
        )

        assert 0.0 <= result.confidence_score <= 1.0
        assert 0.0 <= result.risk_percentage <= 100.0


# ============================================================================
# EDGE CASES & CORNER CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_gaze_coordinates_at_boundaries(self):
        """Test gaze coordinates at 0.0 and 1.0 boundaries."""
        # At 0.0
        point1 = GazeDataPoint(
            timestamp=0.0,
            gaze_x=0.0,
            gaze_y=0.0,
            confidence=0.0,
        )
        assert point1.gaze_x == 0.0

        # At 1.0
        point2 = GazeDataPoint(
            timestamp=0.0,
            gaze_x=1.0,
            gaze_y=1.0,
            confidence=1.0,
        )
        assert point2.gaze_x == 1.0

    def test_age_at_boundaries(self):
        """Test age at 0 and 120 boundaries."""
        user1 = UserBase(
            email="baby@example.com",
            age=0,
            gender=Gender.MALE,
            age_group=AgeGroup.TODDLER,
        )
        assert user1.age == 0

        user2 = UserBase(
            email="old@example.com",
            age=120,
            gender=Gender.FEMALE,
            age_group=AgeGroup.OLDER_ADULT,
        )
        assert user2.age == 120

    def test_calibration_points_at_boundaries(self):
        """Test calibration points at grid boundaries."""
        # Corner point
        point = CalibrationPoint(
            screen_x=0.0,
            screen_y=0.0,
            gaze_x=0.0,
            gaze_y=0.0,
            timestamp=0.0,
            confidence=1.0,
        )
        assert point.screen_x == 0.0
        assert point.screen_y == 0.0

        # Opposite corner
        point2 = CalibrationPoint(
            screen_x=1.0,
            screen_y=1.0,
            gaze_x=1.0,
            gaze_y=1.0,
            timestamp=0.0,
            confidence=1.0,
        )
        assert point2.screen_x == 1.0


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestSchemaPerformance:
    """Test schema creation performance."""

    def test_bulk_gaze_data_point_creation(self):
        """Test creating many GazeDataPoint objects."""
        points = [
            GazeDataPoint(
                timestamp=i * 0.033,  # 30Hz sampling
                gaze_x=0.5 + 0.1 * (i % 10) / 10,
                gaze_y=0.5 + 0.1 * ((i // 10) % 10) / 10,
                confidence=0.95,
            )
            for i in range(1000)
        ]
        assert len(points) == 1000

    def test_bulk_calibration_point_creation(self):
        """Test creating many CalibrationPoint objects."""
        points = [
            CalibrationPoint(
                screen_x=0.25 * (i % 4) + 0.125,
                screen_y=0.25 * (i // 4) + 0.125,
                gaze_x=0.25 * (i % 4) + 0.12,
                gaze_y=0.25 * (i // 4) + 0.12,
                timestamp=i * 0.1,
                confidence=0.90 + 0.05 * (i % 10) / 10,
            )
            for i in range(100)
        ]
        assert len(points) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
