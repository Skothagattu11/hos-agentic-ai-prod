# 🚀 Dynamic Personalization - Deployment Guide

**Status**: Ready for Production Deployment
**Date**: 2025-10-24
**Version**: 1.0.0

---

## 📋 Pre-Deployment Checklist

Before starting deployment:

- [ ] ✅ All code reviewed and tested
- [ ] ✅ Database backup created
- [ ] ✅ Environment variables prepared
- [ ] ✅ Team notified of deployment
- [ ] ✅ Rollback plan ready
- [ ] ✅ Monitoring configured

---

## 🗂️ Step 1: Database Migrations

### 1.1 Backup Current Database

**Via Supabase Dashboard**:
1. Navigate to Database → Backups
2. Create manual backup: `pre-dynamic-personalization-backup`
3. Wait for completion (download backup if possible)

**Via SQL** (optional):
```sql
-- Verify existing plan_items structure
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'plan_items'
ORDER BY ordinal_position;
```

### 1.2 Run Migrations

**Navigate to**: https://app.supabase.com → Your Project → SQL Editor

Run each migration **in order**:

#### Migration 1: Task Library
```bash
# Copy contents of: supabase/migrations/001_create_task_library.sql
# Paste into SQL Editor
# Click "Run"
```

**Expected Output**: `Success. No rows returned`

**Verify**:
```sql
SELECT COUNT(*) FROM task_library;
-- Should return 0 (table created, not populated yet)

SELECT COUNT(*) FROM pg_policies WHERE tablename = 'task_library';
-- Should return 5 (RLS policies created)
```

#### Migration 2: User Task Feedback
```bash
# Copy contents of: supabase/migrations/002_create_user_task_feedback.sql
# Paste into SQL Editor
# Click "Run"
```

#### Migration 3: User Preference Profile
```bash
# Copy contents of: supabase/migrations/003_create_user_preference_profile.sql
# Paste into SQL Editor
# Click "Run"
```

#### Migration 4: Task Rotation State
```bash
# Copy contents of: supabase/migrations/004_create_task_rotation_state.sql
# Paste into SQL Editor
# Click "Run"
```

#### Migration 5: Modify plan_items
```bash
# Copy contents of: supabase/migrations/005_modify_plan_items_table.sql
# Paste into SQL Editor
# Click "Run"
```

### 1.3 Verify Migrations

```sql
-- Check all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'task_library',
    'user_task_feedback',
    'user_preference_profile',
    'task_rotation_state'
  )
ORDER BY table_name;

-- Should return 4 rows

-- Check plan_items was modified
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'plan_items'
  AND column_name IN (
    'task_library_id',
    'variation_group',
    'is_dynamic',
    'dynamic_metadata'
  );

-- Should return 4 rows
```

---

## 🌱 Step 2: Seed Task Library

### 2.1 Prepare Environment

```bash
cd hos-agentic-ai-prod

# Ensure dependencies installed
pip install -r requirements.txt

# Verify .env has Supabase credentials
cat .env | grep SUPABASE
```

### 2.2 Run Seed Script

```bash
python -m services.seeding.task_library_seed
```

**Expected Output**:
```
============================================================
  TASK LIBRARY SEED SCRIPT
============================================================
Total tasks to seed: 50

✅ Connected to database
  ✓ Inserted: Morning Lemon Water (hydration)
  ✓ Inserted: Green Tea Ritual (hydration)
  ...
✅ Successfully seeded 50 tasks into task_library!

📊 Task Distribution:
  • hydration: 8 tasks
  • movement: 12 tasks
  • nutrition: 10 tasks
  • recovery: 6 tasks
  • wellness: 8 tasks
  • work: 6 tasks

🔒 Database connection closed
```

### 2.3 Verify Seeding

```sql
-- Check task counts
SELECT category, COUNT(*) as count
FROM task_library
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- Check sample tasks
SELECT id, name, category, difficulty
FROM task_library
LIMIT 10;

-- Verify archetype fit scoring
SELECT name, archetype_fit->>'foundation_builder' as foundation_fit
FROM task_library
WHERE category = 'hydration'
LIMIT 5;
```

---

## ⚙️ Step 3: Configure Environment

### 3.1 Update .env File

Add these variables to your `.env` file:

```env
# =====================================================
# Dynamic Personalization Feature Flags
# =====================================================

# Master switch - Set to false initially for testing
ENABLE_DYNAMIC_PLANS=false

# Task library version
TASK_LIBRARY_VERSION=v1

# Feedback collection
FEEDBACK_COLLECTION_ENABLED=true

# Phase 2 features
ADAPTIVE_LEARNING_ENABLED=true
WEEKLY_SUMMARIES_ENABLED=true

# Task rotation threshold (hours)
ROTATION_THRESHOLD_HOURS=48

# Learning phase criteria
DISCOVERY_MIN_DAYS=7
DISCOVERY_MIN_TASKS=15
ESTABLISHMENT_MIN_DAYS=21
ESTABLISHMENT_MIN_TASKS=40
```

### 3.2 Verify Configuration

```bash
# Test configuration loading
python -c "
from config.dynamic_personalization_config import get_config
config = get_config()
print('✅ Config loaded successfully')
print(f'   Enabled: {config.is_enabled()}')
print(f'   Feedback: {config.is_feedback_enabled()}')
print(f'   Adaptive: {config.is_adaptive_learning_enabled()}')
"
```

---

## 🔌 Step 4: Deploy Backend

### 4.1 Verify Router Registration

Check that feedback router is registered in `openai_main.py`:

```bash
grep -A 5 "DYNAMIC_PERSONALIZATION ENDPOINTS" services/api_gateway/openai_main.py
```

Should show:
```python
# 🎯 DYNAMIC PERSONALIZATION ENDPOINTS (Phase 1 & 2)
try:
    from services.api_gateway.feedback_endpoints import router as feedback_router
    app.include_router(feedback_router)
    print("✅ [DYNAMIC_PERSONALIZATION] Feedback endpoints registered successfully")
```

### 4.2 Start Backend (Local Testing)

```bash
# Start backend
python start_openai.py
```

**Look for**:
```
✅ [DYNAMIC_PERSONALIZATION] Feedback endpoints registered successfully
   - POST /api/v1/feedback/task
   - GET /api/v1/feedback/profile/{user_id}
   - POST /api/v1/feedback/clear-context/{user_id}
   - GET /api/v1/feedback/health
```

### 4.3 Verify API Documentation

Open: http://localhost:8002/docs

**Check for new endpoints**:
- `/api/v1/feedback/task` (POST)
- `/api/v1/feedback/profile/{user_id}` (GET)
- `/api/v1/feedback/health` (GET)

---

## 🧪 Step 5: Testing

### 5.1 Run Test Suite

```bash
# Run comprehensive tests
python testing/test_dynamic_personalization.py
```

**Expected**:
```
============================================================
DYNAMIC PERSONALIZATION - TEST SUITE
============================================================
Test User ID: a57f70b4-d0a4-4aef-b721-a4b526f64869

TEST 1: Configuration Loading
✅ PASSED: Configuration Loading

TEST 2: Database Connection
✅ PASSED: Database Connection

... (10 total tests)

============================================================
TEST SUMMARY
============================================================
Total Tests:  10
✅ Passed:    10
❌ Failed:    0
Success Rate: 100.0%
============================================================
```

### 5.2 Test API Endpoints

```bash
# Make script executable
chmod +x testing/test_api_endpoints.sh

# Run API tests
./testing/test_api_endpoints.sh
```

**Should see**:
```
========================================
Dynamic Personalization API Tests
========================================

TEST 1: Feedback Service Health Check
✅ PASSED: Feedback service is healthy

TEST 2: Record Task Feedback (Completed)
✅ PASSED: Feedback recorded successfully

... (8 tests)
```

### 5.3 Manual API Testing

**Test 1: Record Feedback**
```bash
curl -X POST http://localhost:8002/api/v1/feedback/task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "a57f70b4-d0a4-4aef-b721-a4b526f64869",
    "task_name": "Morning Lemon Water",
    "category": "hydration",
    "completed": true,
    "satisfaction_rating": 5
  }'
```

**Expected Response**:
```json
{
  "feedback_id": "uuid-here",
  "status": "success",
  "message": "Feedback recorded and preferences updated"
}
```

**Test 2: Get Profile**
```bash
curl http://localhost:8002/api/v1/feedback/profile/a57f70b4-d0a4-4aef-b721-a4b526f64869
```

---

## 🚦 Step 6: Gradual Rollout

### Phase 1: Testing Only (Day 1-2)

**Config**:
```env
ENABLE_DYNAMIC_PLANS=false  # Still using AI generation
FEEDBACK_COLLECTION_ENABLED=true  # Start collecting feedback
```

**Goal**: Collect feedback data without changing plan generation

**Monitor**:
```sql
-- Check feedback collection
SELECT COUNT(*) as feedback_count,
       COUNT(DISTINCT user_id) as user_count
FROM user_task_feedback
WHERE created_at > NOW() - INTERVAL '24 hours';

-- Check preference profiles being created
SELECT COUNT(*) as profile_count
FROM user_preference_profile
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### Phase 2: Canary (10% Users) (Day 3-5)

**Config**:
```env
ENABLE_DYNAMIC_PLANS=true  # Enable for testing
```

**Implementation**: Add user ID filtering in plan generation code:
```python
# In your routine generation endpoint
TEST_USERS = ["a57f70b4-d0a4-4aef-b721-a4b526f64869", ...]  # 10% of users

if user_id in TEST_USERS and config.is_enabled():
    # Use dynamic generation
    ...
else:
    # Use AI generation
    ...
```

**Monitor**:
- Error rates
- API latency
- Task variety metrics
- User feedback

### Phase 3: Beta (50% Users) (Day 6-10)

**Expand TEST_USERS list** to 50% of user base

**Monitor**:
- Completion rate changes
- User satisfaction
- System performance

### Phase 4: Full Rollout (100%) (Day 11+)

**Remove user ID filtering**:
```python
# All users now use dynamic generation
if config.is_enabled():
    # Use dynamic generation
    ...
```

**Monitor all metrics** for 1 week

---

## 📊 Step 7: Monitoring & Validation

### 7.1 Key Metrics Dashboard

**Monitor these queries**:

```sql
-- 1. Daily feedback volume
SELECT
    DATE(created_at) as date,
    COUNT(*) as feedback_count,
    COUNT(DISTINCT user_id) as user_count,
    AVG(CASE WHEN satisfaction_rating IS NOT NULL THEN satisfaction_rating END) as avg_satisfaction
FROM user_task_feedback
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 2. Completion rate by learning phase
SELECT
    upp.current_learning_phase,
    COUNT(DISTINCT utf.user_id) as user_count,
    AVG(CASE WHEN utf.completed THEN 1.0 ELSE 0.0 END) as completion_rate
FROM user_preference_profile upp
LEFT JOIN user_task_feedback utf ON upp.user_id = utf.user_id
WHERE utf.created_at > NOW() - INTERVAL '7 days'
GROUP BY upp.current_learning_phase;

-- 3. Task variety per user
SELECT
    user_id,
    COUNT(DISTINCT variation_group) as variety_count,
    COUNT(*) as total_tasks
FROM task_rotation_state
WHERE last_used_at > NOW() - INTERVAL '7 days'
GROUP BY user_id
HAVING COUNT(DISTINCT variation_group) > 0
ORDER BY variety_count DESC
LIMIT 20;

-- 4. Dynamic vs AI plans
SELECT
    is_dynamic,
    COUNT(*) as plan_count,
    COUNT(DISTINCT user_id) as user_count
FROM plan_items
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY is_dynamic;

-- 5. Learning phase distribution
SELECT
    current_learning_phase,
    COUNT(*) as user_count,
    AVG(total_tasks_completed) as avg_tasks,
    AVG(avg_completion_rate) as avg_completion
FROM user_preference_profile
GROUP BY current_learning_phase
ORDER BY
    CASE current_learning_phase
        WHEN 'discovery' THEN 1
        WHEN 'establishment' THEN 2
        WHEN 'mastery' THEN 3
    END;
```

### 7.2 Success Criteria

**Phase 1 (Week 1-2)**:
- ✅ Dynamic plan success rate > 95%
- ✅ API latency < 500ms
- ✅ Task variety: 80% users see 3+ variations/week
- ✅ Zero critical bugs

**Phase 2 (Week 3-4)**:
- ✅ Completion rate improvement: +15-20%
- ✅ Affinity accuracy: 70%+
- ✅ Weekly summary engagement: 60%+
- ✅ User satisfaction: 4+/5

---

## 🔙 Rollback Plan

If issues occur, follow this rollback procedure:

### Immediate Rollback (< 5 minutes)

**Set environment variable**:
```env
ENABLE_DYNAMIC_PLANS=false
```

**Restart backend**:
```bash
# Kill current process
pkill -f start_openai.py

# Restart
python start_openai.py
```

System will **immediately** fall back to AI generation.

### Database Rollback (if needed)

```sql
-- 1. Disable RLS temporarily
ALTER TABLE task_library DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_task_feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_preference_profile DISABLE ROW LEVEL SECURITY;
ALTER TABLE task_rotation_state DISABLE ROW LEVEL SECURITY;

-- 2. Clear data (if needed)
TRUNCATE TABLE task_rotation_state;
TRUNCATE TABLE user_task_feedback;
TRUNCATE TABLE user_preference_profile;
TRUNCATE TABLE task_library;

-- 3. Remove columns from plan_items
ALTER TABLE plan_items
DROP COLUMN IF EXISTS task_library_id,
DROP COLUMN IF EXISTS variation_group,
DROP COLUMN IF EXISTS is_dynamic,
DROP COLUMN IF EXISTS dynamic_metadata;

-- 4. Drop tables
DROP TABLE IF EXISTS task_rotation_state CASCADE;
DROP TABLE IF EXISTS user_preference_profile CASCADE;
DROP TABLE IF EXISTS user_task_feedback CASCADE;
DROP TABLE IF EXISTS task_library CASCADE;
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue 1**: Migrations fail
- **Check**: RLS not already enabled
- **Fix**: Review migration files, run manually one-by-one

**Issue 2**: Seed script fails
- **Check**: Database credentials in `.env`
- **Fix**: Verify `SUPABASE_SERVICE_KEY` has write permissions

**Issue 3**: API endpoints not showing
- **Check**: Router registration in `openai_main.py`
- **Fix**: Restart backend, check imports

**Issue 4**: Feedback not updating preferences
- **Check**: Feature flags enabled
- **Fix**: Verify `FEEDBACK_COLLECTION_ENABLED=true`

**Issue 5**: Plans still using AI
- **Check**: `ENABLE_DYNAMIC_PLANS` value
- **Fix**: Ensure set to `true` and backend restarted

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test configuration
from config.dynamic_personalization_config import get_config
config = get_config()
print(config.get_config_summary())
```

---

## ✅ Post-Deployment Checklist

After successful deployment:

- [ ] ✅ All migrations applied
- [ ] ✅ Task library seeded (50 tasks)
- [ ] ✅ Feature flags configured
- [ ] ✅ API endpoints accessible
- [ ] ✅ Tests passing (10/10)
- [ ] ✅ Monitoring queries saved
- [ ] ✅ Team trained on new features
- [ ] ✅ Documentation updated
- [ ] ✅ Rollback plan tested
- [ ] ✅ Success metrics baseline recorded

---

## 🎉 Congratulations!

Your dynamic personalization system is now live!

**Next Steps**:
1. Monitor metrics daily for first week
2. Collect user feedback
3. Iterate on task library (add more variations)
4. Plan Phase 3 features (mode detection, archetype transitions)

**Questions?** Review:
- `DYNAMIC_PERSONALIZATION_COMPLETE.md` - Full system overview
- `examples/dynamic_personalization_integration.py` - Code examples
- API Docs: http://localhost:8002/docs

---

**Deployment Date**: _________________
**Deployed By**: _________________
**Status**: _________________
