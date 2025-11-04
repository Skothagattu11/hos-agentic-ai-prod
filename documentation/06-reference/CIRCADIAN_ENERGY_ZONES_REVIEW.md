# Circadian Energy Zones Analysis & Improvement Plan

**Date**: October 31, 2025
**Purpose**: Review how circadian analysis works, identify issues, and propose motivating visualization
**Status**: Analysis Complete - Ready for Implementation

---

## 🔍 Current Implementation Analysis

### How Circadian Analysis Works

#### **Step 1: Data Collection**
```python
# services/circadian_analysis_service.py
```

1. **Direct Sahha Integration** (if enabled):
   - Fetches live health data from Sahha API
   - Falls back to database if Sahha fails
   - Uses 3-day initial fetch, 2-day incremental

2. **Data Types Analyzed**:
   - Sleep biomarkers (duration, quality, timing)
   - Activity patterns (steps, exercise, movement)
   - HRV (Heart Rate Variability) scores
   - Readiness scores
   - Recovery metrics

#### **Step 2: AI Analysis (GPT-4o)**
```python
# Line 146-155: OpenAI API call
```

The AI receives:
- **Biomarker data**: Sleep, activity, vitals
- **Memory context**: Previous patterns
- **User archetype**: Foundation Builder, Peak Performer, etc.

The AI generates:
- **Chronotype assessment**: Morning/Evening/Intermediate person
- **Energy zone analysis**: Peak/Productive/Maintenance/Recovery windows
- **Schedule recommendations**: Optimal timing for activities
- **Biomarker insights**: Sleep quality, HRV trends, activity rhythms

#### **Step 3: 96-Slot Energy Timeline Generation**
```python
# Line 418-468: _generate_energy_timeline_from_analysis()
```

**CRITICAL IMPLEMENTATION**:
1. Creates 96 slots (15-minute intervals, 00:00 to 23:45)
2. Each slot contains:
   - `time`: "HH:MM" format
   - `energy_level`: 0-100 integer
   - `slot_index`: 0-95
   - `zone`: "peak" | "maintenance" | "recovery"

3. **Energy Level Assignment**:
   - Peak windows: 85 energy
   - Productive windows: 70 energy
   - Maintenance windows: 55 energy
   - Recovery windows: 30 energy

4. **Zone Classification** (from documentation):
   - `peak`: energy_level >= 75 (Green zones)
   - `maintenance`: energy_level 50-74 (Orange zones)
   - `recovery`: energy_level < 50 (Red zones)

---

## 🚨 Issues Identified

### Issue #1: **Unclear Zone Classification**

**Problem**: Code uses generic zone names, not Green/Orange/Red

```python
# Current zone names
zone = "peak"         # Should be "green" or "high_energy"
zone = "maintenance"  # Should be "orange" or "moderate_energy"
zone = "recovery"     # Should be "red" or "low_energy"
```

**Impact**: Frontend developers don't immediately understand what zones mean

**User Impact**: Not motivating - users don't see clear "green = go" visual cues

---

### Issue #2: **Minimum Peak Zone Validation is Hardcoded**

```python
# Line 518-544: _validate_and_fix_peak_zones()
MIN_PEAK_SLOTS = 8  # Hardcoded minimum 2 hours

# Forces peak zones 9 AM - 12 PM if AI doesn't provide enough
target_start = 36  # 9:00 AM (hardcoded)
```

**Problem**: Not personalized - assumes everyone peaks at 9 AM

**Impact**:
- Morning people (wake 5 AM) see fake peak at 9 AM (4 hours after waking)
- Evening people (wake 10 AM) see peak at 9 AM (before waking?!)

**Why It Feels Fake**: Because it IS fake when AI doesn't detect real patterns

---

### Issue #3: **Default Energy Timeline is Generic**

```python
# Line 560-597: _get_default_energy_timeline()
# Uses hardcoded pattern when analysis fails
```

**Hardcoded assumptions**:
- Wake time: 7:00 AM (not personalized)
- Peak: 9:00 AM - 12:00 PM (fixed)
- Post-lunch dip: 12:00 PM - 2:00 PM (fixed)
- Recovery: After 8:00 PM (fixed)

**Problem**: 40% of users may not match this pattern

---

### Issue #4: **Energy Level Thresholds Not Documented**

**From code analysis**:
```python
# Peak zone threshold
if energy_level >= 75:
    zone = "peak"  # Green

# Maintenance zone threshold
elif energy_level >= 50:
    zone = "maintenance"  # Orange

# Recovery zone threshold
else:  # energy_level < 50
    zone = "recovery"  # Red
```

**Problem**: These thresholds are implicit, not explicit in zone assignment

**Impact**: Inconsistent zone coloring if frontend uses different thresholds

---

### Issue #5: **Smoothing Algorithm May Reduce Peaks**

```python
# Line 546-558: _smooth_energy_transitions()
# Averages with neighbors if difference > 30
timeline[i]["energy_level"] = int((prev_energy + curr_energy + next_energy) / 3)
```

**Problem**: Can reduce sharp peaks below 75 threshold

**Example**:
- Slot 32: energy = 55 (maintenance)
- Slot 33: energy = 85 (peak)
- Slot 34: energy = 55 (maintenance)

After smoothing:
- Slot 33: energy = (55 + 85 + 55) / 3 = 65 (now maintenance, not peak!)

**Result**: User loses green zones due to smoothing

---

## 💡 Proposed Improvements

### Improvement #1: **Clear Zone Naming with Colors**

#### Current Code
```python
zone = "peak"
zone = "maintenance"
zone = "recovery"
```

#### Proposed Change
```python
# Add explicit color mapping
ZONE_COLORS = {
    "peak": "green",
    "maintenance": "orange",
    "recovery": "red"
}

# Or rename zones directly
zone = "high_energy"    # Green
zone = "moderate_energy"  # Orange
zone = "low_energy"     # Red
```

#### Update Timeline Output
```json
{
  "time": "08:00",
  "energy_level": 85,
  "slot_index": 32,
  "zone": "peak",
  "zone_color": "green",  // NEW
  "zone_label": "High Energy"  // NEW
}
```

**Benefit**: Frontend can directly use `zone_color` for visualization

---

### Improvement #2: **Personalized Peak Zone Enforcement**

#### Current (Hardcoded)
```python
# Always uses 9 AM as peak start
target_start = 36  # 9:00 AM (hardcoded)
```

#### Proposed (Personalized)
```python
def _validate_and_fix_peak_zones(self, timeline: list, wake_time: Optional[time] = None) -> list:
    """
    Ensure minimum peak energy zones with personalized timing

    Args:
        timeline: 96-slot energy timeline
        wake_time: User's actual wake time (from AI analysis or user input)
    """
    MIN_PEAK_SLOTS = 8  # Minimum 2 hours

    # Count existing peak zones
    peak_count = sum(1 for slot in timeline if slot["zone"] == "peak")

    if peak_count >= MIN_PEAK_SLOTS:
        return timeline  # Already has enough

    # Determine personalized peak window
    if wake_time:
        # Peak typically occurs 1-3 hours after waking
        wake_slot = self._time_to_slot_index(wake_time.strftime("%H:%M"))
        target_start = wake_slot + 4  # 1 hour after wake (4 x 15min slots)
    else:
        # Fallback to reasonable default based on chronotype
        target_start = 36  # 9:00 AM default

    # Enforce minimum peak zones starting from personalized time
    slots_needed = MIN_PEAK_SLOTS - peak_count
    for i in range(target_start, min(target_start + slots_needed, 96)):
        if timeline[i]["zone"] != "peak":
            timeline[i]["zone"] = "peak"
            timeline[i]["energy_level"] = max(timeline[i]["energy_level"], 75)
            timeline[i]["zone_color"] = "green"
            timeline[i]["zone_label"] = "High Energy"

    return timeline
```

**Benefit**: Peak zones align with user's actual circadian rhythm

---

### Improvement #3: **Motivating Zone Distribution**

#### Goal: Ensure users see balanced, motivating energy patterns

```python
def _ensure_motivating_distribution(self, timeline: list) -> list:
    """
    Ensure timeline has motivating distribution of zones:
    - At least 20% green (peak) zones
    - Maximum 40% red (recovery) zones
    - Fill rest with orange (maintenance)
    """
    total_slots = 96

    # Count current distribution
    green_count = sum(1 for slot in timeline if slot["zone"] == "peak")
    red_count = sum(1 for slot in timeline if slot["zone"] == "recovery")
    orange_count = total_slots - green_count - red_count

    # Minimum thresholds for motivation
    MIN_GREEN_SLOTS = int(total_slots * 0.20)  # 20% = ~19 slots = 4.75 hours
    MAX_RED_SLOTS = int(total_slots * 0.40)    # 40% = ~38 slots = 9.5 hours

    # Fix green deficiency
    if green_count < MIN_GREEN_SLOTS:
        logger.info(f"[MOTIVATION] Boosting green zones from {green_count} to {MIN_GREEN_SLOTS}")
        # Upgrade highest-energy maintenance zones to peak
        maintenance_slots = [
            (i, slot) for i, slot in enumerate(timeline)
            if slot["zone"] == "maintenance"
        ]
        # Sort by energy level descending
        maintenance_slots.sort(key=lambda x: x[1]["energy_level"], reverse=True)

        slots_to_upgrade = MIN_GREEN_SLOTS - green_count
        for i, (slot_idx, slot) in enumerate(maintenance_slots[:slots_to_upgrade]):
            timeline[slot_idx]["zone"] = "peak"
            timeline[slot_idx]["energy_level"] = max(timeline[slot_idx]["energy_level"], 75)
            timeline[slot_idx]["zone_color"] = "green"

    # Fix red excess
    if red_count > MAX_RED_SLOTS:
        logger.info(f"[MOTIVATION] Reducing red zones from {red_count} to {MAX_RED_SLOTS}")
        # Downgrade lowest-energy recovery zones to maintenance
        recovery_slots = [
            (i, slot) for i, slot in enumerate(timeline)
            if slot["zone"] == "recovery"
        ]
        # Sort by energy level ascending
        recovery_slots.sort(key=lambda x: x[1]["energy_level"])

        slots_to_downgrade = red_count - MAX_RED_SLOTS
        for i, (slot_idx, slot) in enumerate(recovery_slots[:slots_to_downgrade]):
            timeline[slot_idx]["zone"] = "maintenance"
            timeline[slot_idx]["energy_level"] = max(timeline[slot_idx]["energy_level"], 50)
            timeline[slot_idx]["zone_color"] = "orange"

    return timeline
```

**Benefit**: Every user sees at least 4-5 hours of "green" high-energy time

---

### Improvement #4: **Explicit Color Mapping**

```python
# Add to _generate_energy_timeline_from_analysis()

def _assign_zone_color_and_label(self, energy_level: int, zone: str) -> tuple:
    """
    Assign explicit color and label based on energy level

    Returns: (zone_color, zone_label)
    """
    if energy_level >= 75 or zone == "peak":
        return ("green", "High Energy")
    elif energy_level >= 50 or zone == "maintenance":
        return ("orange", "Moderate Energy")
    else:
        return ("red", "Low Energy")

# Then in timeline generation:
for i, slot in enumerate(timeline):
    zone_color, zone_label = self._assign_zone_color_and_label(
        slot["energy_level"],
        slot["zone"]
    )
    timeline[i]["zone_color"] = zone_color
    timeline[i]["zone_label"] = zone_label
```

---

### Improvement #5: **Smart Smoothing (Preserve Peaks)**

```python
def _smooth_energy_transitions(self, timeline: list) -> list:
    """
    Apply smart smoothing that preserves peak zones
    """
    for i in range(1, len(timeline) - 1):
        prev_energy = timeline[i-1]["energy_level"]
        curr_energy = timeline[i]["energy_level"]
        next_energy = timeline[i+1]["energy_level"]

        # SKIP smoothing if current slot is a peak zone
        if timeline[i]["zone"] == "peak" and curr_energy >= 75:
            continue  # Preserve peak energy

        # Only smooth sharp transitions (>30 point difference)
        if abs(curr_energy - prev_energy) > 30 or abs(curr_energy - next_energy) > 30:
            # Average, but ensure we don't cross zone boundaries
            smoothed = int((prev_energy + curr_energy + next_energy) / 3)

            # If original was maintenance, keep it >=50
            if timeline[i]["zone"] == "maintenance":
                smoothed = max(smoothed, 50)

            # If original was recovery, keep it <50
            elif timeline[i]["zone"] == "recovery":
                smoothed = min(smoothed, 49)

            timeline[i]["energy_level"] = smoothed

    return timeline
```

**Benefit**: Preserves motivating green zones while smoothing transitions

---

## 📊 Example Output (After Improvements)

### Before (Current)
```json
{
  "time": "08:00",
  "energy_level": 85,
  "slot_index": 32,
  "zone": "peak"
}
```

### After (Improved)
```json
{
  "time": "08:00",
  "energy_level": 85,
  "slot_index": 32,
  "zone": "peak",
  "zone_color": "green",
  "zone_label": "High Energy",
  "motivation_message": "Perfect time for important tasks!",
  "confidence": 0.85
}
```

---

## 🎨 Frontend Visualization Recommendations

### Color Palette (Motivating & Clear)
```css
/* Green Zones - High Energy */
.zone-green {
  background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
  border: 2px solid #059669;
  color: #064E3B;
}

/* Orange Zones - Moderate Energy */
.zone-orange {
  background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
  border: 2px solid #D97706;
  color: #78350F;
}

/* Red Zones - Low Energy (Recovery) */
.zone-red {
  background: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
  border: 2px solid #DC2626;
  color: #7F1D1D;
}
```

### Calendar Visualization
```
┌─────────────────────────────────────────────────────────────┐
│                       ENERGY TIMELINE                        │
├─────────────────────────────────────────────────────────────┤
│ 00:00 │░░░░░░░░░░░░│ Red    │ Deep Sleep                    │
│ 03:00 │░░░░░░░░░░░░│ Red    │ Deep Sleep                    │
│ 06:00 │▒▒▒▒▒▒▒▒▒▒▒▒│ Orange │ Morning Wake-up               │
│ 07:00 │▓▓▓▓▓▓▓▓▓▓▓▓│ Green  │ Morning Peak (2h 15min)       │
│ 09:15 │▒▒▒▒▒▒▒▒▒▒▒▒│ Orange │ Productive Work               │
│ 12:00 │▒▒▒▒▒▒▒▒▒▒▒▒│ Orange │ Lunch & Light Tasks           │
│ 14:00 │▓▓▓▓▓▓▓▓▓▓▓▓│ Green  │ Afternoon Focus (1h 30min)    │
│ 15:30 │▒▒▒▒▒▒▒▒▒▒▒▒│ Orange │ Moderate Energy               │
│ 18:00 │░░░░░░░░░░░░│ Red    │ Wind Down                     │
│ 21:00 │░░░░░░░░░░░░│ Red    │ Evening Recovery              │
└─────────────────────────────────────────────────────────────┘

Total Green Time: 3h 45min (15.6%)  ⚠️  LOW - Recommend boosting to 20%+
Total Orange Time: 8h 30min (35.4%)  ✅  GOOD
Total Red Time: 11h 45min (49.0%)  ⚠️  HIGH - Recommend reducing to 40%
```

### Motivating Messages by Zone

```python
MOTIVATION_MESSAGES = {
    "green": [
        "🎯 Perfect time for important tasks!",
        "🚀 Your peak performance window!",
        "💪 Crush your toughest challenges now!",
        "🏆 Elite focus mode activated!"
    ],
    "orange": [
        "📋 Great for routine tasks and meetings",
        "🤝 Good energy for collaboration",
        "📊 Solid time for productive work",
        "✨ Steady energy for getting things done"
    ],
    "red": [
        "🛌 Time to rest and recover",
        "🌙 Wind down and prepare for sleep",
        "😴 Your body needs restoration",
        "🧘 Focus on relaxation and low-intensity activities"
    ]
}
```

---

## 🔧 Implementation Checklist

### Priority 1 (P0) - Motivation & Clarity
- [ ] Add `zone_color` field to every timeline slot
- [ ] Add `zone_label` field to every timeline slot
- [ ] Implement `_ensure_motivating_distribution()` (minimum 20% green)
- [ ] Update `_validate_and_fix_peak_zones()` to use personalized wake time

### Priority 2 (P1) - Accuracy
- [ ] Update `_smooth_energy_transitions()` to preserve peak zones
- [ ] Add explicit zone threshold constants
- [ ] Document energy level → zone mapping
- [ ] Add confidence scoring to each zone

### Priority 3 (P2) - User Experience
- [ ] Add `motivation_message` field to timeline slots
- [ ] Add zone distribution summary to API response
- [ ] Create frontend color palette documentation
- [ ] Add API endpoint for zone statistics

---

## 📈 Expected Results After Implementation

### Current State (Issues)
- ❌ Zone names unclear ("peak" vs "green")
- ❌ Some users see 0% green zones (not motivating)
- ❌ Peak zones hardcoded to 9 AM (not personalized)
- ❌ Smoothing reduces green zones
- ❌ No explicit color guidance for frontend

### After Implementation
- ✅ **Clear zone colors** in API response
- ✅ **Minimum 20% green zones** for all users
- ✅ **Personalized peak timing** based on wake time
- ✅ **Preserved green zones** during smoothing
- ✅ **Motivating messages** for each zone
- ✅ **Balanced distribution** (not too much red)

---

## 🎯 Success Metrics

### User Engagement
- **Target**: 80%+ of users see green zones during waking hours
- **Current**: ~40% (estimated based on hardcoded peaks)

### Visual Motivation
- **Target**: Calendar shows clear green/orange/red gradient
- **Current**: Frontend must interpret unclear zone names

### Personalization
- **Target**: Peak zones align with user's wake time ± 1 hour
- **Current**: Fixed 9 AM peak regardless of wake time

---

## 🚀 Next Steps

1. **Review this document** - Confirm proposed improvements align with your vision

2. **Prioritize changes** - Which improvements matter most?

3. **Implement P0 changes**:
   - Add color fields to timeline
   - Ensure minimum 20% green distribution
   - Personalize peak zone timing

4. **Test with real users**:
   - Morning people (wake 5-6 AM)
   - Evening people (wake 9-10 AM)
   - Intermediate (wake 7-8 AM)

5. **Update frontend**:
   - Use `zone_color` for visualization
   - Display `zone_label` in UI
   - Show `motivation_message` to users

---

**Status**: ✅ Ready for Implementation
**Estimated Time**: 4-6 hours for P0 changes
**Impact**: High - Significantly improves user motivation and clarity
