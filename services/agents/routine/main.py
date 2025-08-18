"""
HolisticOS Routine Plan Agent
Integrates existing routine planning logic with HolisticOS system prompts and event-driven architecture
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from shared_libs.event_system.base_agent import BaseAgent
from shared_libs.utils.system_prompts import get_system_prompt

# Import existing logic from original agents
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../health-agent-main/health_agents'))

from routine_plan_agent import (
    RoutinePlanService, 
    RoutinePlanResult,
    create_personalized_routine_plan
)
from supabase_adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)

class HolisticRoutineAgent(BaseAgent):
    """
    HolisticOS Routine Plan Agent
    
    Combines existing routine planning functionality with HolisticOS system architecture
    Features:
    - Preserves existing Supabase data fetching mechanism
    - Integrates HolisticOS system prompts for enhanced planning
    - Event-driven communication with other agents
    - Multi-archetype support for personalized routine planning
    """
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="routine_plan_agent",
            agent_type="plan_generation"  # Uses HolisticOS plan generation prompts
        )
        
        # Initialize existing routine service
        self.routine_service = RoutinePlanService()
        
        # Initialize Supabase adapter to preserve existing data flow
        self.supabase = SupabaseAsyncPGAdapter()
        
        logger.debug(f"Initialized HolisticRoutineAgent with system prompt length: {len(self.system_prompt)}")
        logger.debug(f"Available archetypes: {self.routine_service.get_available_archetypes()}")
    
    async def process_message(self, message_type: str, data: dict) -> dict:
        """
        Process incoming messages from the event system
        
        Handles:
        - routine_plan_request: Create personalized routine plan
        - user_data_update: Update user context
        - archetype_update: Change user archetype preference
        """
        try:
            if message_type == "routine_plan_request":
                return await self._handle_routine_request(data)
            elif message_type == "user_data_update":
                return await self._handle_user_update(data)
            elif message_type == "archetype_update":
                return await self._handle_archetype_update(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {"status": "error", "message": f"Unknown message type: {message_type}"}
                
        except Exception as e:
            logger.error(f"Error processing message {message_type}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_routine_request(self, data: dict) -> dict:
        """Handle routine plan generation request"""
        try:
            user_id = data.get("user_id")
            archetype = data.get("archetype", "Foundation Builder")  # Default archetype
            behavior_analysis = data.get("behavior_analysis")
            
            if not user_id:
                return {"status": "error", "message": "user_id is required"}
            
            # Validate archetype
            available_archetypes = self.routine_service.get_available_archetypes()
            if archetype not in available_archetypes:
                logger.warning(f"Invalid archetype {archetype}, using Foundation Builder")
                archetype = "Foundation Builder"
            
            # Get user context from Supabase (preserving existing data flow)
            user_context = await self.supabase.get_user_context(user_id)
            if not user_context:
                return {"status": "error", "message": f"No user context found for user_id: {user_id}"}
            
            # Log input data (preserving existing logging pattern)
            await self._log_input_data(user_id, user_context, archetype, behavior_analysis)
            
            # Generate routine plan using existing service with HolisticOS enhancements
            routine_result = await self._create_enhanced_routine_plan(
                user_context, 
                archetype,
                behavior_analysis
            )
            
            # Log output data
            await self._log_output_data(user_id, routine_result, archetype)
            
            # Publish completion event
            await self.publish_event("routine_plan_completed", {
                "user_id": user_id,
                "routine_plan": routine_result.dict(),
                "archetype": archetype,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            })
            
            return {
                "status": "success",
                "routine_plan": routine_result.dict(),
                "archetype": archetype,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Error handling routine request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _create_enhanced_routine_plan(
        self, 
        user_context, 
        archetype: str = "Foundation Builder",
        behavior_analysis: Optional[dict] = None
    ) -> RoutinePlanResult:
        """
        Create enhanced routine plan using HolisticOS system prompts
        
        Combines existing routine logic with HolisticOS system architecture
        """
        try:
            # Use existing routine service but with HolisticOS enhancements
            result = await create_personalized_routine_plan(
                user_context, 
                archetype,
                behavior_analysis
            )
            
            # Enhanced with HolisticOS system context
            if hasattr(result, 'routine') and hasattr(result.routine, 'summary'):
                enhanced_summary = f"""
{self.system_prompt[:200]}...

{archetype.upper()} ROUTINE ANALYSIS:
{result.routine.summary}

This routine plan is generated using HolisticOS intelligent agents optimized for your {archetype} archetype, 
specific health profile, and behavioral patterns.
"""
                result.routine.summary = enhanced_summary
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating enhanced routine plan: {str(e)}")
            # Return fallback result
            return RoutinePlanResult(
                date=datetime.now().strftime("%Y-%m-%d"),
                routine=self._create_fallback_routine(archetype)
            )
    
    def _create_fallback_routine(self, archetype: str):
        """Create fallback routine plan in case of errors"""
        from routine_plan_agent import (
            DailyRoutine, RoutineTimeBlock, RoutineTask
        )
        
        return DailyRoutine(
            summary=f"HolisticOS {archetype} Routine Agent - Fallback plan due to processing error",
            morning_wakeup=RoutineTimeBlock(
                time_range="6:00-7:00 AM",
                why_it_matters=f"Gentle {archetype}-style morning routine to start the day",
                tasks=[
                    RoutineTask(
                        task="Hydration and light stretching",
                        reason="Foundation building for the day ahead"
                    ),
                    RoutineTask(
                        task="5-minute mindfulness or gratitude practice",
                        reason="Mental clarity and positive mindset"
                    )
                ]
            ),
            focus_block=RoutineTimeBlock(
                time_range="9:00-11:00 AM",
                why_it_matters="Peak cognitive performance window",
                tasks=[
                    RoutineTask(
                        task="Priority task work with focus technique",
                        reason="Maximizing productive output during peak hours"
                    ),
                    RoutineTask(
                        task="Movement break every 45 minutes",
                        reason="Maintaining energy and preventing fatigue"
                    )
                ]
            ),
            afternoon_recharge=RoutineTimeBlock(
                time_range="3:00-3:30 PM",
                why_it_matters="Energy restoration and afternoon productivity boost",
                tasks=[
                    RoutineTask(
                        task="10-minute walk or light movement",
                        reason="Combating afternoon energy dip"
                    ),
                    RoutineTask(
                        task="Healthy snack and hydration",
                        reason="Sustained energy for remainder of day"
                    )
                ]
            ),
            evening_winddown=RoutineTimeBlock(
                time_range="8:30-9:30 PM", 
                why_it_matters="Preparation for restorative sleep",
                tasks=[
                    RoutineTask(
                        task="Light stretching or relaxation exercise",
                        reason="Physical and mental transition to rest"
                    ),
                    RoutineTask(
                        task="Reflection on the day and tomorrow's priorities",
                        reason="Mental closure and preparation for tomorrow"
                    )
                ]
            )
        )
    
    async def _handle_user_update(self, data: dict) -> dict:
        """Handle user data updates"""
        try:
            user_id = data.get("user_id")
            update_type = data.get("update_type", "general")
            
            logger.debug(f"Processing user update for {user_id}: {update_type}")
            
            return {"status": "success", "message": "User update processed"}
            
        except Exception as e:
            logger.error(f"Error handling user update: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_archetype_update(self, data: dict) -> dict:
        """Handle archetype preference updates"""
        try:
            user_id = data.get("user_id")
            new_archetype = data.get("archetype")
            
            # Validate archetype
            available_archetypes = self.routine_service.get_available_archetypes()
            if new_archetype not in available_archetypes:
                return {
                    "status": "error", 
                    "message": f"Invalid archetype. Available options: {', '.join(available_archetypes)}"
                }
            
            logger.debug(f"Updating archetype for {user_id} to {new_archetype}")
            
            # In a full implementation, you might store this preference in the database
            # For now, just acknowledge the update
            
            return {
                "status": "success", 
                "message": f"Archetype updated to {new_archetype}",
                "archetype": new_archetype,
                "available_archetypes": available_archetypes
            }
            
        except Exception as e:
            logger.error(f"Error handling archetype update: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _log_input_data(self, user_id: str, user_context, archetype: str, behavior_analysis=None):
        """Log input data for debugging and analysis (preserving existing pattern)"""
        try:
            # Get next input file number (preserving existing numbering system)
            input_file_number = await self._get_next_file_number("input")
            
            input_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_type": "routine_plan",
                "user_id": user_id,
                "archetype": archetype,
                "user_context_summary": {
                    "date_range": str(user_context.date_range) if hasattr(user_context, 'date_range') else "N/A",
                    "scores_count": len(user_context.scores) if hasattr(user_context, 'scores') else 0,
                    "biomarkers_count": len(user_context.biomarkers) if hasattr(user_context, 'biomarkers') else 0
                },
                "behavior_analysis_available": behavior_analysis is not None,
                "system_prompt_length": len(self.system_prompt),
                "available_archetypes": self.routine_service.get_available_archetypes()
            }
            
            # Write to input file (preserving existing pattern)
            input_file_path = f"/mnt/c/dev_skoth/health-agent-main/holisticos-mvp/logs/input_{input_file_number}.txt"
            os.makedirs(os.path.dirname(input_file_path), exist_ok=True)
            
            with open(input_file_path, 'w') as f:
                f.write(json.dumps(input_data, indent=2, default=str))
            
            logger.debug(f"Input data logged to {input_file_path}")
            
        except Exception as e:
            logger.error(f"Error logging input data: {str(e)}")
    
    async def _log_output_data(self, user_id: str, routine_result: RoutinePlanResult, archetype: str):
        """Log output data for debugging and analysis"""
        try:
            # Get corresponding output file number
            output_file_number = await self._get_next_file_number("output")
            
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_type": "routine_plan", 
                "user_id": user_id,
                "archetype": archetype,
                "routine_plan": routine_result.dict(),
                "agent_id": self.agent_id
            }
            
            # Write to output file
            output_file_path = f"/mnt/c/dev_skoth/health-agent-main/holisticos-mvp/logs/output_{output_file_number}.txt"
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            with open(output_file_path, 'w') as f:
                f.write(json.dumps(output_data, indent=2, default=str))
            
            logger.debug(f"Output data logged to {output_file_path}")
            
        except Exception as e:
            logger.error(f"Error logging output data: {str(e)}")
    
    async def _get_next_file_number(self, file_type: str) -> int:
        """Get next available file number for logging (preserving existing pattern)"""
        try:
            log_dir = "/mnt/c/dev_skoth/health-agent-main/holisticos-mvp/logs"
            os.makedirs(log_dir, exist_ok=True)
            
            existing_files = [f for f in os.listdir(log_dir) if f.startswith(f"{file_type}_") and f.endswith('.txt')]
            
            if not existing_files:
                return 1
            
            numbers = []
            for filename in existing_files:
                try:
                    number = int(filename.replace(f"{file_type}_", "").replace(".txt", ""))
                    numbers.append(number)
                except ValueError:
                    continue
            
            return max(numbers) + 1 if numbers else 1
            
        except Exception as e:
            logger.error(f"Error getting next file number: {str(e)}")
            return 1

# Entry point for running the agent standalone
async def main():
    """Run the routine agent in standalone mode for testing"""
    agent = HolisticRoutineAgent()
    
    print("🏃‍♂️ HolisticOS Routine Agent Started")
    print(f"Available archetypes: {agent.routine_service.get_available_archetypes()}")
    print("Waiting for events...")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Routine Agent")

if __name__ == "__main__":
    asyncio.run(main())