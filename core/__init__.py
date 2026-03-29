"""
SpectrumIA Core Module

Core processing functionality for eye-tracking and gaze estimation.
"""

from .config import (
    PROJECT_ROOT,
    APP_VERSION,
    APP_DEBUG,
    SUPABASE_URL,
    GAZE_CALIBRATION_POINTS,
    validate_config,
)

__version__ = APP_VERSION
__all__ = [
    "PROJECT_ROOT",
    "APP_VERSION",
    "APP_DEBUG",
    "SUPABASE_URL",
    "GAZE_CALIBRATION_POINTS",
    "validate_config",
]
