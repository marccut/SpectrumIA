-- ============================================================================
-- SpectrumIA — canonical Row Level Security policies
-- ============================================================================
-- This is the single source of truth for clinical-table RLS.
-- Schema contract: every ownership column referenced below is UUID, matching
-- auth.uid(); casts are intentionally avoided so PostgreSQL keeps type and
-- index semantics intact.
--
-- The application creates a PostgREST client with the anon key plus the
-- current Streamlit session JWT (models/database.py). The service role is not
-- used by the clinical-data client and does not need an RLS policy.
-- ============================================================================

begin;

-- ---------------------------------------------------------------------------
-- Incremental schema required by questionnaire persistence.
-- Kept here as well as in the full schema so this canonical deployment can be
-- applied safely to an existing SpectrumIA database.
-- ---------------------------------------------------------------------------
create table if not exists public.questionnaire_results (
  questionnaire_result_id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references public.users(user_id) on delete cascade,
  questionnaire_name varchar(20) not null check (
    questionnaire_name in ('CAT-Q', 'RAADS-R')
  ),
  total_score double precision not null check (total_score >= 0.0),
  subscale_scores jsonb not null default '{}'::jsonb,
  raw_responses jsonb not null default '{}'::jsonb,
  risk_level varchar(20) not null check (
    risk_level in ('low', 'moderate', 'high')
  ),
  camouflage_weight double precision not null check (
    camouflage_weight >= 0.0 and camouflage_weight <= 1.0
  ),
  interpretation text not null default '',
  created_at timestamp with time zone not null default current_timestamp
);

create index if not exists idx_questionnaire_results_user_id
  on public.questionnaire_results(user_id);
create index if not exists idx_questionnaire_results_name
  on public.questionnaire_results(questionnaire_name);
create index if not exists idx_questionnaire_results_created_at
  on public.questionnaire_results(created_at desc);

-- ---------------------------------------------------------------------------
-- Enable RLS on every clinical table.
-- ---------------------------------------------------------------------------
alter table public.users enable row level security;
alter table public.calibration_sessions enable row level security;
alter table public.assessment_sessions enable row level security;
alter table public.assessment_results enable row level security;
alter table public.questionnaire_results enable row level security;
alter table public.gaze_data enable row level security;
alter table public.gaze_metrics enable row level security;

-- ---------------------------------------------------------------------------
-- Remove policy names from the previous implementation.
-- PostgreSQL combines permissive policies with OR, so leaving a weaker legacy
-- policy active would bypass the canonical ownership checks below.
-- ---------------------------------------------------------------------------
drop policy if exists "Users can view their own profile" on public.users;
drop policy if exists "Users can update their own profile" on public.users;
drop policy if exists "Service role has full access to users" on public.users;

drop policy if exists "Users can view their own calibrations"
  on public.calibration_sessions;
drop policy if exists "Users can create their own calibrations"
  on public.calibration_sessions;
drop policy if exists "Users can update their own calibrations"
  on public.calibration_sessions;
drop policy if exists "Service role has full access to calibration_sessions"
  on public.calibration_sessions;

drop policy if exists "Users can view their own assessments"
  on public.assessment_sessions;
drop policy if exists "Users can create their own assessments"
  on public.assessment_sessions;
drop policy if exists "Users can update their own assessments"
  on public.assessment_sessions;
drop policy if exists "Service role has full access to assessment_sessions"
  on public.assessment_sessions;

drop policy if exists "Users can view their own results"
  on public.assessment_results;
drop policy if exists "Users can create their own results"
  on public.assessment_results;
drop policy if exists "Users can update their own results"
  on public.assessment_results;
drop policy if exists "Service role has full access to assessment_results"
  on public.assessment_results;

drop policy if exists "Users can view their own questionnaire results"
  on public.questionnaire_results;
drop policy if exists "Users can create their own questionnaire results"
  on public.questionnaire_results;
drop policy if exists "Service role has full access to questionnaire_results"
  on public.questionnaire_results;

drop policy if exists "Users can view their gaze metrics"
  on public.gaze_metrics;
drop policy if exists "Users can insert their gaze metrics"
  on public.gaze_metrics;
drop policy if exists "Service role has full access to gaze_metrics"
  on public.gaze_metrics;

-- ---------------------------------------------------------------------------
-- Remove canonical names so this migration is repeatable.
-- ---------------------------------------------------------------------------
drop policy if exists users_select_own on public.users;
drop policy if exists users_insert_own on public.users;
drop policy if exists users_update_own on public.users;

drop policy if exists calib_select_own on public.calibration_sessions;
drop policy if exists calib_insert_own on public.calibration_sessions;
drop policy if exists calib_update_own on public.calibration_sessions;

drop policy if exists assess_select_own on public.assessment_sessions;
drop policy if exists assess_insert_own on public.assessment_sessions;
drop policy if exists assess_update_own on public.assessment_sessions;

drop policy if exists results_select_own on public.assessment_results;
drop policy if exists results_insert_own on public.assessment_results;

drop policy if exists questionnaire_results_select_own
  on public.questionnaire_results;
drop policy if exists questionnaire_results_insert_own
  on public.questionnaire_results;

drop policy if exists gaze_data_select_own on public.gaze_data;
drop policy if exists gaze_data_insert_own on public.gaze_data;

drop policy if exists gaze_metrics_select_own on public.gaze_metrics;
drop policy if exists gaze_metrics_insert_own on public.gaze_metrics;

-- ---------------------------------------------------------------------------
-- users
-- ---------------------------------------------------------------------------
create policy users_select_own on public.users
  for select to authenticated
  using (user_id = auth.uid());

create policy users_insert_own on public.users
  for insert to authenticated
  with check (user_id = auth.uid());

create policy users_update_own on public.users
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- calibration_sessions
-- ---------------------------------------------------------------------------
create policy calib_select_own on public.calibration_sessions
  for select to authenticated
  using (user_id = auth.uid());

create policy calib_insert_own on public.calibration_sessions
  for insert to authenticated
  with check (user_id = auth.uid());

create policy calib_update_own on public.calibration_sessions
  for update to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- assessment_sessions
-- A session can reference only a calibration owned by the same user.
-- ---------------------------------------------------------------------------
create policy assess_select_own on public.assessment_sessions
  for select to authenticated
  using (user_id = auth.uid());

create policy assess_insert_own on public.assessment_sessions
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from public.calibration_sessions c
      where c.calibration_id = assessment_sessions.calibration_id
        and c.user_id = auth.uid()
    )
  );

create policy assess_update_own on public.assessment_sessions
  for update to authenticated
  using (user_id = auth.uid())
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from public.calibration_sessions c
      where c.calibration_id = assessment_sessions.calibration_id
        and c.user_id = auth.uid()
    )
  );

-- ---------------------------------------------------------------------------
-- assessment_results
-- A result can reference only an assessment session owned by the same user.
-- Results are immutable to authenticated users after insertion.
-- ---------------------------------------------------------------------------
create policy results_select_own on public.assessment_results
  for select to authenticated
  using (
    user_id = auth.uid()
    and exists (
      select 1 from public.assessment_sessions s
      where s.session_id = assessment_results.session_id
        and s.user_id = auth.uid()
    )
  );

create policy results_insert_own on public.assessment_results
  for insert to authenticated
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from public.assessment_sessions s
      where s.session_id = assessment_results.session_id
        and s.user_id = auth.uid()
    )
  );

-- ---------------------------------------------------------------------------
-- questionnaire_results
-- Results are append-only and belong directly to the authenticated user.
-- ---------------------------------------------------------------------------
create policy questionnaire_results_select_own on public.questionnaire_results
  for select to authenticated
  using (user_id = auth.uid());

create policy questionnaire_results_insert_own on public.questionnaire_results
  for insert to authenticated
  with check (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- gaze_data — ownership inherited through assessment_sessions.
-- ---------------------------------------------------------------------------
create policy gaze_data_select_own on public.gaze_data
  for select to authenticated
  using (exists (
    select 1 from public.assessment_sessions s
    where s.session_id = gaze_data.session_id
      and s.user_id = auth.uid()
  ));

create policy gaze_data_insert_own on public.gaze_data
  for insert to authenticated
  with check (exists (
    select 1 from public.assessment_sessions s
    where s.session_id = gaze_data.session_id
      and s.user_id = auth.uid()
  ));

-- ---------------------------------------------------------------------------
-- gaze_metrics — ownership inherited through assessment_sessions.
-- ---------------------------------------------------------------------------
create policy gaze_metrics_select_own on public.gaze_metrics
  for select to authenticated
  using (exists (
    select 1 from public.assessment_sessions s
    where s.session_id = gaze_metrics.session_id
      and s.user_id = auth.uid()
  ));

create policy gaze_metrics_insert_own on public.gaze_metrics
  for insert to authenticated
  with check (exists (
    select 1 from public.assessment_sessions s
    where s.session_id = gaze_metrics.session_id
      and s.user_id = auth.uid()
  ));

-- ---------------------------------------------------------------------------
-- Views
-- Existing views are hardened in place. security_invoker makes every query
-- use the caller's RLS permissions instead of the view owner's privileges.
-- ---------------------------------------------------------------------------
alter view if exists public.assessment_summary
  set (security_invoker = true);
alter view if exists public.high_risk_assessments
  set (security_invoker = true);
alter view if exists public.user_assessment_history
  set (security_invoker = true);

revoke all on public.assessment_summary from public, anon;
revoke all on public.high_risk_assessments from public, anon;
revoke all on public.user_assessment_history from public, anon;

grant select on public.assessment_summary to authenticated;
grant select on public.high_risk_assessments to authenticated;
grant select on public.user_assessment_history to authenticated;

commit;

-- Verification queries (run separately after applying the migration):
-- select schemaname, tablename, policyname, cmd, roles
--   from pg_policies
--   where schemaname = 'public'
--     and tablename in (
--       'users', 'calibration_sessions', 'assessment_sessions',
--       'assessment_results', 'questionnaire_results',
--       'gaze_data', 'gaze_metrics'
--     )
--   order by tablename, policyname;
--
-- select relname, relrowsecurity
--   from pg_class
--   where relname in (
--     'users', 'calibration_sessions', 'assessment_sessions',
--     'assessment_results', 'questionnaire_results',
--     'gaze_data', 'gaze_metrics'
--   );
