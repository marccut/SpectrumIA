-- ============================================================================
-- SpectrumIA - Row Level Security (RLS) Policies
-- ============================================================================
--
-- This file contains RLS policies for production Supabase deployment
-- These policies ensure users can only access their own data
--
-- To apply these policies:
-- 1. Login to Supabase dashboard
-- 2. Go to SQL Editor
-- 3. Copy and paste each section
-- 4. Execute the SQL
--
-- ============================================================================

-- ============================================================================
-- 1. ENABLE RLS ON ALL TABLES
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibration_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE gaze_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 2. USERS TABLE POLICIES
-- ============================================================================

-- Users can view their own profile
CREATE POLICY "Users can view their own profile"
  ON users FOR SELECT
  USING (auth.uid()::uuid = user_id);

-- Users can update their own profile
CREATE POLICY "Users can update their own profile"
  ON users FOR UPDATE
  USING (auth.uid()::uuid = user_id)
  WITH CHECK (auth.uid()::uuid = user_id);

-- Service role can do everything
CREATE POLICY "Service role has full access to users"
  ON users FOR ALL
  USING (current_setting('role') = 'authenticated' AND auth.role() = 'service_role');

-- ============================================================================
-- 3. CALIBRATION SESSIONS POLICIES
-- ============================================================================

-- Users can view their own calibration sessions
CREATE POLICY "Users can view their own calibrations"
  ON calibration_sessions FOR SELECT
  USING (auth.uid()::uuid = user_id);

-- Users can insert their own calibration sessions
CREATE POLICY "Users can create their own calibrations"
  ON calibration_sessions FOR INSERT
  WITH CHECK (auth.uid()::uuid = user_id);

-- Users can update their own calibration sessions
CREATE POLICY "Users can update their own calibrations"
  ON calibration_sessions FOR UPDATE
  USING (auth.uid()::uuid = user_id)
  WITH CHECK (auth.uid()::uuid = user_id);

-- Service role can do everything
CREATE POLICY "Service role has full access to calibration_sessions"
  ON calibration_sessions FOR ALL
  USING (current_setting('role') = 'authenticated' AND auth.role() = 'service_role');

-- ============================================================================
-- 4. ASSESSMENT SESSIONS POLICIES
-- ============================================================================

-- Users can view their own assessment sessions
CREATE POLICY "Users can view their own assessments"
  ON assessment_sessions FOR SELECT
  USING (auth.uid()::uuid = user_id);

-- Users can insert their own assessment sessions
CREATE POLICY "Users can create their own assessments"
  ON assessment_sessions FOR INSERT
  WITH CHECK (auth.uid()::uuid = user_id);

-- Users can update their own assessment sessions
CREATE POLICY "Users can update their own assessments"
  ON assessment_sessions FOR UPDATE
  USING (auth.uid()::uuid = user_id)
  WITH CHECK (auth.uid()::uuid = user_id);

-- Service role can do everything
CREATE POLICY "Service role has full access to assessment_sessions"
  ON assessment_sessions FOR ALL
  USING (current_setting('role') = 'authenticated' AND auth.role() = 'service_role');

-- ============================================================================
-- 5. GAZE METRICS POLICIES
-- ============================================================================

-- Users can view gaze metrics from their assessment sessions
CREATE POLICY "Users can view their gaze metrics"
  ON gaze_metrics FOR SELECT
  USING (
    session_id IN (
      SELECT session_id FROM assessment_sessions
      WHERE user_id = auth.uid()::uuid
    )
  );

-- Users can insert gaze metrics for their assessment sessions
CREATE POLICY "Users can insert their gaze metrics"
  ON gaze_metrics FOR INSERT
  WITH CHECK (
    session_id IN (
      SELECT session_id FROM assessment_sessions
      WHERE user_id = auth.uid()::uuid
    )
  );

-- Service role can do everything
CREATE POLICY "Service role has full access to gaze_metrics"
  ON gaze_metrics FOR ALL
  USING (current_setting('role') = 'authenticated' AND auth.role() = 'service_role');

-- ============================================================================
-- 6. ASSESSMENT RESULTS POLICIES
-- ============================================================================

-- Users can view their own assessment results
CREATE POLICY "Users can view their own results"
  ON assessment_results FOR SELECT
  USING (
    session_id IN (
      SELECT session_id FROM assessment_sessions
      WHERE user_id = auth.uid()::uuid
    )
  );

-- Users can insert their own assessment results
CREATE POLICY "Users can create their own results"
  ON assessment_results FOR INSERT
  WITH CHECK (
    session_id IN (
      SELECT session_id FROM assessment_sessions
      WHERE user_id = auth.uid()::uuid
    )
  );

-- Users can update their own assessment results (for corrections)
CREATE POLICY "Users can update their own results"
  ON assessment_results FOR UPDATE
  USING (
    session_id IN (
      SELECT session_id FROM assessment_sessions
      WHERE user_id = auth.uid()::uuid
    )
  )
  WITH CHECK (
    session_id IN (
      SELECT session_id FROM assessment_sessions
      WHERE user_id = auth.uid()::uuid
    )
  );

-- Service role can do everything
CREATE POLICY "Service role has full access to assessment_results"
  ON assessment_results FOR ALL
  USING (current_setting('role') = 'authenticated' AND auth.role() = 'service_role');

-- ============================================================================
-- 7. VERIFICATION QUERIES
-- ============================================================================

-- Check all RLS policies
-- SELECT schemaname, tablename, policyname, permissive, roles, qual, with_check
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- ORDER BY tablename, policyname;

-- Check which tables have RLS enabled
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY tablename;

-- ============================================================================
-- NOTES FOR PRODUCTION
-- ============================================================================
--
-- These RLS policies ensure:
-- 1. Users can ONLY access their own data
-- 2. Service role (backend) has full access for operations
-- 3. Unauthorized users cannot see other users' assessments
-- 4. Data is protected at the database level, not just application level
--
-- Important:
-- - Always test RLS policies in development first
-- - Monitor query performance with RLS enabled
-- - Use appropriate indexes to optimize RLS queries
-- - Regularly audit RLS policies for security
-- - Document any policy changes in git
--
-- ============================================================================
