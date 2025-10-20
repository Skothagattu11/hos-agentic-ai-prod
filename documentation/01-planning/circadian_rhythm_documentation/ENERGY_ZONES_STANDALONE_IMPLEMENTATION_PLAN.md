# Energy Zones Standalone Service - Implementation Plan

## Overview

This plan outlines the implementation of a standalone Energy Zones Service that:
1. Auto-detects user mode (recovery/productive/performance) from health data
2. Calculates personalized energy zones based on sleep patterns and biomarkers
3. Provides zones via new API endpoints without modifying existing functionality
4. Enables existing routine planning to optionally consume energy zones

## Database Changes

### New Tables Required

#### 1. Energy Zones Cache Table
```sql
CREATE TABLE energy_zones_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    calculation_date DATE NOT NULL,
    detected_mode VARCHAR(20) NOT NULL, -- 'recovery', 'productive', 'performance'
    wake_time TIME NOT NULL,
    bedtime TIME NOT NULL,
    chronotype VARCHAR(20), -- 'morning_lark', 'evening_owl', 'neutral'
    zones_data JSONB NOT NULL, -- Complete zones information as JSON
    confidence_score FLOAT NOT NULL, -- 0.0 to 1.0
    biomarker_snapshot JSONB, -- Health data used for calculation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    UNIQUE(user_id, calculation_date)
);

-- Indexes for performance
CREATE INDEX idx_energy_zones_cache_user_date ON energy_zones_cache(user_id, calculation_date);
CREATE INDEX idx_energy_zones_cache_expires ON energy_zones_cache(expires_at);
CREATE INDEX idx_energy_zones_cache_mode ON energy_zones_cache(user_id, detected_mode);
```

#### 2. Sleep Schedule Inference Table
```sql
CREATE TABLE sleep_schedule_inferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    inference_date DATE NOT NULL,
    estimated_wake_time TIME NOT NULL,
    estimated_bedtime TIME NOT NULL,
    chronotype VARCHAR(20),
    confidence_score FLOAT NOT NULL,
    data_sources TEXT[], -- ['sleep_duration', 'readiness_patterns', 'plan_analysis']
    sleep_duration_avg_minutes INTEGER,
    readiness_pattern_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, inference_date)
);

CREATE INDEX idx_sleep_inferences_user ON sleep_schedule_inferences(user_id, inference_date);
```

#### 3. Energy Zone Definitions Table (Reference Data)
```sql
CREATE TABLE energy_zone_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_name VARCHAR(50) NOT NULL, -- 'foundation', 'peak', 'maintenance', 'recovery'
    mode_type VARCHAR(20) NOT NULL, -- 'recovery', 'productive', 'performance'
    start_offset_hours FLOAT NOT NULL, -- Hours after wake time
    duration_hours FLOAT NOT NULL,
    base_energy_level INTEGER NOT NULL, -- 0-100
    intensity_level VARCHAR(10) NOT NULL, -- 'low', 'moderate', 'high'
    optimal_activities TEXT[], -- ['focus_work', 'light_activity', 'rest']
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(zone_name, mode_type)
);

-- Insert default zone definitions
INSERT INTO energy_zone_definitions (zone_name, mode_type, start_offset_hours, duration_hours, base_energy_level, intensity_level, optimal_activities, description) VALUES
('foundation', 'recovery', 0.0, 2.0, 40, 'low', '{"gentle_movement","hydration","breathing"}', 'Gentle awakening and basic needs'),
('foundation', 'productive', 0.0, 1.5, 60, 'moderate', '{"light_exercise","planning","nutrition"}', 'Standard morning routine'),
('foundation', 'performance', 0.0, 1.0, 75, 'moderate', '{"dynamic_warmup","goal_setting","optimization"}', 'High-energy morning activation'),
('peak', 'recovery', 2.5, 1.5, 50, 'low', '{"light_tasks","reading","gentle_focus"}', 'Best available cognitive window'),
('peak', 'productive', 2.0, 2.0, 80, 'high', '{"focus_work","problem_solving","creativity"}', 'Prime cognitive performance'),
('peak', 'performance', 1.5, 2.5, 90, 'high', '{"strategic_work","complex_tasks","peak_performance"}', 'Maximum cognitive output'),
('maintenance', 'recovery', 4.5, 3.0, 45, 'low', '{"routine_tasks","light_activity","maintenance"}', 'Steady, gentle progress'),
('maintenance', 'productive', 4.0, 3.5, 65, 'moderate', '{"steady_work","communication","moderate_activity"}', 'Sustained productive activity'),
('maintenance', 'performance', 4.0, 4.0, 75, 'moderate', '{"project_work","collaboration","training"}', 'Sustained high performance'),
('recovery', 'recovery', 10.0, 2.0, 30, 'low', '{"rest","gentle_stretching","preparation"}', 'Wind-down and restoration'),
('recovery', 'productive', 10.0, 1.5, 50, 'low', '{"reflection","light_prep","relaxation"}', 'Gentle evening routine'),
('recovery', 'performance', 10.0, 1.0, 60, 'low', '{"review","optimization","recovery_protocols"}', 'Structured recovery and preparation');
```

### Existing Tables - No Modifications Required

The implementation will NOT modify any existing tables:
- `user_health_context` - remains unchanged
- `plan_items` - remains unchanged
- `time_blocks` - remains unchanged
- All other existing tables remain untouched

## New Files Structure

### Core Service Files

#### 1. Energy Zones Service
```
services/energy_zones_service.py
├── EnergyZonesService (main class)
├── SleepScheduleAnalyzer
├── ModeDetector
├── ZoneCalculator
└── EnergyZonesCache
```

#### 2. Data Models
```
shared_libs/data_models/energy_zones_models.py
├── EnergyZonesResult
├── EnergyZone
├── SleepSchedule
├── RoutineWithZonesRequest
└── EnergyZoneDefinition
```

#### 3. Utility Classes
```
shared_libs/utils/sleep_pattern_analyzer.py
├── SleepPatternAnalyzer
├── ChronotypeDetector
└── ScheduleInferenceEngine

shared_libs/utils/energy_calculators.py
├── BiomarkerEnergyProcessor
├── ZoneEnergyCalculator
└── ConfidenceScoreCalculator
```

### API Integration Files

#### 4. New API Endpoints (additions to existing files)
```
services/api_gateway/openai_main.py
├── GET /api/v1/energy-zones/{user_id}
├── POST /api/v1/routine-plan-with-zones/{user_id}
└── GET /api/v1/energy-zones/{user_id}/current
```

#### 5. Enhanced Routine Agent (minimal addition)
```
agents/routine_plan_agent.py
└── create_routine_with_zones() [NEW METHOD ONLY]
```

## Implementation Timeline

### Phase 1: Foundation (Week 1)

#### Day 1-2: Database Setup
- [ ] Create new database tables with migrations
- [ ] Insert reference data for energy zone definitions
- [ ] Create indexes for performance optimization
- [ ] Test database connectivity and basic CRUD operations

#### Day 3-4: Core Data Models
- [ ] Implement `energy_zones_models.py` with all data classes
- [ ] Create serialization/deserialization methods
- [ ] Add validation logic for energy zone data
- [ ] Unit tests for data models

#### Day 5-7: Sleep Schedule Analysis
- [ ] Implement `SleepScheduleAnalyzer` class
- [ ] Build sleep pattern inference from biomarker data
- [ ] Create chronotype detection algorithm
- [ ] Test with sample user data

### Phase 2: Energy Zones Calculation (Week 2)

#### Day 8-10: Mode Detection
- [ ] Implement auto-mode detection using existing logic
- [ ] Integrate with current biomarker processing
- [ ] Create confidence scoring for mode detection
- [ ] Test mode detection accuracy

#### Day 11-12: Zone Calculation Engine
- [ ] Implement `ZoneCalculator` with personalized algorithms
- [ ] Build energy level calculation based on biomarkers
- [ ] Create zone timing adjustment logic
- [ ] Integrate with zone definitions table

#### Day 13-14: Caching and Persistence
- [ ] Implement `EnergyZonesCache` for performance
- [ ] Add cache invalidation logic
- [ ] Create data persistence layer
- [ ] Performance testing and optimization

### Phase 3: API Integration (Week 3)

#### Day 15-16: Core Service Implementation
- [ ] Implement main `EnergyZonesService` class
- [ ] Integrate all components (sleep analysis, mode detection, zone calculation)
- [ ] Add error handling and logging
- [ ] Unit tests for service methods

#### Day 17-18: API Endpoints
- [ ] Add new endpoints to `openai_main.py`
- [ ] Implement request/response handling
- [ ] Add input validation and error responses
- [ ] API documentation and testing

#### Day 19-21: Routine Planning Integration
- [ ] Add `create_routine_with_zones()` method to routine agent
- [ ] Test integration with existing routine planning
- [ ] Ensure no breaking changes to existing functionality
- [ ] End-to-end testing

## Testing Strategy

### Unit Tests
- [ ] Data model validation and serialization
- [ ] Sleep schedule inference algorithms
- [ ] Mode detection logic
- [ ] Zone calculation accuracy
- [ ] Caching functionality

### Integration Tests
- [ ] Database operations and migrations
- [ ] API endpoint functionality
- [ ] Service integration with existing components
- [ ] Error handling and edge cases

### End-to-End Tests
- [ ] Complete energy zones calculation flow
- [ ] Routine planning with energy zones
- [ ] Performance under load
- [ ] Data consistency and caching

## API Usage Examples

### 1. Get Energy Zones (Standalone)
```bash
GET /api/v1/energy-zones/user123

Response:
{
  "success": true,
  "data": {
    "user_id": "user123",
    "detected_mode": "productive",
    "confidence_score": 0.82,
    "sleep_schedule": {
      "estimated_wake_time": "07:30:00",
      "estimated_bedtime": "22:30:00",
      "chronotype": "morning_lark"
    },
    "energy_zones": [
      {
        "zone_name": "foundation",
        "start_time": "07:30:00",
        "end_time": "09:00:00",
        "energy_level": 60,
        "recommended_intensity": "moderate",
        "optimal_activities": ["light_exercise", "planning", "nutrition"]
      },
      {
        "zone_name": "peak",
        "start_time": "09:30:00",
        "end_time": "11:30:00",
        "energy_level": 80,
        "recommended_intensity": "high",
        "optimal_activities": ["focus_work", "problem_solving", "creativity"]
      }
    ]
  }
}
```

### 2. Generate Routine with Energy Zones
```bash
POST /api/v1/routine-plan-with-zones/user123
Body: {"archetype": "Foundation Builder"}

Response:
{
  "success": true,
  "data": {
    "routine_plan": "1. **Personal Foundation Time (7:30-9:00 AM):** Foundation Setting and Energy Building...",
    "energy_zones_used": [...],
    "detected_mode": "productive",
    "archetype": "Foundation Builder"
  }
}
```

### 3. Get Current Energy Zone
```bash
GET /api/v1/energy-zones/user123/current

Response:
{
  "success": true,
  "data": {
    "current_zone": {
      "zone_name": "peak",
      "energy_level": 80,
      "time_remaining_minutes": 45,
      "recommended_action": "This is your optimal focus time - tackle challenging work now"
    }
  }
}
```

## Performance Considerations

### Caching Strategy
- Energy zones cached for 24 hours per user
- Sleep schedule inferences cached for 7 days
- Mode detection results cached for 4 hours
- Automatic cache invalidation when new health data arrives

### Database Optimization
- Indexes on frequently queried columns
- JSONB for flexible zone data storage
- Partitioning by date for large datasets
- Connection pooling for concurrent requests

### API Performance
- Response time target: < 500ms for zone calculation
- Concurrent user support: 100+ simultaneous requests
- Graceful degradation when external services are slow
- Rate limiting to prevent abuse

## Monitoring and Alerting

### Metrics to Track
- Energy zone calculation accuracy
- API response times
- Cache hit/miss ratios
- Mode detection confidence scores
- User adoption of energy zones feature

### Alerts
- High error rates in zone calculation
- Cache performance degradation
- Database connection issues
- Unusual patterns in user data

## Migration Strategy

### Rollout Plan
1. **Week 1**: Deploy database changes and core service (read-only mode)
2. **Week 2**: Enable energy zones calculation API (beta users)
3. **Week 3**: Enable routine planning with zones (gradual rollout)
4. **Week 4**: Full production deployment with monitoring

### Rollback Plan
- All new functionality is additive (no existing code changes)
- Can disable new endpoints without affecting existing functionality
- Database tables can be dropped without impacting current operations
- Zero-downtime rollback capability

## Success Metrics

### Technical Success
- [ ] 99.5% uptime for energy zones API
- [ ] < 500ms average response time
- [ ] 95%+ cache hit ratio
- [ ] Zero breaking changes to existing functionality

### User Experience Success
- [ ] Energy zones calculation accuracy > 80%
- [ ] User satisfaction with personalized timing
- [ ] Increased engagement with routine planning
- [ ] Positive feedback on zone-based schedules

## Risk Mitigation

### Technical Risks
- **Database performance**: Mitigated by proper indexing and caching
- **API reliability**: Mitigated by error handling and fallback mechanisms
- **Integration complexity**: Mitigated by standalone service design
- **Data quality**: Mitigated by confidence scoring and validation

### Business Risks
- **User adoption**: Mitigated by gradual rollout and user feedback
- **Accuracy concerns**: Mitigated by confidence scores and transparency
- **Performance impact**: Mitigated by caching and optimization
- **Maintenance overhead**: Mitigated by clean architecture and documentation

This implementation plan provides a complete standalone Energy Zones Service while preserving all existing functionality and ensuring a smooth integration path.