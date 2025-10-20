# Phase 2 Implementation Complete - Engagement Data + Behavior Analysis

## ✅ What Was Implemented

### 1. **Engagement Data Fetching** ✅

**File**: `services/insights_v2/data_aggregation_service.py`

**New Methods:**
- `fetch_behavioral_data()` - Main entry point for engagement data
- `_fetch_engagement_context()` - Fetches plan_items + task_checkins
- `_fetch_journal_data()` - Fetches daily_journals (self-reported metrics)

**Data Sources Connected:**
- ✅ **plan_items** table - Task completion data
- ✅ **task_checkins** table - Completion status tracking
- ✅ **daily_journals** table - Self-reported energy, mood, stress

**Metrics Extracted:**
- Total tasks (last 3 days)
- Completed tasks count
- Overall completion rate
- Morning/afternoon/evening completion rates
- Daily check-in count
- Average energy level (1-5 scale)
- Average mood rating (1-5 scale)
- Average stress level (1-5 scale)

---

### 2. **Behavior Analysis Context** ✅

**New Method:**
- `_fetch_behavior_analysis()` - Fetches latest holistic_analysis_results

**Data Source:**
- ✅ **holistic_analysis_results** table

**Data Extracted:**
- Archetype
- Psychological patterns
- Barriers identified
- Motivation patterns
- Key insights from behavior analysis
- Analysis date

**Integration:**
- Added to `InsightContext.latest_analysis_summary`
- Available to AI prompt for psychology-aware insights

---

## 🎯 What This Enables

### **Before Phase 2** (Health Data Only):
```
Title: "Low Steps But High Active Minutes"
Content: "Only 2,262 steps/day but 222 min/day active. Consider adding more steps."
```

### **After Phase 2** (Health + Engagement + Behavior Analysis):
```
Title: "Morning energy 8/10 but only 40% task completion + 2,200 steps"
Content: "Your behavior analysis identified you as a morning person. Health data shows high morning energy (8/10 self-reported), but you're completing only 40% of morning tasks and averaging 2,200 steps. Your peak performance window is underutilized."
Recommendation: "Based on your perfectionist tendency (from behavior analysis), schedule 2-3 high-priority tasks in morning block (6-9 AM) and add a 15-min walk after each completed task to hit 5,000 morning steps."
Data Points: ["morning_energy_journal", "morning_steps_sahha", "morning_completion_rate_plan_items", "behavior_analysis_patterns"]
```

---

## 📊 Complete Data Pipeline

```
User Request
    ↓
API Endpoint (/api/v2/insights/{user_id}/generate)
    ↓
Data Aggregation Service
    ↓
┌─────────────────────┬───────────────────────┬────────────────────────┐
│ Sahha API           │ Supabase              │ Supabase               │
│ (Health Data)       │ (Engagement Data)     │ (Behavior Analysis)    │
│ - Sleep (40 biomark)│ - plan_items          │ - holistic_analysis_   │
│ - Steps (86 scores) │ - task_checkins       │   results              │
│ - Heart rate        │ - daily_journals      │ - Psychological        │
│ - Energy scores     │ - Completion rates    │   patterns             │
│ - Readiness         │ - Self-reported       │ - Barriers             │
│                     │   mood/energy/stress  │ - Motivations          │
└───────────┬─────────┴──────────┬────────────┴───────────┬───────────┘
            │                    │                        │
            └────────────┬───────┴────────────────────────┘
                         ↓
            Build InsightContext
            (health + engagement + behavior + baselines)
                         ↓
            OpenAI GPT-4o API Call
            (Enhanced prompt with all data)
                         ↓
            Parse & Validate
            (Quality thresholds)
                         ↓
            Return Personalized Insights
```

---

## 🔧 Technical Implementation Details

### **SQL Queries Used:**

**1. Plan Items Query:**
```sql
SELECT id, title, task_type, time_block, plan_date, scheduled_time
FROM plan_items
WHERE profile_id = $1 AND plan_date >= $2 AND plan_date <= $3
ORDER BY plan_date DESC
```

**2. Task Check-ins Query:**
```sql
SELECT completion_status, plan_item_id, planned_date
FROM task_checkins
WHERE profile_id = $1 AND planned_date >= $2 AND planned_date <= $3
```

**3. Daily Journals Query:**
```sql
SELECT energy_level, mood_rating, stress_level, journal_date
FROM daily_journals
WHERE profile_id = $1 AND journal_date >= $2 AND journal_date <= $3
ORDER BY journal_date DESC
```

**4. Behavior Analysis Query:**
```sql
SELECT id, archetype, psychological_patterns, barriers_identified,
       motivation_patterns, key_insights, analysis_date, created_at
FROM holistic_analysis_results
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 1
```

### **Data Models Updated:**

**BehaviorDataWindow** (now fully populated):
```python
@dataclass
class BehaviorDataWindow:
    # Task completion
    total_tasks: int
    completed_tasks: int
    completion_rate: float

    # Timing patterns
    morning_completion_rate: float
    afternoon_completion_rate: float
    evening_completion_rate: float

    # Self-reported metrics
    avg_energy_level: Optional[float]  # 1-5 scale
    avg_mood_level: Optional[float]    # 1-5 scale
    avg_stress_level: Optional[float]  # 1-5 scale
    daily_check_in_count: int
```

**InsightContext** (now includes behavior analysis):
```python
@dataclass
class InsightContext:
    health_data: HealthDataWindow
    behavior_data: BehaviorDataWindow
    baselines: UserBaselines
    latest_analysis_summary: Optional[Dict[str, Any]]  # NEW!
```

---

## 🧪 Testing

### **Test Command:**
```bash
# Restart server to pick up changes
python start_openai.py

# Run test
python testing/test_insights_v2_simple.py
```

### **Expected Results:**

**Logs should show:**
```
[INSIGHTS_V2] Extracted engagement data: 15 tasks, 73.3% completion, 2 check-ins
[INSIGHTS_V2] Built complete context: health_data=2262 steps, behavior_data=15 tasks, analysis_summary=present
```

**Insights should reference:**
- Task completion rates
- Self-reported energy/mood/stress
- Behavior analysis patterns
- Connections between health and engagement

---

## 📈 Example Insights Phase 2 Can Generate

### **1. Sleep-Performance Connection**
```
Title: "6.2hr sleep nights = 45% task completion vs 85% on 7+ hr nights"
Content: "3-day pattern: Your task completion rate is 85%+ on days with 7+ hours sleep, but drops to 45% after <6.5 hr nights. Your behavior analysis noted perfectionist tendencies—poor sleep may trigger avoidance."
Recommendation: "Prioritize 7+ hour sleep before high-task days. Set a 10 PM wind-down alarm to protect sleep window."
Data Points: ["sleep_duration", "task_completion_rate", "behavior_perfectionism"]
```

### **2. Energy-Activity Mismatch**
```
Title: "Self-reported energy 8/10 but only 2,200 steps by noon"
Content: "Daily journals show morning energy at 8/10, but Sahha data shows only 2,200 steps by midday (vs baseline 5,500). High energy window underutilized."
Recommendation: "Add 2,000-step walk after morning routine completion. Your behavior analysis shows you're a 'morning person'—leverage this."
Data Points: ["morning_energy_journal", "morning_steps", "behavior_chronotype"]
```

### **3. Stress-Completion Pattern**
```
Title: "Stress 4/5 coincides with 30% evening task completion"
Content: "When daily journals report stress ≥4/5, evening task completion drops to 30% (vs 75% baseline). Behavior analysis identified 'overwhelm avoidance' pattern."
Recommendation: "On high-stress days, reduce evening tasks from 5 to 2. Quality over quantity aligns with your Foundation Builder archetype."
Data Points: ["stress_level_journal", "evening_completion_rate", "behavior_patterns"]
```

---

## 🎯 What's Next (Optional Enhancements)

### **Phase 3: 30-Day Baselines** (Medium Priority)
- Implement baseline calculations for engagement metrics
- Cache in Redis (24-hour TTL)
- Enable "vs baseline" comparisons for task completion

### **Phase 4: Storage & Retrieval** (Medium Priority)
- Store insights in `holistic_insights` table
- Implement retrieval endpoints
- Add user feedback tracking

### **Phase 5: Deduplication** (Low Priority)
- Check last 7 days of insights
- Skip if similar insight already generated
- Only regenerate if data changed significantly

---

## ✅ Verification Checklist

Before testing:
- [x] Engagement data fetching implemented
- [x] Journal data fetching implemented
- [x] Behavior analysis fetching implemented
- [x] All SQL queries use `fetch()` method correctly
- [x] Error handling with try-except blocks
- [x] Debug logging added

After testing:
- [ ] Server restarts without errors
- [ ] Engagement data extracted successfully
- [ ] Journal data extracted successfully
- [ ] Behavior analysis extracted successfully
- [ ] Insights reference engagement metrics
- [ ] Insights reference self-reported data
- [ ] Insights reference behavior analysis patterns

---

## 🚀 Ready to Test!

**Next Steps:**
1. Restart server: `python start_openai.py`
2. Run test: `python testing/test_insights_v2_simple.py`
3. Verify insights now include:
   - Task completion data
   - Self-reported metrics
   - Behavior analysis context
   - Connections between all data sources

**Expected Outcome:**
- Insights are **10x more personalized**
- References user's actual task performance
- Connects health data to routine execution
- Uses psychology from behavior analysis
- Generates 1-3 high-quality, deeply personalized insights

---

## 📝 Summary

**Phase 2 Complete**: Engagement data + behavior analysis fully integrated!

**Data Sources Connected:**
1. ✅ Sahha API (health data)
2. ✅ plan_items (task tracking)
3. ✅ task_checkins (completion status)
4. ✅ daily_journals (self-reported metrics)
5. ✅ holistic_analysis_results (behavior analysis)

**Ready for production testing!** 🎉
