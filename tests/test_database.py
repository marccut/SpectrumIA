"""
SpectrumIA Integration Tests - Database Client

Testa operações CRUD do cliente Supabase.
Mocks Supabase para testes sem dependência de banco de dados real.

Referências:
- pytest mocking
- Supabase client testing
- CRUD operation validation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from models.schemas import (
    UserCreate,
    Gender,
    AgeGroup,
    CalibrationSessionCreate,
    AssessmentSessionCreate,
    GazeDataPoint,
    AssessmentResultsResponse,
    ScreeningResult,
    AssessmentMetricsSnapshot,
    RiskFactors,
)
from models.database import SupabaseClient, get_db


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Create a mocked SupabaseClient for testing."""
    with patch('models.database.create_client') as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        client = SupabaseClient()
        client.client = mock_client
        return client


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return UserCreate(
        email="test@example.com",
        age=30,
        gender=Gender.FEMALE,
        age_group=AgeGroup.ADULT,
        first_name="Maria",
        last_name="Silva",
    )


@pytest.fixture
def sample_gaze_points():
    """Sample gaze data points."""
    return [
        GazeDataPoint(
            timestamp=i * 0.033,
            gaze_x=0.5 + 0.1 * (i % 10) / 10,
            gaze_y=0.5 + 0.1 * ((i // 10) % 10) / 10,
            confidence=0.95,
            is_blink=i % 30 == 0,
        )
        for i in range(100)
    ]


# ============================================================================
# USER OPERATIONS TESTS
# ============================================================================

class TestUserOperations:
    """Test user CRUD operations."""

    def test_create_user_success(self, mock_supabase_client, sample_user_data):
        """Test successful user creation."""
        # Mock response
        user_id = str(uuid4())
        mock_response = MagicMock()
        mock_response.data = [{
            "user_id": user_id,
            "email": sample_user_data.email,
            "age": sample_user_data.age,
            "gender": sample_user_data.gender.value,
            "age_group": sample_user_data.age_group.value,
            "first_name": sample_user_data.first_name,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }]

        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = mock_response

        # Test
        result = mock_supabase_client.create_user(sample_user_data)

        assert result.email == sample_user_data.email
        assert result.age == sample_user_data.age
        assert result.is_active is True

    def test_create_user_api_error(self, mock_supabase_client, sample_user_data):
        """Test user creation with API error."""
        # Mock API error
        from postgrest.exceptions import APIError
        (mock_supabase_client.client.table()
         .insert()
         .execute.side_effect) = APIError({"message": "Email already exists", "code": "23505", "details": "", "hint": ""})

        # Test
        with pytest.raises(APIError):
            mock_supabase_client.create_user(sample_user_data)

    def test_get_user_success(self, mock_supabase_client):
        """Test successful user retrieval."""
        user_id = str(uuid4())
        mock_response = MagicMock()
        mock_response.data = {
            "user_id": user_id,
            "email": "test@example.com",
            "age": 30,
            "gender": "female",
            "age_group": "adult",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

        (mock_supabase_client.client.table()
         .select()
         .eq()
         .single()
         .execute.return_value) = mock_response

        result = mock_supabase_client.get_user(user_id)

        assert result.user_id == user_id
        assert result.email == "test@example.com"

    def test_get_user_not_found(self, mock_supabase_client):
        """Test user not found scenario."""
        from postgrest.exceptions import APIError
        (mock_supabase_client.client.table()
         .select()
         .eq()
         .single()
         .execute.side_effect) = APIError({"message": "No rows found", "code": "PGRST116", "details": "", "hint": ""})

        result = mock_supabase_client.get_user("nonexistent-id")

        assert result is None

    def test_list_users_success(self, mock_supabase_client):
        """Test listing users."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "user_id": str(uuid4()),
                "email": "user1@example.com",
                "age": 25,
                "gender": "male",
                "age_group": "adult",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True,
            },
            {
                "user_id": str(uuid4()),
                "email": "user2@example.com",
                "age": 35,
                "gender": "female",
                "age_group": "adult",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": True,
            },
        ]

        (mock_supabase_client.client.table()
         .select()
         .eq()
         .order()
         .range()
         .execute.return_value) = mock_response

        results = mock_supabase_client.list_users(limit=10)

        assert len(results) == 2
        assert results[0].email == "user1@example.com"


# ============================================================================
# CALIBRATION OPERATIONS TESTS
# ============================================================================

class TestCalibrationOperations:
    """Test calibration session CRUD operations."""

    def test_create_calibration_session_success(self, mock_supabase_client):
        """Test successful calibration session creation."""
        user_id = str(uuid4())
        session_id = str(uuid4())

        calib_data = CalibrationSessionCreate(
            user_id=user_id,
            num_points=9,
            calibration_distance_cm=50.0,
        )

        mock_response = MagicMock()
        mock_response.data = [{
            "calibration_id": session_id,
            "user_id": user_id,
            "status": "pending",
            "num_points": 9,
            "calibration_points": [],
            "mean_error_pixels": 0.0,
            "max_error_pixels": 0.0,
            "validity_score": 0.0,
            "created_at": datetime.utcnow().isoformat(),
        }]

        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = mock_response

        result = mock_supabase_client.create_calibration_session(calib_data)

        assert result.user_id == user_id
        assert result.num_points == 9
        assert result.status == "pending"

    def test_update_calibration_session(self, mock_supabase_client):
        """Test updating calibration session."""
        session_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [{
            "calibration_id": session_id,
            "user_id": str(uuid4()),
            "status": "completed",
            "num_points": 9,
            "mean_error_pixels": 15.5,
            "max_error_pixels": 25.0,
            "validity_score": 0.85,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }]

        (mock_supabase_client.client.table()
         .update()
         .eq()
         .execute.return_value) = mock_response

        updates = {
            "status": "completed",
            "mean_error_pixels": 15.5,
            "validity_score": 0.85,
        }

        result = mock_supabase_client.update_calibration_session(session_id, updates)

        assert result.status == "completed"
        assert result.validity_score == 0.85


# ============================================================================
# ASSESSMENT OPERATIONS TESTS
# ============================================================================

class TestAssessmentOperations:
    """Test assessment session CRUD operations."""

    def test_create_assessment_session_success(self, mock_supabase_client):
        """Test successful assessment session creation."""
        user_id = str(uuid4())
        calib_id = str(uuid4())
        session_id = str(uuid4())

        session_data = AssessmentSessionCreate(
            user_id=user_id,
            calibration_id=calib_id,
            assessment_type="asd_screening",
        )

        mock_response = MagicMock()
        mock_response.data = [{
            "session_id": session_id,
            "user_id": user_id,
            "calibration_id": calib_id,
            "status": "pending",
            "assessment_type": "asd_screening",
            "stimuli": [],
            "total_duration_ms": 0,
            "samples_count": 0,
            "signal_quality_mean": 0.0,
            "created_at": datetime.utcnow().isoformat(),
        }]

        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = mock_response

        result = mock_supabase_client.create_assessment_session(session_data)

        assert result.user_id == user_id
        assert result.status == "pending"

    def test_list_user_assessments(self, mock_supabase_client):
        """Test listing user's assessments."""
        user_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [
            {
                "session_id": str(uuid4()),
                "user_id": user_id,
                "calibration_id": str(uuid4()),
                "status": "completed",
                "assessment_type": "asd_screening",
                "stimuli": [],
                "total_duration_ms": 120000,
                "samples_count": 3600,
                "signal_quality_mean": 0.92,
                "created_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
            },
        ]

        (mock_supabase_client.client.table()
         .select()
         .eq()
         .order()
         .limit()
         .execute.return_value) = mock_response

        results = mock_supabase_client.list_user_assessments(user_id)

        assert len(results) == 1
        assert results[0].status == "completed"


# ============================================================================
# GAZE DATA OPERATIONS TESTS
# ============================================================================

class TestGazeDataOperations:
    """Test gaze data insertion and retrieval."""

    def test_insert_gaze_data_success(self, mock_supabase_client, sample_gaze_points):
        """Test successful gaze data insertion."""
        session_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [{"gaze_data_id": str(uuid4())} for _ in sample_gaze_points]

        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = mock_response

        count = mock_supabase_client.insert_gaze_data(session_id, sample_gaze_points)

        assert count == len(sample_gaze_points)

    def test_get_gaze_data_success(self, mock_supabase_client):
        """Test retrieving gaze data."""
        session_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [
            {
                "timestamp": i * 0.033,
                "gaze_x": 0.5,
                "gaze_y": 0.5,
                "confidence": 0.95,
                "is_blink": False,
                "head_pitch": 0.0,
                "head_yaw": 0.0,
                "head_roll": 0.0,
            }
            for i in range(10)
        ]

        (mock_supabase_client.client.table()
         .select()
         .eq()
         .order()
         .execute.return_value) = mock_response

        results = mock_supabase_client.get_gaze_data(session_id)

        assert len(results) == 10
        assert all(p.gaze_x == 0.5 for p in results)


# ============================================================================
# RESULTS OPERATIONS TESTS
# ============================================================================

class TestResultsOperations:
    """Test assessment results operations."""

    def test_create_assessment_results_success(self, mock_supabase_client):
        """Test successful results creation."""
        result_id = str(uuid4())
        session_id = str(uuid4())
        user_id = str(uuid4())

        metrics = AssessmentMetricsSnapshot(
            mean_social_attention_index=0.35,
        )

        risk_factors = RiskFactors(
            reduced_eye_gaze=True,
            reduced_social_attention=True,
        )

        results = AssessmentResultsResponse(
            result_id=result_id,
            session_id=session_id,
            user_id=user_id,
            assessment_type="asd_screening",
            metrics_snapshot=metrics,
            risk_factors=risk_factors,
            risk_factor_count=2,
            screening_result=ScreeningResult.MODERATE_RISK,
            confidence_score=0.75,
            risk_percentage=35.0,
            assessment_completed_at=datetime.utcnow(),
            results_generated_at=datetime.utcnow(),
        )

        mock_response = MagicMock()
        mock_response.data = [{
            "result_id": result_id,
            "session_id": session_id,
            "user_id": user_id,
            "screening_result": "moderate_risk",
        }]

        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = mock_response

        result = mock_supabase_client.create_assessment_results(results)

        assert result.result_id == result_id
        assert result.screening_result == ScreeningResult.MODERATE_RISK

    def test_list_user_results(self, mock_supabase_client):
        """Test listing user's results."""
        user_id = str(uuid4())

        mock_response = MagicMock()
        mock_response.data = [
            {
                "result_id": str(uuid4()),
                "session_id": str(uuid4()),
                "user_id": user_id,
                "screening_result": "high_risk",
                "risk_percentage": 75.0,
                "confidence_score": 0.9,
                "metrics_snapshot": {"mean_social_attention_index": 0.25},
                "risk_factors": {},
                "risk_factor_count": 5,
                "assessment_completed_at": datetime.utcnow().isoformat(),
                "results_generated_at": datetime.utcnow().isoformat(),
            },
        ]

        (mock_supabase_client.client.table()
         .select()
         .eq()
         .order()
         .limit()
         .execute.return_value) = mock_response

        results = mock_supabase_client.list_user_results(user_id)

        assert len(results) == 1
        assert results[0].risk_percentage == 75.0

    def test_delete_expired_results(self, mock_supabase_client):
        """Test deleting expired results."""
        mock_response = MagicMock()
        mock_response.data = [{"result_id": str(uuid4())} for _ in range(5)]

        (mock_supabase_client.client.table()
         .delete()
         .lt()
         .execute.return_value) = mock_response

        count = mock_supabase_client.delete_expired_results()

        assert count == 5


# ============================================================================
# DATABASE SINGLETON TESTS
# ============================================================================

class TestDatabaseSingleton:
    """Test database client singleton pattern."""

    def test_get_db_returns_singleton(self):
        """Test that get_db returns singleton instance."""
        with patch('models.database.SupabaseClient'):
            db1 = get_db()
            db2 = get_db()

            assert db1 is db2


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in database operations."""

    def test_api_error_handling(self, mock_supabase_client, sample_user_data):
        """Test proper API error handling."""
        from postgrest.exceptions import APIError

        (mock_supabase_client.client.table()
         .insert()
         .execute.side_effect) = APIError({"message": "Connection timeout", "code": "08006", "details": "", "hint": ""})

        with pytest.raises(APIError):
            mock_supabase_client.create_user(sample_user_data)

    def test_missing_required_field(self):
        """Test handling of missing required fields."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")  # Missing required fields


# ============================================================================
# INTEGRATION SCENARIO TESTS
# ============================================================================

class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    def test_full_assessment_workflow(self, mock_supabase_client, sample_user_data, sample_gaze_points):
        """Test complete assessment workflow: create user → calibration → assessment → results."""

        # 1. Create user
        user_id = str(uuid4())
        user_response = MagicMock()
        user_response.data = [{
            "user_id": user_id,
            "email": sample_user_data.email,
            "age": sample_user_data.age,
            "gender": sample_user_data.gender.value,
            "age_group": sample_user_data.age_group.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }]
        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = user_response

        user = mock_supabase_client.create_user(sample_user_data)
        assert user.user_id == user_id

        # 2. Create calibration
        calib_id = str(uuid4())
        calib_response = MagicMock()
        calib_response.data = [{
            "calibration_id": calib_id,
            "user_id": user_id,
            "status": "completed",
            "num_points": 9,
            "validity_score": 0.9,
            "created_at": datetime.utcnow().isoformat(),
        }]
        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = calib_response

        calib = mock_supabase_client.create_calibration_session(
            CalibrationSessionCreate(user_id=user_id, num_points=9)
        )
        assert calib.calibration_id == calib_id

        # 3. Create assessment
        session_id = str(uuid4())
        session_response = MagicMock()
        session_response.data = [{
            "session_id": session_id,
            "user_id": user_id,
            "calibration_id": calib_id,
            "status": "completed",
            "samples_count": len(sample_gaze_points),
            "created_at": datetime.utcnow().isoformat(),
        }]
        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = session_response

        session = mock_supabase_client.create_assessment_session(
            AssessmentSessionCreate(user_id=user_id, calibration_id=calib_id)
        )
        assert session.session_id == session_id

        # 4. Insert gaze data
        gaze_response = MagicMock()
        gaze_response.data = [{"gaze_data_id": str(uuid4())} for _ in sample_gaze_points]
        (mock_supabase_client.client.table()
         .insert()
         .execute.return_value) = gaze_response

        count = mock_supabase_client.insert_gaze_data(session_id, sample_gaze_points)
        assert count == len(sample_gaze_points)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
