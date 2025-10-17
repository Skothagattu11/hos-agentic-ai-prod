# Real Data & AI Connection - Complete

## ✅ What Was Connected

### 1. OpenAI GPT-4o API ✅
**File**: `services/insights_v2/insights_generation_service.py`

**Changes:**
- ✅ Uncommented real OpenAI API call (lines 290-303)
- ✅ Added AsyncOpenAI client initialization (lines 429-439)
- ✅ Configured with `gpt-4o` model
- ✅ JSON response format for structured insights
- ✅ Temperature: 0.7, Max tokens: 1500

**Code:**
```python
# Real API call
response = await self.openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.7,
    max_tokens=1500
)
return json.loads(response.choices[0].message.content)
```

### 2. SahhaDataService for Health Data ✅
**File**: `services/insights_v2/data_aggregation_service.py`

**Changes:**
- ✅ Imported `SahhaDataService` (line 365)
- ✅ Calls `fetch_health_data_for_analysis()` (lines 203-208)
- ✅ Extracts sleep, activity, heart rate metrics
- ✅ Falls back to Supabase if Sahha fails

**Data Fetched:**
- Sleep duration and quality
- Steps and active minutes
- Heart rate and HRV
- Energy and readiness scores

### 3. Supabase for Behavioral Data ✅
**File**: `services/insights_v2/data_aggregation_service.py`

**Changes:**
- ✅ Imported `SupabaseAsyncPGAdapter` (line 366)
- ✅ Connected to behavioral data queries
- ✅ Fallback for health data if Sahha unavailable

**Data Fetched:**
- Task completion rates (from `plan_items`)
- Check-in data (mood, energy, stress)
- Analysis history

### 4. Baseline Calculations ✅
**File**: `services/insights_v2/baseline_calculation_service.py`

**Changes:**
- ✅ Connected Supabase for 30-day queries (lines 270-282)
- ✅ Calculates rolling averages
- ✅ Quality assessment based on data points

**Baselines Calculated:**
- Sleep duration (30-day avg)
- Activity levels (30-day avg)
- Energy scores (30-day avg)
- Task completion rates (30-day avg)

## 🔄 Data Flow (Now with Real Data)

```
User Request
    ↓
API Endpoint (/api/v2/insights/{user_id}/generate)
    ↓
Data Aggregation Service
    ↓
┌────────────────────────┬────────────────────────┐
│ Sahha API              │ Supabase               │
│ (Real Health Data)     │ (Real Behavioral Data) │
│ - Last 3 days          │ - Task completion      │
│ - Sleep, steps, HR     │ - Check-ins            │
│ - Energy scores        │ - Mood/stress/energy   │
└──────────┬─────────────┴──────────┬─────────────┘
           │                        │
           └────────┬───────────────┘
                    ↓
        Baseline Calculation
        (30-day rolling avg from Supabase)
                    ↓
        Build InsightContext
        (Real user data + baselines)
                    ↓
    OpenAI GPT-4o API Call
    (Real AI generation)
                    ↓
    Parse & Validate
    (Quality thresholds)
                    ↓
    Return Real Insights
```

## 🧪 Testing with Real Data

### Step 1: Restart Server
```bash
# Stop current server (Ctrl+C)
python start_openai.py
```

**Expected startup logs:**
```
[INSIGHTS_V2] Initialized with OpenAI GPT-4o client
[INSIGHTS_V2] Data Aggregation Service initialized with Sahha + Supabase
[INSIGHTS_V2] Baseline Service initialized with Supabase
✅ [INSIGHTS_V2] Endpoints registered successfully
```

### Step 2: Run Test Script
```bash
python testing/test_insights_v2_simple.py
```

**Expected behavior:**
- ✅ Health Check: 200 OK
- ✅ Generate Insights: 200 OK with **REAL AI-generated insights**
- ✅ API Key Validation: 401 Unauthorized

### Step 3: Check Results

**What You'll See Now:**
- Real insights based on user's actual data
- Personalized recommendations
- Archetype-specific language
- Real AI-generated titles and content
- Higher quality/relevance scores
- Generation time: 2-5 seconds (real API call)

**Example Real Output:**
```json
{
  "status": "success",
  "user_id": "6241b25a-c2de-49fe-9476-1ada99ffe5ca",
  "insights": [
    {
      "category": "sleep",
      "priority": "high",
      "title": "Consistent 7.5hr sleep pattern detected",
      "content": "Your recent sleep data shows a stable pattern averaging 7.5 hours, which aligns well with recovery needs for your activity level.",
      "recommendation": "Maintain this schedule and consider tracking sleep quality metrics.",
      "confidence_score": 0.87,
      "actionability_score": 0.82
    },
    ...
  ],
  "metadata": {
    "insights_count": 4,
    "generation_time_ms": 2500,
    "model_used": "gpt-4o"
  }
}
```

## 🔍 Differences: Mock vs Real

| Aspect | Mock Data | Real Data |
|--------|-----------|-----------|
| **Health Data** | Hardcoded values | From Sahha API |
| **Behavioral Data** | Empty/placeholder | From Supabase tables |
| **Baselines** | N/A | 30-day rolling avg |
| **AI Generation** | Hardcoded response | GPT-4o API call |
| **Insights Quality** | Fixed scores | AI-determined scores |
| **Personalization** | Generic | User-specific |
| **Generation Time** | <1ms | 2-5 seconds |
| **Cost** | $0 | ~$0.014 per call |

## 💰 Cost Tracking

**Per Request:**
- GPT-4o API call: ~$0.014
- Sahha API call: Free (included in plan)
- Supabase queries: Free (generous limits)

**Monthly Cost (100 users, 1x/day):**
- 100 users × 30 days × $0.014 = **$42/month**

## 🐛 Troubleshooting

### Issue: "No OpenAI client - using mock data"
**Solution:** Check `.env` file has `OPENAI_API_KEY=your_key_here`

### Issue: "Sahha fetch failed"
**Solution:** Normal - will fall back to Supabase. Check Sahha credentials if needed.

### Issue: Empty insights or N/A values
**Solution:** User may not have enough data yet. System gracefully handles missing data.

### Issue: OpenAI API error
**Solution:** Check API key validity, account credits, and rate limits

## 📊 Monitoring

**Check logs for:**
```
[INSIGHTS_V2] Initialized with OpenAI GPT-4o client ✅
[INSIGHTS_V2] Data Aggregation Service initialized ✅
[INSIGHTS_V2] Baseline Service initialized ✅
```

**If you see:**
```
[INSIGHTS_V2] No AI client available, using mock data ❌
```
Then OpenAI API key is not configured.

## ✅ Verification Checklist

Before testing:
- [ ] Server restarted
- [ ] OpenAI API key in .env
- [ ] Supabase credentials in .env
- [ ] User has some data in database

After testing:
- [ ] Insights generated successfully
- [ ] Generation time > 1 second (proves real API call)
- [ ] Insights are personalized (not generic)
- [ ] Different from mock data

## 🎯 Next Steps

1. **Restart server now**
2. **Run test script**
3. **Verify real insights generated**
4. **Integrate with UI**
5. **Monitor costs and usage**

---

**Status**: ✅ All connections complete - Ready for real data testing!
