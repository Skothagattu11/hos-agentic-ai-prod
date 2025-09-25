# Energy Zone Schedule Examples

## Overview
Real-world examples showing how energy zones would work for different users with different data scenarios.

---

## **User 1: Sarah - Peak Performer Archetype**

### **Data Profile**
- **Archetype**: Peak Performer
- **Baseline**: Tracks HRV, sleep metrics, uses wearables consistently
- **Typical Schedule**: 6 AM wake, works 9-5, gym regular

### **Scenario A: High Energy Day**

#### **Yesterday's Data**
```json
{
  "sleep_score": 87,
  "readiness_score": 82,
  "activity_score": 76,
  "sleep_duration": "7h 45m",
  "sleep_efficiency": 91
}
```

#### **Today's Current State** (7:00 AM)
```json
{
  "current_readiness": 85,
  "hrv_score": 58,
  "time_of_day_factor": 10  // Morning boost
}
```

#### **Energy Zone Calculation**
```
Energy Score = (87 × 0.4) + (82 × 0.4) + (10 × 0.2) = 69.6
Zone Classification: PRODUCTIVE ZONE (69.6/100)
```

#### **Generated Schedule**

**🌅 MORNING OPTIMIZATION BLOCK (6:15-7:45 AM)**
```json
{
  "energy_zone": "productive",
  "zone_message": "⚡ Strong energy detected - optimal for performance protocols",
  "time_adjustment": "Standard timing with intensity boost",
  "activities": [
    {
      "time": "6:15-6:25 AM",
      "task": "HRV-Guided Power Breathing",
      "intensity": "85%",
      "description": "10 deep breaths with HRV feedback - capitalize on strong readiness",
      "zone_optimization": "Enhanced from basic breathing - your metrics support intensity"
    },
    {
      "time": "6:25-6:55 AM",
      "task": "Performance-Focused Movement",
      "intensity": "85%",
      "description": "25-min structured workout with power intervals",
      "zone_optimization": "Upgraded from 20-min routine - excellent recovery metrics"
    },
    {
      "time": "6:55-7:15 AM",
      "task": "Optimization Nutrition Protocol",
      "intensity": "85%",
      "description": "Precision fuel timing + supplement stack",
      "zone_optimization": "Full protocol enabled - energy supports complexity"
    }
  ]
}
```

**🎯 PEAK PERFORMANCE BLOCK (8:45-11:00 AM)**
```json
{
  "energy_zone": "productive",
  "zone_message": "🚀 Prime cognitive window - tackle your most challenging work",
  "activities": [
    {
      "time": "8:45-10:15 AM",
      "task": "Strategic Deep Work Session",
      "intensity": "85%",
      "description": "90-min focused cognitive work - complex problem solving",
      "zone_optimization": "Extended session - strong energy supports longer focus"
    },
    {
      "time": "10:15-10:25 AM",
      "task": "Performance Data Review",
      "intensity": "85%",
      "description": "Quick metrics check and optimization adjustments",
      "zone_optimization": "Added analytical component - energy supports data processing"
    }
  ]
}
```

---

### **Scenario B: Recovery Day**

#### **Yesterday's Data**
```json
{
  "sleep_score": 45,
  "readiness_score": 38,
  "activity_score": 28,
  "sleep_duration": "5h 20m",
  "sleep_efficiency": 67,
  "notes": "Late meeting, poor sleep quality"
}
```

#### **Today's Current State** (7:30 AM)
```json
{
  "current_readiness": 42,
  "hrv_score": 31,
  "time_of_day_factor": 8  // Later wake = reduced morning boost
}
```

#### **Energy Zone Calculation**
```
Energy Score = (45 × 0.4) + (38 × 0.4) + (8 × 0.2) = 34.8
Zone Classification: RECOVERY ZONE (34.8/100)
```

#### **Generated Schedule**

**🌱 GENTLE RESTORATION BLOCK (7:30-9:00 AM)**
```json
{
  "energy_zone": "recovery",
  "zone_message": "🌱 Recovery mode activated - your body needs restoration today",
  "time_adjustment": "Later start (+60 min), reduced intensity",
  "activities": [
    {
      "time": "7:30-7:40 AM",
      "task": "Restorative Breathing",
      "intensity": "40%",
      "description": "Gentle 4-7-8 breathing - activate parasympathetic recovery",
      "zone_optimization": "Simplified from power breathing - focus on calm activation"
    },
    {
      "time": "7:40-8:00 AM",
      "task": "Gentle Movement Flow",
      "intensity": "40%",
      "description": "15-min light stretching and mobility work",
      "zone_optimization": "Reduced from 25-min workout - honoring low energy state"
    },
    {
      "time": "8:00-8:20 AM",
      "task": "Recovery Nutrition Support",
      "intensity": "40%",
      "description": "Hydration focus + simple anti-inflammatory breakfast",
      "zone_optimization": "Simplified nutrition - easy preparation, recovery-focused"
    }
  ]
}
```

**🔋 MAINTENANCE WORK BLOCK (10:00-11:30 AM)**
```json
{
  "energy_zone": "recovery",
  "zone_message": "Take it easy - administrative tasks and gentle progress only",
  "activities": [
    {
      "time": "10:00-11:00 AM",
      "task": "Light Administrative Work",
      "intensity": "40%",
      "description": "Email processing, simple tasks - no complex decisions",
      "zone_optimization": "Downgraded from strategic work - protecting cognitive resources"
    },
    {
      "time": "11:00-11:15 AM",
      "task": "Recovery Check-in",
      "intensity": "40%",
      "description": "Brief energy assessment and hydration",
      "zone_optimization": "Added recovery support - monitoring for improvement"
    }
  ]
}
```

---

## **User 2: Mike - Foundation Builder Archetype**

### **Data Profile**
- **Archetype**: Foundation Builder
- **Baseline**: Basic fitness tracker, focuses on consistency over optimization
- **Typical Schedule**: 7:30 AM wake, work from home, building healthy habits

### **Scenario A: Good Energy Day**

#### **Yesterday's Data**
```json
{
  "sleep_score": 72,
  "readiness_score": 68,
  "activity_score": 64,
  "sleep_duration": "7h 15m",
  "activity_minutes": 45
}
```

#### **Today's Current State** (8:00 AM)
```json
{
  "energy_self_report": 7,  // User reported feeling good
  "time_of_day_factor": 8   // Later morning start
}
```

#### **Energy Zone Calculation**
```
Energy Score = (72 × 0.4) + (68 × 0.4) + (8 × 0.2) = 57.6
Zone Classification: MAINTENANCE ZONE (57.6/100)
```

#### **Generated Schedule**

**🌅 GENTLE BUILDING BLOCK (8:00-9:30 AM)**
```json
{
  "energy_zone": "maintenance",
  "zone_message": "🔋 Steady energy - perfect for consistent foundation building",
  "time_adjustment": "Comfortable timing, sustainable intensity",
  "activities": [
    {
      "time": "8:00-8:10 AM",
      "task": "Peaceful Morning Ritual",
      "intensity": "60%",
      "description": "Gentle awakening with warm water and gratitude",
      "zone_optimization": "Standard routine - good energy supports consistency"
    },
    {
      "time": "8:10-8:25 AM",
      "task": "Foundation Movement",
      "intensity": "60%",
      "description": "15-min walk or light stretching - building the habit",
      "zone_optimization": "Maintained duration - energy supports full routine"
    },
    {
      "time": "8:25-8:45 AM",
      "task": "Nourishing Breakfast Prep",
      "intensity": "60%",
      "description": "Mindful meal preparation - simple, healthy choices",
      "zone_optimization": "Full preparation time - energy allows for mindful cooking"
    }
  ]
}
```

**🏗️ PRODUCTIVE BUILDING BLOCK (10:30 AM-12:00 PM)**
```json
{
  "energy_zone": "maintenance",
  "zone_message": "Building momentum - steady progress on your foundation",
  "activities": [
    {
      "time": "10:30-11:30 AM",
      "task": "Focused Work Session",
      "intensity": "60%",
      "description": "60-min productive work - steady, manageable pace",
      "zone_optimization": "Standard session length - energy supports sustained focus"
    },
    {
      "time": "11:30-12:00 PM",
      "task": "Habit Building Activity",
      "intensity": "60%",
      "description": "Practice one small habit - reading, organizing, or planning",
      "zone_optimization": "Added skill building - good energy supports growth"
    }
  ]
}
```

---

### **Scenario B: Low Energy Day**

#### **Yesterday's Data**
```json
{
  "sleep_score": 55,
  "readiness_score": 48,
  "activity_score": 35,
  "sleep_duration": "6h 30m",
  "notes": "Restless night, stressed about work deadline"
}
```

#### **Today's Current State** (8:30 AM)
```json
{
  "energy_self_report": 4,  // User feeling tired
  "time_of_day_factor": 6   // Later wake time
}
```

#### **Energy Zone Calculation**
```
Energy Score = (55 × 0.4) + (48 × 0.4) + (6 × 0.2) = 42.4
Zone Classification: MAINTENANCE ZONE (42.4/100) - borderline Recovery
```

#### **Generated Schedule**

**🌱 EXTRA GENTLE BLOCK (8:30-10:00 AM)**
```json
{
  "energy_zone": "maintenance_recovery",
  "zone_message": "🌱 Take it extra easy today - small steps still count",
  "time_adjustment": "Later start (+60 min), very gentle approach",
  "activities": [
    {
      "time": "8:30-8:40 AM",
      "task": "Comfort Morning Ritual",
      "intensity": "45%",
      "description": "Extra gentle start - warm drink and deep breathing",
      "zone_optimization": "Extended comfort time - honoring lower energy"
    },
    {
      "time": "8:40-8:50 AM",
      "task": "Minimal Movement",
      "intensity": "45%",
      "description": "5-10 min very light stretching or short walk around house",
      "zone_optimization": "Reduced from 15-min - protecting limited energy"
    },
    {
      "time": "8:50-9:15 AM",
      "task": "Simple Nourishment",
      "intensity": "45%",
      "description": "Easy breakfast - minimal prep, maximum nutrition",
      "zone_optimization": "Simplified prep - using convenience foods mindfully"
    }
  ]
}
```

**🔋 GENTLE PROGRESS BLOCK (11:00 AM-12:00 PM)**
```json
{
  "energy_zone": "maintenance_recovery",
  "zone_message": "Gentle progress - every small step builds your foundation",
  "activities": [
    {
      "time": "11:00-11:45 AM",
      "task": "Light Work Tasks",
      "intensity": "45%",
      "description": "Simple, low-pressure tasks - emails, easy admin work",
      "zone_optimization": "Shortened session - protecting cognitive resources"
    },
    {
      "time": "11:45-12:00 PM",
      "task": "Self-Care Check-in",
      "intensity": "45%",
      "description": "Brief rest, hydration, or gentle mood boost activity",
      "zone_optimization": "Added self-care - extra support for challenging day"
    }
  ]
}
```

---

## **Key Insights from Examples**

### **Energy Zone Impact on Scheduling**
- **Peak/Productive**: Earlier starts, longer sessions, enhanced activities
- **Maintenance**: Standard timing, sustainable pace, consistent habits
- **Recovery**: Later starts, shorter sessions, gentler alternatives

### **Archetype-Specific Adaptations**
- **Peak Performer**: Focus on optimization, metrics, performance enhancement
- **Foundation Builder**: Focus on consistency, comfort, sustainable building

### **Data-Driven Personalization**
- **Good Data**: More precise zone classification and confident adjustments
- **Limited Data**: Conservative approach using self-reports and time factors
- **Poor Sleep**: Automatic recovery mode regardless of other factors

### **User Communication Patterns**
- **Zone messaging**: Explains why the schedule looks this way
- **Activity optimization notes**: Shows how tasks were adjusted
- **Energy-appropriate language**: Matches user's archetype and energy state

This system provides **immediate value** from existing data while being **simple enough** to understand and **flexible enough** to handle different user types and data availability scenarios.