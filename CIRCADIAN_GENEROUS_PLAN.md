# Circadian Rhythm - Generous & Motivating Analysis Plan

**Issue:** Current analysis is too strict - shows 0 peak energy periods, everything is just maintenance (40)
**Goal:** Make analysis more generous and motivating while still being data-driven

---

## 🎯 Current Problem

### Current Output Analysis:
```
- Peak energy periods: 0 (NONE!)
- Maintenance periods: 06:00-21:45 (ALL DAY at level 40)
- Recovery periods: Sleep times (level 25-30)
- Result: Flat, boring, demotivating
```

### Issues:
1. ❌ **Too strict**: No peak energy zones at all
2. ❌ **Not motivating**: Everything is "maintenance"
3. ❌ **Ignores natural rhythms**: Humans have morning/afternoon energy peaks
4. ❌ **Too conservative with insufficient data**: Defaults to flat 40 everywhere

---

## 💡 Solution: Generous Baseline + Data-Driven Adjustments

### Strategy:

**PHASE 1: Insufficient Data (New Users)**
- Generate **GENEROUS baseline** that motivates
- Show clear peak energy periods (morning + afternoon)
- Medium energy for most of day
- Only recovery during sleep

**PHASE 2: With Data (Existing Users)**
- Start with generous baseline
- Adjust based on actual performance
- Only reduce energy zones if user consistently underperforms
- Keep optimistic bias until data proves otherwise

---

## 📊 New Energy Level Framework

### Energy Levels (More Generous):

```
PEAK (70-90):     High energy, best performance windows
PRODUCTIVE (55-70): Good energy, can handle most tasks
MAINTENANCE (40-55): Moderate energy, routine tasks
RECOVERY (20-40):   Low energy, rest/sleep periods
```

### Generous Distribution (Default for New Users):

**Morning Peak (07:00-10:00):**
- Energy: 75-85 (PEAK)
- Duration: 3 hours
- Rationale: Natural cortisol peak, fresh after sleep

**Productive Morning (10:00-13:00):**
- Energy: 60-70 (PRODUCTIVE)
- Duration: 3 hours
- Rationale: Sustained energy before lunch

**Post-Lunch Dip (13:00-14:30):**
- Energy: 50-55 (MAINTENANCE)
- Duration: 1.5 hours
- Rationale: Natural post-meal dip

**Afternoon Peak (14:30-17:00):**
- Energy: 65-75 (PRODUCTIVE)
- Duration: 2.5 hours
- Rationale: Second wind, second peak

**Evening Wind Down (17:00-21:00):**
- Energy: 45-60 (MAINTENANCE)
- Duration: 4 hours
- Rationale: Gradual decline towards sleep

**Sleep Prep (21:00-22:00):**
- Energy: 35-40 (RECOVERY transition)
- Duration: 1 hour
- Rationale: Preparing for sleep

**Sleep (22:00-07:00):**
- Energy: 20-35 (RECOVERY)
- Duration: 9 hours
- Rationale: Deep rest

---

## 🔧 Implementation Strategy

### File to Modify:
`services/circadian_analysis_service.py` (or wherever circadian analysis happens)

### Step 1: Add Generous Baseline Function

```python
def generate_generous_baseline_energy_timeline(
    chronotype: str = "moderate",
    archetype: str = "Foundation Builder"
) -> List[Dict]:
    """
    Generate a generous, motivating energy timeline when data is insufficient.

    Shows:
    - 2 clear peak periods (morning + afternoon)
    - Productive windows for most of waking hours
    - Only recovery during sleep

    This creates a motivating baseline that users can live up to.
    """
    timeline = []

    for slot_index in range(96):  # 24 hours * 4 (15-min slots)
        time_str = f"{slot_index // 4:02d}:{(slot_index % 4) * 15:02d}"
        hour = slot_index // 4

        # GENEROUS ENERGY ASSIGNMENT
        if 7 <= hour < 10:  # Morning Peak (07:00-10:00)
            zone = "peak"
            energy = 75 + (slot_index % 4) * 2  # 75-83

        elif 10 <= hour < 13:  # Productive Morning (10:00-13:00)
            zone = "productive"
            energy = 65 + (slot_index % 4)  # 65-68

        elif 13 <= hour < 14 or (hour == 14 and slot_index % 4 < 2):  # Post-lunch dip (13:00-14:30)
            zone = "maintenance"
            energy = 52 + (slot_index % 4)  # 52-55

        elif (hour == 14 and slot_index % 4 >= 2) or 15 <= hour < 17:  # Afternoon Peak (14:30-17:00)
            zone = "productive"
            energy = 68 + (slot_index % 4)  # 68-71

        elif 17 <= hour < 21:  # Evening Maintenance (17:00-21:00)
            zone = "maintenance"
            energy = 50 - ((hour - 17) * 2)  # 50 declining to 42

        elif 21 <= hour < 22:  # Sleep Prep (21:00-22:00)
            zone = "recovery"
            energy = 38 - (slot_index % 4) * 2  # 38 declining to 32

        else:  # Sleep Time (22:00-07:00)
            zone = "recovery"
            energy = 25 + (slot_index % 4)  # 25-28

        timeline.append({
            "time": time_str,
            "zone": zone,
            "slot_index": slot_index,
            "energy_level": energy
        })

    return timeline
```

### Step 2: Detect Data Quality

```python
def assess_data_quality(user_data: Dict) -> str:
    """
    Determine if we have enough data for accurate analysis.

    Returns:
        "insufficient" - Use generous baseline
        "moderate" - Use generous baseline with minor adjustments
        "good" - Use data-driven with generous bias
        "excellent" - Use full data-driven analysis
    """
    sleep_data_points = len(user_data.get('sleep_sessions', []))
    activity_data_points = len(user_data.get('activity_scores', []))
    days_of_data = user_data.get('data_span_days', 0)

    # Insufficient data - use generous baseline
    if days_of_data < 3 or sleep_data_points < 3:
        return "insufficient"

    # Moderate data - generous baseline with minor tweaks
    if days_of_data < 7 or sleep_data_points < 5:
        return "moderate"

    # Good data - data-driven with generous bias
    if days_of_data < 14:
        return "good"

    # Excellent data - full data-driven
    return "excellent"
```

### Step 3: Apply Generous Bias

```python
def apply_generous_bias_to_energy_levels(
    raw_timeline: List[Dict],
    data_quality: str,
    user_performance_trend: str = "improving"
) -> List[Dict]:
    """
    Apply generous bias to energy levels based on data quality and user performance.

    Rules:
    - Insufficient data: Use full generous baseline
    - Moderate data: Boost energy by 10-15 points
    - Good data: Boost energy by 5-10 points
    - Excellent data + improving: Boost by 5 points
    - Excellent data + declining: Use raw data (show reality)
    """
    if data_quality == "insufficient":
        return generate_generous_baseline_energy_timeline()

    boosted_timeline = []
    for slot in raw_timeline:
        energy = slot['energy_level']

        # Apply boost based on data quality
        if data_quality == "moderate":
            boost = 12
        elif data_quality == "good":
            boost = 8
        elif user_performance_trend == "improving":
            boost = 5
        else:  # declining performance
            boost = 0  # Show reality

        # Cap at 90 (don't exceed maximum)
        boosted_energy = min(energy + boost, 90)

        # Reclassify zone based on boosted energy
        if boosted_energy >= 70:
            zone = "peak"
        elif boosted_energy >= 55:
            zone = "productive"
        elif boosted_energy >= 40:
            zone = "maintenance"
        else:
            zone = "recovery"

        boosted_timeline.append({
            **slot,
            "energy_level": boosted_energy,
            "zone": zone,
            "original_energy": energy,
            "boost_applied": boost
        })

    return boosted_timeline
```

### Step 4: Performance Trend Detection

```python
def detect_user_performance_trend(user_id: str) -> str:
    """
    Detect if user is improving, stable, or declining.

    Returns:
        "improving" - Show generous energy to encourage
        "stable" - Show moderate generosity
        "declining" - Show more realistic (lower) energy to indicate need for rest
    """
    # Fetch last 14 days of check-in data
    recent_checkins = get_recent_checkins(user_id, days=14)

    if len(recent_checkins) < 7:
        return "improving"  # Default to optimistic

    # Calculate completion rates for two weeks
    week1_completion = calculate_completion_rate(recent_checkins[:7])
    week2_completion = calculate_completion_rate(recent_checkins[7:14])

    # Check trend
    if week2_completion > week1_completion + 10:
        return "improving"
    elif week2_completion < week1_completion - 15:
        return "declining"
    else:
        return "stable"
```

---

## 📊 Expected Output (Generous Baseline)

### Summary:
```json
{
  "summary": {
    "peak_energy_periods": [
      "07:00-10:00",      // Morning peak (3 hours)
      "14:30-17:00"       // Afternoon peak (2.5 hours)
    ],
    "productive_periods": [
      "10:00-13:00",      // Productive morning (3 hours)
      "14:30-17:00"       // Productive afternoon (2.5 hours)
    ],
    "maintenance_periods": [
      "13:00-14:30",      // Post-lunch dip (1.5 hours)
      "17:00-21:00"       // Evening (4 hours)
    ],
    "recovery_periods": [
      "21:00-07:00"       // Sleep (10 hours)
    ],
    "total_peak_minutes": 330,        // 5.5 hours (vs 0 currently!)
    "total_productive_minutes": 330,  // 5.5 hours
    "total_maintenance_minutes": 330, // 5.5 hours
    "total_recovery_minutes": 600     // 10 hours
  }
}
```

### Energy Timeline Sample:
```json
[
  { "time": "07:00", "zone": "peak", "energy_level": 75 },
  { "time": "07:15", "zone": "peak", "energy_level": 77 },
  { "time": "07:30", "zone": "peak", "energy_level": 79 },
  { "time": "10:00", "zone": "productive", "energy_level": 65 },
  { "time": "13:00", "zone": "maintenance", "energy_level": 52 },
  { "time": "14:30", "zone": "productive", "energy_level": 68 },
  { "time": "17:00", "zone": "maintenance", "energy_level": 50 },
  { "time": "22:00", "zone": "recovery", "energy_level": 28 }
]
```

---

## 🎯 Benefits

### For New Users:
- ✅ **Motivating**: Shows clear peak periods they can leverage
- ✅ **Optimistic**: Assumes they have good energy until proven otherwise
- ✅ **Actionable**: Clear windows for peak performance tasks
- ✅ **Not overwhelming**: Still shows realistic post-lunch dip

### For Existing Users:
- ✅ **Adaptive**: Adjusts based on actual performance
- ✅ **Encouraging**: Maintains generous bias if improving
- ✅ **Realistic**: Shows lower energy only if consistently underperforming
- ✅ **Progressive**: Energy zones improve as user improves

### For System:
- ✅ **Better engagement**: Users see potential, not limitations
- ✅ **Self-fulfilling**: Higher energy expectations → better performance
- ✅ **Progressive disclosure**: Start optimistic, adjust with data
- ✅ **Motivational psychology**: Focus on strengths, not weaknesses

---

## 🔄 Adjustment Logic

### When to Show More Peak Energy:
1. User is new (< 7 days of data)
2. User is improving (completion rate increasing)
3. User consistently meets/exceeds task completion
4. Sleep quality is good (>7 hours, high efficiency)

### When to Show More Low Energy:
1. User consistently underperforms (< 40% completion for 14+ days)
2. Sleep quality declining (< 6 hours, low efficiency)
3. User explicitly reports low energy in check-ins
4. HRV trends showing increased stress/poor recovery

---

## 📝 Implementation Checklist

- [ ] Create `generate_generous_baseline_energy_timeline()` function
- [ ] Create `assess_data_quality()` function
- [ ] Create `apply_generous_bias_to_energy_levels()` function
- [ ] Create `detect_user_performance_trend()` function
- [ ] Update main circadian analysis function to use generous baseline
- [ ] Add logic to switch between generous and realistic based on performance
- [ ] Update energy zone thresholds (70+ peak, 55+ productive, 40+ maintenance)
- [ ] Test with new user (should show 2 peak periods)
- [ ] Test with improving user (should maintain generous zones)
- [ ] Test with declining user (should show more realistic/lower zones)

---

## 🚀 Implementation Priority

**Phase 1 (Quick Win):**
1. Add generous baseline function
2. Use it when data is insufficient
3. Deploy immediately

**Phase 2 (Smart Adjustments):**
1. Add data quality detection
2. Add performance trend detection
3. Apply generous bias based on both

**Phase 3 (Advanced):**
1. Machine learning for personalized energy patterns
2. Real-time adjustments based on check-ins
3. Predictive energy forecasting

---

## 🎯 Expected Impact

### Current (Demotivating):
- Peak periods: 0
- All day maintenance: 40
- User sees: "I have no peak energy"

### After Fix (Motivating):
- Peak periods: 2 (5.5 hours)
- Productive periods: 2 (5.5 hours)
- User sees: "I have two great energy windows to use!"

**Psychological Shift:** From "I'm just maintaining" → "I have peak performance windows!"

---

## 📌 Key Principle

**"Show potential, not limitations"**

- Start generous and optimistic
- Adjust down only with clear evidence
- Always bias towards showing capability
- Make low energy the exception, not the rule
