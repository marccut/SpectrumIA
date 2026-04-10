"""
SpectrumIA Pydantic Schemas

Data models for API requests, responses, and database persistence.
Aligns with Supabase PostgreSQL schema and eye-tracking feature structures.

Scientific References:
- Klin et al. (2002) - Visual fixation patterns
- Jones & Klin (2013) - Attention to eyes
- Frazier et al. (2018) - Gaze meta-analysis
- Carpenter et al. (2021) - Digital behavioral phenotyping
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


# ============================================================================
# Enums
# ============================================================================

class Gender(str, Enum):
    """Biological sex categories."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_SPECIFIED = "not_specified"


class AgeGroup(str, Enum):
    """Age group categories."""
    TODDLER = "toddler"  # 18-36 months
    PRESCHOOL = "preschool"  # 3-5 years
    SCHOOL = "school"  # 6-12 years
    ADOLESCENT = "adolescent"  # 13-17 years
    ADULT = "adult"  # 18-65 years
    OLDER_ADULT = "older_adult"  # 65+ years


class AssessmentStatus(str, Enum):
    """Assessment session status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ScreeningResult(str, Enum):
    """Screening result categories."""
    LOW_RISK = "low_risk"
    MODERATE_RISK = "moderate_risk"
    HIGH_RISK = "high_risk"
    INCONCLUSIVE = "inconclusive"


class AOIType(str, Enum):
    """Area of Interest types."""
    EYES = "eyes"
    MOUTH = "mouth"
    NOSE = "nose"
    FACE_OVAL = "face_oval"
    BACKGROUND = "background"


# ============================================================================
# User/Patient Models
# ============================================================================

class UserBase(BaseModel):
    """Base user information."""
    email: str = Field(..., description="User email address")
    age: int = Field(..., ge=0, le=120, description="Age in years")
    gender: Gender = Field(..., description="Biological sex")
    age_group: AgeGroup = Field(..., description="Age group category")


class UserCreate(UserBase):
    """User creation request."""
    password: Optional[str] = Field(None, description="Password (optional for OAuth)")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    notes: Optional[str] = None


class UserResponse(UserBase):
    """User response model."""
    user_id: str = Field(..., description="Unique user identifier")
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


# ============================================================================
# Calibration Models
# ============================================================================

class CalibrationPoint(BaseModel):
    """Single calibration point."""
    point_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    screen_x: float = Field(..., ge=0.0, le=1.0, description="Normalized screen X position")
    screen_y: float = Field(..., ge=0.0, le=1.0, description="Normalized screen Y position")
    gaze_x: float = Field(..., ge=0.0, le=1.0, description="Gaze X coordinate")
    gaze_y: float = Field(..., ge=0.0, le=1.0, description="Gaze Y coordinate")
    timestamp: float = Field(..., description="Timestamp in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    distance_pixels: float = Field(0.0, description="Distance from target in pixels")


class CalibrationSessionCreate(BaseModel):
    """Calibration session creation."""
    user_id: str
    num_points: int = Field(9, ge=4, le=16, description="Number of calibration points")
    calibration_distance_cm: float = Field(50.0, description="Distance from screen in cm")


class CalibrationSessionResponse(BaseModel):
    """Calibration session response."""
    calibration_id: str
    user_id: str
    status: AssessmentStatus
    num_points: int
    calibration_points: List[CalibrationPoint] = []
    mean_error_pixels: float = 0.0
    max_error_pixels: float = 0.0
    validity_score: float = Field(0.0, ge=0.0, le=1.0)
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Gaze Data Models
# ============================================================================

class GazeDataPoint(BaseModel):
    """Single gaze data point."""
    timestamp: float = Field(..., description="Timestamp in seconds")
    gaze_x: float = Field(..., ge=0.0, le=1.0, description="Normalized gaze X")
    gaze_y: float = Field(..., ge=0.0, le=1.0, description="Normalized gaze Y")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    is_blink: bool = Field(False, description="Whether a blink was detected")
    head_pitch: float = Field(0.0, description="Head pitch in degrees")
    head_yaw: float = Field(0.0, description="Head yaw in degrees")
    head_roll: float = Field(0.0, description="Head roll in degrees")


class FixationMetricsModel(BaseModel):
    """Fixation analysis metrics."""
    count: int = 0
    mean_duration_ms: float = 0.0
    median_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    total_duration_ms: float = 0.0
    std_duration_ms: float = 0.0


class SaccadeMetricsModel(BaseModel):
    """Saccade analysis metrics."""
    count: int = 0
    mean_amplitude_deg: float = 0.0
    mean_velocity_deg_per_sec: float = 0.0
    median_velocity_deg_per_sec: float = 0.0
    mean_peak_velocity_deg_per_sec: float = 0.0
    latency_ms: float = 0.0


class SocialAttentionMetricsModel(BaseModel):
    """Social attention metrics - CORE ASD METRIC."""
    social_attention_index: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="(eyes + mouth) / total - Key ASD biomarker (Jones & Klin 2013)"
    )
    eye_preference: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="eyes / (eyes + mouth) - Reduced in ASD"
    )
    mouth_preference: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="mouth / (eyes + mouth)"
    )
    time_on_eyes_ms: float = 0.0
    time_on_mouth_ms: float = 0.0
    time_on_face_ms: float = 0.0
    attention_shifts: int = 0


class ScanpathMetricsModel(BaseModel):
    """Scanpath and temporal metrics."""
    entropy: float = 0.0
    time_to_first_fixation_ms: float = 0.0
    fixation_density: float = 0.0
    transition_count: int = 0
    path_length_deg: float = 0.0
    mean_gaze_position: Tuple[float, float] = (0.0, 0.0)


class GazeMetricsModel(BaseModel):
    """Comprehensive eye-tracking metrics."""
    timestamp: float
    stimulus_id: Optional[str] = None
    fixations: FixationMetricsModel
    saccades: SaccadeMetricsModel
    social_attention: SocialAttentionMetricsModel
    scanpath: ScanpathMetricsModel
    aoi_metrics: Dict[str, Dict] = {}
    blink_count: int = 0
    blink_rate: float = 0.0
    gaze_confidence_mean: float = 0.0
    signal_quality: float = Field(0.0, ge=0.0, le=1.0)


# ============================================================================
# Assessment Models
# ============================================================================

class StimulusRecord(BaseModel):
    """Single stimulus presentation during assessment."""
    stimulus_id: str
    stimulus_name: str = Field(..., description="e.g., 'face_video_01'")
    stimulus_type: str = Field(..., description="e.g., 'face', 'geometric', 'mixed'")
    duration_ms: int = Field(..., ge=1000, description="Stimulus duration")
    gaze_samples: List[GazeDataPoint] = []
    metrics: Optional[GazeMetricsModel] = None
    start_timestamp: float = 0.0
    end_timestamp: float = 0.0


class AssessmentSessionCreate(BaseModel):
    """Assessment session creation."""
    user_id: str
    calibration_id: str = Field(..., description="Reference to calibration session")
    assessment_type: str = Field(default="asd_screening", description="Type of assessment")


class AssessmentSessionResponse(BaseModel):
    """Assessment session response."""
    session_id: str
    user_id: str
    calibration_id: str
    status: AssessmentStatus
    assessment_type: str
    stimuli: List[StimulusRecord] = []
    total_duration_ms: int = 0
    samples_count: int = 0
    signal_quality_mean: float = 0.0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Results Models
# ============================================================================

class AssessmentMetricsSnapshot(BaseModel):
    """Aggregated metrics across all stimuli."""
    # Social Attention (CORE)
    mean_social_attention_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mean SAI across assessment"
    )
    sai_std: float = 0.0

    # Eye / Mouth Preference
    mean_eye_preference: float = Field(0.0, ge=0.0, le=1.0)
    mean_mouth_preference: float = Field(0.0, ge=0.0, le=1.0)
    eye_preference_trend: str = Field("stable", description="'decreasing', 'stable', 'increasing'")

    # Fixation Metrics
    mean_fixation_duration_ms: float = 0.0
    mean_fixation_count: int = 0

    # Saccade Metrics
    mean_saccade_amplitude_deg: float = 0.0
    mean_saccade_velocity_deg_per_sec: float = 0.0

    # Scanpath
    mean_scanpath_entropy: float = 0.0
    mean_time_to_first_fixation_ms: float = 0.0

    # Blink
    mean_blink_rate: float = 0.0

    # Quality
    signal_quality_mean: float = 0.0
    valid_stimuli_count: int = 0
    total_stimuli_count: int = 0


class RiskFactors(BaseModel):
    """Risk factors identified during assessment."""
    reduced_eye_gaze: bool = False
    reduced_mouth_gaze: bool = False
    atypical_fixation_patterns: bool = False
    reduced_social_attention: bool = False
    increased_scanpath_entropy: bool = False
    increased_blink_rate: bool = False
    poor_signal_quality: bool = False


class AssessmentResultsCreate(BaseModel):
    """Assessment results creation."""
    session_id: str
    user_id: str


class AssessmentResultsResponse(BaseModel):
    """Assessment results response."""
    result_id: str
    session_id: str
    user_id: str
    assessment_type: str

    # Metrics
    metrics_snapshot: AssessmentMetricsSnapshot

    # Risk Factors
    risk_factors: RiskFactors
    risk_factor_count: int = Field(0, ge=0, le=7, description="Number of risk factors identified")

    # Screening Result
    screening_result: ScreeningResult
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    risk_percentage: float = Field(0.0, ge=0.0, le=100.0)

    # Clinical Notes
    clinical_notes: Optional[str] = None
    interpretation: Optional[str] = None

    # Metadata
    assessment_completed_at: datetime
    results_generated_at: datetime
    expires_at: Optional[datetime] = None

    # Recommendations
    recommend_clinical_evaluation: bool = False
    recommendation_text: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Export/Report Models
# ============================================================================

class AssessmentSummary(BaseModel):
    """Summary of assessment for export/report."""
    user_id: str
    user_email: str
    age: int
    gender: Gender
    assessment_date: datetime
    screening_result: ScreeningResult
    risk_percentage: float
    confidence_score: float
    key_findings: List[str] = []
    recommendations: List[str] = []
    detailed_metrics: AssessmentMetricsSnapshot
    signal_quality: float


class BulkAssessmentExport(BaseModel):
    """Bulk export of multiple assessments."""
    export_date: datetime
    user_count: int
    assessment_count: int
    assessments: List[AssessmentSummary]
    filter_criteria: Dict[str, str] = {}


# ============================================================================
# Helper Methods for Data Conversion
# ============================================================================

def gaze_metrics_to_model(gaze_metrics: dict) -> GazeMetricsModel:
    """Convert GazeMetrics dataclass to Pydantic model."""
    return GazeMetricsModel(**gaze_metrics)


def create_assessment_results(
    session_id: str,
    user_id: str,
    metrics_snapshot: AssessmentMetricsSnapshot,
    risk_factors: RiskFactors
) -> AssessmentResultsResponse:
    """Create assessment results from metrics and risk factors."""
    risk_factor_count = sum([
        risk_factors.reduced_eye_gaze,
        risk_factors.reduced_mouth_gaze,
        risk_factors.atypical_fixation_patterns,
        risk_factors.reduced_social_attention,
        risk_factors.increased_scanpath_entropy,
        risk_factors.increased_blink_rate,
        risk_factors.poor_signal_quality,
    ])

    # Determine screening result based on risk factors
    if risk_factor_count == 0:
        screening_result = ScreeningResult.LOW_RISK
        confidence_score = 0.9
        risk_percentage = 5.0
    elif risk_factor_count <= 2:
        screening_result = ScreeningResult.MODERATE_RISK
        confidence_score = 0.75
        risk_percentage = 35.0
    elif risk_factor_count <= 4:
        screening_result = ScreeningResult.HIGH_RISK
        confidence_score = 0.85
        risk_percentage = 65.0
    else:
        screening_result = ScreeningResult.HIGH_RISK
        confidence_score = 0.90
        risk_percentage = 85.0

    return AssessmentResultsResponse(
        result_id=str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        assessment_type="asd_screening",
        metrics_snapshot=metrics_snapshot,
        risk_factors=risk_factors,
        risk_factor_count=risk_factor_count,
        screening_result=screening_result,
        confidence_score=confidence_score,
        risk_percentage=risk_percentage,
        assessment_completed_at=datetime.utcnow(),
        results_generated_at=datetime.utcnow(),
        recommend_clinical_evaluation=screening_result in [
            ScreeningResult.MODERATE_RISK,
            ScreeningResult.HIGH_RISK
        ],
    )
