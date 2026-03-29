-- ============================================================================
-- SpectrumIA Supabase PostgreSQL Schema Migrations
--
-- Schema completo para persistência de dados de eye-tracking e avaliação ASD
-- Baseado em modelos Pydantic (schemas.py)
--
-- Referências Científicas:
-- - Klin et al. (2002) - Visual fixation patterns
-- - Jones & Klin (2013) - Attention to eyes in autism
-- - Frazier et al. (2018) - Gaze meta-analysis
-- - Carpenter et al. (2021) - Digital behavioral phenotyping
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USERS TABLE - Patient/Participant data
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    gender VARCHAR(50) NOT NULL CHECK (gender IN ('male', 'female', 'other', 'not_specified')),
    age_group VARCHAR(50) NOT NULL CHECK (
        age_group IN ('toddler', 'preschool', 'school', 'adolescent', 'adult', 'older_adult')
    ),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_email CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_is_active ON users(is_active);


-- ============================================================================
-- 2. CALIBRATION SESSIONS TABLE - Gaze calibration data
-- ============================================================================

CREATE TABLE IF NOT EXISTS calibration_sessions (
    calibration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (
        status IN ('pending', 'in_progress', 'completed', 'cancelled', 'failed')
    ),
    num_points INTEGER NOT NULL CHECK (num_points >= 4 AND num_points <= 16),
    calibration_distance_cm FLOAT DEFAULT 50.0,

    -- JSON array of calibration points
    calibration_points JSONB DEFAULT '[]'::jsonb,

    -- Validation metrics
    mean_error_pixels FLOAT DEFAULT 0.0,
    max_error_pixels FLOAT DEFAULT 0.0,
    validity_score FLOAT CHECK (validity_score >= 0.0 AND validity_score <= 1.0),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Cleanup
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

CREATE INDEX idx_calibration_user_id ON calibration_sessions(user_id);
CREATE INDEX idx_calibration_status ON calibration_sessions(status);
CREATE INDEX idx_calibration_created_at ON calibration_sessions(created_at DESC);


-- ============================================================================
-- 3. ASSESSMENT SESSIONS TABLE - Complete assessment tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS assessment_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    calibration_id UUID NOT NULL REFERENCES calibration_sessions(calibration_id) ON DELETE RESTRICT,
    status VARCHAR(50) NOT NULL CHECK (
        status IN ('pending', 'in_progress', 'completed', 'cancelled', 'failed')
    ),
    assessment_type VARCHAR(100) DEFAULT 'asd_screening',

    -- Stimulus presentation info (JSON array)
    stimuli JSONB DEFAULT '[]'::jsonb,

    -- Session metrics
    total_duration_ms INTEGER DEFAULT 0,
    samples_count INTEGER DEFAULT 0,
    signal_quality_mean FLOAT CHECK (signal_quality_mean >= 0.0 AND signal_quality_mean <= 1.0),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Cleanup
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '90 days')
);

CREATE INDEX idx_assessment_user_id ON assessment_sessions(user_id);
CREATE INDEX idx_assessment_calibration_id ON assessment_sessions(calibration_id);
CREATE INDEX idx_assessment_status ON assessment_sessions(status);
CREATE INDEX idx_assessment_created_at ON assessment_sessions(created_at DESC);


-- ============================================================================
-- 4. GAZE DATA TABLE - Raw eye-tracking samples
-- ============================================================================

CREATE TABLE IF NOT EXISTS gaze_data (
    gaze_data_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(session_id) ON DELETE CASCADE,

    -- Gaze coordinates (normalized 0-1)
    timestamp FLOAT NOT NULL,
    gaze_x FLOAT NOT NULL CHECK (gaze_x >= 0.0 AND gaze_x <= 1.0),
    gaze_y FLOAT NOT NULL CHECK (gaze_y >= 0.0 AND gaze_y <= 1.0),

    -- Quality metrics
    confidence FLOAT CHECK (confidence >= 0.0 AND confidence <= 1.0),
    is_blink BOOLEAN DEFAULT FALSE,

    -- Head pose (degrees)
    head_pitch FLOAT DEFAULT 0.0,
    head_yaw FLOAT DEFAULT 0.0,
    head_roll FLOAT DEFAULT 0.0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gaze_data_session_id ON gaze_data(session_id);
CREATE INDEX idx_gaze_data_timestamp ON gaze_data(session_id, timestamp);
CREATE INDEX idx_gaze_data_blink ON gaze_data(is_blink) WHERE is_blink = TRUE;


-- ============================================================================
-- 5. GAZE METRICS TABLE - Extracted eye-tracking features
-- ============================================================================

CREATE TABLE IF NOT EXISTS gaze_metrics (
    metrics_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES assessment_sessions(session_id) ON DELETE CASCADE,
    stimulus_id VARCHAR(100),

    -- Timestamp
    timestamp FLOAT NOT NULL,

    -- Fixation metrics
    fixation_count INTEGER DEFAULT 0,
    fixation_mean_duration_ms FLOAT DEFAULT 0.0,
    fixation_median_duration_ms FLOAT DEFAULT 0.0,
    fixation_std_duration_ms FLOAT DEFAULT 0.0,
    fixation_total_duration_ms FLOAT DEFAULT 0.0,

    -- Saccade metrics
    saccade_count INTEGER DEFAULT 0,
    saccade_mean_amplitude_deg FLOAT DEFAULT 0.0,
    saccade_mean_velocity_deg_per_sec FLOAT DEFAULT 0.0,
    saccade_peak_velocity_deg_per_sec FLOAT DEFAULT 0.0,
    saccade_latency_ms FLOAT DEFAULT 0.0,

    -- CORE: Social Attention Index (Jones & Klin 2013)
    social_attention_index FLOAT CHECK (social_attention_index >= 0.0 AND social_attention_index <= 1.0),
    eye_preference FLOAT CHECK (eye_preference >= 0.0 AND eye_preference <= 1.0),
    mouth_preference FLOAT CHECK (mouth_preference >= 0.0 AND mouth_preference <= 1.0),
    time_on_eyes_ms FLOAT DEFAULT 0.0,
    time_on_mouth_ms FLOAT DEFAULT 0.0,
    time_on_face_ms FLOAT DEFAULT 0.0,
    attention_shifts INTEGER DEFAULT 0,

    -- Scanpath metrics
    scanpath_entropy FLOAT DEFAULT 0.0,
    time_to_first_fixation_ms FLOAT DEFAULT 0.0,
    fixation_density FLOAT DEFAULT 0.0,
    path_length_deg FLOAT DEFAULT 0.0,

    -- Blink metrics
    blink_count INTEGER DEFAULT 0,
    blink_rate FLOAT DEFAULT 0.0,

    -- Quality
    gaze_confidence_mean FLOAT DEFAULT 0.0,
    signal_quality FLOAT CHECK (signal_quality >= 0.0 AND signal_quality <= 1.0),

    -- Per-AOI metrics (JSON)
    aoi_metrics JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gaze_metrics_session_id ON gaze_metrics(session_id);
CREATE INDEX idx_gaze_metrics_stimulus_id ON gaze_metrics(stimulus_id);
CREATE INDEX idx_gaze_metrics_sai ON gaze_metrics(social_attention_index);
CREATE INDEX idx_gaze_metrics_created_at ON gaze_metrics(created_at DESC);


-- ============================================================================
-- 6. ASSESSMENT RESULTS TABLE - Final screening results
-- ============================================================================

CREATE TABLE IF NOT EXISTS assessment_results (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL UNIQUE REFERENCES assessment_sessions(session_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assessment_type VARCHAR(100) DEFAULT 'asd_screening',

    -- Aggregated metrics snapshot
    metrics_snapshot JSONB NOT NULL,

    -- Risk factors assessment
    risk_factors JSONB NOT NULL,
    risk_factor_count INTEGER CHECK (risk_factor_count >= 0 AND risk_factor_count <= 7),

    -- Screening result
    screening_result VARCHAR(50) NOT NULL CHECK (
        screening_result IN ('low_risk', 'moderate_risk', 'high_risk', 'inconclusive')
    ),
    confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    risk_percentage FLOAT CHECK (risk_percentage >= 0.0 AND risk_percentage <= 100.0),

    -- Clinical interpretation
    clinical_notes TEXT,
    interpretation TEXT,
    recommend_clinical_evaluation BOOLEAN DEFAULT FALSE,
    recommendation_text TEXT,

    -- Timestamps
    assessment_completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    results_generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '90 days'),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_results_user_id ON assessment_results(user_id);
CREATE INDEX idx_results_screening_result ON assessment_results(screening_result);
CREATE INDEX idx_results_created_at ON assessment_results(created_at DESC);
CREATE INDEX idx_results_expires_at ON assessment_results(expires_at);


-- ============================================================================
-- 7. AUDIT LOG TABLE - Track all database changes
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);


-- ============================================================================
-- 8. VIEWS - Commonly used queries
-- ============================================================================

-- View: Assessments with user info
CREATE OR REPLACE VIEW assessment_summary AS
SELECT
    a.session_id,
    a.user_id,
    u.email,
    u.age,
    u.gender,
    a.assessment_type,
    a.status,
    a.total_duration_ms,
    a.samples_count,
    a.signal_quality_mean,
    r.screening_result,
    r.confidence_score,
    r.risk_percentage,
    a.created_at,
    a.completed_at
FROM assessment_sessions a
JOIN users u ON a.user_id = u.user_id
LEFT JOIN assessment_results r ON a.session_id = r.session_id
ORDER BY a.created_at DESC;


-- View: High-risk assessments
CREATE OR REPLACE VIEW high_risk_assessments AS
SELECT
    r.result_id,
    r.user_id,
    u.email,
    r.screening_result,
    r.risk_percentage,
    r.confidence_score,
    r.recommend_clinical_evaluation,
    r.results_generated_at
FROM assessment_results r
JOIN users u ON r.user_id = u.user_id
WHERE r.screening_result IN ('high_risk', 'moderate_risk')
ORDER BY r.risk_percentage DESC;


-- View: User assessment history
CREATE OR REPLACE VIEW user_assessment_history AS
SELECT
    u.user_id,
    u.email,
    COUNT(DISTINCT a.session_id) as total_assessments,
    MAX(a.completed_at) as last_assessment,
    COUNT(DISTINCT CASE WHEN r.screening_result = 'high_risk' THEN r.result_id END) as high_risk_count,
    COUNT(DISTINCT CASE WHEN r.screening_result = 'moderate_risk' THEN r.result_id END) as moderate_risk_count,
    COUNT(DISTINCT CASE WHEN r.screening_result = 'low_risk' THEN r.result_id END) as low_risk_count
FROM users u
LEFT JOIN assessment_sessions a ON u.user_id = a.user_id
LEFT JOIN assessment_results r ON a.session_id = r.session_id
GROUP BY u.user_id, u.email;


-- ============================================================================
-- 9. FUNCTIONS - Helper stored procedures
-- ============================================================================

-- Function: Mark expired records for cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_records()
RETURNS TABLE(table_name TEXT, deleted_count INT) AS $$
DECLARE
    expired_calibrations INT;
    expired_assessments INT;
    expired_results INT;
BEGIN
    -- Delete expired calibration sessions (30 days)
    DELETE FROM calibration_sessions
    WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS expired_calibrations = ROW_COUNT;

    -- Delete expired assessment sessions (90 days)
    DELETE FROM assessment_sessions
    WHERE expires_at < CURRENT_TIMESTAMP
    AND completed_at IS NOT NULL;
    GET DIAGNOSTICS expired_assessments = ROW_COUNT;

    -- Delete expired results (90 days)
    DELETE FROM assessment_results
    WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS expired_results = ROW_COUNT;

    RETURN QUERY
    SELECT 'calibration_sessions'::TEXT, expired_calibrations
    UNION ALL
    SELECT 'assessment_sessions'::TEXT, expired_assessments
    UNION ALL
    SELECT 'assessment_results'::TEXT, expired_results;
END;
$$ LANGUAGE plpgsql;


-- Function: Calculate average SAI per user
CREATE OR REPLACE FUNCTION get_user_avg_sai(user_id_param UUID)
RETURNS FLOAT AS $$
SELECT AVG(social_attention_index)
FROM gaze_metrics
WHERE session_id IN (
    SELECT session_id FROM assessment_sessions
    WHERE user_id = user_id_param
)
AND social_attention_index IS NOT NULL;
$$ LANGUAGE SQL;


-- ============================================================================
-- 10. TRIGGERS - Automatic timestamp updates
-- ============================================================================

-- Trigger: Update users.updated_at
CREATE OR REPLACE FUNCTION update_users_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_users_timestamp();


-- ============================================================================
-- 11. PERMISSIONS & SECURITY
-- ============================================================================

-- Note: In production, configure RLS (Row Level Security) policies
-- Example RLS policy for users:
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Users can view their own data"
--   ON users FOR SELECT
--   USING (auth.uid()::uuid = user_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check all tables created
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public' ORDER BY table_name;

-- Check all indexes
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;

-- ============================================================================
