"""
Enhanced Memory Prompt Service - Phase 4.2 Sprint 1
Transforms generic agent prompts into memory-informed, personalized coaching prompts

Key Functions:
1. Memory Context Building: Constructs comprehensive 4-layer memory context
2. Agent-Specific Enhancement: Tailors memory context for each agent type
3. Personalization Instructions: Adds specific guidance for using memory data
4. Progressive Intelligence: Leverages all memory layers for optimal personalization
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .holistic_memory_service import HolisticMemoryService

logger = logging.getLogger(__name__)

class EnhancedMemoryPromptsService:
    """
    Service to enhance agent prompts with comprehensive 4-layer memory context
    
    Transforms basic prompts into memory-informed coaching that references:
    - Long-term patterns and preferences
    - Short-term changes and adaptations  
    - Meta-learning insights
    - Working memory context
    """
    
    def __init__(self):
        self.memory_service = HolisticMemoryService()
        self.context_cache = {}  # Cache memory contexts for short periods
        self.cache_duration_minutes = 10  # Cache contexts for 10 minutes
        
    async def enhance_agent_prompt(self, base_prompt: str, user_id: str, agent_type: str) -> str:
        """
        Add comprehensive 4-layer memory context to any agent prompt
        
        Args:
            base_prompt: Original system prompt for the agent
            user_id: User ID for memory retrieval
            agent_type: Type of agent (behavior_analysis, nutrition_planning, routine_planning, insights_generation)
            
        Returns:
            Enhanced prompt with full memory context and personalization instructions
        """
        try:
            logger.info(f"Enhancing {agent_type} prompt with memory context for user {user_id[:8]}...")
            
            # Get comprehensive memory context
            memory_context = await self._build_comprehensive_memory_context(user_id, agent_type)
            
            # Add agent-specific memory enhancement
            agent_specific_context = await self._add_agent_specific_context(user_id, agent_type)
            
            # Combine all contexts
            full_memory_context = f"{memory_context}\n\n{agent_specific_context}"
            
            # Build enhanced prompt
            enhanced_prompt = f"""{base_prompt}

{full_memory_context}

CRITICAL PERSONALIZATION INSTRUCTIONS FOR {agent_type.upper().replace('_', ' ')}:

1. REFERENCE SPECIFIC MEMORY: Always reference specific past successes, failures, and patterns from the user's memory profile above
2. BUILD ON ESTABLISHED PATTERNS: Use established behavioral patterns rather than starting with generic recommendations
3. AVOID FAILED APPROACHES: Explicitly avoid strategies that have failed before (check failure patterns in memory)
4. ADAPT TO LEARNING VELOCITY: Use the user's learning velocity from meta-memory to pace your recommendations appropriately
5. CONSIDER RECENT CHANGES: Factor in any recent preference changes or pattern shifts from short-term memory
6. LEVERAGE META-INSIGHTS: Use meta-memory insights about how this user learns best to optimize your approach
7. PERSONALIZE LANGUAGE: Adapt your communication style based on the user's historical response patterns

MEMORY-INFORMED OUTPUT REQUIREMENTS:
- Begin analysis by acknowledging what you know about this user from their memory profile
- Reference specific past experiences when making recommendations
- Explain why recommendations build on or diverge from previous successful strategies
- Adapt complexity and pacing based on user's demonstrated learning patterns
- Connect current analysis to historical trends and patterns"""

            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error enhancing prompt for {agent_type}: {e}")
            # Return original prompt if enhancement fails
            return f"{base_prompt}\n\nNote: Memory enhancement temporarily unavailable - using standard analysis."
    
    async def _build_comprehensive_memory_context(self, user_id: str, agent_type: str) -> str:
        """
        Build rich memory context from all 4 layers
        
        Returns formatted memory context string with all relevant user data
        """
        try:
            # Check cache first
            cache_key = f"{user_id}_{agent_type}"
            if self._is_cache_valid(cache_key):
                return self.context_cache[cache_key]['context']
            
            # Get all memory layers
            longterm = await self.memory_service.get_user_longterm_memory(user_id)
            recent_patterns = await self.memory_service.get_recent_patterns(user_id, days=7)
            meta_memory = await self.memory_service.get_meta_memory(user_id)
            working_memory = await self.memory_service.get_working_memory(user_id)
            
            # Format comprehensive memory context
            memory_context = f"""
═══════════════════════════════════════════════════════════════════════
USER MEMORY PROFILE - 4-Layer Intelligence System
═══════════════════════════════════════════════════════════════════════

🧠 LONG-TERM MEMORY (What we know works/fails for this user):
{self._format_longterm_memory(longterm)}

📊 SHORT-TERM MEMORY (Recent changes and adaptations - Last 7 days):
{self._format_shortterm_memory(recent_patterns)}

🎯 META-MEMORY (How this user learns and adapts):
{self._format_meta_memory(meta_memory)}

💭 WORKING MEMORY (Current session context):
{self._format_working_memory(working_memory)}

═══════════════════════════════════════════════════════════════════════
MEMORY-BASED INSIGHTS FOR PERSONALIZATION:
═══════════════════════════════════════════════════════════════════════
{self._generate_memory_insights(longterm, recent_patterns, meta_memory, working_memory)}
"""

            # Cache the context
            self.context_cache[cache_key] = {
                'context': memory_context,
                'timestamp': datetime.now()
            }
            
            return memory_context
            
        except Exception as e:
            logger.error(f"Error building memory context: {e}")
            return f"""
USER MEMORY PROFILE - Limited Data Available:
- Memory service temporarily unavailable
- Using standard analysis approach
- Error: {str(e)}
"""
    
    def _format_longterm_memory(self, longterm_memory) -> str:
        """Format long-term memory data for prompt context"""
        if not longterm_memory:
            return "• No established long-term patterns yet (new user)"
        
        try:
            formatted = []
            
            # Behavioral patterns
            if hasattr(longterm_memory, 'behavioral_patterns') and longterm_memory.behavioral_patterns:
                patterns = longterm_memory.behavioral_patterns
                formatted.append(f"• Behavioral Patterns: {self._format_dict_insights(patterns)}")
            
            # Health goals
            if hasattr(longterm_memory, 'health_goals') and longterm_memory.health_goals:
                goals = longterm_memory.health_goals
                formatted.append(f"• Health Goals: {self._format_dict_insights(goals)}")
            
            # Preference patterns
            if hasattr(longterm_memory, 'preference_patterns') and longterm_memory.preference_patterns:
                prefs = longterm_memory.preference_patterns
                formatted.append(f"• Established Preferences: {self._format_dict_insights(prefs)}")
            
            # Success strategies
            if hasattr(longterm_memory, 'success_strategies') and longterm_memory.success_strategies:
                success = longterm_memory.success_strategies
                formatted.append(f"• Proven Success Strategies: {self._format_dict_insights(success)}")
            
            # Failure patterns
            if hasattr(longterm_memory, 'failure_patterns') and longterm_memory.failure_patterns:
                failures = longterm_memory.failure_patterns
                formatted.append(f"• Known Failure Patterns (AVOID): {self._format_dict_insights(failures)}")
            
            return '\n'.join(formatted) if formatted else "• Long-term patterns still developing"
            
        except Exception as e:
            return f"• Long-term memory format error: {e}"
    
    def _format_shortterm_memory(self, recent_patterns) -> str:
        """Format short-term memory data for prompt context"""
        if not recent_patterns:
            return "• No recent pattern changes detected"
        
        try:
            formatted = []
            
            # Recent pattern shifts
            if hasattr(recent_patterns, 'pattern_shifts') and recent_patterns.pattern_shifts:
                shifts = recent_patterns.pattern_shifts
                formatted.append(f"• Recent Pattern Shifts: {self._format_list_insights(shifts)}")
            
            # Adherence trends
            if hasattr(recent_patterns, 'adherence_trends') and recent_patterns.adherence_trends:
                adherence = recent_patterns.adherence_trends
                formatted.append(f"• Adherence Trends: {self._format_dict_insights(adherence)}")
            
            # Preference changes
            if hasattr(recent_patterns, 'preference_changes') and recent_patterns.preference_changes:
                changes = recent_patterns.preference_changes
                formatted.append(f"• Recent Preference Changes: {self._format_list_insights(changes)}")
            
            # Engagement patterns
            if hasattr(recent_patterns, 'engagement_patterns') and recent_patterns.engagement_patterns:
                engagement = recent_patterns.engagement_patterns
                formatted.append(f"• Engagement Patterns: {self._format_dict_insights(engagement)}")
            
            return '\n'.join(formatted) if formatted else "• No significant recent changes"
            
        except Exception as e:
            return f"• Short-term memory format error: {e}"
    
    def _format_meta_memory(self, meta_memory) -> str:
        """Format meta-memory data for prompt context"""
        if not meta_memory:
            return "• Meta-learning patterns still developing"
        
        try:
            formatted = []
            
            # Learning velocity
            if hasattr(meta_memory, 'learning_velocity') and meta_memory.learning_velocity:
                velocity = meta_memory.learning_velocity
                formatted.append(f"• Learning Velocity: {self._format_dict_insights(velocity)}")
            
            # Adaptation patterns
            if hasattr(meta_memory, 'adaptation_patterns') and meta_memory.adaptation_patterns:
                adaptation = meta_memory.adaptation_patterns
                formatted.append(f"• Adaptation Patterns: {self._format_dict_insights(adaptation)}")
            
            # Success predictors
            if hasattr(meta_memory, 'success_predictors') and meta_memory.success_predictors:
                predictors = meta_memory.success_predictors
                formatted.append(f"• Success Predictors: {self._format_dict_insights(predictors)}")
            
            # Effective approaches
            if hasattr(meta_memory, 'effective_approaches') and meta_memory.effective_approaches:
                approaches = meta_memory.effective_approaches
                formatted.append(f"• Most Effective Approaches: {self._format_dict_insights(approaches)}")
            
            # Response patterns
            if hasattr(meta_memory, 'response_patterns') and meta_memory.response_patterns:
                responses = meta_memory.response_patterns
                formatted.append(f"• Response Patterns: {self._format_dict_insights(responses)}")
            
            return '\n'.join(formatted) if formatted else "• Meta-learning insights developing"
            
        except Exception as e:
            return f"• Meta-memory format error: {e}"
    
    def _format_working_memory(self, working_memory) -> str:
        """Format working memory data for prompt context"""
        if not working_memory:
            return "• No current session context"
        
        try:
            formatted = []
            
            # Session goals
            if hasattr(working_memory, 'session_goals') and working_memory.session_goals:
                goals = working_memory.session_goals
                formatted.append(f"• Current Session Goals: {self._format_list_insights(goals)}")
            
            # Immediate feedback
            if hasattr(working_memory, 'recent_feedback') and working_memory.recent_feedback:
                feedback = working_memory.recent_feedback
                formatted.append(f"• Recent User Feedback: {self._format_list_insights(feedback)}")
            
            # Context data
            if hasattr(working_memory, 'context_data') and working_memory.context_data:
                context = working_memory.context_data
                formatted.append(f"• Session Context: {self._format_dict_insights(context)}")
            
            return '\n'.join(formatted) if formatted else "• Session context available"
            
        except Exception as e:
            return f"• Working memory format error: {e}"
    
    def _generate_memory_insights(self, longterm, recent_patterns, meta_memory, working_memory) -> str:
        """Generate actionable insights from memory data"""
        insights = []
        
        try:
            # Analyze patterns across memory layers
            if longterm and recent_patterns:
                insights.append("✓ User has established patterns - build on proven strategies")
            
            if meta_memory and hasattr(meta_memory, 'learning_velocity'):
                insights.append("✓ Meta-learning data available - optimize pacing and complexity")
            
            if working_memory:
                insights.append("✓ Session context available - align with current goals")
            
            # Default insight if no specific patterns
            if not insights:
                insights.append("• New user profile - establish baseline and gather preferences")
            
            return '\n'.join(insights)
            
        except Exception as e:
            return f"• Insight generation error: {e}"
    
    async def _add_agent_specific_context(self, user_id: str, agent_type: str) -> str:
        """Add agent-specific memory context and instructions"""
        try:
            if agent_type == "behavior_analysis":
                return await self._add_behavior_specific_context(user_id)
            elif agent_type == "nutrition_planning":
                return await self._add_nutrition_specific_context(user_id)
            elif agent_type == "routine_planning":
                return await self._add_routine_specific_context(user_id)
            elif agent_type == "insights_generation":
                return await self._add_insights_specific_context(user_id)
            else:
                return f"AGENT-SPECIFIC CONTEXT ({agent_type}): Use memory profile to personalize analysis"
                
        except Exception as e:
            logger.error(f"Error adding agent-specific context: {e}")
            return f"AGENT-SPECIFIC CONTEXT: Memory context available for {agent_type}"
    
    async def _add_behavior_specific_context(self, user_id: str) -> str:
        """Add behavior analysis specific memory context"""
        return """
🎯 BEHAVIOR ANALYSIS - MEMORY-ENHANCED INSTRUCTIONS:

ANALYSIS FOCUS AREAS:
1. Compare current patterns against established behavioral patterns from long-term memory
2. Identify deviations from successful strategies (reference success_strategies)
3. Note any recent behavioral shifts from short-term memory
4. Apply meta-learning insights about user's response patterns
5. Consider current session goals from working memory

MEMORY-INFORMED ANALYSIS APPROACH:
• If user has established patterns: Focus on evolution and optimization of proven strategies
• If patterns are shifting: Analyze whether changes are positive adaptations or concerning deviations
• Use failure patterns to identify risks and areas needing attention
• Reference meta-memory to understand how user typically responds to behavioral insights
• Adapt analysis depth based on user's demonstrated learning velocity

OUTPUT REQUIREMENTS:
- Explicitly reference past behavioral successes and how current data relates
- Identify patterns that are consistent with or divergent from user's historical profile
- Provide behavior change recommendations that build on established strengths
- Flag any concerning deviations from successful historical patterns
"""
    
    async def _add_nutrition_specific_context(self, user_id: str) -> str:
        """Add nutrition planning specific memory context"""
        return """
🍎 NUTRITION PLANNING - MEMORY-ENHANCED INSTRUCTIONS:

PLANNING FOCUS AREAS:
1. Reference established dietary preferences and restrictions from long-term memory
2. Build on previously successful nutrition strategies
3. Avoid meal plans that have failed before (check failure patterns)
4. Consider recent preference changes from short-term memory
5. Adapt recommendations based on user's learning velocity and adherence patterns

MEMORY-INFORMED PLANNING APPROACH:
• If user has successful nutrition history: Evolve and optimize proven meal strategies
• If user struggles with adherence: Use meta-memory insights about what motivates this user
• Consider cultural/lifestyle preferences established in long-term memory
• Factor in recent dietary changes or challenges from short-term memory
• Use success predictors to identify nutrition approaches most likely to work

OUTPUT REQUIREMENTS:
- Reference specific past nutrition successes and how current plan builds on them
- Acknowledge established dietary preferences and restrictions
- Explain how recommendations avoid previously unsuccessful approaches
- Include adherence strategies based on user's historical response patterns
- Adapt meal complexity based on user's demonstrated preparation preferences
"""
    
    async def _add_routine_specific_context(self, user_id: str) -> str:
        """Add routine planning specific memory context"""
        return """
🏃 ROUTINE PLANNING - MEMORY-ENHANCED INSTRUCTIONS:

PLANNING FOCUS AREAS:
1. Build on successful exercise patterns from long-term memory
2. Consider time preferences and schedule constraints from established patterns
3. Avoid workout types/intensities that have led to abandonment (failure patterns)
4. Factor in recent activity changes from short-term memory
5. Use meta-memory insights about optimal progression pacing for this user

MEMORY-INFORMED PLANNING APPROACH:
• If user has consistent exercise history: Optimize and progress successful routines
• If user struggles with consistency: Use meta-memory to identify successful motivation strategies
• Reference established preferences for workout timing, intensity, and types
• Consider recent schedule changes or physical condition changes
• Apply success predictors to choose routine formats most likely to be sustained

OUTPUT REQUIREMENTS:
- Explicitly build upon previously successful workout patterns
- Acknowledge user's established time preferences and scheduling constraints
- Avoid exercise modalities that have previously led to routine abandonment
- Include progression strategies based on user's historical adaptation patterns
- Adapt routine complexity based on user's demonstrated consistency patterns
"""
    
    async def _add_insights_specific_context(self, user_id: str) -> str:
        """Add insights generation specific memory context"""
        return """
🔍 INSIGHTS GENERATION - MEMORY-ENHANCED INSTRUCTIONS:

INSIGHT FOCUS AREAS:
1. Analyze patterns across all memory layers to identify deep insights
2. Compare current analysis against historical analysis results
3. Identify breakthrough patterns and concerning trend reversals
4. Use meta-memory to predict user's likely response to different insight types
5. Generate actionable insights that align with user's proven learning style

MEMORY-INFORMED INSIGHT APPROACH:
• Cross-reference insights against user's historical data to validate patterns
• Identify insights that contradict or confirm established behavioral patterns
• Use meta-memory to determine optimal insight complexity and presentation style
• Focus on insights that connect to user's established health goals and values
• Generate predictive insights based on user's historical progression patterns

OUTPUT REQUIREMENTS:
- Reference specific historical data points that support or contradict insights
- Connect insights to user's long-term health goals and established patterns
- Provide insight confidence levels based on historical data depth
- Include actionable next steps that align with user's proven success strategies
- Adapt insight complexity based on user's demonstrated analytical preferences
"""
    
    def _format_dict_insights(self, data: Any) -> str:
        """Format dictionary data into readable insights"""
        if not data:
            return "No data available"
        
        try:
            if isinstance(data, dict):
                items = []
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        items.append(f"{key}: {json.dumps(value)[:100]}...")
                    else:
                        items.append(f"{key}: {value}")
                return "; ".join(items[:3])  # Limit to first 3 items
            else:
                return str(data)[:200]  # Limit length
        except Exception:
            return "Data format not accessible"
    
    def _format_list_insights(self, data: Any) -> str:
        """Format list data into readable insights"""
        if not data:
            return "No data available"
        
        try:
            if isinstance(data, list):
                items = [str(item)[:50] for item in data[:3]]  # First 3 items, truncated
                return "; ".join(items)
            else:
                return str(data)[:200]
        except Exception:
            return "Data format not accessible"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached memory context is still valid"""
        if cache_key not in self.context_cache:
            return False
        
        cache_time = self.context_cache[cache_key]['timestamp']
        age_minutes = (datetime.now() - cache_time).total_seconds() / 60
        
        return age_minutes < self.cache_duration_minutes
    
    async def cleanup(self):
        """Clean shutdown"""
        if self.memory_service:
            await self.memory_service.cleanup()
        self.context_cache.clear()

# Convenience function for easy integration
async def enhance_prompt_with_memory(base_prompt: str, user_id: str, agent_type: str) -> str:
    """
    Convenience function to enhance any agent prompt with memory context
    
    Usage:
        enhanced_prompt = await enhance_prompt_with_memory(
            base_prompt="Your system prompt here",
            user_id="user123",
            agent_type="behavior_analysis"
        )
    """
    service = EnhancedMemoryPromptsService()
    try:
        return await service.enhance_agent_prompt(base_prompt, user_id, agent_type)
    finally:
        await service.cleanup()