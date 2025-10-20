# Dynamic User Timezone - Implementation Plan

**Goal:** Use each user's actual timezone when generating routines, not a hardcoded timezone.

**Status:** Planning Only (No Implementation Yet)

---

## 🎯 Requirement

When a user generates a routine at 9 PM in THEIR timezone:
- ✅ Routine should be dated TODAY in their timezone
- ✅ Works for users in ANY timezone (EST, PST, IST, JST, etc.)
- ✅ NOT hardcoded to EST or any specific timezone

---

## 📍 Where to Get User's Timezone

### Option 1: From API Request (Recommended) ⭐

**How it works:**
- Flutter app detects user's current timezone
- Sends timezone in API request
- Backend uses that timezone for date calculation

**Pros:**
- ✅ Most accurate (uses device's current timezone)
- ✅ Works immediately
- ✅ No database changes needed
- ✅ Handles traveling users (timezone changes automatically)

**Cons:**
- ⚠️ Requires Flutter app update
- ⚠️ Need to coordinate backend + frontend changes

**Implementation:**

**Backend (hos-agentic-ai-prod):**
```python
# Update PlanGenerationRequest model
class PlanGenerationRequest(BaseModel):
    archetype: str
    preferences: Optional[dict] = None
    timezone: Optional[str] = None  # NEW: IANA timezone (e.g., "America/New_York")

# Use in routine generation
async def generate_routine(user_id: str, request: PlanGenerationRequest):
    user_timezone = request.timezone or "America/New_York"  # Fallback to EST
    date = get_user_local_date(user_timezone)
```

**Frontend (HolisticOS-app Flutter):**
```dart
import 'package:timezone/timezone.dart' as tz;

// In routine generation request
Future<void> generateRoutine() async {
  final String userTimezone = tz.local.name; // e.g., "America/New_York"

  final response = await http.post(
    Uri.parse('$baseUrl/api/user/$userId/routine/generate'),
    headers: headers,
    body: jsonEncode({
      'archetype': archetype,
      'preferences': preferences,
      'timezone': userTimezone, // NEW: Send user's timezone
    }),
  );
}
```

---

### Option 2: From User Profile in Database

**How it works:**
- User sets timezone in their profile settings
- Backend fetches timezone from database during generation
- Uses that timezone for date calculation

**Pros:**
- ✅ No API changes needed
- ✅ User can manually set timezone
- ✅ Timezone persisted across sessions

**Cons:**
- ⚠️ Requires database schema change
- ⚠️ Doesn't auto-update when user travels
- ⚠️ User must manually set timezone in profile

**Implementation:**

**Database Migration:**
```sql
-- Add timezone column to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'America/New_York';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_timezone ON users(timezone);
```

**Backend Query:**
```python
async def get_user_timezone(user_id: str) -> str:
    """Fetch user's timezone from database"""
    query = "SELECT timezone FROM users WHERE id = $1"
    result = await db.fetchrow(query, user_id)

    if result and result['timezone']:
        return result['timezone']
    else:
        return "America/New_York"  # Fallback to EST

# Use in routine generation
async def generate_routine(user_id: str, request: PlanGenerationRequest):
    user_timezone = await get_user_timezone(user_id)
    date = get_user_local_date(user_timezone)
```

**Flutter Profile Settings:**
```dart
// In user profile screen
DropdownButton<String>(
  value: selectedTimezone,
  items: [
    'America/New_York',     // EST/EDT
    'America/Los_Angeles',  // PST/PDT
    'America/Chicago',      // CST/CDT
    'Europe/London',        // GMT/BST
    'Asia/Kolkata',         // IST
    'Asia/Tokyo',           // JST
    // ... more timezones
  ].map((tz) => DropdownMenuItem(value: tz, child: Text(tz))).toList(),
  onChanged: (String? newTimezone) {
    // Update user timezone in database
    await updateUserTimezone(newTimezone);
  },
)
```

---

### Option 3: Hybrid Approach (Best of Both) 🌟

**How it works:**
1. **First preference:** Use timezone from API request (if sent)
2. **Second preference:** Use timezone from user profile (if set)
3. **Fallback:** Use EST as default

**Pros:**
- ✅ Most flexible solution
- ✅ Auto-detects timezone when app sends it
- ✅ Respects user preference when manually set
- ✅ Graceful fallback

**Cons:**
- ⚠️ Requires both backend + database + frontend changes
- ⚠️ More complex implementation

**Implementation:**

**Backend:**
```python
async def get_effective_timezone(user_id: str, request_timezone: Optional[str]) -> str:
    """
    Get effective timezone with priority:
    1. Request timezone (most accurate - from device)
    2. User profile timezone (user preference)
    3. Fallback to EST
    """
    # Priority 1: Timezone from request
    if request_timezone:
        return request_timezone

    # Priority 2: Timezone from user profile
    query = "SELECT timezone FROM users WHERE id = $1"
    result = await db.fetchrow(query, user_id)
    if result and result['timezone']:
        return result['timezone']

    # Priority 3: Fallback to EST
    return "America/New_York"

# Use in routine generation
async def generate_routine(user_id: str, request: PlanGenerationRequest):
    user_timezone = await get_effective_timezone(user_id, request.timezone)
    date = get_user_local_date(user_timezone)
```

---

## 🛠️ Implementation Steps

### Recommended: Option 1 (API Request) + Fallback to EST

**Step 1: Backend Changes (hos-agentic-ai-prod)**

1. **Create timezone utility** (`shared_libs/utils/timezone_helper.py`):
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
        user_timezone: IANA timezone string (e.g., "America/New_York", "Asia/Tokyo", "Europe/London")

    Returns:
        Date string in format "YYYY-MM-DD" in user's timezone

    Defaults to America/New_York (EST/EDT) if timezone not provided.
    """
    default_tz = "America/New_York"

    try:
        tz_str = user_timezone or default_tz
        user_tz = ZoneInfo(tz_str)
        local_date = datetime.now(user_tz).strftime("%Y-%m-%d")
        logger.debug(f"Generated date {local_date} for timezone {tz_str}")
        return local_date
    except Exception as e:
        # Fallback to EST if timezone is invalid
        logger.warning(f"Invalid timezone '{user_timezone}', falling back to EST: {e}")
        est_tz = ZoneInfo(default_tz)
        return datetime.now(est_tz).strftime("%Y-%m-%d")


def validate_timezone(timezone_str: str) -> bool:
    """
    Validate if timezone string is valid IANA timezone.

    Args:
        timezone_str: Timezone string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        ZoneInfo(timezone_str)
        return True
    except Exception:
        return False


# Common timezone mappings for reference
COMMON_TIMEZONES = {
    "EST": "America/New_York",      # Eastern Standard Time
    "PST": "America/Los_Angeles",   # Pacific Standard Time
    "CST": "America/Chicago",       # Central Standard Time
    "MST": "America/Denver",        # Mountain Standard Time
    "IST": "Asia/Kolkata",          # India Standard Time
    "JST": "Asia/Tokyo",            # Japan Standard Time
    "GMT": "Europe/London",         # Greenwich Mean Time
    "CET": "Europe/Paris",          # Central European Time
    "AEST": "Australia/Sydney",     # Australian Eastern Standard Time
}
```

2. **Update PlanGenerationRequest model** (in `services/api_gateway/openai_main.py`):
```python
class PlanGenerationRequest(BaseModel):
    archetype: str
    preferences: Optional[dict] = None
    timezone: Optional[str] = None  # NEW: IANA timezone string
```

3. **Update routine generation functions** (6 locations):

**Replace:**
```python
"date": datetime.now().strftime("%Y-%m-%d")
```

**With:**
```python
from shared_libs.utils.timezone_helper import get_user_local_date

# In function signature, get timezone from request:
async def run_memory_enhanced_routine_generation(
    user_id: str,
    archetype: str,
    preferences: dict = None,
    user_timezone: str = None  # NEW parameter
):
    # ... existing code ...

    routine_result = {
        "date": get_user_local_date(user_timezone),  # Use user's timezone
        # ... rest of routine
    }
```

4. **Pass timezone through the call chain:**

```python
# In generate_fresh_routine_plan endpoint:
@router.post("/api/user/{user_id}/routine/generate")
async def generate_fresh_routine_plan(
    user_id: str,
    request: PlanGenerationRequest,
    # ...
):
    # Extract timezone from request
    user_timezone = request.timezone

    # Pass to generation function
    routine_plan = await run_memory_enhanced_routine_generation(
        user_id,
        archetype,
        preferences,
        user_timezone  # NEW: Pass timezone
    )
```

---

**Step 2: Frontend Changes (HolisticOS-app Flutter)**

1. **Add timezone package** to `pubspec.yaml`:
```yaml
dependencies:
  timezone: ^0.9.0  # For timezone detection
```

2. **Initialize timezone data** in `main.dart`:
```dart
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize timezone database
  tz.initializeTimeZones();

  runApp(MyApp());
}
```

3. **Get user's timezone** and send in API request:
```dart
import 'package:timezone/timezone.dart' as tz;

class ApiService {
  Future<RoutinePlan> generateRoutine({
    required String userId,
    required String archetype,
    Map<String, dynamic>? preferences,
  }) async {
    // Get user's current timezone
    final String userTimezone = tz.local.name; // e.g., "America/New_York"

    final response = await http.post(
      Uri.parse('$baseUrl/api/user/$userId/routine/generate'),
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: jsonEncode({
        'archetype': archetype,
        'preferences': preferences,
        'timezone': userTimezone, // NEW: Send timezone
      }),
    );

    // ... handle response
  }
}
```

4. **Optional: Show timezone in UI**:
```dart
// In profile or settings screen
Text('Your timezone: ${tz.local.name}')
```

---

**Step 3: Testing**

**Test Case 1: User in EST at 9 PM**
```
Input:
  - User timezone: "America/New_York"
  - Time: 9:00 PM EST

Expected Output:
  - Routine date: TODAY (not tomorrow)

Verification:
  curl -X POST http://localhost:8002/api/user/TEST/routine/generate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: hosa_flutter_app_2024" \
    -d '{"archetype": "Foundation Builder", "timezone": "America/New_York"}'
```

**Test Case 2: User in India (IST) at 11 PM**
```
Input:
  - User timezone: "Asia/Kolkata"
  - Time: 11:00 PM IST

Expected Output:
  - Routine date: TODAY (not tomorrow)

Verification:
  curl -X POST http://localhost:8002/api/user/TEST/routine/generate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: hosa_flutter_app_2024" \
    -d '{"archetype": "Foundation Builder", "timezone": "Asia/Kolkata"}'
```

**Test Case 3: User in Japan (JST) at 10 PM**
```
Input:
  - User timezone: "Asia/Tokyo"
  - Time: 10:00 PM JST

Expected Output:
  - Routine date: TODAY (not tomorrow)

Verification:
  curl -X POST http://localhost:8002/api/user/TEST/routine/generate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: hosa_flutter_app_2024" \
    -d '{"archetype": "Foundation Builder", "timezone": "Asia/Tokyo"}'
```

**Test Case 4: No timezone provided (Fallback)**
```
Input:
  - User timezone: null (not provided)

Expected Output:
  - Falls back to EST
  - Routine date: Based on EST timezone

Verification:
  curl -X POST http://localhost:8002/api/user/TEST/routine/generate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: hosa_flutter_app_2024" \
    -d '{"archetype": "Foundation Builder"}'
```

---

## 📋 Implementation Checklist

### Backend (hos-agentic-ai-prod):
- [ ] Create `shared_libs/utils/timezone_helper.py` with `get_user_local_date()`
- [ ] Update `PlanGenerationRequest` model to include `timezone` field
- [ ] Update `generate_fresh_routine_plan()` endpoint to extract timezone from request
- [ ] Update `run_memory_enhanced_routine_generation()` to accept timezone parameter
- [ ] Update `run_routine_planning_4o()` line 4706 - pass timezone
- [ ] Update `run_routine_planning_4o()` line 4722 - pass timezone
- [ ] Update `run_routine_planning_gpt4o()` line 4310 - pass timezone
- [ ] Update `run_routine_planning_gpt4o()` line 4324 - pass timezone
- [ ] Update `run_nutrition_planning_4o()` line 4244 - pass timezone
- [ ] Update `run_nutrition_planning_4o()` line 4257 - pass timezone
- [ ] Test with multiple timezones

### Frontend (HolisticOS-app):
- [ ] Add `timezone` package to pubspec.yaml
- [ ] Initialize timezone database in main.dart
- [ ] Update API service to detect and send user's timezone
- [ ] Update routine generation API call to include timezone
- [ ] Update nutrition generation API call to include timezone
- [ ] Test on multiple devices/simulators with different timezones

### Testing:
- [ ] Test EST user at 9 PM (should show today)
- [ ] Test PST user at 11 PM (should show today)
- [ ] Test IST user at 10 PM (should show today)
- [ ] Test JST user at 11:30 PM (should show today)
- [ ] Test without timezone (should fallback to EST)
- [ ] Test invalid timezone (should fallback to EST)
- [ ] Verify no breaking changes to existing functionality

---

## 🚀 Deployment Strategy

### Phase 1: Backend Only (Backward Compatible)
1. Deploy backend changes with timezone support
2. Timezone parameter is **optional** - defaults to EST
3. Old Flutter apps (without timezone) still work
4. New Flutter apps can send timezone

### Phase 2: Frontend Update
1. Update Flutter app to send timezone
2. All new users automatically get correct timezone
3. All existing users get correct timezone on next update

### Phase 3: Optional Enhancements
1. Add timezone to user profile (Option 2)
2. Let users manually override timezone in settings
3. Show timezone in profile/settings UI

---

## 🎯 Benefits

### For Users:
- ✅ Routines always show correct date in their timezone
- ✅ Works for users anywhere in the world
- ✅ No manual timezone setup required (auto-detected)
- ✅ Handles traveling users (timezone auto-updates)

### For Development:
- ✅ Clean, maintainable solution
- ✅ Backward compatible (no breaking changes)
- ✅ Gradual rollout possible
- ✅ Easy to test and verify

### For Business:
- ✅ Global app support
- ✅ Better user experience
- ✅ No user complaints about wrong dates
- ✅ Scalable solution

---

## 🔄 Alternative: Quick Backend-Only Fix

If you want to fix backend FIRST without waiting for Flutter update:

```python
# In backend, try to infer timezone from request headers
from datetime import datetime
from zoneinfo import ZoneInfo

def get_timezone_from_request(request: Request) -> str:
    """
    Try to infer timezone from HTTP request headers.
    This is a temporary workaround until Flutter sends timezone explicitly.
    """
    # Check if Flutter app can send custom header
    timezone_header = request.headers.get('X-User-Timezone')
    if timezone_header:
        return timezone_header

    # Fallback to EST
    return "America/New_York"
```

Then Flutter app can send timezone in header:
```dart
headers: {
  'Content-Type': 'application/json',
  'X-API-Key': apiKey,
  'X-User-Timezone': tz.local.name,  // Send timezone in header
}
```

---

## 📝 Summary

**Recommended Solution:** Option 1 (API Request)

**Changes Required:**
- Backend: Add timezone parameter to API, use in date calculation
- Frontend: Detect and send user's timezone in API request

**Deployment:**
- Phase 1: Backend (backward compatible)
- Phase 2: Frontend update
- No breaking changes

**Timeline:**
- Backend: 30-45 minutes
- Frontend: 15-30 minutes
- Testing: 30 minutes
- **Total: ~2 hours**

**Result:**
- ✅ Works for ALL users in ANY timezone
- ✅ Routines always dated correctly
- ✅ Global app support
