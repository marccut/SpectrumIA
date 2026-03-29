# 🚀 STEP 1: Create Supabase Production Project

**Estimated Time**: 15 minutes
**Status**: READY TO START
**Prerequisites**: Supabase account (free)

---

## 📋 What You'll Do

Create a new Supabase project with these details:
- **Project Name**: spectrumia-production
- **Database Password**: [Generate strong password - save this!]
- **Region**: [Choose closest to your location]
- **Pricing**: Pro (required for production)

---

## ⏱️ Timeline

```
Step 1a: Go to Supabase       (1 min)
Step 1b: Create project       (2 min)
Step 1c: Wait for init        (3 min) [Supabase does this]
Step 1d: Copy credentials     (5 min)
Step 1e: Save credentials     (4 min)

TOTAL: 15 minutes
```

---

## 🎯 STEP 1A: Access Supabase Dashboard

### If you DON'T have a Supabase account:

```
1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with email or GitHub
4. Verify email
5. Create first organization "SpectrumIA"
6. Then continue to Step 1B below
```

### If you ALREADY have a Supabase account:

```
1. Go to https://app.supabase.com
2. Sign in with your credentials
3. Continue to Step 1B below
```

---

## 🎯 STEP 1B: Create Production Project

Once logged in to Supabase dashboard:

### Location 1: Dashboard Home

```
Look for the blue button that says:
   ▶ "New project" or "Create a new project"

Click it.
```

### Location 2: Project Creation Form

You'll see a form with these fields:

**FIELD 1: Project Name**
```
Label: "Name"
Value: spectrumia-production
Type: Text field
Action: Type this exact name
```

**FIELD 2: Database Password**
```
Label: "Password"
Important: This is your PostgreSQL password - SAVE THIS!

Options:
  a) Click "Generate a password" (Recommended)
  b) Or type your own strong password (min 16 chars)

Password Requirements:
  ✅ At least 16 characters
  ✅ Include uppercase letters
  ✅ Include lowercase letters
  ✅ Include numbers
  ✅ Include special characters

Example: "aB3$mN9@xK2!pL5&vW8%"

⚠️ CRITICAL: Save this password in your password manager NOW!
           You'll need it for DATABASE_URL
```

**FIELD 3: Region**
```
Label: "Region"
Options:
  - us-west-1 (N. California) - US West
  - us-east-1 (N. Virginia) - US East
  - eu-west-1 (Ireland) - Europe
  - eu-central-1 (Frankfurt) - Europe
  - ap-southeast-1 (Singapore) - Asia

Choice: Select the region CLOSEST to your main users
(Or us-east-1 if you're in North America)
```

**FIELD 4: Pricing Plan**
```
Label: "Pricing Plan"
Options:
  - Free (for development)
  - Pro (for production) ← SELECT THIS
  - Team (for organizations)

⚠️ IMPORTANT: Must select "Pro" for production!
Billing: You'll be charged for usage
         (but generous free tier included)
```

### Submit the Form

```
Look for button that says:
   ▶ "Create project" (usually blue button)

Click it.

You'll see: "Creating project..."
Wait 2-3 minutes...
```

---

## 🎯 STEP 1C: Wait for Project Initialization

Supabase will automatically:
```
✓ Create PostgreSQL database
✓ Setup Vector/PgVector extension
✓ Create default schema
✓ Setup authentication system
✓ Configure API endpoints
✓ Generate API keys

Time: 2-3 minutes
Status indicator: Look for progress bar or "Setting up..."
```

**Your screen will show:**
```
┌────────────────────────────────────────┐
│  Setting up your project               │
│  ████████████░░░░░░░░░░░░  (60%)       │
│                                        │
│  Creating database...                  │
└────────────────────────────────────────┘
```

When done, you'll see your project dashboard with these tabs:
- Home
- SQL Editor
- Table Editor
- Auth
- Storage
- Settings
- ⚙️ (gear icon)

---

## 🎯 STEP 1D: Retrieve Project Credentials

Once project is created and ready:

### Navigate to Settings → API

```
1. Click the gear icon ⚙️ (bottom left)
2. Select "Settings"
3. In sidebar, find "API"
4. You'll see the API section
```

### You'll see a section like this:

```
┌─────────────────────────────────────────────────┐
│ PROJECT API                                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ Project URL:                                    │
│ https://[project-id].supabase.co               │
│                                                 │
│ Anon key:                                       │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...       │
│ [Copy button]                                   │
│                                                 │
│ Service role key:                               │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...       │
│ [Copy button]                                   │
│                                                 │
│ JWT secret:                                     │
│ [hidden] [Show] [Copy]                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Copy These Values (Click Copy button for each):

**1. Project URL**
```
Format: https://[project-id].supabase.co

Example: https://abcdefgh123456.supabase.co

Save as: SUPABASE_URL
```

**2. Anon Key (Public Key)**
```
Format: Long JWT token starting with "eyJ..."

Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...

Save as: SUPABASE_ANON_KEY
```

**3. Service Role Key (Secret Key)**
```
Format: Long JWT token starting with "eyJ..."

⚠️ SECURITY: This is SECRET! Keep it safe!
   Only use in backend, never in client code!

Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...

Save as: SUPABASE_SERVICE_ROLE_KEY
```

### Also Get JWT Secret

Still in Settings → API section:

**Find "JWT Settings" or look for JWT Secret field:**
```
There should be a field showing:
│ JWT secret:
│ [masked value] [Show] [Copy]

Click [Show] or [Copy]

Format: Random string, example: "super-secret-jwt-key-12345"

Save as: JWT_SECRET
```

### Get DATABASE_URL

Still in Settings, look for "Database" section:

```
Settings → Database (or Connections)

You should see:
│ Connection string:
│ postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres

The [password] is the one you created in Step 1B!

Save as: DATABASE_URL
```

**If you can't find it:**
```
Format it yourself:
postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres

Where:
  [password] = The password from Step 1B
  [project-id] = The ID from your URL (before .supabase.co)
```

---

## 🎯 STEP 1E: Save Credentials Securely

Create a text file with your credentials:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI...
JWT_SECRET=your-jwt-secret-here
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
DATABASE_PASSWORD=aB3$mN9@xK2!pL5&vW8%
```

### Save in a SECURE location:

**Option 1: Password Manager** ✅ RECOMMENDED
```
1. Open your password manager (1Password, KeePass, Bitwarden, etc)
2. Create new entry: "SpectrumIA Production"
3. Paste all credentials
4. Add project URL in notes
5. Save
```

**Option 2: Encrypted Text File** ✅ GOOD
```
1. Create file: spectrumia-prod-credentials.txt
2. Paste all credentials
3. Encrypt with GPG or similar
4. Store in secure location
5. DO NOT commit to git!
```

**Option 3: Environment File** ✅ TEMPORARY
```
This is what you'll do in Step 6!
Create .env.production file
But use PASSWORD MANAGER as primary storage
```

---

## ✅ STEP 1 COMPLETION CHECKLIST

- [ ] Supabase account created (if needed)
- [ ] Logged into https://app.supabase.com
- [ ] Created project "spectrumia-production"
- [ ] Selected appropriate region
- [ ] Project initialization complete (2-3 minutes)
- [ ] Copied SUPABASE_URL
- [ ] Copied SUPABASE_ANON_KEY
- [ ] Copied SUPABASE_SERVICE_ROLE_KEY
- [ ] Copied JWT_SECRET
- [ ] Created DATABASE_URL
- [ ] Saved all 5 credentials securely
- [ ] Credentials NOT stored in plain text
- [ ] Credentials NOT committed to git

---

## 🎯 Success Indicators

**STEP 1 is COMPLETE when you have:**

✅ Supabase project running
✅ All 5 credentials saved
✅ Can access project dashboard
✅ See "SQL Editor" tab available
✅ See "Settings → API" with credentials

**Visual confirmation:**
```
Your Supabase dashboard shows:
┌─────────────────────────────────┐
│ Project: spectrumia-production  │
│ Region: [your region]           │
│ Tier: Pro                       │
│ Status: Active ✅              │
└─────────────────────────────────┘
```

---

## 🔄 Troubleshooting Step 1

### Issue: "Can't find API section"
```
Solution:
1. In dashboard, click gear icon ⚙️ (bottom left)
2. Click "Settings"
3. In left sidebar, find "API"
4. If not visible, scroll down in sidebar
```

### Issue: "JWT Secret not showing"
```
Solution:
1. Go to Settings → Authentication
2. Look for "JWT Settings"
3. Or go to Settings → API
4. Scroll down to JWT section
5. Click "Show" to reveal the secret
```

### Issue: "Can't find DATABASE_URL"
```
Solution:
1. Go to Settings → Database
2. Look for "Connection string"
3. Or format it manually:
   postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres
```

### Issue: "Project initialization stuck"
```
Solution:
1. Wait 5 more minutes (sometimes it takes longer)
2. Refresh the page
3. If still stuck, check email for error
4. Or delete and create new project
```

---

## ⏭️ Next Step

Once STEP 1 is complete:

→ Proceed to **STEP 2: Configure Project Settings**

File: `STEP2_CONFIGURE_SETTINGS.md`

---

**STEP 1: Create Supabase Project**
**Status**: Ready to execute
**Estimated Time**: 15 minutes
**Target Completion**: Within 20 minutes (including Supabase init time)

