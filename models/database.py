"""
SpectrumIA Supabase Database Client

Handles all database operations for SpectrumIA using Supabase (PostgreSQL).
Manages users, calibrations, assessments, and results persistence.

Integration Points:
- User registration and authentication
- Calibration session storage
- Assessment session tracking
- Gaze metrics persistence
- Results generation and retrieval
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import json
import uuid

from supabase import create_client, Client
from postgrest.exceptions import APIError

from core.config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    RESULTS_RETENTION_DAYS,
)

from .schemas import (
    UserResponse,
    UserCreate,
    CalibrationSessionResponse,
    CalibrationSessionCreate,
    AssessmentSessionResponse,
    AssessmentSessionCreate,
    AssessmentResultsResponse,
    AssessmentResultsCreate,
    GazeDataPoint,
    GazeMetricsModel,
    ScreeningResult,
)

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase database client for SpectrumIA.

    Provides methods for CRUD operations on:
    - Users
    - Calibration sessions
    - Assessment sessions
    - Gaze data
    - Assessment results
    """

    def __init__(self, access_token: Optional[str]):
        """Initialize an RLS-enforced client for one authenticated session."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL plus SUPABASE_KEY in environment."
            )
        if not access_token:
            raise ValueError("Authenticated Supabase access token is required.")

        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.client.postgrest.auth(access_token)
        logger.info("Supabase client initialized with session JWT (RLS enforced)")

    # ========================================================================
    # User Operations
    # ========================================================================

    def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            UserResponse with created user details

        Raises:
            APIError: If user creation fails
        """
        try:
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            response = (
                self.client.table("users")
                .insert({
                    "user_id": user_id,
                    "email": user_data.email,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "age": user_data.age,
                    "gender": user_data.gender.value,
                    "age_group": user_data.age_group.value,
                    "notes": user_data.notes,
                    "is_active": True,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                })
                .execute()
            )

            logger.info(f"User created: {user_id}")
            return self._format_user_response(response.data[0])

        except APIError as e:
            logger.error(f"Error creating user: {e}")
            raise

    def get_user(self, user_id: str) -> Optional[UserResponse]:
        """
        Retrieve user by ID.

        Args:
            user_id: User ID

        Returns:
            UserResponse or None if not found
        """
        try:
            response = (
                self.client.table("users")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            return self._format_user_response(response.data)
        except APIError as e:
            if "No rows found" in str(e):
                return None
            logger.error(f"Error retrieving user: {e}")
            raise

    def list_users(self, limit: int = 100, offset: int = 0) -> List[UserResponse]:
        """
        List all active users.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of UserResponse objects
        """
        try:
            response = (
                self.client.table("users")
                .select("*")
                .eq("is_active", True)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return [self._format_user_response(user) for user in response.data]
        except APIError as e:
            logger.error(f"Error listing users: {e}")
            raise

    # ========================================================================
    # Calibration Operations
    # ========================================================================

    def create_calibration_session(
        self,
        calibration_data: CalibrationSessionCreate
    ) -> CalibrationSessionResponse:
        """
        Create a new calibration session.

        Args:
            calibration_data: Calibration session data

        Returns:
            CalibrationSessionResponse with session details
        """
        try:
            calibration_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            response = (
                self.client.table("calibration_sessions")
                .insert({
                    "calibration_id": calibration_id,
                    "user_id": calibration_data.user_id,
                    "status": "pending",
                    "num_points": calibration_data.num_points,
                    "calibration_distance_cm": calibration_data.calibration_distance_cm,
                    "calibration_points": [],
                    "mean_error_pixels": 0.0,
                    "max_error_pixels": 0.0,
                    "validity_score": 0.0,
                    "created_at": now.isoformat(),
                })
                .execute()
            )

            logger.info(f"Calibration session created: {calibration_id}")
            return self._format_calibration_response(response.data[0])

        except APIError as e:
            logger.error(f"Error creating calibration session: {e}")
            raise

    def update_calibration_session(
        self,
        calibration_id: str,
        updates: Dict[str, Any]
    ) -> CalibrationSessionResponse:
        """
        Update calibration session.

        Args:
            calibration_id: Calibration session ID
            updates: Dictionary of fields to update

        Returns:
            Updated CalibrationSessionResponse
        """
        try:
            response = (
                self.client.table("calibration_sessions")
                .update(updates)
                .eq("calibration_id", calibration_id)
                .execute()
            )

            logger.info(f"Calibration session updated: {calibration_id}")
            return self._format_calibration_response(response.data[0])

        except APIError as e:
            logger.error(f"Error updating calibration session: {e}")
            raise

    def get_calibration_session(
        self,
        calibration_id: str
    ) -> Optional[CalibrationSessionResponse]:
        """
        Retrieve calibration session.

        Args:
            calibration_id: Calibration session ID

        Returns:
            CalibrationSessionResponse or None if not found
        """
        try:
            response = (
                self.client.table("calibration_sessions")
                .select("*")
                .eq("calibration_id", calibration_id)
                .single()
                .execute()
            )
            return self._format_calibration_response(response.data)
        except APIError as e:
            if "No rows found" in str(e):
                return None
            logger.error(f"Error retrieving calibration session: {e}")
            raise

    # ========================================================================
    # Assessment Operations
    # ========================================================================

    def create_assessment_session(
        self,
        session_data: AssessmentSessionCreate
    ) -> AssessmentSessionResponse:
        """
        Create a new assessment session.

        Args:
            session_data: Assessment session creation data

        Returns:
            AssessmentSessionResponse with session details
        """
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            response = (
                self.client.table("assessment_sessions")
                .insert({
                    "session_id": session_id,
                    "user_id": session_data.user_id,
                    "calibration_id": session_data.calibration_id,
                    "status": "pending",
                    "assessment_type": session_data.assessment_type,
                    "stimuli": [],
                    "total_duration_ms": 0,
                    "samples_count": 0,
                    "signal_quality_mean": 0.0,
                    "created_at": now.isoformat(),
                    "started_at": None,
                    "completed_at": None,
                })
                .execute()
            )

            logger.info(f"Assessment session created: {session_id}")
            return self._format_assessment_response(response.data[0])

        except APIError as e:
            logger.error(f"Error creating assessment session: {e}")
            raise

    def update_assessment_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> AssessmentSessionResponse:
        """
        Update assessment session.

        Args:
            session_id: Assessment session ID
            updates: Dictionary of fields to update

        Returns:
            Updated AssessmentSessionResponse
        """
        try:
            response = (
                self.client.table("assessment_sessions")
                .update(updates)
                .eq("session_id", session_id)
                .execute()
            )

            logger.info(f"Assessment session updated: {session_id}")
            return self._format_assessment_response(response.data[0])

        except APIError as e:
            logger.error(f"Error updating assessment session: {e}")
            raise

    def get_assessment_session(
        self,
        session_id: str
    ) -> Optional[AssessmentSessionResponse]:
        """
        Retrieve assessment session.

        Args:
            session_id: Assessment session ID

        Returns:
            AssessmentSessionResponse or None if not found
        """
        try:
            response = (
                self.client.table("assessment_sessions")
                .select("*")
                .eq("session_id", session_id)
                .single()
                .execute()
            )
            return self._format_assessment_response(response.data)
        except APIError as e:
            if "No rows found" in str(e):
                return None
            logger.error(f"Error retrieving assessment session: {e}")
            raise

    def list_user_assessments(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[AssessmentSessionResponse]:
        """
        List all assessment sessions for a user.

        Args:
            user_id: User ID
            limit: Maximum number of sessions to return

        Returns:
            List of AssessmentSessionResponse objects
        """
        try:
            response = (
                self.client.table("assessment_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return [self._format_assessment_response(sess) for sess in response.data]
        except APIError as e:
            logger.error(f"Error listing assessments: {e}")
            raise

    # ========================================================================
    # Gaze Data Operations
    # ========================================================================

    def insert_gaze_data(
        self,
        session_id: str,
        gaze_samples: List[GazeDataPoint]
    ) -> int:
        """
        Insert gaze data for an assessment session.

        Args:
            session_id: Assessment session ID
            gaze_samples: List of GazeDataPoint objects

        Returns:
            Number of samples inserted
        """
        try:
            data = [
                {
                    "gaze_data_id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "timestamp": sample.timestamp,
                    "gaze_x": sample.gaze_x,
                    "gaze_y": sample.gaze_y,
                    "confidence": sample.confidence,
                    "is_blink": sample.is_blink,
                    "head_pitch": sample.head_pitch,
                    "head_yaw": sample.head_yaw,
                    "head_roll": sample.head_roll,
                }
                for sample in gaze_samples
            ]

            response = (
                self.client.table("gaze_data")
                .insert(data)
                .execute()
            )

            logger.info(f"Inserted {len(response.data)} gaze samples for session {session_id}")
            return len(response.data)

        except APIError as e:
            logger.error(f"Error inserting gaze data: {e}")
            raise

    def get_gaze_data(
        self,
        session_id: str
    ) -> List[GazeDataPoint]:
        """
        Retrieve gaze data for an assessment session.

        Args:
            session_id: Assessment session ID

        Returns:
            List of GazeDataPoint objects
        """
        try:
            response = (
                self.client.table("gaze_data")
                .select("*")
                .eq("session_id", session_id)
                .order("timestamp", desc=False)
                .execute()
            )

            return [
                GazeDataPoint(
                    timestamp=row["timestamp"],
                    gaze_x=row["gaze_x"],
                    gaze_y=row["gaze_y"],
                    confidence=row["confidence"],
                    is_blink=row["is_blink"],
                    head_pitch=row.get("head_pitch", 0.0),
                    head_yaw=row.get("head_yaw", 0.0),
                    head_roll=row.get("head_roll", 0.0),
                )
                for row in response.data
            ]

        except APIError as e:
            logger.error(f"Error retrieving gaze data: {e}")
            raise

    def insert_gaze_metrics(
        self,
        session_id: str,
        metrics: GazeMetricsModel,
    ) -> str:
        """
        Insert extracted gaze metrics for one stimulus into gaze_metrics table.

        Args:
            session_id: Assessment session ID
            metrics: GazeMetricsModel with nested sub-models

        Returns:
            metrics_id of the inserted row
        """
        try:
            data = {
                "metrics_id": str(uuid.uuid4()),
                "session_id": session_id,
                "stimulus_id": metrics.stimulus_id,
                "timestamp": metrics.timestamp,
                # Fixation metrics (flattened from metrics.fixations)
                "fixation_count": metrics.fixations.count,
                "fixation_mean_duration_ms": metrics.fixations.mean_duration_ms,
                "fixation_median_duration_ms": metrics.fixations.median_duration_ms,
                "fixation_std_duration_ms": metrics.fixations.std_duration_ms,
                "fixation_total_duration_ms": metrics.fixations.total_duration_ms,
                # Saccade metrics (flattened from metrics.saccades)
                "saccade_count": metrics.saccades.count,
                "saccade_mean_amplitude_deg": metrics.saccades.mean_amplitude_deg,
                "saccade_mean_velocity_deg_per_sec": metrics.saccades.mean_velocity_deg_per_sec,
                "saccade_peak_velocity_deg_per_sec": metrics.saccades.mean_peak_velocity_deg_per_sec,
                "saccade_latency_ms": metrics.saccades.latency_ms,
                # Social attention metrics — CORE ASD biomarkers
                "social_attention_index": metrics.social_attention.social_attention_index,
                "eye_preference": metrics.social_attention.eye_preference,
                "mouth_preference": metrics.social_attention.mouth_preference,
                "time_on_eyes_ms": metrics.social_attention.time_on_eyes_ms,
                "time_on_mouth_ms": metrics.social_attention.time_on_mouth_ms,
                "time_on_face_ms": metrics.social_attention.time_on_face_ms,
                "attention_shifts": metrics.social_attention.attention_shifts,
                # Scanpath metrics
                "scanpath_entropy": metrics.scanpath.entropy,
                "time_to_first_fixation_ms": metrics.scanpath.time_to_first_fixation_ms,
                "fixation_density": metrics.scanpath.fixation_density,
                "path_length_deg": metrics.scanpath.path_length_deg,
                # Blink and quality
                "blink_count": metrics.blink_count,
                "blink_rate": metrics.blink_rate,
                "gaze_confidence_mean": metrics.gaze_confidence_mean,
                "signal_quality": metrics.signal_quality,
                # AOI metrics as JSON
                "aoi_metrics": metrics.aoi_metrics,
            }

            response = (
                self.client.table("gaze_metrics")
                .insert(data)
                .execute()
            )

            metrics_id = response.data[0]["metrics_id"]
            logger.info(
                "Inserted gaze metrics for stimulus '%s' in session %s (id=%s)",
                metrics.stimulus_id, session_id, metrics_id,
            )
            return metrics_id

        except APIError as e:
            logger.error("Error inserting gaze metrics: %s", e)
            raise

    # ========================================================================
    # Results Operations
    # ========================================================================

    def create_assessment_results(
        self,
        results_data: AssessmentResultsResponse
    ) -> AssessmentResultsResponse:
        """
        Create assessment results.

        Args:
            results_data: Assessment results response

        Returns:
            Created AssessmentResultsResponse
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=RESULTS_RETENTION_DAYS)

            response = (
                self.client.table("assessment_results")
                .insert({
                    "result_id": results_data.result_id,
                    "session_id": results_data.session_id,
                    "user_id": results_data.user_id,
                    "assessment_type": results_data.assessment_type,
                    "metrics_snapshot": results_data.metrics_snapshot.model_dump(),
                    "risk_factors": results_data.risk_factors.model_dump(),
                    "risk_factor_count": results_data.risk_factor_count,
                    "screening_result": results_data.screening_result.value,
                    "confidence_score": results_data.confidence_score,
                    "risk_percentage": results_data.risk_percentage,
                    "clinical_notes": results_data.clinical_notes,
                    "interpretation": results_data.interpretation,
                    "assessment_completed_at": results_data.assessment_completed_at.isoformat(),
                    "results_generated_at": results_data.results_generated_at.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "recommend_clinical_evaluation": results_data.recommend_clinical_evaluation,
                    "recommendation_text": results_data.recommendation_text,
                    "created_at": now.isoformat(),
                })
                .execute()
            )

            logger.info(f"Assessment results created: {results_data.result_id}")
            return self._format_results_response(response.data[0])

        except APIError as e:
            logger.error(f"Error creating assessment results: {e}")
            raise

    def get_assessment_results(
        self,
        result_id: str
    ) -> Optional[AssessmentResultsResponse]:
        """
        Retrieve assessment results.

        Args:
            result_id: Result ID

        Returns:
            AssessmentResultsResponse or None if not found
        """
        try:
            response = (
                self.client.table("assessment_results")
                .select("*")
                .eq("result_id", result_id)
                .single()
                .execute()
            )
            return self._format_results_response(response.data)
        except APIError as e:
            if "No rows found" in str(e):
                return None
            logger.error(f"Error retrieving assessment results: {e}")
            raise

    def list_user_results(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[AssessmentResultsResponse]:
        """
        List all assessment results for a user.

        Args:
            user_id: User ID
            limit: Maximum number of results to return

        Returns:
            List of AssessmentResultsResponse objects
        """
        try:
            response = (
                self.client.table("assessment_results")
                .select("*")
                .eq("user_id", user_id)
                .order("results_generated_at", desc=True)
                .limit(limit)
                .execute()
            )
            return [self._format_results_response(result) for result in response.data]
        except APIError as e:
            logger.error(f"Error listing results: {e}")
            raise

    def delete_expired_results(self) -> int:
        """
        Delete expired assessment results.

        Returns:
            Number of results deleted
        """
        try:
            now = datetime.now(timezone.utc).isoformat()
            response = (
                self.client.table("assessment_results")
                .delete()
                .lt("expires_at", now)
                .execute()
            )

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Deleted {deleted_count} expired assessment results")
            return deleted_count

        except APIError as e:
            logger.error(f"Error deleting expired results: {e}")
            raise

    # ========================================================================
    # Questionnaire Operations
    # ========================================================================

    def save_questionnaire_result(
        self,
        user_id: str,
        questionnaire_name: str,
        total_score: float,
        subscale_scores: Dict[str, float],
        raw_responses: Dict[str, int],
        risk_level: str,
        camouflage_weight: float,
        interpretation: str,
    ) -> Dict[str, Any]:
        """Persist one immutable CAT-Q or RAADS-R result for the current user."""
        if questionnaire_name not in {"CAT-Q", "RAADS-R"}:
            raise ValueError("Unsupported questionnaire name.")
        if risk_level not in {"low", "moderate", "high"}:
            raise ValueError("Invalid questionnaire risk level.")
        if not 0.0 <= camouflage_weight <= 1.0:
            raise ValueError("Camouflage weight must be between 0 and 1.")

        questionnaire_result_id = str(uuid.uuid4())
        data = {
            "questionnaire_result_id": questionnaire_result_id,
            "user_id": user_id,
            "questionnaire_name": questionnaire_name,
            "total_score": total_score,
            "subscale_scores": subscale_scores,
            "raw_responses": raw_responses,
            "risk_level": risk_level,
            "camouflage_weight": camouflage_weight,
            "interpretation": interpretation,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            response = (
                self.client.table("questionnaire_results")
                .insert(data)
                .execute()
            )
            logger.info(
                "Questionnaire result created: %s (%s)",
                questionnaire_result_id,
                questionnaire_name,
            )
            return response.data[0]
        except APIError as e:
            logger.error("Error saving questionnaire result: %s", e)
            raise

    # ========================================================================
    # Helper Formatting Methods
    # ========================================================================

    def _format_user_response(self, data: Dict) -> UserResponse:
        """Format database user record to UserResponse."""
        return UserResponse(
            user_id=data["user_id"],
            email=data["email"],
            age=data["age"],
            gender=data["gender"],
            age_group=data["age_group"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_active=data["is_active"],
        )

    def _format_calibration_response(self, data: Dict) -> CalibrationSessionResponse:
        """Format database calibration record to CalibrationSessionResponse."""
        return CalibrationSessionResponse(
            calibration_id=data["calibration_id"],
            user_id=data["user_id"],
            status=data["status"],
            num_points=data["num_points"],
            calibration_points=data.get("calibration_points", []),
            mean_error_pixels=data.get("mean_error_pixels", 0.0),
            max_error_pixels=data.get("max_error_pixels", 0.0),
            validity_score=data.get("validity_score", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )

    def _format_assessment_response(self, data: Dict) -> AssessmentSessionResponse:
        """Format database assessment record to AssessmentSessionResponse."""
        return AssessmentSessionResponse(
            session_id=data["session_id"],
            user_id=data["user_id"],
            calibration_id=data["calibration_id"],
            status=data["status"],
            assessment_type=data["assessment_type"],
            stimuli=data.get("stimuli", []),
            total_duration_ms=data.get("total_duration_ms", 0),
            samples_count=data.get("samples_count", 0),
            signal_quality_mean=data.get("signal_quality_mean", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )

    def _format_results_response(self, data: Dict) -> AssessmentResultsResponse:
        """Format database results record to AssessmentResultsResponse."""
        return AssessmentResultsResponse(
            result_id=data["result_id"],
            session_id=data["session_id"],
            user_id=data["user_id"],
            assessment_type=data["assessment_type"],
            metrics_snapshot=data["metrics_snapshot"],
            risk_factors=data["risk_factors"],
            risk_factor_count=data["risk_factor_count"],
            screening_result=ScreeningResult(data["screening_result"]),
            confidence_score=data["confidence_score"],
            risk_percentage=data["risk_percentage"],
            clinical_notes=data.get("clinical_notes"),
            interpretation=data.get("interpretation"),
            assessment_completed_at=datetime.fromisoformat(data["assessment_completed_at"]),
            results_generated_at=datetime.fromisoformat(data["results_generated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            recommend_clinical_evaluation=data.get("recommend_clinical_evaluation", False),
            recommendation_text=data.get("recommendation_text"),
        )


def get_db(access_token: Optional[str]) -> SupabaseClient:
    """Create an RLS-enforced database client for the current user session.

    The client is intentionally not cached globally: Streamlit serves multiple
    user sessions in one process, so a mutable shared PostgREST token could
    leak one user's authorization context into another session.
    """
    if not access_token:
        raise ValueError("Authenticated Supabase access token is required.")
    return SupabaseClient(access_token=access_token)
