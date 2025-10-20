# Timezone Fix Plan - Routine Date Issue

**Issue:** Routines created after 9 PM EST are being saved/displayed with tomorrow's date instead of today's date.

**Root Cause:** Server uses UTC timezone, not user's local timezone.

---

## 🔍 Problem Analysis

### Current Behavior:
```
User creates routine at 9:00 PM EST
  ↓
Server time = 2:00 AM UTC (next day)
  ↓
datetime.now().strftime("%Y-%m-%d") = Tomorrow's date
  ↓
Routine saved with tomorrow's date ❌
```

### Expected Behavior:
```
User creates routine at 9:00 PM EST
  ↓
Convert to user's timezone (EST)
  ↓
Get date in user's timezone = Today's date
  ↓
Routine saved with today's date ✅
```

---

## 📍 Code Locations (All in hos-agentic-ai-prod)

### Issue Found in These Functions:

**File:** `services/api_gateway/openai_main.py`

1. **Line 4244** - `run_nutrition_planning_4o()`:
   ```python
   "date": datetime.now().strftime("%Y-%m-%d"),  # ❌ Uses server UTC time
   ```

2. **Line 4257** - `run_nutrition_planning_4o()` (fallback):
   ```python
   "date": datetime.now().strftime("%Y-%m-%d"),  # ❌ Uses server UTC time
   ```

3. **Line 4310** - `run_routine_planning_gpt4o()`:
   ```python
   "date": datetime.now().strftime("%Y-%m-%d"),  # ❌ Uses server UTC time
   ```

4. **Line 4324** - `run_routine_planning_gpt4o()` (fallback):
   ```python
   "date": datetime.now().strftime("%Y-%m-%d"),  # ❌ Uses server UTC time
   ```

5. **Line 4706** - `run_routine_planning_4o()`:
   ```python
   "date": datetime.now().strftime("%Y-%m-%d"),  # ❌ Uses server UTC time
   ```

6. **Line 4722** - `run_routine_planning_4o()` (fallback):
   ```python
   "date": datetime.now().strftime("%Y-%m-%d"),  # ❌ Uses server UTC time
   ```

---

## 💡 Solution Options

### Option 1: Use User's Timezone (Recommended)

**Pros:**
- Accurate for all users regardless of location
- Respects user's actual date/time
- Most correct solution

**Cons:**
- Need to get user's timezone from request or user profile
- Slightly more complex

**Implementation:**
```python
from datetime import datetime
from zoneinfo import ZoneInfo

def get_user_local_date(user_timezone: str = "America/New_York") -> str:
    """Get current date in user's timezone"""
    user_tz = ZoneInfo(user_timezone)
    return datetime.now(user_tz).strftime("%Y-%m-%d")

# Usage in routine/nutrition functions:
"date": get_user_local_date(user_timezone)
```

### Option 2: Use EST/EDT Timezone (Quick Fix)

**Pros:**
- Simple to implement
- Works for US East Coast users
- No need to fetch user timezone

**Cons:**
- Hardcoded timezone
- Won't work for users in other timezones
- Not ideal for global app

**Implementation:**
```python
from datetime import datetime
from zoneinfo import ZoneInfo

def get_est_date() -> str:
    """Get current date in EST/EDT timezone"""
    est_tz = ZoneInfo("America/New_York")
    return datetime.now(est_tz).strftime("%Y-%m-%d")

# Usage:
"date": get_est_date()
```

### Option 3: Client-Side Date Sending

**Pros:**
- Client knows exact local date
- No server-side timezone logic needed

**Cons:**
- Requires Flutter app changes
- Need to update API contract
- More deployment complexity

**Implementation:**
```python
# API accepts date in request
@router.post("/api/user/{user_id}/routine/generate")
async def generate_routine(
    user_id: str,
    request: PlanGenerationRequest  # Add date field
):
    date = request.date or datetime.now().strftime("%Y-%m-%d")
    # Use provided date
```

---

## 🎯 Recommended Approach

**Use Option 1 (User's Timezone) with Option 2 as fallback**

### Step 1: Add Utility Function

Create `/Users/kothagattu/Desktop/OG/hos-agentic-ai-prod/shared_libs/utils/timezone_helper.py`:

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_user_local_date(user_timezone: Optional[str] = None) -> str:
    """
    Get current date in user's timezone.

    Args:
        user_timezone: IANA timezone string (e.g., "America/New_York", "Asia/Tokyo")

    Returns:
        Date string in format "YYYY-MM-DD" in user's timezone

    Falls back to EST if user_timezone is not provided or invalid.
    """
    # Default to EST/EDT for US users
    default_tz = "America/New_York"

    try:
        tz_str = user_timezone or default_tz
        user_tz = ZoneInfo(tz_str)
        local_date = datetime.now(user_tz).strftime("%Y-%m-%d")
        logger.debug(f"Generated date {local_date} for timezone {tz_str}")
        return local_date
    except Exception as e:
        # Fallback to EST if timezone is invalid
        logger.warning(f"Invalid timezone {user_timezone}, falling back to EST: {e}")
        est_tz = ZoneInfo(default_tz)
        return datetime.now(est_tz).strftime("%Y-%m-%d")


def get_user_timezone_from_db(user_id: str, db) -> Optional[str]:
    """
    Fetch user's timezone from database.

    Args:
        user_id: User ID
        db: Database connection

    Returns:
        IANA timezone string or None if not found
    """
    try:
        # Query users table for timezone column
        # NOTE: Assumes users table has a 'timezone' column
        result = db.query("SELECT timezone FROM users WHERE id = $1", user_id)
        return result[0]["timezone"] if result else None
    except Exception as e:
        logger.warning(f"Could not fetch timezone for user {user_id}: {e}")
        return None
```

### Step 2: Update All Date References

In `services/api_gateway/openai_main.py`, replace ALL instances:

```python
# OLD (6 locations):
"date": datetime.now().strftime("%Y-%m-%d")

# NEW:
from shared_libs.utils.timezone_helper import get_user_local_date

"date": get_user_local_date()  # Defaults to EST
```

### Step 3: Optional - Add Timezone to Users Table

If user timezone is not stored yet, add to database:

```sql
-- Add timezone column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'America/New_York';

-- Update existing users to EST (can be changed by users later)
UPDATE users SET timezone = 'America/New_York' WHERE timezone IS NULL;
```

### Step 4: Optional - Fetch User Timezone in API

```python
# In routine generation function:
async def run_memory_enhanced_routine_generation(...):
    # Fetch user timezone from database (if available)
    user_timezone = await get_user_timezone_from_db(user_id, db)

    # Use in date calculation
    routine_result = {
        "date": get_user_local_date(user_timezone),
        # ... rest of routine
    }
```

---

## 🧪 Testing Plan

### Test Case 1: EST User at 9 PM EST

**Current Behavior:**
- Time: 9:00 PM EST = 2:00 AM UTC (next day)
- Expected: Today's date
- Actual: Tomorrow's date ❌

**After Fix:**
- Time: 9:00 PM EST
- Expected: Today's date
- Actual: Today's date ✅

### Test Case 2: EST User at 11:59 PM EST

**Current Behavior:**
- Time: 11:59 PM EST = 4:59 AM UTC (next day)
- Expected: Today's date
- Actual: Tomorrow's date ❌

**After Fix:**
- Time: 11:59 PM EST
- Expected: Today's date
- Actual: Today's date ✅

### Test Case 3: EST User at 1:00 AM EST

**Current Behavior:**
- Time: 1:00 AM EST = 6:00 AM UTC (same day)
- Expected: Today's date
- Actual: Today's date ✅

**After Fix:**
- Time: 1:00 AM EST
- Expected: Today's date
- Actual: Today's date ✅

### Test Commands:

```bash
# Test with current time
python -c "
from datetime import datetime
from zoneinfo import ZoneInfo

# Server time (UTC)
utc_now = datetime.now()
print(f'Server UTC: {utc_now.strftime(\"%Y-%m-%d %H:%M %Z\")}')

# User time (EST)
est_tz = ZoneInfo('America/New_York')
est_now = datetime.now(est_tz)
print(f'User EST: {est_now.strftime(\"%Y-%m-%d %H:%M %Z\")}')
print(f'Date in UTC: {utc_now.strftime(\"%Y-%m-%d\")}')
print(f'Date in EST: {est_now.strftime(\"%Y-%m-%d\")}')
"

# Test routine generation
curl -X POST http://localhost:8002/api/user/TEST_USER/routine/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: hosa_flutter_app_2024" \
  -d '{"archetype": "Foundation Builder"}'

# Check the date field in response
```

---

## 📋 Implementation Checklist

- [ ] Create `shared_libs/utils/timezone_helper.py` with utility functions
- [ ] Update Line 4244 in openai_main.py (nutrition function)
- [ ] Update Line 4257 in openai_main.py (nutrition fallback)
- [ ] Update Line 4310 in openai_main.py (routine gpt4o)
- [ ] Update Line 4324 in openai_main.py (routine gpt4o fallback)
- [ ] Update Line 4706 in openai_main.py (routine 4o)
- [ ] Update Line 4722 in openai_main.py (routine 4o fallback)
- [ ] Test with 9 PM EST scenario
- [ ] Test with 11:59 PM EST scenario
- [ ] Test with 1 AM EST scenario
- [ ] Optional: Add timezone column to users table
- [ ] Optional: Update Flutter app to send timezone

---

## 🚀 Deployment Impact

### Zero Breaking Changes:
- ✅ All dates will now be accurate
- ✅ No API changes required
- ✅ No Flutter app changes required
- ✅ Backward compatible (defaults to EST)

### Immediate Benefits:
- ✅ Routines created at 9 PM EST show today's date
- ✅ Routines created at 11:59 PM EST show today's date
- ✅ All US East Coast users fixed

### Future Enhancements:
- ⏳ Add timezone selection in user profile
- ⏳ Support global timezones
- ⏳ Flutter app sends timezone in request

---

## 🎯 Summary

**Quick Fix (15 minutes):**
1. Create `timezone_helper.py` with `get_user_local_date()` function (defaults to EST)
2. Replace 6 instances of `datetime.now().strftime("%Y-%m-%d")` with `get_user_local_date()`
3. Test with 9 PM EST scenario
4. Deploy

**Complete Fix (1 hour):**
1. Quick fix above +
2. Add timezone column to users table
3. Fetch user timezone from database
4. Pass timezone to `get_user_local_date(timezone)`
5. Comprehensive testing across timezones

**Recommendation:** Start with Quick Fix, then enhance with Complete Fix in next release.
