# 🚀 Phase 8.1: Supabase Production Setup - Step-by-Step Guide

**Status**: IN PROGRESS
**Date Started**: 2026-03-27
**Estimated Duration**: 2-3 hours

---

## 📋 Overview

This guide provides detailed step-by-step instructions for setting up SpectrumIA in Supabase production environment. We'll create a production project, apply the database schema, configure security policies, and set up authentication.

---

## ✅ Pre-Setup Checklist

Before starting, ensure you have:

- [ ] Supabase account (https://supabase.com) - if not, create one
- [ ] Access to project credentials
- [ ] Access to your organization's secrets management system
- [ ] Database backups planned
- [ ] Reviewed PHASE8_PRODUCTION_DEPLOYMENT.md
- [ ] Read this entire guide before starting

---

## 📊 Phase 8.1 Breakdown

| Task | Time | Status |
|------|------|--------|
| 1. Create Supabase Project | 15 min | ⏳ |
| 2. Configure Project Settings | 15 min | ⏳ |
| 3. Apply Database Migrations | 30 min | ⏳ |
| 4. Configure RLS Policies | 45 min | ⏳ |
| 5. Setup Authentication | 30 min | ⏳ |
| 6. Create Environment Variables | 15 min | ⏳ |
| **TOTAL** | **2.5 hours** | |

---

## 🎯 Step 1: Create Supabase Production Project

### 1.1 Create Organization (if needed)

```
1. Go to https://app.supabase.com
2. Sign in with your account
3. Click "New organization" (if you don't have one)
4. Enter organization name: "SpectrumIA"
5. Click "Create organization"
```

### 1.2 Create Production Project

```
1. In the organization dashboard, click "New project"
2. Fill in project details:
   - Name: spectrumia-production
   - Database password: [GENERATE STRONG PASSWORD] ⚠️ Save this securely
   - Region: [Choose closest to your users]
     * US East 1 (N. Virginia) - For North America
     * EU West 1 (Ireland) - For Europe
     * Asia Pacific (Singapore) - For Asia
   - Pricing: Pro (required for production)

3. Click "Create new project"
4. Wait for project initialization (2-3 minutes)
```

### 1.3 Retrieve Project Credentials

Once project is created:

```
1. Click on your project name
2. Go to "Settings" → "API"
3. You'll see the following keys:
   ✅ Project URL: https://[project-id].supabase.co
   ✅ Anon (public) key: Used for client-side operations
   ✅ Service role key: For server-side operations (KEEP SECRET!)

4. Save these credentials:
   - SUPABASE_URL = Project URL
   - SUPABASE_ANON_KEY = Anon key
   - SUPABASE_SERVICE_ROLE_KEY = Service role key
```

---

## 🎯 Step 2: Configure Project Settings

### 2.1 Enable Required Extensions

```
1. Go to "SQL Editor" in dashboard
2. Copy and paste this SQL:

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

3. Click "Run"
4. Verify success message
```

### 2.2 Set Database Connection Limits

```
1. Go to Settings → Database
2. Set connection settings:
   - Max connections: 100
   - Idle timeout: 5 minutes
   - Statement timeout: 30 seconds
```

### 2.3 Configure Backup Settings

```
1. Go to Settings → Backups
2. Set backup frequency:
   - Daily backups: Enabled
   - Point-in-time recovery: Enabled
   - Retention: 30 days (minimum for production)
3. Enable automated backups
```

---

## 🎯 Step 3: Apply Database Migrations

### 3.1 Review Schema

File: `models/migrations.sql` (424 lines)

The schema includes:
- **users** - Patient/participant data
- **calibration_sessions** - Gaze calibration records
- **assessment_sessions** - Assessment tracking
- **gaze_metrics** - Eye-tracking data points
- **assessment_results** - Final scores and classifications
- Functions and triggers for automation

### 3.2 Apply Main Schema

```
1. In "SQL Editor", click "New Query"
2. Copy entire contents of: models/migrations.sql
3. Paste into SQL editor
4. Click "Run"
5. Verify all tables created successfully

Expected output:
✅ uuid-ossp extension created
✅ users table created
✅ calibration_sessions table created
✅ assessment_sessions table created
✅ gaze_metrics table created
✅ assessment_results table created
✅ All indexes created
✅ All functions created
✅ All triggers created
```

### 3.3 Verify Schema

```
1. Click "SQL Editor" → "New Query"
2. Run verification query:

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

3. Expected tables (5 main):
   ✅ users
   ✅ calibration_sessions
   ✅ assessment_sessions
   ✅ gaze_metrics
   ✅ assessment_results
```

### 3.4 Check Indexes

```
1. Run verification query:

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY indexname;

Expected indexes (~12 total):
✅ idx_users_email
✅ idx_users_created_at
✅ idx_users_is_active
✅ idx_calibration_user_id
✅ idx_calibration_status
✅ idx_calibration_created_at
✅ idx_assessment_user_id
✅ idx_assessment_calibration_id
✅ idx_assessment_status
✅ idx_assessment_created_at
✅ idx_gaze_session_id
✅ idx_results_session_id
```

---

## 🎯 Step 4: Configure RLS (Row Level Security)

### 4.1 Enable RLS on Tables

File: `models/rls_policies.sql`

```
1. In "SQL Editor", click "New Query"
2. Copy entire contents of: models/rls_policies.sql
3. Paste into SQL editor
4. Click "Run"
5. All RLS policies will be created
```

### 4.2 Verify RLS Policies

```
1. Run verification query:

SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

Expected policies (~15 total):
✅ users: "Users can view their own profile"
✅ users: "Users can update their own profile"
✅ calibration_sessions: "Users can view their own calibrations"
✅ calibration_sessions: "Users can create their own calibrations"
✅ calibration_sessions: "Users can update their own calibrations"
✅ assessment_sessions: "Users can view their own assessments"
✅ assessment_sessions: "Users can create their own assessments"
✅ assessment_sessions: "Users can update their own assessments"
✅ gaze_metrics: "Users can view their gaze metrics"
✅ gaze_metrics: "Users can insert their gaze metrics"
✅ assessment_results: "Users can view their own results"
✅ assessment_results: "Users can create their own results"
✅ assessment_results: "Users can update their own results"
✅ All service_role policies for backend access
```

### 4.3 Check RLS Status

```
1. Run status query:

SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

Expected output - all tables should have:
✅ rowsecurity = TRUE (RLS enabled)
```

---

## 🎯 Step 5: Setup Authentication

### 5.1 Configure Email Settings

```
1. Go to Settings → Authentication
2. Scroll to "Email Confirmations"
3. Configure:
   - Enable email confirmations: ON
   - Email confirmation expiry: 24 hours
   - Additional email types:
     * Enable password recovery: ON
     * Password recovery expiry: 24 hours

4. Under "Email Template":
   - Customize email templates if needed
   - Test with a sample email
```

### 5.2 Configure JWT Settings

```
1. In Authentication settings, find "JWT Settings"
2. Configure:
   - JWT Expiry: 3600 (1 hour for access token)
   - JWT Secret: [Auto-generated - copy and save securely]

3. Save the JWT secret to your secrets manager
```

### 5.3 Setup Authentication Providers

For production, enable:

```
1. Email/Password (already default)
   - Enable: ON
   - Auto-confirm users: OFF (for verification)

2. (Optional) Google OAuth
   - Go to Google Cloud Console
   - Create OAuth 2.0 credentials
   - Copy Client ID and Client Secret
   - Paste into Supabase settings
   - Enable Google provider

3. (Optional) GitHub OAuth
   - Go to GitHub Settings → Developer settings
   - Create OAuth App
   - Copy Client ID and Client Secret
   - Paste into Supabase settings
   - Enable GitHub provider
```

### 5.4 Verify Authentication

```
1. In "Database" → "Tables", click "users" table
2. Go to "Authentication" settings
3. Under "JWT Bearer", set the token source:
   - Authorization header: Bearer [token]
   - User field: user_id

4. Test by creating a test user (via API or Dashboard)
```

---

## 🎯 Step 6: Create Environment Variables

### 6.1 Create .env.production File

```bash
# From terminal in project root:

# Copy the template
cp .env.production.example .env.production

# Edit with your actual values
nano .env.production  # or use your preferred editor
```

### 6.2 Fill in Required Variables

```env
# MANDATORY VARIABLES - Must be filled in

# From Supabase Project Settings → API
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# From Supabase Project Settings → Authentication → JWT Settings
JWT_SECRET=your-jwt-secret-here

# From PostgreSQL connection string
DATABASE_URL=postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres

# Application settings
ENVIRONMENT=production
APP_DEBUG=false
APP_VERSION=0.1.0
LOG_LEVEL=INFO
```

### 6.3 Secure Credentials

```bash
# SECURITY CHECKLIST:
# ✅ Never commit .env.production to git
# ✅ Add to .gitignore (should already be there)
# ✅ Store in secure secrets manager:
#    - AWS Secrets Manager
#    - HashiCorp Vault
#    - GitHub Secrets (for CI/CD)
#    - Azure Key Vault
# ✅ Restrict file permissions:
chmod 600 .env.production
# ✅ Only authorized personnel access
# ✅ Audit access logs
```

---

## 🧪 Testing Phase 8.1

### 8.1.1 Database Connection Test

```python
# test_phase8_1.py
import os
from models.database import get_db
from models.schemas import UserCreate

# Test connection
try:
    db = get_db()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

# Test user creation
try:
    user_data = UserCreate(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        age=30,
        gender="other",
        age_group="adult"
    )
    result = db.from_('users').insert({
        'email': user_data.email,
        'first_name': user_data.first_name,
        'last_name': user_data.last_name,
        'age': user_data.age,
        'gender': user_data.gender,
        'age_group': user_data.age_group
    }).execute()
    print("✅ User creation successful")
except Exception as e:
    print(f"❌ User creation failed: {e}")
    exit(1)
```

Run test:
```bash
export $(cat .env.production | xargs)
python test_phase8_1.py
```

### 8.1.2 RLS Policy Test

```python
# Verify RLS policies are working
# Create two users and verify one cannot see the other's data

from supabase import create_client, Client
from models.database import get_db

# Connect with User 1's JWT
user1_token = "user1_jwt_token"
user1_client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY"),
    options={
        'headers': {'Authorization': f'Bearer {user1_token}'}
    }
)

# User 1 should see their own data
try:
    result = user1_client.from_('users').select('*').execute()
    assert len(result.data) == 1
    assert result.data[0]['user_id'] == user1_id
    print("✅ RLS: User can view own profile")
except Exception as e:
    print(f"❌ RLS test failed: {e}")
```

---

## 📝 Deliverables Checklist

After completing Phase 8.1, you should have:

- [ ] Supabase production project created
- [ ] Project URL and credentials saved securely
- [ ] Database schema applied (5 tables + indexes)
- [ ] RLS policies configured and verified
- [ ] Authentication settings configured
- [ ] JWT secret securely stored
- [ ] .env.production created with all variables
- [ ] Credentials stored in secrets manager
- [ ] Database backups enabled
- [ ] Connection tested and verified
- [ ] RLS policies tested
- [ ] Documentation updated
- [ ] Team notified of production database

---

## ⚠️ Important Security Notes

### Credentials Management

```bash
# NEVER do this:
git add .env.production  ❌
export SUPABASE_KEY=sk_... ❌ (in shell history)

# DO this instead:
source .env.production   ✅ (from file)
export $(cat .env.production | xargs) ✅

# For CI/CD:
Use GitHub Secrets, not environment files ✅
```

### Database Backups

```bash
# Enable in Supabase Dashboard
1. Settings → Backups
2. Automatic backups: Daily
3. Retention: 30 days minimum
4. Test restore procedure before going live
```

### Monitoring

```bash
# Enable logging in Supabase:
1. Settings → Database
2. Enable query logging
3. Monitor slow queries
4. Set alerts for failures
```

---

## 🚨 Troubleshooting

### Issue: "Connection refused"

```
Solution:
1. Verify SUPABASE_URL is correct
2. Check internet connection
3. Verify IP whitelist (if applicable)
4. Check Supabase project status
```

### Issue: "Permission denied" on RLS policies

```
Solution:
1. Verify policies were created (check pg_policies)
2. Use service_role key for backend operations
3. Ensure JWT tokens are valid
4. Check RLS policy syntax
```

### Issue: "JWT invalid"

```
Solution:
1. Verify JWT_SECRET matches Supabase setting
2. Check token expiration
3. Verify token format (Bearer [token])
4. Check Authorization header
```

---

## ✅ Phase 8.1 Completion Checklist

- [ ] Supabase project created
- [ ] Database schema applied
- [ ] All 5 tables created
- [ ] All ~12 indexes created
- [ ] RLS policies configured
- [ ] Authentication setup
- [ ] .env.production file created
- [ ] Credentials secured
- [ ] Connection tested
- [ ] RLS tested
- [ ] Backups enabled
- [ ] Monitoring configured
- [ ] Documentation complete
- [ ] Team trained

---

## 📊 Timeline Summary

| Phase | Time | Total |
|-------|------|-------|
| Create project | 15 min | 15 min |
| Configure settings | 15 min | 30 min |
| Apply migrations | 30 min | 60 min |
| Configure RLS | 45 min | 105 min |
| Setup auth | 30 min | 135 min |
| Create env vars | 15 min | 150 min |
| **TOTAL** | | **2.5 hours** |

---

## 🎯 Next Phase

After completing Phase 8.1:
→ Proceed to **Phase 8.2: Streamlit Cloud Deployment**

---

## 📞 Support References

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [JWT Authentication](https://supabase.com/docs/guides/auth/jwts)
- [Database Backups](https://supabase.com/docs/guides/platform/backups)

---

**Phase 8.1: Supabase Production Setup - IN PROGRESS**

Started: 2026-03-27
Target Completion: 2026-03-27 (estimated 2.5 hours from start)

