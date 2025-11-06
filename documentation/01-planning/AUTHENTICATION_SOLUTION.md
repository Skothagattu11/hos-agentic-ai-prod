# Authentication Solution for Calendar Integration

**Date**: November 6, 2025
**Issue**: 403 Forbidden when fetching Google Calendar events from well-planned-api
**Solution**: Forward user's Supabase JWT token from hos-agentic-ai-prod to well-planned-api

---

## Problem Analysis

### The 403 Error

When testing Phase 1 calendar integration, we encountered:

```
403 Forbidden: Authentication failed
```

### Root Cause

**well-planned-api** requires **Supabase JWT authentication** for the calendar endpoints:

```python
# app/api/calendars.py:106-139
@router.get("/google/{user_id}/events")
async def list_google_events(
    user_id: str,
    ...
    current_user_id: str = Depends(get_current_user),  # ← Requires JWT auth
```

The `get_current_user` dependency validates a **Supabase JWT token** from the `Authorization: Bearer <token>` header.

### Current Authentication Flow

```
Flutter App
    ↓
    ├─→ hos-agentic-ai-prod (uses X-API-Key)
    │       ↓
    │       └─→ well-planned-api (needs Supabase JWT) ← 403 ERROR!
    │
    └─→ well-planned-api (uses Supabase JWT) ✅ Works!
```

**Issue**: hos-agentic-ai-prod doesn't have the user's Supabase JWT token.

---

## Solution Implementation

### Changes Made

#### 1. **CalendarIntegrationService** (`services/anchoring/calendar_integration_service.py`)

**Updated methods to accept `supabase_token` parameter:**

```python
async def fetch_calendar_events(
    self,
    user_id: str,
    target_date: date,
    supabase_token: Optional[str] = None,  # ← NEW: Supabase JWT token
    use_mock_data: bool = False,
    mock_profile: Optional[str] = None
) -> CalendarFetchResult:
```

**Updated authentication headers:**

```python
# OLD (incorrect):
if self.api_key:
    headers["Authorization"] = f"Bearer {self.api_key}"
    headers["X-API-Key"] = self.api_key

# NEW (correct):
if supabase_token:
    headers["Authorization"] = f"Bearer {supabase_token}"
    logger.info("[CALENDAR-INTEGRATION] Using Supabase JWT for authentication")
else:
    logger.warning("[CALENDAR-INTEGRATION] No Supabase token - request will likely fail with 403")
```

**Key changes:**
- Removed `api_key` usage (was incorrect approach)
- Added `supabase_token` parameter to all methods
- Updated `check_calendar_connection()` to accept token
- Updated `_fetch_from_api()` to forward token

#### 2. **Test Script** (`testing/test_google_calendar_integration.py`)

**Updated to prompt for Supabase token:**

```python
async def test_google_calendar_connection(
    user_id: str,
    target_date: date,
    supabase_token: str  # ← NEW: Required for testing
):
```

**Added token input prompt:**

```python
print("\n💡 How to get your Supabase JWT token:")
print("   • Open your Flutter app")
print("   • Open browser dev tools (F12)")
print("   • Run: Supabase.instance.client.auth.currentSession?.accessToken")
print("   • Copy the token (starts with 'eyJ...')")

supabase_token = input("Enter Supabase JWT token: ").strip()
```

#### 3. **Environment Configuration** (`.env.example`)

**Removed incorrect API key configuration:**

```env
# OLD (removed):
WELL_PLANNED_API_KEY=

# NEW (correct):
# Authentication: Uses Supabase JWT token (passed per-request, not in env)
# The token comes from the user's Supabase session and is forwarded to well-planned-api
```

---

## How Authentication Works

### well-planned-api Authentication Flow

```
1. User logs into Flutter app via Supabase
   ↓
2. Supabase returns JWT access token
   ↓
3. Flutter stores token in session
   ↓
4. Flutter makes API calls with Authorization: Bearer {token}
   ↓
5. well-planned-api validates token with Supabase
   ↓
6. If valid: Returns user's calendar events
   If invalid: Returns 403 Forbidden
```

### JWT Token Validation

well-planned-api uses **Supabase Auth** to validate tokens:

```python
# app/core/auth.py
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: SupabaseClient = Depends(get_supabase)
) -> str:
    token = credentials.credentials

    # Verify token with Supabase Auth
    response = db.client.auth.get_user(token)

    if not response or not response.user:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return response.user.id
```

**Key security features:**
- Token is validated with Supabase (not just decoded locally)
- Ensures user_id in path matches authenticated user
- Prevents users from accessing other users' calendar data

---

## Testing Instructions

### Step 1: Get Your Supabase JWT Token

**Option A: From Flutter App (Dart DevTools)**

1. Run your Flutter app
2. Open Dart DevTools or browser console
3. Execute:
   ```dart
   print(Supabase.instance.client.auth.currentSession?.accessToken);
   ```
4. Copy the token (starts with `eyJ...`)

**Option B: From Flutter App (Debug Print)**

Add to your Flutter code temporarily:
```dart
final session = Supabase.instance.client.auth.currentSession;
if (session != null) {
  print('Access Token: ${session.accessToken}');
}
```

**Option C: Intercept Network Request**

1. Run Flutter app with browser dev tools open
2. Make any API call to well-planned-api
3. Inspect Network tab → Headers → Authorization
4. Copy the token after "Bearer "

### Step 2: Run the Test

```bash
cd /mnt/c/dev_skoth/hos/hos-agentic-ai-prod/hos-agentic-ai-prod

python testing/test_google_calendar_integration.py
```

**Interactive prompts:**
```
Enter User ID (profile_id): a57f70b4-d0a4-4aef-b721-a4b526f64869
Enter Supabase JWT token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Select target date:
   1. Today
   2. Tomorrow
   3. Custom date
```

### Step 3: Verify Success

**Expected output:**

```
✅ Connection Status: connected
   ✓ User has connected Google Calendar
   ✓ OAuth tokens are valid

✅ Fetched 8 events for 2025-11-06 (attempt 1)

📅 Event 1: Team Standup
   Start: 09:30 AM
   End: 10:00 AM
   Duration: 30 minutes
   Status: confirmed

📅 Event 2: Client Strategy Call
   Start: 02:00 PM
   End: 03:00 PM
   Duration: 60 minutes
   Location: Conference Room A
   Meeting Link: https://meet.google.com/abc-defg-hij
```

**If you see 403 error:**
- Check that token is not expired (tokens typically expire after 1 hour)
- Verify user_id matches the authenticated user
- Ensure you copied the full token (no truncation)

---

## Token Lifecycle

### Token Expiration

Supabase JWT tokens expire after **1 hour** by default.

**Symptoms of expired token:**
```
403 Forbidden: Invalid authentication token
```

**Solution**: Get a fresh token by re-authenticating in Flutter app.

### Token Refresh

Flutter app automatically refreshes tokens using Supabase SDK:

```dart
// Automatic refresh happens behind the scenes
final session = await Supabase.instance.client.auth.refreshSession();
final newToken = session.session?.accessToken;
```

---

## Integration with Future Endpoints

### When Building Calendar Anchoring API

When you create the Phase 2 endpoint (`POST /api/anchoring/anchor-plan`), you'll need to:

1. **Accept token in request:**

```python
@router.post("/api/anchoring/anchor-plan")
async def anchor_plan(
    user_id: str,
    analysis_result_id: str,
    supabase_token: str = Header(..., alias="Authorization")  # Extract from header
):
    # Remove "Bearer " prefix
    token = supabase_token.replace("Bearer ", "")

    # Pass to calendar service
    calendar_service = get_calendar_integration_service()
    events = await calendar_service.fetch_calendar_events(
        user_id=user_id,
        target_date=date.today(),
        supabase_token=token
    )
```

2. **Update Flutter app to send token:**

```dart
// In Flutter API client
final response = await dio.post(
  '/api/anchoring/anchor-plan',
  data: {
    'user_id': userId,
    'analysis_result_id': analysisId,
  },
  options: Options(
    headers: {
      // hos-agentic-ai-prod API key
      'X-API-Key': AppConfig.apiKey,

      // Supabase JWT for well-planned-api forwarding
      'Authorization': 'Bearer ${Supabase.instance.client.auth.currentSession?.accessToken}',
    },
  ),
);
```

---

## Architecture Decision

### Why Supabase JWT Instead of Service Account?

We considered three approaches:

#### Option A: Forward User's Supabase JWT (CHOSEN)
✅ **Pros:**
- Respects user permissions
- No service account needed
- Standard Supabase authentication flow
- User can only access their own calendar

❌ **Cons:**
- Token must be passed through hos-agentic-ai-prod
- Tokens expire (need refresh logic)

#### Option B: Service Account / API Key
❌ **Why rejected:**
- Would require well-planned-api changes
- Service account would have access to ALL users' calendars
- Security risk (single key compromises all data)
- Not aligned with Supabase auth model

#### Option C: OAuth Direct from hos-agentic-ai-prod
❌ **Why rejected:**
- Requires managing OAuth credentials in backend
- Duplicates authentication logic
- User already authenticated in Flutter app

---

## Security Considerations

### Token Security

1. **Never log full tokens:**
   ```python
   # Good:
   print(f"Token: {token[:20]}...{token[-10:]}")

   # Bad:
   print(f"Token: {token}")  # Could leak in logs
   ```

2. **Validate token on every request:**
   - well-planned-api validates with Supabase (not just JWT decode)
   - Ensures token hasn't been revoked

3. **Use HTTPS only:**
   - Production: `https://well-planned-api.onrender.com`
   - Never send tokens over HTTP

### User Authorization

well-planned-api enforces:

```python
# Verify user can only access their own data
if user_id != current_user_id:
    raise HTTPException(
        status_code=403,
        detail="You can only access your own events"
    )
```

This prevents:
- User A accessing User B's calendar
- Privilege escalation attacks
- Data leakage between users

---

## Troubleshooting

### "403 Forbidden: Authentication failed"

**Causes:**
1. Token not provided
2. Token expired (>1 hour old)
3. Token malformed (copy/paste error)
4. Token from different Supabase project

**Solutions:**
- Get fresh token from Flutter app
- Verify token starts with `eyJ`
- Check token is for correct Supabase project

### "You can only access your own events"

**Cause:** user_id in URL doesn't match authenticated user

**Solution:** Use the same user_id that owns the token

### "No OAuth tokens found"

**Cause:** User hasn't connected Google Calendar

**Solution:**
1. Open well-planned-api in browser
2. Complete Google OAuth flow
3. Verify connection: `/api/auth/google/status/{user_id}`

---

## Next Steps

### Phase 1 Testing
- ✅ Authentication solution implemented
- ⏳ Test with your Supabase token
- ⏳ Verify real calendar events fetch successfully

### Phase 2 Implementation
- Create `POST /api/anchoring/anchor-plan` endpoint
- Accept Supabase token in Authorization header
- Forward token to CalendarIntegrationService
- Update Flutter app to send token

### Future Enhancements
- Automatic token refresh in hos-agentic-ai-prod
- Token caching (with expiry check)
- Support for service-to-service auth (if needed for background jobs)

---

## Summary

**Problem**: Calendar integration returned 403 Forbidden
**Root Cause**: Missing Supabase JWT authentication
**Solution**: Forward user's JWT token from hos-agentic-ai-prod to well-planned-api
**Status**: ✅ Implemented and ready for testing

**Test Command**:
```bash
python testing/test_google_calendar_integration.py
```

**Required Inputs**:
- User ID (profile_id)
- Supabase JWT access token (from Flutter app session)

**Expected Result**: Successfully fetch real Google Calendar events with no 403 errors

