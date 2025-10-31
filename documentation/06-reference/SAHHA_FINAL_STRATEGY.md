# Final Sahha Data Strategy

**Date**: October 31, 2025
**Approach**: Always-Live with Database Fallback

---

## 🎯 Simple Strategy

```
User requests plan
    ↓
1. Fetch LIVE from Sahha API (30-60s)
    ↓
    ├─> SUCCESS? Use fresh data ✅
    │   └─> Archive to database in background
    │
    └─> FAILED? Use database as fallback ⚠️
        └─> Return plan with available data
```

---

## 📋 What We Have Now

### 1. **Always-Live Fetching** (`services/sahha_data_service.py`)

```python
# Method: get_sahha_data_live()

- ALWAYS fetches from Sahha API first
- Falls back to database if Sahha fails
- Archives to database in background
```

### 2. **Background Scheduler** (`services/background/scheduler_service.py`)

```python
# Independent automated tasks:

- Every 30 min: Refresh active users (keeps database warm)
- Every 10 min: Check for stale data
- Daily 2 AM: Cleanup old data
```

### 3. **Fixed Biomarker Validation** (`shared_libs/data_models/health_models.py`)

```python
# BiomarkerData model now handles null timestamps

- created_at: Optional (handles Sahha nulls)
- Auto-fills with current time if None
- No more "skipping biomarker" warnings
```

---

## 🚀 Usage

### In Plan Generation (`services/api_gateway/openai_main.py`):

```python
from services.sahha_data_service import get_sahha_data_service

@router.post("/api/user/{user_id}/routine/generate")
async def generate_routine(user_id: str, request: RoutineRequest):

    # Get Sahha data (always live)
    sahha_service = get_sahha_data_service()
    health_context = await sahha_service.get_sahha_data_live(
        user_id=user_id,
        days=7
    )

    # Generate plan
    plan = await generate_plan_with_context(health_context, request)

    return plan
```

---

## ⏱️ Expected Performance

### Sahha API Working:
```
- Fetch Sahha: 30-60 seconds
- Generate Plan: 40 seconds
- TOTAL: 70-100 seconds
- Data: ✅ LIVE (0-5 min old)
```

### Sahha API Down:
```
- Sahha fails: 5 seconds (timeout)
- Load database: 2 seconds
- Generate Plan: 40 seconds
- TOTAL: 47 seconds
- Data: ⚠️  DATABASE (may be hours old)
```

---

## 🔧 What Background Scheduler Does

### Purpose: Keep Database Warm

Even though we always fetch live, the scheduler keeps the database populated:

1. **Redundancy**: If Sahha API is down, we have recent data
2. **Analytics**: Historical data in your database for analysis
3. **Proactive**: Reduces peak load on Sahha API

### How It Works:

```
# Runs independently (NO user requests needed)

Every 30 minutes:
  → Find active users (used app in last 24h)
  → Fetch fresh Sahha data for them
  → Store in database (scores + biomarkers tables)

Every 10 minutes:
  → Find users with stale database cache
  → Refresh their data

Daily at 2 AM:
  → Delete data older than 7 days
```

---

## 📊 Benefits

### Always Fresh Data
- ✅ Every plan uses latest Sahha data
- ✅ Real-time health metrics
- ✅ No stale recommendations

### Reliable Fallback
- ✅ System works even if Sahha is down
- ✅ Uses recent database cache
- ✅ Graceful degradation

### Simple Architecture
- ✅ No complex cache logic
- ✅ Straightforward data flow
- ✅ Easy to debug

---

## 🧪 Testing

### Test 1: Normal Operation (Sahha Working)

```bash
# Make request
POST /api/user/user123/routine/generate

# Expected logs:
[SAHHA_LIVE] Fetching LIVE from Sahha API...
[SAHHA_LIVE] ✅ Fresh: 156 biomarkers + 89 scores
[QUEUE] Job SYNC_SAHHA_DATA queued (archiving in background)

# Expected time: ~70 seconds
```

### Test 2: Sahha API Down (Fallback)

```bash
# Simulate Sahha down (disconnect network or use mock)
POST /api/user/user123/routine/generate

# Expected logs:
[SAHHA_LIVE] Fetching LIVE from Sahha API...
[SAHHA_LIVE] Sahha failed: Connection timeout
[SAHHA_LIVE] ⚠️  Falling back to database...
[SAHHA_LIVE] ✅ Using database: 89 scores + 156 biomarkers

# Expected time: ~47 seconds (faster because database)
```

### Test 3: Background Scheduler

```bash
# Check scheduler status
GET /api/admin/scheduler/status

# Expected response:
{
  "running": true,
  "total_jobs": 4,
  "jobs": [
    {
      "id": "sahha_refresh_active_users",
      "next_run": "2025-10-31T19:30:00Z"
    },
    ...
  ]
}
```

---

## 🔴 What We Removed

### Deleted Complex Cache Logic:
- ❌ `get_sahha_data_with_cache()` - Not needed
- ❌ `_check_cache_freshness()` - Not needed
- ❌ `_refresh_in_background()` - Scheduler handles this
- ❌ `CACHE_FRESHNESS_MINUTES` - Not needed

### Kept Simple:
- ✅ `get_sahha_data_live()` - Always fetch live
- ✅ Database fallback - Reliability
- ✅ Background archival - Redundancy
- ✅ Background scheduler - Keep database warm

---

## 📝 Files Changed

### 1. `services/sahha_data_service.py`
- ✅ Removed cache-first logic
- ✅ Kept `get_sahha_data_live()` method
- ✅ Simple database fallback

### 2. `shared_libs/data_models/health_models.py`
- ✅ Fixed `BiomarkerData` to handle null timestamps
- ✅ Added validator to auto-fill None values

### 3. `services/background/scheduler_service.py`
- ✅ Created background scheduler (if you want it)
- ✅ Runs independently every 30 minutes
- ✅ Optional - can enable/disable

---

## ✅ Production Checklist

- [x] Sahha data always fetches live
- [x] Database fallback works
- [x] Background archival non-blocking
- [x] Biomarker validation fixed
- [ ] Start background scheduler (optional)
- [ ] Test with production Sahha API
- [ ] Monitor response times

---

## 🎯 Next Steps

### Option 1: Deploy As-Is (Recommended)
```bash
# Already working:
- Live Sahha fetch ✅
- Database fallback ✅
- Background archival ✅

# Just deploy and test:
git add .
git commit -m "feat: always-live Sahha fetch with database fallback"
git push origin main
```

### Option 2: Add Background Scheduler (Optional)
```bash
# Add to openai_main.py startup:

from services.background.scheduler_service import get_scheduler

@app.on_event("startup")
async def startup_event():
    # Start scheduler
    scheduler = get_scheduler()
    await scheduler.start()
    logger.info("✅ Background scheduler started")

# Install dependency:
pip install apscheduler
```

---

## 📊 Summary

**What You Have**:
- ✅ **Always fresh Sahha data** (your priority)
- ✅ **Simple architecture** (easy to maintain)
- ✅ **Reliable fallback** (works when Sahha is down)
- ✅ **No warnings** (biomarker validation fixed)

**What Background Scheduler Does** (Optional):
- 🔄 **Keeps database warm** (redundancy)
- 🔄 **Runs independently** (doesn't slow down API)
- 🔄 **Proactive refresh** (less peak load)

**Performance**:
- ⏱️ **70-100 seconds** (Sahha working)
- ⏱️ **47 seconds** (Sahha down, using database)

---

**Status**: ✅ Ready to deploy
**Complexity**: 🟢 Simple
**Reliability**: 🟢 High
