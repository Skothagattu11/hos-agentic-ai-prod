# Race Condition Fix Plan: Behavior Analysis & Routine Creation

## Problem Statement

Currently, the system has a race condition between standalone API calls that creates duplicate analyses and inconsistent database state:

### Issues Identified:
1. **Standalone Behavior Analysis** creates analysis but doesn't properly update `archetype_analysis_tracking`
2. **Routine/Nutrition APIs** don't check for recent analyses before creating new ones
3. **Threshold checking** happens from old timestamps instead of recent analyses
4. **Database coordination** between different tables is inconsistent

### Test Case Example:
```
10:00:00 - Behavior Analysis API → Creates analysis ✅
10:00:03 - Routine Generation API → Creates DUPLICATE analysis ❌ (should reuse)
```

## Root Cause Analysis

### Current Flow (Problematic):
```
Behavior Analysis API
├── Creates analysis in holistic_analysis_results ✅
├── Updates archetype_analysis_tracking (async) ⚠️
└── Returns immediately

Routine Generation API (3 seconds later)
├── Checks archetype_analysis_tracking ❌ (may not be updated yet)
├── Finds no recent entry or old entry
├── Checks threshold from old timestamp
└── Creates duplicate analysis
```

### Database Coordination Issues:
1. **Async Updates**: `archetype_analysis_tracking` updated asynchronously
2. **Race Condition**: Routine API checks before behavior API completes updates
3. **Multiple Sources of Truth**: Different tables updated at different times
4. **No Transaction Boundaries**: Updates not atomic

## Solution Architecture

### Core Principles:
1. **Single Source of Truth**: Use `holistic_analysis_results` for recent analysis checks
2. **Coordinated Updates**: Ensure all database updates complete before returning
3. **Shared Analysis Logic**: Centralize analysis retrieval and creation
4. **Proper Threshold Tracking**: Update archetype tracking synchronously

## Implementation Plan

### Phase 1: Fix Database Coordination

#### 1.1 Synchronous Archetype Tracking Updates
```python
# services/agents/memory/holistic_memory_service.py
async def store_analysis_result(self, user_id: str, analysis_type: str, 
                              analysis_result: Dict[str, Any], archetype_used: str = None, 
                              analysis_trigger: str = "scheduled") -> str:
    """Store complete analysis with SYNCHRONOUS archetype tracking"""
    try:
        db = await self._ensure_db_connection()
        
        # Start transaction for atomic updates
        async with db.transaction():
            # Step 1: Store analysis result
            insert_query = """
                INSERT INTO holistic_analysis_results (
                    user_id, analysis_type, archetype, analysis_result, 
                    input_summary, agent_id, analysis_date, analysis_trigger
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_DATE, $7)
                ON CONFLICT (user_id, analysis_type, analysis_date, archetype, analysis_trigger) 
                DO UPDATE SET
                    analysis_result = EXCLUDED.analysis_result,
                    input_summary = EXCLUDED.input_summary,
                    created_at = NOW()
                RETURNING id
            """
            
            result = await db.fetchrow(insert_query, user_id, analysis_type, archetype_used, 
                                     json.dumps(analysis_result), json.dumps(input_summary), 
                                     'memory_service', analysis_trigger)
            
            if not result:
                raise Exception("Failed to store analysis result")
                
            analysis_id = str(result['id'])
            
            # Step 2: SYNCHRONOUSLY update archetype tracking
            if archetype_used and analysis_type == "behavior_analysis":
                await self._update_archetype_tracking_sync(db, user_id, archetype_used)
            
            # Step 3: Extract insights (within transaction)
            try:
                from services.insights_extraction_service import insights_service
                if analysis_id:
                    await insights_service.extract_and_store_insights(
                        analysis_result=analysis_result,
                        analysis_type=analysis_type,
                        user_id=user_id,
                        archetype=archetype_used or "Foundation Builder",
                        source_analysis_id=analysis_id
                    )
            except Exception as e:
                logger.warning(f"Failed to extract insights: {str(e)}")
                # Don't fail transaction for insights errors
            
            return analysis_id
            
    except Exception as e:
        logger.error(f"[ANALYSIS_RESULTS_ERROR] Failed to store for {user_id}: {e}")
        return ""

async def _update_archetype_tracking_sync(self, db, user_id: str, archetype: str):
    """Synchronously update archetype tracking within transaction"""
    try:
        # UPSERT archetype tracking entry
        tracking_query = """
            INSERT INTO archetype_analysis_tracking (
                user_id, archetype, last_analysis_at, analysis_count
            ) VALUES ($1, $2, NOW(), 1)
            ON CONFLICT (user_id, archetype) 
            DO UPDATE SET
                last_analysis_at = NOW(),
                analysis_count = archetype_analysis_tracking.analysis_count + 1,
                updated_at = NOW()
        """
        
        await db.execute(tracking_query, user_id, archetype)
        logger.info(f"[MEMORY_SERVICE] Updated archetype tracking: {user_id} + {archetype}")
        
    except Exception as e:
        logger.error(f"[MEMORY_SERVICE] Archetype tracking error for {user_id}: {e}")
        raise  # Re-raise to fail the transaction
```

#### 1.2 Recent Analysis Checker Service
```python
# services/recent_analysis_checker.py
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

class RecentAnalysisChecker:
    """Service to check for recent analyses and prevent duplicates"""
    
    def __init__(self):
        from services.agents.memory.holistic_memory_service import HolisticMemoryService
        self.memory_service = HolisticMemoryService()
    
    async def get_recent_behavior_analysis(self, user_id: str, archetype: str, 
                                         minutes_threshold: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get recent behavior analysis if exists within threshold
        
        Args:
            user_id: User identifier
            archetype: Archetype to check for
            minutes_threshold: Time window to consider "recent"
            
        Returns:
            Recent analysis result or None
        """
        try:
            # Get recent analysis history
            recent_analyses = await self.memory_service.get_analysis_history(
                user_id=user_id,
                analysis_type="behavior_analysis", 
                archetype=archetype,
                limit=1
            )
            
            if not recent_analyses:
                return None
                
            latest_analysis = recent_analyses[0]
            
            # Check if analysis is within time threshold
            age_minutes = (datetime.now(timezone.utc) - latest_analysis.created_at).total_seconds() / 60
            
            if age_minutes <= minutes_threshold:
                logger.info(f"[RECENT_ANALYSIS] Found recent analysis ({age_minutes:.1f} min old) for {user_id[:8]}... + {archetype}")
                return latest_analysis.analysis_result
            
            logger.debug(f"[RECENT_ANALYSIS] Analysis too old ({age_minutes:.1f} min) for {user_id[:8]}... + {archetype}")
            return None
            
        except Exception as e:
            logger.error(f"[RECENT_ANALYSIS_ERROR] Failed to check for {user_id}: {e}")
            return None
    
    async def should_create_new_analysis(self, user_id: str, archetype: str, 
                                       force_refresh: bool = False) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Determine if new analysis should be created or recent one reused
        
        Returns:
            (should_create_new: bool, existing_analysis: Optional[dict])
        """
        if force_refresh:
            return True, None
            
        # Check for recent analysis first
        recent_analysis = await self.get_recent_behavior_analysis(user_id, archetype)
        
        if recent_analysis:
            return False, recent_analysis
        
        # No recent analysis - check if threshold exceeded
        from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
        ondemand_service = await get_ondemand_service()
        decision, metadata = await ondemand_service.should_run_analysis(user_id, False, archetype)
        
        should_create = (decision == AnalysisDecision.FRESH_ANALYSIS)
        
        logger.info(f"[RECENT_ANALYSIS] Decision for {user_id[:8]}... + {archetype}: {'CREATE' if should_create else 'SKIP'}")
        
        return should_create, None

# Global instance
recent_analysis_checker = RecentAnalysisChecker()
```

### Phase 2: Fix Shared Analysis Logic

#### 2.1 Enhanced Shared Behavior Analysis
```python
# services/api_gateway/openai_main.py - Updated function
async def get_or_create_shared_behavior_analysis(user_id: str, archetype: str, force_refresh: bool = False) -> dict:
    """
    Enhanced shared behavior analysis with proper coordination
    Prevents duplicate analyses through recent analysis checking
    """
    try:
        from services.recent_analysis_checker import recent_analysis_checker
        
        # Step 1: Check if we should create new analysis or reuse recent one
        should_create, existing_analysis = await recent_analysis_checker.should_create_new_analysis(
            user_id, archetype, force_refresh
        )
        
        if not should_create and existing_analysis:
            logger.info(f"[SHARED_ANALYSIS] Reusing recent behavior analysis for {user_id[:8]}... + {archetype}")
            return existing_analysis
        
        # Step 2: Use enhanced request coordination to prevent duplicates
        from services.enhanced_request_deduplication import enhanced_deduplicator
        
        should_process, cached_result = await enhanced_deduplicator.coordinate_request(
            user_id, archetype, "behavior_analysis"
        )
        
        if not should_process and cached_result:
            logger.info(f"[SHARED_ANALYSIS] Using coordinated cache for {user_id[:8]}... + {archetype}")
            return cached_result
        
        # Step 3: Create fresh analysis
        logger.info(f"[SHARED_ANALYSIS] Creating fresh behavior analysis for {user_id[:8]}... + {archetype}")
        
        try:
            # Get analysis decision for trigger type
            from services.ondemand_analysis_service import get_ondemand_service, AnalysisDecision
            ondemand_service = await get_ondemand_service()
            decision, metadata = await ondemand_service.should_run_analysis(user_id, force_refresh, archetype)
            
            # Determine analysis trigger with timestamp uniqueness
            if decision == AnalysisDecision.FRESH_ANALYSIS:
                from datetime import datetime
                timestamp = datetime.now().strftime("%H%M%S")
                analysis_trigger = f"threshold_exceeded_{timestamp}"
            else:
                analysis_trigger = "scheduled"
            
            # Run fresh analysis
            fresh_analysis = await run_memory_enhanced_behavior_analysis(user_id, archetype)
            
            if fresh_analysis and fresh_analysis.get("status") == "success":
                # Store with proper trigger and synchronous archetype tracking
                from services.agents.memory.holistic_memory_service import HolisticMemoryService
                memory_service = HolisticMemoryService()
                
                await memory_service.store_analysis_result(
                    user_id=user_id,
                    analysis_type="behavior_analysis",
                    analysis_result=fresh_analysis,
                    archetype_used=archetype,
                    analysis_trigger=analysis_trigger
                )
                
                # Complete coordination (cache result)
                enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", fresh_analysis)
                
                logger.info(f"[SHARED_ANALYSIS] Fresh analysis completed and stored for {user_id[:8]}... + {archetype}")
                return fresh_analysis
            else:
                # Analysis failed - try cached fallback
                logger.warning(f"[SHARED_ANALYSIS] Fresh analysis failed, trying cached for {user_id[:8]}...")
                cached_fallback = await ondemand_service.get_cached_behavior_analysis(user_id, archetype)
                
                if cached_fallback:
                    enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", cached_fallback)
                    return cached_fallback
                else:
                    raise Exception("Both fresh and cached analysis failed")
                    
        except Exception as e:
            logger.error(f"[SHARED_ANALYSIS_ERROR] Failed to create analysis for {user_id}: {e}")
            # Mark coordination as failed
            enhanced_deduplicator.complete_request(user_id, archetype, "behavior_analysis", {"error": str(e)})
            raise
            
    except Exception as e:
        logger.error(f"[SHARED_ANALYSIS_ERROR] Coordination failed for {user_id}: {e}")
        # Return empty analysis as fallback
        return {
            "status": "error",
            "error": str(e),
            "archetype": archetype,
            "timestamp": datetime.now().isoformat()
        }
```

#### 2.2 Update Routine/Nutrition Endpoints
```python
# services/api_gateway/openai_main.py - Updated endpoints

@app.post("/api/user/{user_id}/routine/generate", response_model=RoutinePlanResponse)
async def generate_fresh_routine_plan(user_id: str, request: PlanGenerationRequest, http_request: Request):
    """Generate routine plan with enhanced coordination"""
    
    # Enhanced coordination instead of simple deduplication
    from services.enhanced_request_deduplication import enhanced_deduplicator
    
    archetype = request.archetype or "Foundation Builder"
    
    try:
        # Step 1: Coordinate routine request (prevents duplicates, waits for in-progress)
        should_process, cached_result = await enhanced_deduplicator.coordinate_request(
            user_id, archetype, "routine"
        )
        
        if not should_process and cached_result:
            logger.info(f"[ROUTINE_GENERATE] Using coordinated result for {user_id[:8]}...")
            return RoutinePlanResponse(
                status="success",
                user_id=user_id,
                routine_plan=cached_result,
                metadata={"source": "coordinated_cache"}
            )
        
        # Step 2: Get shared behavior analysis (with proper coordination)
        force_refresh = request.preferences.get('force_refresh', False) if request.preferences else False
        behavior_analysis = await get_or_create_shared_behavior_analysis(user_id, archetype, force_refresh)
        
        if not behavior_analysis or behavior_analysis.get("status") == "error":
            enhanced_deduplicator.complete_request(user_id, archetype, "routine", {"error": "Behavior analysis failed"})
            raise HTTPException(status_code=500, detail="Failed to get behavior analysis")
        
        # Step 3: Generate routine plan
        routine_result = await run_memory_enhanced_routine_generation(user_id, archetype, behavior_analysis)
        
        # Step 4: Store result and complete coordination
        enhanced_deduplicator.complete_request(user_id, archetype, "routine", routine_result)
        
        return RoutinePlanResponse(
            status="success",
            user_id=user_id,
            routine_plan=routine_result,
            metadata={"source": "fresh_generation"}
        )
        
    except Exception as e:
        # Complete coordination with error
        enhanced_deduplicator.complete_request(user_id, archetype, "routine", {"error": str(e)})
        logger.error(f"[ROUTINE_GENERATE_ERROR] Failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Routine generation failed: {str(e)}")
```

### Phase 3: Testing & Validation

#### 3.1 Integration Test Suite
```python
# test_race_condition_fix.py
import asyncio
import pytest
from datetime import datetime

class TestRaceConditionFix:
    """Test suite for race condition fixes"""
    
    async def test_standalone_behavior_analysis_updates_tracking(self):
        """Test that standalone behavior analysis updates archetype tracking"""
        user_id = "test_user_race_condition"
        archetype = "Peak Performer"
        
        # Clear any existing data
        await self.cleanup_test_data(user_id, archetype)
        
        # Call behavior analysis API
        response = await self.call_behavior_analysis_api(user_id, archetype)
        assert response["status"] == "success"
        
        # Check that archetype_analysis_tracking was updated
        tracking_entry = await self.get_archetype_tracking(user_id, archetype)
        assert tracking_entry is not None
        assert tracking_entry["analysis_count"] == 1
        
        # Check that analysis is stored in holistic_analysis_results
        analysis_entry = await self.get_analysis_result(user_id, archetype, "behavior_analysis")
        assert analysis_entry is not None
    
    async def test_routine_reuses_recent_behavior_analysis(self):
        """Test that routine generation reuses recent behavior analysis"""
        user_id = "test_user_routine_reuse"
        archetype = "Foundation Builder"
        
        # Clear any existing data
        await self.cleanup_test_data(user_id, archetype)
        
        # Step 1: Call behavior analysis API
        behavior_response = await self.call_behavior_analysis_api(user_id, archetype)
        assert behavior_response["status"] == "success"
        
        # Step 2: Call routine generation API immediately
        routine_response = await self.call_routine_generation_api(user_id, archetype)
        assert routine_response["status"] == "success"
        
        # Step 3: Verify only ONE behavior analysis was created
        behavior_analyses = await self.get_all_behavior_analyses(user_id, archetype)
        assert len(behavior_analyses) == 1, f"Expected 1 behavior analysis, found {len(behavior_analyses)}"
        
        # Step 4: Verify routine was generated
        routine_analyses = await self.get_all_routine_analyses(user_id, archetype)
        assert len(routine_analyses) == 1
    
    async def test_concurrent_requests_coordination(self):
        """Test that concurrent requests are properly coordinated"""
        user_id = "test_user_concurrent"
        archetype = "Systematic Improver"
        
        # Clear any existing data
        await self.cleanup_test_data(user_id, archetype)
        
        # Launch concurrent requests
        tasks = [
            self.call_behavior_analysis_api(user_id, archetype),
            self.call_routine_generation_api(user_id, archetype),
            self.call_nutrition_generation_api(user_id, archetype),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Request failed: {result}")
            assert result.get("status") == "success"
        
        # Verify only ONE behavior analysis was created
        behavior_analyses = await self.get_all_behavior_analyses(user_id, archetype)
        assert len(behavior_analyses) == 1, f"Expected 1 behavior analysis, found {len(behavior_analyses)}"
    
    async def test_threshold_tracking_across_apis(self):
        """Test that threshold tracking works correctly across different APIs"""
        user_id = "test_user_threshold"
        archetype = "Resilience Rebuilder"
        
        # Clear any existing data
        await self.cleanup_test_data(user_id, archetype)
        
        # Step 1: Behavior analysis (should be initial - 7 days)
        behavior_response = await self.call_behavior_analysis_api(user_id, archetype)
        analysis_mode_1 = behavior_response.get("metadata", {}).get("analysis_mode")
        assert analysis_mode_1 == "initial"
        
        # Step 2: Wait briefly, then call routine (should reuse, not create new)
        await asyncio.sleep(2)
        routine_response = await self.call_routine_generation_api(user_id, archetype)
        
        # Step 3: Check archetype tracking shows correct timestamp
        tracking_entry = await self.get_archetype_tracking(user_id, archetype)
        assert tracking_entry["analysis_count"] == 1
        
        # Step 4: Simulate time passage and threshold exceeded
        await self.simulate_new_data_points(user_id, 60)  # Add data to exceed threshold
        
        # Step 5: Call behavior analysis again (should create new - threshold exceeded)
        behavior_response_2 = await self.call_behavior_analysis_api(user_id, archetype)
        analysis_mode_2 = behavior_response_2.get("metadata", {}).get("analysis_mode")
        assert analysis_mode_2 == "follow_up"  # Should be follow_up since archetype already analyzed
        
        # Step 6: Check that 2 behavior analyses exist now
        behavior_analyses = await self.get_all_behavior_analyses(user_id, archetype)
        assert len(behavior_analyses) == 2
        
        # Step 7: Check archetype tracking updated
        tracking_entry_final = await self.get_archetype_tracking(user_id, archetype)
        assert tracking_entry_final["analysis_count"] == 2
```

#### 3.2 Validation Scripts
```python
# scripts/validate_race_condition_fix.py
"""
Validation script to verify race condition fixes work correctly
Run this script to validate the implementation
"""

async def main():
    """Run validation tests for race condition fixes"""
    
    print("🧪 Starting Race Condition Fix Validation...")
    
    # Test 1: Standalone API coordination
    print("\n1️⃣ Testing standalone API coordination...")
    await test_standalone_apis()
    
    # Test 2: Concurrent request handling
    print("\n2️⃣ Testing concurrent request handling...")
    await test_concurrent_requests()
    
    # Test 3: Database consistency
    print("\n3️⃣ Testing database consistency...")
    await test_database_consistency()
    
    # Test 4: Threshold tracking accuracy
    print("\n4️⃣ Testing threshold tracking...")
    await test_threshold_tracking()
    
    print("\n✅ All validation tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Implementation Timeline

### Week 1: Core Fixes
- [ ] Implement synchronous archetype tracking updates
- [ ] Create RecentAnalysisChecker service
- [ ] Enhance RequestDeduplicationService with coordination
- [ ] Update shared behavior analysis logic

### Week 2: Endpoint Updates  
- [ ] Update routine generation endpoint
- [ ] Update nutrition generation endpoint
- [ ] Add proper error handling and coordination
- [ ] Implement coordination middleware

### Week 3: Testing & Validation
- [ ] Create comprehensive test suite
- [ ] Run validation scripts
- [ ] Test with original test case scenario
- [ ] Performance testing with concurrent users

### Week 4: Production Deployment
- [ ] Deploy fixes to staging environment
- [ ] Monitor coordination metrics
- [ ] Deploy to production
- [ ] Monitor production performance

## Success Criteria

### Primary Success Metrics:
1. **No Duplicate Analyses**: Same user + archetype should only create one behavior analysis per threshold period
2. **Proper Threshold Tracking**: `archetype_analysis_tracking` updated synchronously with analysis creation
3. **Coordinated Requests**: Concurrent requests wait for in-progress analyses instead of creating duplicates
4. **Database Consistency**: All related tables updated atomically

### Performance Metrics:
1. **Response Time**: No significant increase in API response times
2. **Database Load**: Minimal increase in database connections/queries
3. **Memory Usage**: Coordination cache stays within reasonable limits
4. **Error Rate**: No increase in error rates due to coordination logic

### Test Case Validation:
```
✅ Behavior Analysis at 10:00:00 → Creates analysis + updates tracking
✅ Routine Generation at 10:00:03 → Reuses existing analysis (no duplicate)
✅ Nutrition Generation at 10:00:05 → Reuses existing analysis (no duplicate)
✅ Database shows: 1 behavior analysis, 1 routine plan, 1 nutrition plan
```

## Monitoring & Maintenance

### Health Checks:
- `/api/health/coordination` - Check coordination service health
- `/api/health/recent-analysis` - Validate recent analysis checking
- `/api/health/database-sync` - Verify database synchronization

### Metrics to Track:
- Coordination cache hit/miss ratio
- Average coordination wait times
- Database transaction success rates
- Archetype tracking update success rates

### Maintenance Tasks:
- Weekly coordination cache cleanup
- Monthly database consistency checks
- Quarterly performance optimization reviews

---

## Summary

This plan addresses the race condition by:
1. **Synchronous database updates** - Ensuring archetype tracking is updated before API returns
2. **Recent analysis checking** - Preventing duplicate analyses by checking for recent ones first
3. **Request coordination** - Using enhanced deduplication service to coordinate concurrent requests
4. **Proper threshold tracking** - Making threshold decisions based on correct timestamps

The implementation maintains backward compatibility while fixing the core coordination issues.