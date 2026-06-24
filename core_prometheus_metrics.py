"""Prometheus metrics for SpectrumIA eye-tracking system"""

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# ============================================================================
# Eye-Tracking Metrics
# ============================================================================

# Gaze tracking confidence
gaze_tracking_confidence = Gauge(
    'gaze_tracking_confidence',
    'Current gaze tracking confidence (0-1)',
    labelnames=['user_id', 'session_id']
)

# Face detection failures
face_detection_failures_total = Counter(
    'face_detection_failures_total',
    'Total face detection failures',
    labelnames=['reason']
)

# Gaze calibration accuracy
gaze_calibration_accuracy_percent = Gauge(
    'gaze_calibration_accuracy_percent',
    'Gaze calibration accuracy percentage',
    labelnames=['user_id']
)

# Fixation duration
fixation_duration_seconds = Histogram(
    'fixation_duration_seconds',
    'Fixation duration in seconds',
    buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

# Saccade amplitude
saccade_amplitude_degrees = Histogram(
    'saccade_amplitude_degrees',
    'Saccade amplitude in degrees',
    buckets=[1, 5, 10, 20, 30]
)

# ============================================================================
# Calibration Metrics
# ============================================================================

calibration_sessions_started_total = Counter(
    'calibration_sessions_started_total',
    'Total calibration sessions started',
    labelnames=['user_id']
)

calibration_sessions_completed_total = Counter(
    'calibration_sessions_completed_total',
    'Total calibration sessions completed',
    labelnames=['user_id']
)

calibration_sessions_failed_total = Counter(
    'calibration_sessions_failed_total',
    'Total calibration sessions failed',
    labelnames=['reason']
)

# ============================================================================
# Assessment Metrics
# ============================================================================

assessment_sessions_started_total = Counter(
    'assessment_sessions_started_total',
    'Total assessment sessions started',
    labelnames=['assessment_type']
)

assessment_sessions_completed_total = Counter(
    'assessment_sessions_completed_total',
    'Total assessment sessions completed',
    labelnames=['assessment_type']
)

assessment_sessions_failed_total = Counter(
    'assessment_sessions_failed_total',
    'Total assessment sessions failed',
    labelnames=['reason']
)

assessment_asd_risk_score = Gauge(
    'assessment_asd_risk_score',
    'ASD risk score from assessment (0-1)',
    labelnames=['user_id', 'assessment_id']
)

assessment_results_generated_total = Counter(
    'assessment_results_generated_total',
    'Total assessment results generated',
    labelnames=['result_type']
)

# ============================================================================
# Database Metrics
# ============================================================================

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    labelnames=['operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    labelnames=['operation', 'status']
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    labelnames=['error_type']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

# ============================================================================
# API Metrics
# ============================================================================

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    labelnames=['method', 'endpoint', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    labelnames=['method', 'endpoint', 'status']
)

# ============================================================================
# System Metrics
# ============================================================================

active_sessions = Gauge(
    'active_sessions',
    'Number of active sessions'
)

users_logged_in = Gauge(
    'users_logged_in',
    'Number of users currently logged in'
)

# ============================================================================
# Decorators for automatic metric tracking
# ============================================================================

def track_http_request(func):
    """Decorator to track HTTP request metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        method = kwargs.get('method', 'GET')
        endpoint = kwargs.get('endpoint', func.__name__)

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            status = kwargs.get('status', '200')
            return result
        except Exception as e:
            status = '500'
            raise
        finally:
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).observe(duration)
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
    return wrapper

def track_db_operation(func):
    """Decorator to track database operation metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        operation = kwargs.get('operation', func.__name__)

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            status = 'success'
            return result
        except Exception as e:
            status = 'error'
            db_errors_total.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            db_query_duration_seconds.labels(operation=operation).observe(duration)
            db_queries_total.labels(operation=operation, status=status).inc()
    return wrapper

# ============================================================================
# Utility functions
# ============================================================================

def record_calibration_event(success: bool, user_id: str = None, reason: str = None):
    """Record a calibration event"""
    calibration_sessions_started_total.labels(user_id=user_id or "unknown").inc()
    if success:
        calibration_sessions_completed_total.labels(user_id=user_id or "unknown").inc()
    else:
        calibration_sessions_failed_total.labels(reason=reason or "unknown").inc()

def record_assessment_event(success: bool, assessment_type: str = "asd", reason: str = None):
    """Record an assessment event"""
    assessment_sessions_started_total.labels(assessment_type=assessment_type).inc()
    if success:
        assessment_sessions_completed_total.labels(assessment_type=assessment_type).inc()
    else:
        assessment_sessions_failed_total.labels(reason=reason or "unknown").inc()

def set_asd_risk_score(score: float, user_id: str = None, assessment_id: str = None):
    """Set ASD risk score"""
    assessment_asd_risk_score.labels(
        user_id=user_id or "unknown",
        assessment_id=assessment_id or "unknown"
    ).set(score)
