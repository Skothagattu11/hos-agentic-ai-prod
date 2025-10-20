# Archetype-Specific Analysis Tracking Implementation Plan

**Document Version**: 1.0  
**Created**: 2025-08-19  
**Author**: Development Team  
**Status**: Planning Phase

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current Situation](#current-situation)
3. [Expected Outcome](#expected-outcome)
4. [Technical Implementation](#technical-implementation)
5. [Detailed Implementation Steps](#detailed-implementation-steps)
6. [Database Changes](#database-changes)
7. [Testing Strategy](#testing-strategy)
8. [Migration Plan](#migration-plan)
9. [Risk Assessment](#risk-assessment)
10. [Timeline & Resources](#timeline--resources)

---

## Executive Summary

This document outlines the implementation of archetype-specific analysis tracking for the HolisticOS health analysis system. The enhancement will provide each user archetype with independent analysis windows, improving analysis quality while maintaining system efficiency.

### Key Benefits:
- **Improved Analysis Quality**: New archetypes get comprehensive 7-day data windows
- **Maintained Efficiency**: Existing archetypes continue using incremental data
- **Perfect Archetype Isolation**: Each archetype maintains independent analysis history
- **Backward Compatibility**: Seamless integration with existing system

---

## Current Situation

### System Behavior (As-Is)
```
User Profile Table: 
- user_id: "user123"
- last_analysis_at: "2025-08-17T10:00:00Z" (global across all archetypes)

Analysis Flow:
1. User requests "Peak Performer" analysis
2. System checks global last_analysis_at: 2 days ago
3. Fetches data from 2 days ago to now
4. Generates analysis based on 2-day window

Problem Scenario:
- User had "Foundation Builder" analysis 2 days ago
- User switches to "Peak Performer" (incompatible archetype)
- System only uses 2 days of data instead of comprehensive 7-day window
- Results in suboptimal behavior analysis for new archetype
```

### Technical Limitations
- **Single Analysis Timestamp**: One `last_analysis_at` per user regardless of archetype
- **Suboptimal Data Windows**: New archetypes don't get full context
- **Cross-Archetype Dependencies**: Analysis decisions affected by unrelated archetypes

### Impact on User Experience
- **Reduced Analysis Quality**: Insufficient data for new archetype analysis
- **Inconsistent Recommendations**: Varying quality based on archetype switching history
- **Suboptimal Personalization**: New archetypes lack comprehensive baseline data

---

## Expected Outcome

### Target System Behavior (To-Be)
```
Enhanced Tracking:
- user_id: "user123" 
- archetype_analysis_dates: {
    "Peak Performer": "2025-08-15T14:30:00Z",
    "Foundation Builder": "2025-08-17T10:00:00Z",
    "Resilience Rebuilder": null (never analyzed)
  }

Improved Analysis Flow:
1. User requests "Peak Performer" analysis
2. System checks Peak Performer last_analysis_at: 4 days ago
3. Fetches data from 4 days ago to now (archetype-specific window)
4. Generates high-quality analysis with relevant historical context

New Archetype Flow:
1. User requests "Resilience Rebuilder" analysis (first time)
2. System detects no previous analysis for this archetype
3. Fetches comprehensive 7-day data window
4. Provides optimal baseline analysis for new archetype
```

### Success Metrics
- **Analysis Quality**: Each archetype gets optimal data window
- **System Efficiency**: Maintains incremental analysis for existing archetypes
- **User Satisfaction**: Consistent high-quality recommendations regardless of archetype history
- **Performance**: No degradation in response times or system throughput

---

## Technical Implementation

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Client Request                           │
│              (user_id + archetype)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            OnDemandAnalysisService                          │
│     Enhanced with Archetype-Specific Logic                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│          ArchetypeAnalysisTracker                           │
│              (New Service)                                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  get_last_analysis_date(user_id, archetype)           ││
│  │  update_last_analysis_date(user_id, archetype, date)  ││
│  │  get_archetype_history(user_id)                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│         archetype_analysis_tracking Table                  │
│              (New Database Table)                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  user_id | archetype | last_analysis_at | analysis_count││
│  │  user123 | Peak Perf | 2025-08-15       | 3             ││
│  │  user123 | Foundation| 2025-08-17       | 1             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities
1. **ArchetypeAnalysisTracker**: Manages archetype-specific timestamps
2. **OnDemandAnalysisService**: Enhanced with archetype-aware logic
3. **Database Layer**: New table for archetype tracking with efficient indexing
4. **Migration Scripts**: Populate existing data and maintain compatibility

---

## Detailed Implementation Steps

### Phase 1: Database Schema Implementation
**Duration**: 1-2 hours

#### Step 1.1: Create New Table
```sql
-- File: supabase/migrations/create_archetype_analysis_tracking.sql
CREATE TABLE archetype_analysis_tracking (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    archetype TEXT NOT NULL,
    last_analysis_at TIMESTAMPTZ NOT NULL,
    analysis_count INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_user_archetype UNIQUE(user_id, archetype)
);

-- Performance indexes
CREATE INDEX idx_archetype_tracking_user_archetype 
ON archetype_analysis_tracking(user_id, archetype);

CREATE INDEX idx_archetype_tracking_last_analysis 
ON archetype_analysis_tracking(user_id, last_analysis_at DESC);
```

#### Step 1.2: Add Table Comments
```sql
COMMENT ON TABLE archetype_analysis_tracking IS 
'Tracks last analysis date for each user-archetype combination to enable archetype-specific data windows';

COMMENT ON COLUMN archetype_analysis_tracking.user_id IS 
'User identifier - references profiles.id';

COMMENT ON COLUMN archetype_analysis_tracking.archetype IS 
'Archetype name (Peak Performer, Foundation Builder, etc.)';

COMMENT ON COLUMN archetype_analysis_tracking.last_analysis_at IS 
'Timestamp of most recent behavior analysis for this user-archetype combination';

COMMENT ON COLUMN archetype_analysis_tracking.analysis_count IS 
'Total number of analyses performed for this user-archetype combination';
```

### Phase 2: Service Layer Implementation
**Duration**: 2-3 hours

#### Step 2.1: Create ArchetypeAnalysisTracker Service
```python
# File: services/archetype_analysis_tracker.py
from typing import Optional, Dict
from datetime import datetime
import logging

class ArchetypeAnalysisTracker:
    """
    Service for managing archetype-specific analysis timestamps
    Enables each archetype to maintain independent analysis windows
    """
    
    def __init__(self):
        self.db = None
        
    async def initialize(self):
        """Initialize database connection"""
        # Implementation details...
        
    async def get_last_analysis_date(self, user_id: str, archetype: str) -> Optional[datetime]:
        """
        Get the last analysis date for specific user + archetype combination
        
        Args:
            user_id: User identifier
            archetype: Archetype name (e.g., "Peak Performer")
            
        Returns:
            datetime: Last analysis date or None if never analyzed
        """
        # Implementation details...
        
    async def update_last_analysis_date(self, user_id: str, archetype: str, 
                                      analysis_date: datetime = None):
        """
        Update last analysis date for specific archetype
        
        Args:
            user_id: User identifier  
            archetype: Archetype name
            analysis_date: Analysis timestamp (defaults to now)
        """
        # Implementation details...
        
    async def get_archetype_history(self, user_id: str) -> Dict[str, datetime]:
        """
        Get analysis dates for all archetypes for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict mapping archetype names to last analysis dates
        """
        # Implementation details...
        
    async def cleanup(self):
        """Clean up resources"""
        # Implementation details...
```

#### Step 2.2: Enhance OnDemandAnalysisService
```python
# File: services/ondemand_analysis_service.py (modifications)

async def should_run_analysis(self, user_id: str, force_refresh: bool = False, 
                            requested_archetype: str = None):
    """
    Enhanced analysis decision with archetype-specific timestamp logic
    """
    # Existing logic...
    
    # NEW: Archetype-specific timestamp resolution
    if requested_archetype:
        archetype_tracker = ArchetypeAnalysisTracker()
        await archetype_tracker.initialize()
        
        archetype_last_analysis = await archetype_tracker.get_last_analysis_date(
            user_id, requested_archetype
        )
        
        if archetype_last_analysis:
            # Use archetype-specific timestamp
            metadata["fixed_timestamp"] = archetype_last_analysis
            metadata["analysis_mode"] = "follow_up"
            metadata["days_to_fetch"] = self._calculate_days_since(archetype_last_analysis)
            metadata["data_source"] = "archetype_specific"
        else:
            # First time for this archetype - use comprehensive 7-day window
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            metadata["fixed_timestamp"] = seven_days_ago
            metadata["analysis_mode"] = "initial"
            metadata["days_to_fetch"] = 7
            metadata["data_source"] = "comprehensive_baseline"
            metadata["reason"] = f"First analysis for archetype '{requested_archetype}' - using 7-day comprehensive window"
        
        await archetype_tracker.cleanup()
    
    # Continue with existing threshold logic...
```

### Phase 3: Integration Layer Updates
**Duration**: 1-2 hours

#### Step 3.1: Update Analysis Storage
```python
# File: services/agents/memory/holistic_memory_service.py (modifications)

async def store_analysis_result(self, user_id: str, analysis_type: str, 
                              analysis_result: Dict[str, Any], archetype_used: str = None):
    """
    Enhanced to update archetype-specific timestamps
    """
    # Existing storage logic...
    
    # NEW: Update archetype tracking
    if archetype_used and analysis_type == "behavior_analysis":
        try:
            archetype_tracker = ArchetypeAnalysisTracker()
            await archetype_tracker.initialize()
            await archetype_tracker.update_last_analysis_date(
                user_id, archetype_used, datetime.now(timezone.utc)
            )
            await archetype_tracker.cleanup()
        except Exception as e:
            logger.warning(f"Failed to update archetype tracking for {user_id}: {e}")
            # Don't fail the main operation if archetype tracking fails
```

#### Step 3.2: Update Data Fetching Logic
```python
# File: services/user_data_service.py (modifications)

async def get_analysis_data(self, user_id: str, since_timestamp: datetime = None, 
                          archetype: str = None):
    """
    Enhanced with archetype-aware data fetching
    """
    # Use provided timestamp or determine archetype-specific timestamp
    if not since_timestamp and archetype:
        archetype_tracker = ArchetypeAnalysisTracker()
        await archetype_tracker.initialize()
        
        since_timestamp = await archetype_tracker.get_last_analysis_date(user_id, archetype)
        if not since_timestamp:
            # Default to 7 days for new archetype
            since_timestamp = datetime.now(timezone.utc) - timedelta(days=7)
            
        await archetype_tracker.cleanup()
    elif not since_timestamp:
        # Fallback to existing logic
        since_timestamp = await self._get_global_last_analysis_timestamp(user_id)
    
    # Continue with existing data fetching logic...
```

### Phase 4: Migration Implementation
**Duration**: 1 hour

#### Step 4.1: Data Migration Script
```sql
-- File: supabase/migrations/populate_archetype_tracking.sql
-- Populate archetype_analysis_tracking from existing holistic_analysis_results

INSERT INTO archetype_analysis_tracking (user_id, archetype, last_analysis_at, analysis_count)
SELECT 
    user_id,
    archetype,
    MAX(created_at) as last_analysis_at,
    COUNT(*) as analysis_count
FROM holistic_analysis_results 
WHERE analysis_type = 'behavior_analysis'
  AND archetype IS NOT NULL
  AND created_at >= NOW() - INTERVAL '90 days'  -- Only migrate recent data
GROUP BY user_id, archetype
ON CONFLICT (user_id, archetype) DO UPDATE SET
    last_analysis_at = GREATEST(
        archetype_analysis_tracking.last_analysis_at, 
        EXCLUDED.last_analysis_at
    ),
    analysis_count = archetype_analysis_tracking.analysis_count + EXCLUDED.analysis_count,
    updated_at = NOW();

-- Add validation query
SELECT 
    COUNT(*) as total_tracking_records,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT archetype) as unique_archetypes
FROM archetype_analysis_tracking;
```

### Phase 5: Error Handling & Fallback
**Duration**: 30 minutes

#### Step 5.1: Implement Graceful Degradation
```python
# File: services/archetype_analysis_tracker.py

async def get_last_analysis_date_with_fallback(self, user_id: str, archetype: str = None):
    """
    Get archetype-specific timestamp with fallback to global timestamp
    Ensures system continues working even if archetype tracking fails
    """
    try:
        if archetype:
            archetype_timestamp = await self.get_last_analysis_date(user_id, archetype)
            if archetype_timestamp:
                return archetype_timestamp, "archetype_specific"
        
        # Fallback to global profiles.last_analysis_at
        global_timestamp = await self._get_global_last_analysis_timestamp(user_id)
        return global_timestamp, "global_fallback"
        
    except Exception as e:
        logger.error(f"Archetype tracking failed for {user_id}: {e}")
        # Emergency fallback to 7-day window
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        return seven_days_ago, "emergency_fallback"
```

---

## Database Changes

### New Tables
1. **archetype_analysis_tracking**
   - Primary storage for archetype-specific timestamps
   - Indexed for fast user + archetype lookups
   - Includes analysis count for future analytics

### Performance Considerations
- **Minimal Impact**: Single additional table with efficient indexes
- **Query Performance**: O(1) lookup for user + archetype combination
- **Storage Overhead**: ~50 bytes per user-archetype combination
- **Expected Size**: 10,000 users × 3 avg archetypes = 30,000 rows (~1.5MB)

### Backup & Recovery
- Table included in standard backup procedures
- Migration scripts are reversible
- Data validation queries included

---

## Testing Strategy

### Unit Tests
```python
# Test file: tests/unit/test_archetype_analysis_tracker.py

class TestArchetypeAnalysisTracker:
    async def test_new_archetype_gets_7_day_window(self):
        """Test that new archetypes get comprehensive 7-day data"""
        
    async def test_existing_archetype_gets_incremental_data(self):
        """Test that existing archetypes get incremental data since last analysis"""
        
    async def test_archetype_switch_independence(self):
        """Test that switching archetypes doesn't affect other archetype timestamps"""
        
    async def test_fallback_behavior(self):
        """Test graceful degradation when archetype tracking fails"""
```

### Integration Tests
```python
# Test file: tests/integration/test_archetype_aware_analysis.py

class TestArchetypeAwareAnalysis:
    async def test_end_to_end_new_archetype_flow(self):
        """Test complete flow for new archetype analysis"""
        
    async def test_end_to_end_existing_archetype_flow(self):
        """Test complete flow for existing archetype analysis"""
        
    async def test_archetype_switching_scenarios(self):
        """Test various archetype switching patterns"""
```

### Performance Tests
- **Load Testing**: 100 concurrent archetype switches
- **Database Performance**: Query response time under load
- **Memory Usage**: Service memory consumption monitoring

### Manual Test Scenarios
1. **New User Journey**
   - User creates account → Selects "Peak Performer" → Should use 7-day window
   
2. **Archetype Switching**
   - User has "Foundation Builder" analysis → Switches to "Peak Performer" → Should use 7-day window
   - Later returns to "Foundation Builder" → Should use incremental from previous Foundation Builder analysis
   
3. **Error Scenarios**
   - Database connection failure → Should fall back to global timestamp
   - Invalid archetype → Should handle gracefully

---

## Migration Plan

### Pre-Migration Checklist
- [ ] Database backup completed
- [ ] Migration scripts validated on staging
- [ ] Service deployments ready
- [ ] Rollback procedures documented
- [ ] Monitoring alerts configured

### Migration Steps
1. **Deploy Database Schema** (5 minutes)
   - Create archetype_analysis_tracking table
   - Add indexes and constraints
   
2. **Populate Historical Data** (10 minutes)
   - Run data migration script
   - Validate data integrity
   
3. **Deploy Service Updates** (15 minutes)
   - Deploy ArchetypeAnalysisTracker service
   - Deploy enhanced OnDemandAnalysisService
   - Deploy integration layer updates
   
4. **Validation** (10 minutes)
   - Test archetype switching scenarios
   - Verify fallback mechanisms
   - Monitor system performance

### Post-Migration Verification
- [ ] All archetype switching scenarios working
- [ ] Performance metrics within acceptable range
- [ ] Error rates normal
- [ ] Data integrity maintained

### Rollback Plan
If issues arise:
1. **Immediate**: Disable archetype-specific logic (feature flag)
2. **Service Rollback**: Deploy previous service versions
3. **Database Rollback**: Drop archetype_analysis_tracking table
4. **Full Recovery**: Restore from pre-migration backup

---

## Risk Assessment

### High Risk
- **Data Loss**: Migration script corruption
  - **Mitigation**: Comprehensive testing, database backups, rollback procedures
  
- **Performance Degradation**: New queries slow down system
  - **Mitigation**: Database indexing, performance testing, query optimization

### Medium Risk
- **Integration Complexity**: Changes affect multiple services
  - **Mitigation**: Phased deployment, comprehensive testing, fallback mechanisms
  
- **User Experience Disruption**: Temporary inconsistent behavior during migration
  - **Mitigation**: Maintenance window scheduling, gradual rollout

### Low Risk
- **Code Complexity**: Additional service layer
  - **Mitigation**: Code reviews, documentation, unit tests
  
- **Storage Overhead**: Additional database table
  - **Mitigation**: Efficient schema design, regular cleanup procedures

---

## Timeline & Resources

### Development Timeline
- **Phase 1** (Database): 1-2 hours
- **Phase 2** (Services): 2-3 hours  
- **Phase 3** (Integration): 1-2 hours
- **Phase 4** (Migration): 1 hour
- **Phase 5** (Error Handling): 30 minutes
- **Testing**: 2-3 hours
- **Documentation**: 1 hour

**Total Estimated Time**: 8-12 hours

### Resource Requirements
- **Developer**: 1 senior developer
- **Database**: Staging and production access
- **Testing**: Access to test user accounts
- **Deployment**: CI/CD pipeline access

### Success Criteria
- [ ] New archetypes get 7-day comprehensive data windows
- [ ] Existing archetypes maintain incremental analysis efficiency
- [ ] System performance remains stable
- [ ] All existing functionality continues working
- [ ] Zero data loss during migration
- [ ] Comprehensive test coverage achieved

---

## Conclusion

This implementation will significantly improve the HolisticOS system by providing archetype-specific analysis tracking. Each archetype will receive optimal data windows - comprehensive baselines for new archetypes and efficient incremental updates for existing ones.

The solution maintains backward compatibility, includes comprehensive error handling, and can be deployed with minimal risk through careful migration procedures.

**Next Steps**:
1. Review and approve this implementation plan
2. Set up development environment and testing data
3. Begin Phase 1 implementation (Database Schema)
4. Proceed through phases with testing at each step
5. Coordinate production deployment during maintenance window

---

**Document Approval**:
- [ ] Technical Review Complete
- [ ] Business Requirements Verified  
- [ ] Timeline Approved
- [ ] Resource Allocation Confirmed
- [ ] Risk Assessment Accepted
- [ ] Ready for Implementation