"""
SpectrumIA Configuration Module

Central configuration management using environment variables and sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
CORE_DIR = PROJECT_ROOT / "core"
MODELS_DIR = PROJECT_ROOT / "models"
ASSETS_DIR = PROJECT_ROOT / "assets"
STIMULI_DIR = PROJECT_ROOT / "stimuli"
TESTS_DIR = PROJECT_ROOT / "tests"

# Application Settings
APP_DEBUG = os.getenv("APP_DEBUG", "False").lower() == "true"
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")

# Eye-Tracking Configuration
GAZE_CALIBRATION_POINTS = int(os.getenv("GAZE_CALIBRATION_POINTS", "9"))
GAZE_SMOOTHING_FACTOR = float(os.getenv("GAZE_SMOOTHING_FACTOR", "0.7"))
MIN_FIXATION_DURATION_MS = int(os.getenv("MIN_FIXATION_DURATION_MS", "100"))
MAX_FIXATION_DURATION_MS = 1000  # Internal constant
SACCADE_VELOCITY_THRESHOLD = 30  # degrees/second

# Assessment Configuration
ASSESSMENT_VIDEO_PATH = Path(os.getenv("ASSESSMENT_VIDEO_PATH", str(STIMULI_DIR / "videos")))
NUM_AOI_REGIONS = int(os.getenv("NUM_AOI_REGIONS", "4"))
MIN_SAMPLES_PER_STIMULUS = int(os.getenv("MIN_SAMPLES_PER_STIMULUS", "30"))

# Session Configuration
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
RESULTS_RETENTION_DAYS = int(os.getenv("RESULTS_RETENTION_DAYS", "90"))

# Feature Extraction Flags
EXTRACT_GAZE_DYNAMICS = os.getenv("EXTRACT_GAZE_DYNAMICS", "True").lower() == "true"
EXTRACT_TEMPORAL_METRICS = os.getenv("EXTRACT_TEMPORAL_METRICS", "True").lower() == "true"
EXTRACT_SCANPATH_ENTROPY = os.getenv("EXTRACT_SCANPATH_ENTROPY", "True").lower() == "true"

# MediaPipe Configuration
MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE = 0.5
MEDIAPIPE_FACE_MESH_MIN_CONFIDENCE = 0.5
MEDIAPIPE_FACE_MESH_MIN_TRACKING_CONFIDENCE = 0.5
FACE_LANDMARKER_MODEL_PATH = str(
    Path(os.getenv("FACE_LANDMARKER_MODEL_PATH", str(ASSETS_DIR / "face_landmarker.task")))
)

# Display Configuration
DISPLAY_CALIBRATION_POINTS = True
DISPLAY_GAZE_POINT = True
DISPLAY_AOI_REGIONS = True
DISPLAY_HEATMAP = True

# Model Configuration
MODEL_EYE_TRACKING = "mediapipe"  # Options: "mediapipe", "deepgaze", "pytorch"
MODEL_GAZE_ESTIMATOR = "3d_face_model"

# Validation
def validate_config():
    """Validate critical configuration settings."""
    if not SUPABASE_URL:
        print("Warning: SUPABASE_URL not configured. Database features will be unavailable.")

    if not ASSESSMENT_VIDEO_PATH.exists():
        print(f"Warning: Assessment video path does not exist: {ASSESSMENT_VIDEO_PATH}")

    if GAZE_SMOOTHING_FACTOR < 0 or GAZE_SMOOTHING_FACTOR > 1:
        raise ValueError(f"GAZE_SMOOTHING_FACTOR must be between 0 and 1, got {GAZE_SMOOTHING_FACTOR}")

    if MIN_SAMPLES_PER_STIMULUS < 10:
        raise ValueError(f"MIN_SAMPLES_PER_STIMULUS should be at least 10, got {MIN_SAMPLES_PER_STIMULUS}")


if __name__ == "__main__":
    validate_config()
    print("✓ Configuration validated successfully")
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  Debug Mode: {APP_DEBUG}")
    print(f"  Version: {APP_VERSION}")
