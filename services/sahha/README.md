# Sahha Direct Integration

**Status**: Implementation in Progress (Phase 1-3 Complete)
**Style**: MVP-focused coding with full enterprise features

## Overview

Direct Sahha API integration with incremental sync and background archival. Replaces the intermediate hos-fapi-hm-sahha service for always-fresh data.

## Architecture

```
User Request
    ↓
Analysis Agent (Behavior/Circadian)
    ↓
[1] Fetch from Sahha (incremental with watermark)
    ↓
[2] Perform Analysis (GPT-4)
    ↓
[3] Submit Background Job (non-blocking)
    ↓
Return Result to User (immediate)

Background:
[4] Job Queue processes archival
    ↓
[5] UPSERT to Supabase (deduplication)
    ↓
[6] Update sync status in archetype_analysis_tracking
```

## Components

### 1. SahhaClient (`sahha_client.py`)

**Purpose**: Direct Sahha API client with incremental fetch

**Features**:
- Token caching (23-hour expiry)
- Incremental fetch with watermarks
- Parallel biomarker + score fetching
- Rate limiting & retry logic

**Usage**:
```python
from services.sahha import get_sahha_client

sahha_client = get_sahha_client()

# Incremental fetch (with watermark)
data = await sahha_client.fetch_health_data(
    external_id="user_123",
    since_timestamp=last_analysis_time  # Watermark
)

# Initial fetch (no watermark)
data = await sahha_client.fetch_health_data(
    external_id="user_123",
    days=7  # Last 7 days
)
```

**Returns**:
```python
{
    "biomarkers": [...],  # List of biomarker dicts
    "scores": [...],      # List of score dicts
    "fetched_at": "2025-10-16T12:00:00",
    "is_incremental": True,
    "watermark": "2025-10-16T08:00:00",  # or None
    "total_items": 150
}
```

### 2. SimpleJobQueue (`simple_queue.py`)

**Purpose**: In-memory async job queue with retry

**Features**:
- Background worker loop
- Automatic retry (3 attempts)
- Exponential backoff (2s, 4s, 8s)
- No Redis dependency (MVP-friendly)

**Limitations** (acceptable for MVP):
- Jobs lost on restart
- Single-server only

**Usage**:
```python
from services.background import get_job_queue

job_queue = get_job_queue()

# Start worker (do once at startup)
await job_queue.start()

# Submit job (non-blocking)
await job_queue.submit_job(
    job_type="SYNC_SAHHA_DATA",
    payload={
        "user_id": "user_123",
        "archetype": "Peak Performer",
        "analysis_type": "behavior_analysis",
        "sahha_data": data,
        "tracking_record_id": 456
    }
)

# Get stats
stats = job_queue.get_stats()
# {"queued": 100, "completed": 95, "failed": 2, "retries": 3}
```

### 3. ArchivalService (`archival_service.py`)

**Purpose**: Archive Sahha data to Supabase with deduplication

**Features**:
- UPSERT for biomarkers (prevents duplicates)
- UPSERT for scores (prevents duplicates)
- Updates sync status in archetype_analysis_tracking
- Handles partial failures gracefully

**Usage**:
```python
from services.background import get_archival_service

archival = get_archival_service()

await archival.archive_sahha_data(
    user_id="user_123",
    archetype="Peak Performer",
    analysis_type="behavior_analysis",
    sahha_data={
        "biomarkers": [...],
        "scores": [...]
    }
)
```

**Database Updates**:
- Inserts/updates biomarkers (unique on: profile_id, type, start_date_time, end_date_time)
- Inserts/updates scores (unique on: profile_id, type, score_date_time)
- Updates archetype_analysis_tracking:
  - `sahha_data_synced = true`
  - `biomarkers_synced = true`
  - `scores_synced = true`
  - `sync_completed_at = now()`
  - `sync_error = null`

## Database Schema

### archetype_analysis_tracking (Extended)

**New Columns**:
- `sahha_data_synced` (boolean): Overall sync status
- `biomarkers_synced` (boolean): Biomarkers synced
- `scores_synced` (boolean): Scores synced
- `archetypes_synced` (boolean): Archetypes synced (future)
- `sync_completed_at` (timestamptz): When archival completed
- `sync_error` (text): Error message if failed

**Key Insight**: `analysis_timestamp` (renamed from `last_analysis_at`) IS the watermark for incremental sync.

### biomarkers (Constraint Added)

**Unique Constraint**: `(profile_id, type, start_date_time, end_date_time)`
- Prevents duplicate biomarkers
- Enables safe UPSERT operations

### scores (Constraint Added)

**Unique Constraint**: `(profile_id, type, score_date_time)`
- Prevents duplicate scores
- Enables safe UPSERT operations

## Environment Variables

```env
# Sahha API Configuration
SAHHA_API_BASE_URL=https://api.sahha.ai
SAHHA_CLIENT_ID=your_client_id
SAHHA_CLIENT_SECRET=your_client_secret

# Rate Limiting
SAHHA_RATE_LIMIT_DELAY=0.5  # seconds between requests
SAHHA_MAX_RETRIES=3
SAHHA_REQUEST_TIMEOUT=30  # seconds
```

## Implementation Status

### ✅ Phase 1: Database Schema (Complete)
- Migration: `migrations/001_add_sahha_sync_tracking.sql`
- Rollback: `migrations/001_rollback_sahha_sync_tracking.sql`
- Added 6 sync tracking columns
- Added unique constraints to biomarkers & scores
- Renamed `last_analysis_at` → `analysis_timestamp` (watermark)

### ✅ Phase 2: Sahha Client (Complete)
- File: `services/sahha/sahha_client.py`
- Token caching implemented
- Incremental fetch with watermarks
- Parallel biomarker + score fetching
- Rate limiting & retry logic

### ✅ Phase 3: Background Archival (Complete)
- File: `services/background/simple_queue.py`
- File: `services/background/archival_service.py`
- In-memory async queue
- UPSERT with deduplication
- Retry logic (3 attempts)
- Sync status tracking

### 🚧 Phase 4: Analysis Integration (In Progress)
- Integrate Sahha client into BehaviorAnalysisAgent
- Integrate Sahha client into CircadianAnalysisAgent
- Update OnDemandAnalysisService for incremental logic
- Add background job submission after analysis

### ⏳ Phase 5: Testing (Pending)
- Unit tests for Sahha client
- Integration tests for archival
- End-to-end analysis flow test

## Usage Example (End-to-End)

```python
# In BehaviorAnalysisAgent.analyze_behavior():

from services.sahha import get_sahha_client
from services.background import get_job_queue
from services.archetype_analysis_tracker import get_archetype_tracker

# 1. Get watermark for incremental sync
tracker = await get_archetype_tracker()
watermark, source = await tracker.get_last_analysis_date_with_fallback(
    user_id, archetype, "behavior_analysis"
)

# 2. Fetch from Sahha (incremental if watermark exists)
sahha_client = get_sahha_client()
health_data = await sahha_client.fetch_health_data(
    external_id=user_id,
    since_timestamp=watermark,  # None = initial (7 days)
    days=7
)

# 3. Perform analysis
analysis_result = await self._run_gpt4_analysis(health_data, ...)

# 4. Store analysis in archetype_analysis_tracking
await tracker.update_last_analysis_date(user_id, archetype, analysis_type="behavior_analysis")

# 5. Submit background job (non-blocking)
job_queue = get_job_queue()
await job_queue.submit_job(
    job_type="SYNC_SAHHA_DATA",
    payload={
        "user_id": user_id,
        "archetype": archetype,
        "analysis_type": "behavior_analysis",
        "sahha_data": health_data
    }
)

# 6. Return immediately (don't wait for archival)
return analysis_result
```

## Benefits

### 1. Data Freshness
- Always current data (3-5 second Sahha response)
- No stale Supabase data

### 2. Storage Efficiency
- Incremental sync: Only store delta (12pm-8pm, not full 7 days)
- UPSERT prevents duplicates
- Expected: 90-96% storage reduction

### 3. API Efficiency
- Smart caching reduces Sahha API calls
- Expected: 40-44% API call reduction

### 4. User Experience
- Analysis returns immediately (archival in background)
- Graceful degradation (fallback if Sahha fails)

## Next Steps

1. Run database migration: `psql < migrations/001_add_sahha_sync_tracking.sql`
2. Set environment variables (SAHHA_CLIENT_ID, SAHHA_CLIENT_SECRET)
3. Integrate into BehaviorAnalysisAgent (Phase 4)
4. Integrate into CircadianAnalysisAgent (Phase 4)
5. Test end-to-end flow (Phase 5)

## Rollback

If issues arise:

```bash
# Rollback database changes
psql < migrations/001_rollback_sahha_sync_tracking.sql

# Revert code changes
git revert <commit>

# Analysis agents will fallback to Supabase fetching
```

## Monitoring

**Key Metrics**:
- Queue stats: `job_queue.get_stats()`
- Sahha API success rate
- Archival success rate (check `sync_error` column)
- Storage growth rate

---

**Last Updated**: 2025-10-16
**Status**: Phase 3 Complete, Phase 4 In Progress
