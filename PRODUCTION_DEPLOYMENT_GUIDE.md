# Production Deployment Guide - Schedule Anchoring API

This guide will help you deploy the schedule anchoring feature to production and integrate it with your Flutter app.

## 📋 Prerequisites

- ✅ Render.com account with existing `dynamic-planning` service
- ✅ Production URL: `https://dynamic-planning.onrender.com`
- ✅ GitHub repo: `https://github.com/HolisticOS/hos-agentic-ai-prod.git`
- ✅ Supabase databases configured (main + calendar)
- ✅ Environment variables configured on Render

---

## Step 1: Update Environment Variables on Render

The anchoring API needs access to BOTH Supabase databases. Add these environment variables to your Render service:

### Go to Render Dashboard:
1. Navigate to https://dashboard.render.com
2. Select your `dynamic-planning` service
3. Go to **Environment** tab
4. Add/Update these variables:

```bash
# Main Database (existing - verify these exist)
SUPABASE_URL=https://ijcckqnqruwvqqbkiubb.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Calendar Database (NEW - add these)
SUPABASE_CAL_URL=https://drcehombkpiyhrckbadz.supabase.co
SUPABASE_CAL_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI (existing - verify)
OPENAI_API_KEY=sk-proj-...

# Gemini (for AI scoring - add if not exists)
GEMINI_API_KEY=AIzaSyAtB5cwtvrUwcGF4gIBmLjbwB-JIYTDTUw

# Environment (existing)
ENVIRONMENT=production
LOG_LEVEL=ERROR
```

**Important:** Use the **service_role** key for both Supabase instances, not the anon key!

---

## Step 2: Deploy Latest Code to Render

### Option A: Auto-Deploy (Recommended)

If you have auto-deploy enabled on Render:

```bash
cd /Users/kothagattu/Desktop/OG/hos-agentic-ai-prod

# Commit latest changes
git add .
git commit -m "Add schedule anchoring endpoint with dual-database support"
git push origin main
```

Render will automatically:
- Pull latest code
- Run `pip install -r requirements.txt` (includes websockets>=13.0)
- Restart the service
- Deploy in ~3-5 minutes

### Option B: Manual Deploy

If auto-deploy is disabled:

1. Go to Render Dashboard → `holistic-api`
2. Click **Manual Deploy** → **Deploy latest commit**
3. Wait for deployment to complete

---

## Step 3: Verify Deployment

### Test the Health Endpoint

```bash
# Replace with your actual Render URL
curl https://dynamic-planning.onrender.com/api/health
```

Expected response:
```json
{
  "overall_status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "openai": {"status": "healthy"}
  }
}
```

### Test the Anchoring Endpoint

```bash
# Replace with your production URL
curl -X POST https://dynamic-planning.onrender.com/api/v1/anchor/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "a57f70b4-d0a4-4aef-b721-a4b526f64869",
    "date": "2025-11-09",
    "schedule_id": "84f49c46-e109-4a7e-bf02-fcc315cffa25",
    "confidence_threshold": 0.7
  }'
```

Expected response:
```json
{
  "anchored_tasks": [...],
  "standalone_tasks": [...],
  "message": "Successfully anchored X tasks using AI-enhanced scoring"
}
```

---

## Step 4: Get Your Production API URL

Your production API URL should be:
```
https://dynamic-planning.onrender.com
```

Or check in Render Dashboard → Service → **Settings** → Look for the URL.

---

## Step 5: Update Flutter App Configuration

### Create Environment Configuration File

**File:** `lib/core/config/api_config.dart`

```dart
class ApiConfig {
  // Production API URL (replace with your actual Render URL)
  static const String productionBaseUrl = 'https://dynamic-planning.onrender.com';

  // Local development URL
  static const String developmentBaseUrl = 'http://localhost:8002';

  // Auto-select based on build mode
  static String get baseUrl {
    // You can also use kReleaseMode from 'package:flutter/foundation.dart'
    const bool isProduction = bool.fromEnvironment('dart.vm.product');
    return isProduction ? productionBaseUrl : developmentBaseUrl;
  }

  // Or manually control
  static String getBaseUrl({bool useProduction = true}) {
    return useProduction ? productionBaseUrl : developmentBaseUrl;
  }
}
```

### Update Anchoring Service

**File:** `lib/core/services/anchoring_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../data/models/anchored_task.dart';
import '../config/api_config.dart';  // Import config

class AnchoringService {
  final String baseUrl;

  AnchoringService({
    String? baseUrl,  // Make optional
  }) : baseUrl = baseUrl ?? ApiConfig.baseUrl;  // Use config default

  // ... rest of the code stays the same
}
```

### Usage in App

```dart
// Automatically uses production in release builds
final service = AnchoringService();

// Or explicitly choose
final prodService = AnchoringService(
  baseUrl: ApiConfig.productionBaseUrl,
);

final devService = AnchoringService(
  baseUrl: ApiConfig.developmentBaseUrl,
);
```

---

## Step 6: Flutter Production Build

### For iOS

```bash
cd /Users/kothagattu/Desktop/OG/HolisticOS-app

# Build for release
flutter build ios --release

# Or build for App Store
flutter build ipa
```

### For Android

```bash
# Build APK
flutter build apk --release

# Or build App Bundle for Play Store
flutter build appbundle
```

### For Web

```bash
flutter build web --release
```

---

## Step 7: Test Production Integration

### Test Script with Production URL

Create a test file to verify production API:

**File:** `test_production_anchoring.py`

```python
import requests
import json

# Production API URL (replace with yours)
PROD_URL = "https://dynamic-planning.onrender.com"

def test_production_anchoring():
    """Test the production anchoring endpoint"""

    url = f"{PROD_URL}/api/v1/anchor/generate"

    payload = {
        "user_id": "a57f70b4-d0a4-4aef-b721-a4b526f64869",
        "date": "2025-11-09",
        "schedule_id": "84f49c46-e109-4a7e-bf02-fcc315cffa25",
        "confidence_threshold": 0.7
    }

    print(f"🔗 Testing production API: {url}")
    print(f"📤 Request: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=60)

        print(f"\n✅ Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Anchored: {len(data['anchored_tasks'])} tasks")
            print(f"✅ Standalone: {len(data['standalone_tasks'])} tasks")
            print(f"✅ Message: {data['message']}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_production_anchoring()
    exit(0 if success else 1)
```

Run it:
```bash
python test_production_anchoring.py
```

---

## Step 8: Monitor Production

### Check Render Logs

1. Go to Render Dashboard → `holistic-api`
2. Click **Logs** tab
3. Look for anchoring requests:

```
🎯 [ANCHORING-REST] Request: user=..., schedule=..., ai=True
📅 [ANCHORING-REST] Fetching schedule tasks for ...
✅ [ANCHORING-REST] Loaded 7 calendar events from saved schedule
📋 [ANCHORING-REST] Fetching plan items for 2025-11-09
✅ [ANCHORING-REST] Found 13 plan items
🤖 [ANCHORING-REST] Running AnchoringCoordinator (AI=True)
✅ [ANCHORING-REST] Anchoring complete: 11 anchored, 2 standalone
```

### Set Up Monitoring (Optional)

Add health check monitoring:
```bash
# Add to Render service settings
Health Check Path: /api/health
```

---

## Troubleshooting

### Issue: "No module named 'websockets.asyncio'"

**Solution:** Ensure `websockets>=13.0` is in `requirements.txt` and redeploy

```bash
# Verify in requirements.txt
grep websockets requirements.txt
# Should show: websockets>=13.0
```

### Issue: "No plan found for date"

**Cause:** User doesn't have a wellness plan for that date

**Solution:** Generate a plan first:
```bash
curl -X POST https://dynamic-planning.onrender.com/api/user/{user_id}/routine/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-11-09"}'
```

### Issue: "Database error"

**Cause:** Missing Supabase environment variables

**Solution:** Verify all environment variables are set in Render dashboard:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_CAL_URL`
- `SUPABASE_CAL_SERVICE_KEY`

### Issue: CORS errors from Flutter web

**Solution:** Add CORS middleware to FastAPI (if not already present):

```python
# In services/api_gateway/openai_main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Production Checklist

- [ ] Environment variables configured on Render
- [ ] Latest code pushed to GitHub
- [ ] Render auto-deployed successfully
- [ ] Health endpoint returns 200
- [ ] Anchoring endpoint tested with curl
- [ ] Flutter app config updated with production URL
- [ ] Production build tested on device
- [ ] Logs monitored for errors
- [ ] CORS configured (if using web)

---

## Summary

**Your Production Flow:**

1. **User Action:** Selects a saved schedule in Flutter app
2. **Flutter:** Calls `https://dynamic-planning.onrender.com/api/v1/anchor/generate`
3. **Backend:**
   - Fetches latest wellness plan for user + date
   - Fetches saved schedule tasks
   - Uses AI to match tasks to schedule
   - Returns anchored tasks with confidence scores
4. **Flutter:** Displays beautiful calendar with anchored tasks

**Next Steps:**
1. Deploy code to Render (auto-deploy on git push)
2. Update Flutter app with production URL
3. Build and test on device
4. Ship to users! 🚀

---

## Need Help?

If you encounter issues:

1. **Check Render logs** first - most errors show there
2. **Test with curl** before testing in Flutter
3. **Verify environment variables** are all set correctly
4. **Check database connectivity** - run health endpoint

Your production URL: `https://dynamic-planning.onrender.com`

Ready to deploy! 🎉
