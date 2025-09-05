"""
Memory Integration Service - Phase 4.1.2
Bridges the existing HolisticMemoryService with the analysis pipeline
Provides simplified interface for memory-enhanced analysis workflows
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from services.agents.memory.holistic_memory_service import HolisticMemoryService, UserMemoryProfile, AnalysisHistory

logger = logging.getLogger(__name__)

@dataclass
class MemoryEnhancedContext:
    """Context object containing health data enhanced with memory"""
    user_id: str
    analysis_mode: str  # "initial", "follow_up", "adaptation"
    days_to_fetch: int
    
    # Memory context
    longterm_memory: Optional[UserMemoryProfile]
    recent_patterns: List[Dict[str, Any]]
    meta_memory: Dict[str, Any]
    analysis_history: List[AnalysisHistory]
    
    # Analysis guidance
    personalized_focus_areas: List[str]
    proven_strategies: Dict[str, Any]
    adaptation_preferences: Dict[str, Any]
    
    created_at: datetime

class MemoryIntegrationService:
    """
    Service that integrates existing memory system with analysis pipeline
    Provides memory-enhanced context for agents and handles memory updates
    """
    
    def __init__(self):
        self.memory_service = HolisticMemoryService()
        
        # Session tracking for working memory
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.debug("[MEMORY_INTEGRATION] Initialized with existing HolisticMemoryService")
    
    async def prepare_memory_enhanced_context(self, user_id: str, ondemand_metadata: dict = None, archetype: str = None) -> MemoryEnhancedContext:
        """
        Prepare memory-enhanced context for analysis
        This is the main entry point for memory-enhanced analysis
        
        Args:
            user_id: User identifier
            ondemand_metadata: Metadata from OnDemandAnalysisService containing analysis_mode and days_to_fetch
        """
        try:
            logger.debug(f"[MEMORY_INTEGRATION] Preparing memory context for user {user_id}")
            
            # Use OnDemandAnalysisService decision for analysis mode, fallback to memory service
            if ondemand_metadata and 'analysis_mode' in ondemand_metadata:
                analysis_mode = ondemand_metadata['analysis_mode']
                days_to_fetch = ondemand_metadata['days_to_fetch']
        # print(f"📊 [MEMORY_INTEGRATION] Using OnDemandAnalysisService decision: {analysis_mode} mode, {days_to_fetch} days")  # Commented to reduce noise
            else:
                # Fallback to memory service for backwards compatibility
                analysis_mode, days_to_fetch = await self.memory_service.determine_analysis_mode(user_id, archetype)
                print(f"⚠️ [MEMORY_INTEGRATION] Fallback to memory service decision: {analysis_mode} mode, {days_to_fetch} days (archetype={archetype})")
            
            # Log memory collection process
            print(f"\n{'='*60}")
            print(f"🧠 [MEMORY_DATA_COLLECTION] User: {user_id[:8]}...")
            print(f"{'='*60}")
            print(f"📊 Analysis Configuration:")
            print(f"   - Mode: {analysis_mode}")
            print(f"   - Days to fetch: {days_to_fetch}")
            print(f"   - Archetype: {archetype if archetype else 'Not specified'}")
            
            # Get all memory layers
            print(f"\n🔍 Fetching Memory Layers:")
            
            # Long-term memory
            longterm_memory = await self.memory_service.get_user_longterm_memory(user_id)
            if longterm_memory:
                print(f"✅ Long-term Memory:")
                print(f"   - Behavioral patterns: {len(longterm_memory.get('behavioral_patterns', {})) if isinstance(longterm_memory, dict) else 'Present'}")
                print(f"   - Health goals: {len(longterm_memory.get('health_goals', {})) if isinstance(longterm_memory, dict) else 'Present'}")
                print(f"   - Preferences: {len(longterm_memory.get('preference_patterns', {})) if isinstance(longterm_memory, dict) else 'Present'}")
            else:
                print(f"⚠️ No long-term memory found")
            
            # Recent patterns
            recent_patterns = await self.memory_service.get_recent_patterns(user_id, days=7)
            print(f"📈 Recent Patterns: {len(recent_patterns) if recent_patterns else 0} patterns found")
            
            # Meta memory
            meta_memory = await self.memory_service.get_meta_memory(user_id)
            if meta_memory:
                print(f"🎯 Meta Memory: Learning patterns available")
            else:
                print(f"⚠️ No meta memory found")
            
            # Analysis history
            analysis_history = await self.memory_service.get_analysis_history(user_id, limit=5)
            print(f"📚 Analysis History: {len(analysis_history) if analysis_history else 0} previous analyses")
            if analysis_history and len(analysis_history) > 0:
                print(f"   - Last analysis: {analysis_history[0].analysis_type if hasattr(analysis_history[0], 'analysis_type') else 'Unknown'}")
            
            # Extract personalized guidance from memory
            personalized_focus_areas = self._extract_focus_areas(longterm_memory, recent_patterns)
            proven_strategies = self._extract_proven_strategies(longterm_memory, meta_memory)
            adaptation_preferences = self._extract_adaptation_preferences(meta_memory)
            
            # Log extracted memory insights
            print(f"\n💡 Memory Insights Extracted:")
            print(f"   - Focus areas: {len(personalized_focus_areas) if personalized_focus_areas else 0}")
            if personalized_focus_areas:
                print(f"     • {', '.join(personalized_focus_areas[:3])}")
            print(f"   - Proven strategies: {len(proven_strategies) if proven_strategies else 0}")
            print(f"   - Adaptation preferences: {'Yes' if adaptation_preferences else 'No'}")
            print(f"{'='*60}\n")
            
            context = MemoryEnhancedContext(
                user_id=user_id,
                analysis_mode=analysis_mode,
                days_to_fetch=days_to_fetch,
                longterm_memory=longterm_memory,
                recent_patterns=recent_patterns,
                meta_memory=meta_memory,
                analysis_history=analysis_history,
                personalized_focus_areas=personalized_focus_areas,
                proven_strategies=proven_strategies,
                adaptation_preferences=adaptation_preferences,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store working memory for this session
            await self._store_session_context(context)
            
        # print(f"📋 MEMORY_CONTEXT: {analysis_mode} mode, {days_to_fetch} days, {len(personalized_focus_areas)} focus areas")  # Commented to reduce noise
            return context
            
        except Exception as e:
            logger.error(f"[MEMORY_INTEGRATION_ERROR] Failed to prepare context for {user_id}: {e}")
            # Return minimal context on error
            return MemoryEnhancedContext(
                user_id=user_id,
                analysis_mode="initial",
                days_to_fetch=7,
                longterm_memory=None,
                recent_patterns=[],
                meta_memory={},
                analysis_history=[],
                personalized_focus_areas=[],
                proven_strategies={},
                adaptation_preferences={},
                created_at=datetime.now(timezone.utc)
            )
    
    async def enhance_agent_prompt(self, base_prompt: str, memory_context: MemoryEnhancedContext, 
                                 agent_type: str) -> str:
        """
        Enhance agent prompt with personalized memory context
        Different agents get different memory perspectives
        """
        try:
            # Use existing memory service prompt enhancement
            enhanced_prompt = await self.memory_service.enhance_prompts_with_memory(base_prompt, memory_context.user_id)
            
            # Add agent-specific memory enhancements
            agent_specific_context = self._build_agent_specific_context(memory_context, agent_type)
            
            if agent_specific_context:
                enhanced_prompt += f"\n\n{agent_specific_context}"
            
            # Add analysis mode context
            mode_context = self._build_analysis_mode_context(memory_context)
            enhanced_prompt += f"\n\n{mode_context}"
            
            logger.debug(f"[MEMORY_INTEGRATION] Enhanced {agent_type} prompt for {memory_context.user_id}")
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"[MEMORY_INTEGRATION_ERROR] Failed to enhance prompt: {e}")
            return base_prompt
    
    async def store_analysis_insights(self, user_id: str, agent_type: str, 
                                    analysis_result: Dict[str, Any], archetype: str) -> bool:
        """
        Store analysis results and extract insights for memory
        Updates all relevant memory layers based on analysis results
        """
        try:
            logger.debug(f"[MEMORY_INTEGRATION] Storing insights from {agent_type} analysis for {user_id}")
            
            # Store complete analysis result
            analysis_id = await self.memory_service.store_analysis_result(
                user_id, agent_type, analysis_result, archetype
            )
            
            # Extract and store insights in different memory layers
            await self._extract_and_store_insights(user_id, agent_type, analysis_result, archetype)
            
            logger.debug(f"[MEMORY_INTEGRATION] Stored analysis insights - ID: {analysis_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MEMORY_INTEGRATION_ERROR] Failed to store insights for {user_id}: {e}")
            return False
    
    async def update_user_memory_profile(self, user_id: str, behavior_analysis: Dict[str, Any],
                                       nutrition_plan: Dict[str, Any], routine_plan: Dict[str, Any]) -> bool:
        """
        Update user's long-term memory profile based on complete analysis
        This consolidates insights from all agents into persistent memory
        """
        try:
            logger.debug(f"[MEMORY_INTEGRATION] Updating memory profile for {user_id}")
            
            # Update behavioral patterns
            if behavior_analysis:
                behavioral_insights = self._extract_behavioral_insights(behavior_analysis)
                await self.memory_service.update_longterm_memory(
                    user_id, "behavioral_patterns", behavioral_insights, confidence_score=0.8
                )
            
            # Update health preferences from nutrition
            if nutrition_plan:
                nutrition_insights = self._extract_nutrition_insights(nutrition_plan)
                await self.memory_service.update_longterm_memory(
                    user_id, "health_preferences", nutrition_insights, confidence_score=0.7
                )
            
            # Update successful strategies from routine
            if routine_plan:
                routine_insights = self._extract_routine_insights(routine_plan)
                await self.memory_service.update_longterm_memory(
                    user_id, "successful_strategies", routine_insights, confidence_score=0.7
                )
            
            # Update meta-memory with learning patterns
            await self._update_meta_learning_patterns(user_id, behavior_analysis, nutrition_plan, routine_plan)
            
            logger.debug(f"[MEMORY_INTEGRATION] Memory profile updated for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MEMORY_INTEGRATION_ERROR] Failed to update memory profile for {user_id}: {e}")
            return False
    
    def _extract_focus_areas(self, longterm_memory: Optional[UserMemoryProfile], 
                           recent_patterns: List[Dict[str, Any]]) -> List[str]:
        """Dynamic extraction of focus areas from memory - adapts to any memory structure"""
        focus_areas = set()  # Use set to avoid duplicates
        
        # From long-term memory - dynamic extraction
        if longterm_memory:
            # Extract from health goals if available
            if longterm_memory.health_goals and isinstance(longterm_memory.health_goals, dict):
                focus_areas.update(longterm_memory.health_goals.keys())
            
            # Extract from behavioral patterns
            if longterm_memory.behavioral_patterns:
                # Look for patterns that suggest focus areas
                for pattern_key, pattern_data in longterm_memory.behavioral_patterns.items():
                    if "goal" in pattern_key.lower():
                        focus_areas.add("goal_achievement")
                    if "sleep" in str(pattern_data).lower():
                        focus_areas.add("sleep_optimization") 
                    if "activity" in str(pattern_data).lower():
                        focus_areas.add("activity_improvement")
                    if "nutrition" in str(pattern_data).lower():
                        focus_areas.add("nutrition_optimization")
        
        # From recent patterns - dynamic extraction
        for pattern in recent_patterns[:5]:  # Look at more recent patterns
            category = pattern.get('category', '')
            content = pattern.get('content', {})
            
            # Extract focus areas from category
            if 'behavior' in category:
                focus_areas.add("behavior_optimization")
            if 'nutrition' in category:
                focus_areas.add("nutrition_planning")  
            if 'routine' in category:
                focus_areas.add("routine_building")
            if 'analysis' in category:
                focus_areas.add("health_analysis")
            
            # Extract focus areas from content
            if isinstance(content, dict):
                content_str = str(content).lower()
                if 'readiness' in content_str:
                    focus_areas.add("readiness_improvement")
                if 'recommendation' in content_str:
                    focus_areas.add("recommendation_following")
                if 'activity' in content_str:
                    focus_areas.add("activity_tracking")
        
        # Convert to list and return, with fallback
        focus_list = list(focus_areas)
        return focus_list if focus_list else ["general_health", "behavior_optimization"]
    
    def _extract_proven_strategies(self, longterm_memory: Optional[UserMemoryProfile], 
                                 meta_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Extract strategies that have worked for this user"""
        proven_strategies = {}
        
        if longterm_memory and longterm_memory.success_predictors and isinstance(longterm_memory.success_predictors, dict):
            proven_strategies.update(longterm_memory.success_predictors)
        
        if meta_memory.get('success_predictors') and isinstance(meta_memory['success_predictors'].get('data'), dict):
            proven_strategies.update(meta_memory['success_predictors'].get('data', {}))
        
        return proven_strategies
    
    def _extract_adaptation_preferences(self, meta_memory: Dict[str, Any]) -> Dict[str, Any]:
        """Extract how user prefers to adapt to changes"""
        preferences = {
            "complexity_tolerance": 0.5,
            "change_pace": "moderate",
            "preferred_communication_style": "supportive"
        }
        
        if meta_memory:
            if 'adaptation_patterns' in meta_memory and isinstance(meta_memory['adaptation_patterns'].get('data'), dict):
                preferences.update(meta_memory['adaptation_patterns'].get('data', {}))
        
        return preferences
    
    def _build_agent_specific_context(self, memory_context: MemoryEnhancedContext, agent_type: str) -> str:
        """Build agent-specific memory context"""
        if agent_type == "behavior_analysis":
            return self._build_behavior_agent_context(memory_context)
        elif agent_type == "nutrition_plan":
            return self._build_nutrition_agent_context(memory_context)
        elif agent_type == "routine_plan":
            return self._build_routine_agent_context(memory_context)
        else:
            return ""
    
    def _build_behavior_agent_context(self, memory_context: MemoryEnhancedContext) -> str:
        """Build behavior-specific memory context"""
        context_parts = ["BEHAVIOR ANALYSIS MEMORY CONTEXT:"]
        
        if memory_context.longterm_memory and memory_context.longterm_memory.behavioral_patterns:
            context_parts.append(f"Known Behavioral Patterns: {memory_context.longterm_memory.behavioral_patterns}")
        
        if memory_context.proven_strategies:
            context_parts.append(f"Proven Behavior Strategies: {memory_context.proven_strategies}")
        
        recent_behaviors = [p for p in memory_context.recent_patterns if 'behavior' in p.get('category', '')]
        if recent_behaviors:
            context_parts.append(f"Recent Behavior Changes: {[p['content'] for p in recent_behaviors[:2]]}")
        
        return "\n  ".join(context_parts)
    
    def _build_nutrition_agent_context(self, memory_context: MemoryEnhancedContext) -> str:
        """Build nutrition-specific memory context"""
        context_parts = ["NUTRITION PLANNING MEMORY CONTEXT:"]
        
        if memory_context.longterm_memory and memory_context.longterm_memory.preference_patterns:
            context_parts.append(f"Food Preferences: {memory_context.longterm_memory.preference_patterns}")
        
        # Look for nutrition-related patterns
        nutrition_patterns = [p for p in memory_context.recent_patterns if 'nutrition' in p.get('category', '').lower()]
        if nutrition_patterns:
            context_parts.append(f"Recent Nutrition Patterns: {[p['content'] for p in nutrition_patterns[:2]]}")
        
        return "\n  ".join(context_parts)
    
    def _build_routine_agent_context(self, memory_context: MemoryEnhancedContext) -> str:
        """Build routine-specific memory context"""
        context_parts = ["ROUTINE PLANNING MEMORY CONTEXT:"]
        
        if memory_context.adaptation_preferences:
            context_parts.append(f"Adaptation Preferences: {memory_context.adaptation_preferences}")
        
        # Look for routine-related successes
        routine_successes = [p for p in memory_context.recent_patterns if 'routine' in p.get('category', '').lower()]
        if routine_successes:
            context_parts.append(f"Recent Routine Success: {[p['content'] for p in routine_successes[:2]]}")
        
        return "\n  ".join(context_parts)
    
    def _build_analysis_mode_context(self, memory_context: MemoryEnhancedContext) -> str:
        """Build context based on analysis mode"""
        mode_context = f"ANALYSIS MODE: {memory_context.analysis_mode.upper()}\n"
        
        if memory_context.analysis_mode == "initial":
            mode_context += "This is an initial analysis. Focus on establishing baseline patterns and comprehensive recommendations."
        elif memory_context.analysis_mode == "follow_up":
            mode_context += "This is a follow-up analysis. Focus on progress since last analysis and adjustments to current strategies."
        else:  # adaptation
            mode_context += "This is an adaptation analysis. Focus on fine-tuning current strategies based on recent feedback."
        
        return mode_context
    
    async def _store_session_context(self, context: MemoryEnhancedContext):
        """Store session context in working memory"""
        session_data = {
            "analysis_mode": context.analysis_mode,
            "focus_areas": context.personalized_focus_areas,
            "session_start": context.created_at.isoformat()
        }
        
        await self.memory_service.store_working_memory(
            context.user_id, self.current_session_id, "memory_integration_agent",
            "analysis_context", session_data, priority=8, expires_hours=24
        )
    
    async def _extract_and_store_insights(self, user_id: str, agent_type: str, 
                                        analysis_result: Dict[str, Any], archetype: str):
        """Extract insights from analysis and store in appropriate memory layers"""
        
        # PHASE 1: Dynamic extraction for short-term memory
        insight_data = {
            # Raw data preservation
            "_raw_analysis": analysis_result,
            "_extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            
            # Basic metadata
            "agent_type": agent_type,
            "archetype": archetype,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_model": analysis_result.get("model_used", "unknown")
        }
        
        # Dynamic extraction based on agent type and actual content
        if agent_type == "behavior_analysis":
            # Extract key behavioral insights
            recommendations = analysis_result.get("recommendations", [])
            insight_data["recommendations"] = recommendations
            insight_data["recommendation_count"] = len(recommendations)
            
            if "behavioral_signature" in analysis_result:
                sig = analysis_result["behavioral_signature"]
                if isinstance(sig, dict):
                    insight_data["behavioral_signature"] = sig.get("signature", "")
                    insight_data["confidence_score"] = sig.get("confidence", 0.0)
            
            if "readiness_level" in analysis_result:
                insight_data["readiness_level"] = analysis_result["readiness_level"]
                
        elif agent_type == "nutrition_plan":
            # Extract nutrition insights
            content = analysis_result.get("content", "")
            if content:
                insight_data["plan_content_length"] = len(str(content))
                insight_data["includes_meal_planning"] = "meal" in str(content).lower()
                
        elif agent_type == "routine_plan":
            # Extract routine insights
            content = analysis_result.get("content", "")
            if content:
                insight_data["plan_content_length"] = len(str(content))
                insight_data["includes_exercise"] = any(word in str(content).lower() 
                                                      for word in ["exercise", "workout", "activity"])
        
        # Store extracted insights in short-term memory
        await self.memory_service.store_shortterm_memory(
            user_id, "analysis_results", insight_data, confidence_score=0.8, expires_days=30
        )
    
    def _extract_behavioral_insights(self, behavior_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamic extraction of behavioral insights - adapts to any analysis structure"""
        insights = {
            # PHASE 1: Raw storage with metadata
            "_raw_analysis": behavior_analysis,  # Complete analysis for future use
            "_extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "_analysis_type": "behavior_analysis",
            "_source_model": behavior_analysis.get("model_used", "unknown"),
        }
        
        # PHASE 1: Smart dynamic extraction from actual structure
        # Extract any field that contains meaningful behavioral data
        
        # Look for signature/summary fields
        if "behavioral_signature" in behavior_analysis:
            signature = behavior_analysis["behavioral_signature"]
            if isinstance(signature, dict):
                insights["behavioral_signature"] = signature.get("signature", "")
                insights["signature_confidence"] = signature.get("confidence", 0.0)
            else:
                insights["behavioral_signature"] = str(signature)
        
        # Extract recommendations (always valuable for memory)
        recommendations = behavior_analysis.get("recommendations", [])
        if recommendations:
            insights["recommendations"] = recommendations
            insights["recommendation_count"] = len(recommendations)
        
        # Extract goals and strategies
        if "primary_goal" in behavior_analysis:
            insights["primary_goal"] = behavior_analysis["primary_goal"]
        
        if "personalized_strategy" in behavior_analysis:
            insights["personalized_strategy"] = behavior_analysis["personalized_strategy"]
        
        # Extract readiness and assessment data
        readiness_level = behavior_analysis.get("readiness_level")
        if readiness_level:
            insights["readiness_level"] = readiness_level
            
        # Extract sophistication assessment
        if "sophistication_assessment" in behavior_analysis:
            insights["sophistication_assessment"] = behavior_analysis["sophistication_assessment"]
        
        # Extract any insights or analysis text
        data_insights = behavior_analysis.get("data_insights")
        if data_insights:
            insights["data_insights"] = data_insights
        
        # Fallback: extract ALL top-level fields (future-proof)
        for key, value in behavior_analysis.items():
            # Skip already processed and metadata fields
            if key in ["model_used", "analysis_type", "_raw_analysis"] or key.startswith("_"):
                continue
            # Store any field we haven't explicitly handled
            if key not in insights:
                insights[f"dynamic_{key}"] = value
        
        return insights
    
    def _extract_nutrition_insights(self, nutrition_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamic extraction of nutrition insights - adapts to any nutrition structure"""
        insights = {
            # PHASE 1: Raw storage with metadata
            "_raw_analysis": nutrition_plan,  # Complete nutrition plan for future use
            "_extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "_analysis_type": "nutrition_plan",
            "_source_model": nutrition_plan.get("model_used", "unknown"),
        }
        
        # PHASE 1: Smart dynamic extraction from actual structure
        
        # Extract nutrition content (main field in current structure)
        content = nutrition_plan.get("content")
        if content:
            insights["nutrition_content"] = content
            # Extract key information from content if it's text
            if isinstance(content, str):
                insights["content_length"] = len(content)
                # Look for specific nutrition patterns in text
                if "calories" in content.lower():
                    insights["includes_calorie_guidance"] = True
                if "protein" in content.lower():
                    insights["includes_protein_guidance"] = True
                if "meal" in content.lower():
                    insights["includes_meal_planning"] = True
        
        # Extract plan type and system info
        plan_type = nutrition_plan.get("plan_type")
        if plan_type:
            insights["plan_type"] = plan_type
            
        # Extract date and archetype
        if "date" in nutrition_plan:
            insights["plan_date"] = nutrition_plan["date"]
        if "archetype" in nutrition_plan:
            insights["archetype"] = nutrition_plan["archetype"]
        
        # Fallback: extract ALL top-level fields (future-proof)
        for key, value in nutrition_plan.items():
            # Skip already processed and metadata fields
            if key in ["model_used", "system", "_raw_analysis"] or key.startswith("_"):
                continue
            # Store any field we haven't explicitly handled
            if key not in insights:
                insights[f"dynamic_{key}"] = value
        
        return insights
    
    def _extract_routine_insights(self, routine_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamic extraction of routine insights - adapts to any routine structure"""
        insights = {
            # PHASE 1: Raw storage with metadata
            "_raw_analysis": routine_plan,  # Complete routine plan for future use
            "_extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "_analysis_type": "routine_plan", 
            "_source_model": routine_plan.get("model_used", "unknown"),
        }
        
        # PHASE 1: Smart dynamic extraction from actual structure
        
        # Extract routine content (main field in current structure)
        content = routine_plan.get("content")
        if content:
            insights["routine_content"] = content
            # Extract key information from content if it's text
            if isinstance(content, str):
                insights["content_length"] = len(content)
                # Look for specific routine patterns in text
                if "morning" in content.lower():
                    insights["includes_morning_routine"] = True
                if "evening" in content.lower():
                    insights["includes_evening_routine"] = True
                if "exercise" in content.lower() or "workout" in content.lower():
                    insights["includes_exercise"] = True
                if "mindfulness" in content.lower() or "meditation" in content.lower():
                    insights["includes_mindfulness"] = True
        
        # Extract plan type and system info
        plan_type = routine_plan.get("plan_type")
        if plan_type:
            insights["plan_type"] = plan_type
            
        # Extract date and archetype
        if "date" in routine_plan:
            insights["plan_date"] = routine_plan["date"]
        if "archetype" in routine_plan:
            insights["archetype"] = routine_plan["archetype"]
        
        # Fallback: extract ALL top-level fields (future-proof)
        for key, value in routine_plan.items():
            # Skip already processed and metadata fields
            if key in ["model_used", "system", "_raw_analysis"] or key.startswith("_"):
                continue
            # Store any field we haven't explicitly handled
            if key not in insights:
                insights[f"dynamic_{key}"] = value
        
        return insights
    
    async def _update_meta_learning_patterns(self, user_id: str, behavior_analysis: Dict[str, Any],
                                           nutrition_plan: Dict[str, Any], routine_plan: Dict[str, Any]):
        """Update meta-memory with learning patterns from this analysis"""
        
        # Analyze adaptation patterns
        adaptation_patterns = {
            "agents_used": ["behavior_analysis", "nutrition_plan", "routine_plan"],
            "complexity_provided": self._assess_complexity_level(behavior_analysis, nutrition_plan, routine_plan),
            "personalization_level": self._assess_personalization_level(behavior_analysis, nutrition_plan, routine_plan),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze learning velocity (would be enhanced with user feedback)
        learning_velocity = {
            "analysis_frequency": "regular",  # Could be calculated from analysis history
            "adaptation_speed": "moderate",   # Could be inferred from user behavior
            "retention_indicators": {}        # Would be populated with follow-up data
        }
        
        await self.memory_service.update_meta_memory(user_id, adaptation_patterns, learning_velocity)
    
    def _assess_complexity_level(self, behavior_analysis: Dict[str, Any], 
                               nutrition_plan: Dict[str, Any], routine_plan: Dict[str, Any]) -> str:
        """Assess complexity level of provided recommendations"""
        total_recommendations = (
            len(behavior_analysis.get("recommendations", [])) +
            len(nutrition_plan.get("recommendations", [])) +
            len(routine_plan.get("recommendations", []))
        )
        
        if total_recommendations > 15:
            return "high"
        elif total_recommendations > 8:
            return "moderate"
        else:
            return "low"
    
    def _assess_personalization_level(self, behavior_analysis: Dict[str, Any],
                                    nutrition_plan: Dict[str, Any], routine_plan: Dict[str, Any]) -> str:
        """Assess how personalized the recommendations are"""
        personalization_indicators = 0
        
        # Check for specific user references, preferences, patterns
        for analysis in [behavior_analysis, nutrition_plan, routine_plan]:
            if "user-specific" in str(analysis).lower() or "your" in str(analysis).lower():
                personalization_indicators += 1
        
        return "high" if personalization_indicators >= 2 else "moderate" if personalization_indicators >= 1 else "low"
    
    async def cleanup(self):
        """Clean shutdown"""
        if self.memory_service:
            await self.memory_service.cleanup()
            logger.debug("[MEMORY_INTEGRATION] Service cleaned up")

# Convenience function for easy integration
async def create_memory_enhanced_analysis_context(user_id: str) -> MemoryEnhancedContext:
    """
    Convenience function to create memory-enhanced context
    Used by analysis endpoints
    """
    service = MemoryIntegrationService()
    try:
        context = await service.prepare_memory_enhanced_context(user_id)
        return context
    finally:
        await service.cleanup()