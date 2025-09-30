"""
On-Demand Analysis Service
Intelligently decides when to run fresh behavior analysis based on data thresholds
Only triggers analysis when users request routine/nutrition plans
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional
from enum import Enum

from services.user_data_service import UserDataService
from services.simple_analysis_tracker import SimpleAnalysisTracker
from services.ai_context_integration_service import AIContextIntegrationService

logger = logging.getLogger(__name__)

class AnalysisDecision(Enum):
    """Decision types for analysis"""
    FRESH_ANALYSIS = "fresh_analysis"           # Run new analysis
    MEMORY_ENHANCED_CACHE = "memory_cache"      # Use cache with memory
    STALE_FORCE_REFRESH = "stale_refresh"       # Force refresh due to staleness
    
class MemoryQuality(Enum):
    """Memory profile quality levels"""
    RICH = "rich"               # Strong memory profile
    DEVELOPING = "developing"   # Building memory profile  
    SPARSE = "sparse"          # Limited memory data

class OnDemandAnalysisService:
    """
    Service that intelligently decides when to run behavior analysis
    Based on data thresholds, time gaps, and memory quality
    """
    
    def __init__(self):
        self.user_service = None
        self.analysis_tracker = None
        self.memory_service = None
        
        # Configurable thresholds
        self.base_data_threshold = 50  # Base threshold for new data points
        self.max_cache_age_days = 7    # Maximum age before forcing refresh
        self.min_cache_age_hours = 1   # Minimum time before considering new analysis
        
    async def initialize(self):
        """Initialize required services"""
        try:
            self.user_service = UserDataService()
            self.analysis_tracker = SimpleAnalysisTracker()
            self.memory_service = AIContextIntegrationService()
            
            logger.debug("[ONDEMAND] Initialized on-demand analysis service")
            return True
        except Exception as e:
            logger.error(f"[ONDEMAND_ERROR] Failed to initialize: {e}")
            return False
    
    async def should_run_analysis(
        self, 
        user_id: str, 
        force_refresh: bool = False,
        requested_archetype: str = None
    ) -> Tuple[AnalysisDecision, Dict[str, Any]]:
        """
        Determine if fresh behavior analysis should run
        
        CRITICAL: This method must be called BEFORE any data fetching or timestamp updates
        to avoid race conditions in threshold detection.
        
        Returns:
            (decision, metadata) where metadata contains:
            - new_data_points: count of new data
            - hours_since_analysis: time since last analysis
            - threshold_used: the calculated threshold
            - memory_quality: quality of memory profile
            - reason: human-readable explanation
            - fixed_timestamp: the timestamp to use for consistent counting
        """
        
        metadata = {
            "new_data_points": 0,
            "hours_since_analysis": 0,
            "threshold_used": self.base_data_threshold,
            "memory_quality": MemoryQuality.SPARSE,
            "reason": "",
            "analysis_mode": "initial",
            "days_to_fetch": 7,
            "fixed_timestamp": None  # Critical for race condition fix
        }
        
        try:
            # Force refresh if requested
            if force_refresh:
                metadata["reason"] = "Force refresh requested by user"
                return (AnalysisDecision.FRESH_ANALYSIS, metadata)
            
            # ARCHETYPE-SPECIFIC TIMESTAMP: Get timestamp for THIS archetype
            last_analysis = None
            timestamp_source = "none"
            
            if requested_archetype:
                # Try archetype-specific timestamp first
                try:
                    from services.archetype_analysis_tracker import get_archetype_tracker
                    archetype_tracker = await get_archetype_tracker()
                    
                    last_analysis, timestamp_source = await archetype_tracker.get_last_analysis_date_with_fallback(
                        user_id, requested_archetype
                    )
                    
                    metadata["timestamp_source"] = timestamp_source
                    
                except Exception as e:
                    logger.warning(f"[ONDEMAND] Archetype tracker failed, using global fallback: {e}")
                    # Fallback to old logic
                    last_analysis = await self.analysis_tracker.get_last_analysis_time(user_id)
                    timestamp_source = "global_fallback"
            else:
                # No archetype specified - use global timestamp
                last_analysis = await self.analysis_tracker.get_last_analysis_time(user_id)
                timestamp_source = "global_fallback"
            
            metadata["fixed_timestamp"] = last_analysis  # Lock this timestamp for consistent use
            
            # ARCHETYPE CHANGE DETECTION: Check if switching archetypes
            if requested_archetype and last_analysis and timestamp_source == "global_fallback":
                # Only check archetype changes when using global timestamp (legacy behavior)
                last_archetype = await self.get_last_archetype(user_id)
                if last_archetype and last_archetype != requested_archetype:
                    # Import archetype manager to assess if fresh analysis needed
                    from services.archetype_manager import archetype_manager
                    should_force = await archetype_manager.should_force_fresh_analysis(
                        user_id, last_archetype, requested_archetype, last_analysis
                    )
                    if should_force:
                        metadata["reason"] = f"Archetype changed from {last_archetype} to {requested_archetype} - incompatible archetypes require fresh analysis"
                        metadata["archetype_change"] = True
                        metadata["previous_archetype"] = last_archetype
                        return (AnalysisDecision.FRESH_ANALYSIS, metadata)
            
            if not last_analysis:
                # New user - always run initial analysis with comprehensive data window
                metadata["analysis_mode"] = "initial"
                metadata["days_to_fetch"] = 7
                metadata["reason"] = "No previous analysis found - initial analysis required"
                return (AnalysisDecision.FRESH_ANALYSIS, metadata)
            
            # Calculate time since last analysis using locked timestamp
            now = datetime.now(timezone.utc)
            time_delta = now - last_analysis
            hours_since = time_delta.total_seconds() / 3600
            days_since = hours_since / 24
            
            metadata["hours_since_analysis"] = hours_since
            
            # Check if analysis is too stale - treat as fresh start
            if days_since > self.max_cache_age_days:
                metadata["analysis_mode"] = "initial" 
                metadata["days_to_fetch"] = 7
                metadata["reason"] = f"Analysis is {days_since:.1f} days old (>{self.max_cache_age_days} days) - fresh start"
                return (AnalysisDecision.STALE_FORCE_REFRESH, metadata)
            
            # CRITICAL FIX: Always count data points before making time-based decisions
            # This ensures we don't miss threshold-crossing data due to recent timestamps
        # print(f"🔍 [ONDEMAND_COUNT] Counting data since LOCKED timestamp: {last_analysis.isoformat()}")  # Commented to reduce noise
            new_data_count = await self._count_new_data_points(user_id, last_analysis)
            metadata["new_data_points"] = new_data_count
        # print(f"📊 [ONDEMAND_COUNT] Found {new_data_count} new data points (using locked timestamp)")  # Commented to reduce noise
            
            # Check if we have enough data to override time-based caching
            memory_quality = await self._assess_memory_quality(user_id, requested_archetype)
            metadata["memory_quality"] = memory_quality
            
            threshold = self._calculate_dynamic_threshold(memory_quality, user_id, days_since, requested_archetype)
            metadata["threshold_used"] = threshold
            
            # DATA-FIRST DECISION: If we have enough new data, analyze regardless of time
            if new_data_count >= threshold:
                # print(f"🎯 [DATA_OVERRIDE] {new_data_count} points ≥ {threshold} threshold - overriding time-based cache")  # Commented for error-only mode
                metadata["analysis_mode"] = "follow_up" if days_since < 3 else "initial"
                metadata["days_to_fetch"] = min(7, max(3, int(days_since) + 1))
                metadata["reason"] = f"Data threshold override: {new_data_count} ≥ {threshold} points (recent but sufficient data)"
                return (AnalysisDecision.FRESH_ANALYSIS, metadata)
            
            # Too recent AND insufficient data - use cache with follow-up parameters  
            if hours_since < self.min_cache_age_hours:
                metadata["analysis_mode"] = "follow_up"
                metadata["days_to_fetch"] = 1
                metadata["reason"] = f"Recent analysis from {hours_since:.1f} hours ago + insufficient data ({new_data_count} < {threshold})"
                return (AnalysisDecision.MEMORY_ENHANCED_CACHE, metadata)
            
            # Remaining cases: sufficient time gap + data count already checked above
            logger.debug(f"[ONDEMAND] User {user_id[:8]}... - {new_data_count} new points, {hours_since:.1f}h since last")
            
            # If we reach here: sufficient time gap + insufficient data
            metadata["analysis_mode"] = "follow_up" 
            metadata["days_to_fetch"] = 1
            metadata["reason"] = f"{new_data_count} new data points < {threshold} threshold + sufficient time gap - using cached with memory"
            return (AnalysisDecision.MEMORY_ENHANCED_CACHE, metadata)
                
        except Exception as e:
            logger.error(f"[ONDEMAND_ERROR] Decision error for {user_id}: {e}")
            metadata["reason"] = f"Error in decision logic: {e}"
            # Default to cache on error
            return (AnalysisDecision.MEMORY_ENHANCED_CACHE, metadata)
    
    async def _count_new_data_points(self, user_id: str, since_timestamp: datetime) -> int:
        """Count new data points since given timestamp"""
        try:
            db = await self.user_service._ensure_db_connection()
            if not db or not hasattr(db, 'client') or not db.client:
                logger.warning(f"[ONDEMAND] Database connection unavailable for {user_id[:8]}... - falling back to threshold=0")
                return 0
            
            # Count new scores - Fix datetime comparison
            scores_result = db.client.table("scores").select("id", count="exact")\
                .eq("profile_id", user_id)\
                .gte("created_at", since_timestamp.isoformat())\
                .execute()
            scores_count = scores_result.count if hasattr(scores_result, 'count') else len(scores_result.data if scores_result.data else [])
            
            # Count new biomarkers - Fix datetime comparison
            biomarkers_result = db.client.table("biomarkers").select("id", count="exact")\
                .eq("profile_id", user_id)\
                .gte("created_at", since_timestamp.isoformat())\
                .execute()
            biomarkers_count = biomarkers_result.count if hasattr(biomarkers_result, 'count') else len(biomarkers_result.data if biomarkers_result.data else [])
            
            total_count = scores_count + biomarkers_count
            
            # print(f"📈 [DATA_COUNT] Scores: {scores_count}, Biomarkers: {biomarkers_count}, Total: {total_count}")  # Commented for error-only mode
            logger.debug(f"[ONDEMAND] User {user_id[:8]}... has {total_count} new data points")
            return total_count
            
        except Exception as e:
            logger.error(f"[ONDEMAND_ERROR] Failed to count data for {user_id}: {e}")
            return 0
    
    async def _assess_memory_quality(self, user_id: str, archetype: str = None) -> MemoryQuality:
        """Assess the quality of user's context data, simplified for AI Context approach"""
        try:
            # Use AI context service to get historical analysis data
            behavior_history = await self.memory_service._get_agent_analysis_history(
                user_id, "behavior_analysis", archetype, limit=10
            )
            circadian_history = await self.memory_service._get_agent_analysis_history(
                user_id, "circadian_analysis", archetype, limit=10
            )

            # Score context richness based on available analyses
            score = 0

            # Check behavior analysis history depth
            if behavior_history:
                if len(behavior_history) >= 5:
                    score += 4
                elif len(behavior_history) >= 3:
                    score += 3
                elif len(behavior_history) >= 1:
                    score += 2

            # Check circadian analysis history depth
            if circadian_history:
                if len(circadian_history) >= 5:
                    score += 4
                elif len(circadian_history) >= 3:
                    score += 3
                elif len(circadian_history) >= 1:
                    score += 2

            # Check if we have AI context available
            try:
                # Try to get existing AI context (indicates user has engagement data)
                ai_context = await self.memory_service.ai_context_service._get_recent_context(user_id, hours=24)
                if ai_context and len(ai_context) > 100:  # Meaningful context length
                    score += 3
            except Exception as e:
                logger.debug(f"[MEMORY_QUALITY] Could not check AI context: {e}")

            # Simplified scoring thresholds
            if score >= 8:
                return MemoryQuality.RICH
            elif score >= 4:
                return MemoryQuality.DEVELOPING
            else:
                return MemoryQuality.SPARSE

        except Exception as e:
            logger.error(f"[ONDEMAND_ERROR] Failed to assess memory quality: {e}")
            return MemoryQuality.SPARSE
    
    def _calculate_dynamic_threshold(
        self, 
        memory_quality: MemoryQuality,
        user_id: str,
        days_since_analysis: float,
        archetype: str = None
    ) -> int:
        """
        Calculate dynamic threshold based on memory quality, archetype complexity, and other factors
        
        Rich memory = lower threshold (can work with less data)
        Sparse memory = higher threshold (needs more data)
        Complex archetypes = higher threshold (need more data for accurate analysis)
        Simple archetypes = lower threshold (can work with less data)
        """
        base = self.base_data_threshold
        
        # Adjust based on memory quality
        if memory_quality == MemoryQuality.RICH:
            # Rich memory can work with 30% less data
            threshold = int(base * 0.7)  # 35 points
        elif memory_quality == MemoryQuality.DEVELOPING:
            # Developing memory needs slightly less data
            threshold = int(base * 0.85)  # 42 points
        else:  # SPARSE
            # Sparse memory needs more data
            threshold = int(base * 1.2)  # 60 points
        
        # NEW: Adjust based on archetype complexity
        if archetype:
            archetype_complexity = self._get_archetype_complexity(archetype)
            if archetype_complexity >= 8:  # Complex archetypes (Peak Performer, Systematic Improver)
                threshold = int(threshold * 1.15)  # 15% more data needed
            elif archetype_complexity <= 4:  # Simple archetypes (Foundation Builder, Resilience Rebuilder)  
                threshold = int(threshold * 0.9)   # 10% less data needed
            # Medium complexity archetypes (5-7) use base threshold
        
        # Adjust based on time gap - longer gaps need less data to trigger
        if days_since_analysis >= 5:
            threshold = int(threshold * 0.7)  # 30% reduction for old analyses
        elif days_since_analysis >= 3:
            threshold = int(threshold * 0.85)  # 15% reduction
        
        # Ensure reasonable bounds
        threshold = max(10, min(100, threshold))  # Between 10 and 100
        
        logger.debug(f"[ONDEMAND] Threshold: {threshold} (memory: {memory_quality.value}, archetype: {archetype})")
        
        return threshold
    
    def _get_archetype_complexity(self, archetype: str) -> int:
        """
        Get complexity level for archetype (1-10 scale)
        Higher complexity = needs more data for accurate analysis
        """
        complexity_map = {
            'Foundation Builder': 3,        # Simple, basic approach
            'Resilience Rebuilder': 4,      # Recovery focus, straightforward
            'Connected Explorer': 5,        # Social elements, moderate complexity
            'Transformation Seeker': 6,     # Ambitious changes, medium-high complexity
            'Systematic Improver': 8,       # Methodical, evidence-based, high complexity  
            'Peak Performer': 9             # Elite optimization, highest complexity
        }
        return complexity_map.get(archetype, 5)  # Default to medium complexity
    
    async def get_cached_behavior_analysis(self, user_id: str, archetype: str = None) -> Optional[Dict[str, Any]]:
        """Get the most recent cached behavior analysis, optionally filtered by archetype"""
        try:
            # Get from AI context service using the agent-specific history method
            analysis_history = await self.memory_service._get_agent_analysis_history(
                user_id, "behavior_analysis", archetype, limit=1
            )

            if not analysis_history:
                logger.info(f"[ONDEMAND] No cached analysis found for archetype '{archetype}' for user {user_id[:8]}")
                return None

            if analysis_history and len(analysis_history) > 0:
                latest = analysis_history[0]
                analysis_result = latest.get('analysis_result')

                if analysis_result:
                    # Extract behavior analysis
                    if isinstance(analysis_result, dict) and 'behavior_analysis' in analysis_result:
                        return analysis_result['behavior_analysis']
                    # If it's already the behavior analysis directly
                    elif isinstance(analysis_result, dict):
                        return analysis_result

            return None

        except Exception as e:
            logger.error(f"[ONDEMAND_ERROR] Failed to get cached analysis: {e}")
            return None
    
    async def get_last_archetype(self, user_id: str) -> Optional[str]:
        """Get the archetype used in the most recent analysis"""
        try:
            # Query the most recent analysis to get its archetype
            analysis_history = await self.memory_service._get_agent_analysis_history(
                user_id, "behavior_analysis", archetype=None, limit=1
            )

            if analysis_history and len(analysis_history) > 0:
                latest = analysis_history[0]
                return latest.get('archetype') or latest.get('archetype_used')
            return None

        except Exception as e:
            logger.error(f"[ONDEMAND_ERROR] Error getting last archetype for {user_id}: {e}")
            return None

    async def cleanup(self):
        """Clean up resources"""
        if self.user_service:
            await self.user_service.cleanup()
        if self.analysis_tracker:
            await self.analysis_tracker.cleanup()
        if self.memory_service:
            await self.memory_service.cleanup()

# Singleton instance
_ondemand_service = None

async def get_ondemand_service() -> OnDemandAnalysisService:
    """Get or create the singleton on-demand analysis service"""
    global _ondemand_service
    
    if _ondemand_service is None:
        _ondemand_service = OnDemandAnalysisService()
        await _ondemand_service.initialize()
    
    return _ondemand_service