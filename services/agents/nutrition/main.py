"""
HolisticOS Nutrition Plan Agent
Integrates existing nutrition planning logic with HolisticOS system prompts and event-driven architecture
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

from nutrition_plan_agent import (
    NutritionPlanService, 
    NutritionPlanResult,
    create_personalized_nutrition_plan
)
from supabase_adapter import SupabaseAsyncPGAdapter

logger = logging.getLogger(__name__)

class HolisticNutritionAgent(BaseAgent):
    """
    HolisticOS Nutrition Plan Agent
    
    Combines existing nutrition planning functionality with HolisticOS system architecture
    Features:
    - Preserves existing Supabase data fetching mechanism
    - Integrates HolisticOS system prompts for enhanced planning
    - Event-driven communication with other agents
    - Structured output with comprehensive meal planning
    """
    
    def __init__(self, redis_url: str = None):
        super().__init__(
            agent_id="nutrition_plan_agent",
            agent_type="plan_generation"  # Uses HolisticOS plan generation prompts
        )
        
        # Initialize existing nutrition service
        self.nutrition_service = NutritionPlanService()
        
        # Initialize Supabase adapter to preserve existing data flow
        self.supabase = SupabaseAsyncPGAdapter()
        
        logger.info(f"Initialized HolisticNutritionAgent with system prompt length: {len(self.system_prompt)}")
    
    async def process_message(self, message_type: str, data: dict) -> dict:
        """
        Process incoming messages from the event system
        
        Handles:
        - nutrition_plan_request: Create personalized nutrition plan
        - user_data_update: Update user context
        """
        try:
            if message_type == "nutrition_plan_request":
                return await self._handle_nutrition_request(data)
            elif message_type == "user_data_update":
                return await self._handle_user_update(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return {"status": "error", "message": f"Unknown message type: {message_type}"}
                
        except Exception as e:
            logger.error(f"Error processing message {message_type}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _handle_nutrition_request(self, data: dict) -> dict:
        """Handle nutrition plan generation request"""
        try:
            user_id = data.get("user_id")
            behavior_analysis = data.get("behavior_analysis")
            
            if not user_id:
                return {"status": "error", "message": "user_id is required"}
            
            # Get user context from Supabase (preserving existing data flow)
            user_context = await self.supabase.get_user_context(user_id)
            if not user_context:
                return {"status": "error", "message": f"No user context found for user_id: {user_id}"}
            
            # Log input data (preserving existing logging pattern)
            await self._log_input_data(user_id, user_context, behavior_analysis)
            
            # Generate nutrition plan using existing service with HolisticOS enhancements
            nutrition_result = await self._create_enhanced_nutrition_plan(
                user_context, 
                behavior_analysis
            )
            
            # Log output data
            await self._log_output_data(user_id, nutrition_result)
            
            # Publish completion event
            await self.publish_event("nutrition_plan_completed", {
                "user_id": user_id,
                "nutrition_plan": nutrition_result.dict(),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            })
            
            return {
                "status": "success",
                "nutrition_plan": nutrition_result.dict(),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            logger.error(f"Error handling nutrition request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _create_enhanced_nutrition_plan(
        self, 
        user_context, 
        behavior_analysis: Optional[dict] = None
    ) -> NutritionPlanResult:
        """
        Create enhanced nutrition plan using HolisticOS system prompts
        
        Combines existing nutrition logic with HolisticOS system architecture
        """
        try:
            # Use existing nutrition service but with HolisticOS enhancements
            result = await create_personalized_nutrition_plan(
                user_context, 
                behavior_analysis
            )
            
            # Enhanced with HolisticOS system context
            if hasattr(result, 'nutrition') and hasattr(result.nutrition, 'summary'):
                enhanced_summary = f"""
{self.system_prompt[:200]}...

PERSONALIZED NUTRITION ANALYSIS:
{result.nutrition.summary}

This nutrition plan is generated using HolisticOS intelligent agents optimized for your specific health profile and behavioral patterns.
"""
                result.nutrition.summary = enhanced_summary
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating enhanced nutrition plan: {str(e)}")
            # Return fallback result
            return NutritionPlanResult(
                date=datetime.now().strftime("%Y-%m-%d"),
                nutrition=self._create_fallback_nutrition()
            )
    
    def _create_fallback_nutrition(self):
        """Create fallback nutrition plan in case of errors"""
        from nutrition_plan_agent import (
            DailyNutrition, NutritionalInfo, VitaminsInfo, 
            NutritionMealBlock, Meal, MealMacros
        )
        
        return DailyNutrition(
            summary="HolisticOS Nutrition Agent - Fallback plan due to processing error",
            nutritional_info=NutritionalInfo(
                calories=2000,
                protein=150,
                protein_percent=30,
                carbs=200,
                carbs_percent=40,
                fat=67,
                fat_percent=30,
                fiber=25,
                sugar=50,
                sodium=2300,
                potassium=3500,
                vitamins=VitaminsInfo(
                    Vitamin_D="1000 IU",
                    Calcium="1000 mg",
                    Iron="18 mg",
                    Magnesium="400 mg"
                )
            ),
            Early_Morning=NutritionMealBlock(
                time_range="5:45-6:15 AM",
                nutrition_tip="Hydration and gentle awakening",
                meals=[Meal(
                    name="Hydration Focus",
                    details="16 oz water with lemon",
                    calories=10,
                    protein=0,
                    macros=MealMacros(carbs=3, fat=0)
                )]
            ),
            Breakfast=NutritionMealBlock(
                time_range="6:30-7:00 AM",
                nutrition_tip="Protein and complex carbs for sustained energy",
                meals=[Meal(
                    name="Balanced Breakfast",
                    details="2 eggs, 1 slice whole grain toast, 1 cup berries",
                    calories=350,
                    protein=20,
                    macros=MealMacros(carbs=35, fat=15)
                )]
            ),
            Morning_Snack=NutritionMealBlock(
                time_range="9:30-10:00 AM",
                nutrition_tip="Mid-morning energy maintenance",
                meals=[Meal(
                    name="Protein Snack",
                    details="Greek yogurt with nuts",
                    calories=150,
                    protein=15,
                    macros=MealMacros(carbs=10, fat=8)
                )]
            ),
            Lunch=NutritionMealBlock(
                time_range="12:00-12:30 PM",
                nutrition_tip="Midday fuel for afternoon productivity",
                meals=[Meal(
                    name="Balanced Lunch",
                    details="Grilled chicken salad with quinoa",
                    calories=450,
                    protein=35,
                    macros=MealMacros(carbs=40, fat=18)
                )]
            ),
            Afternoon_Snack=NutritionMealBlock(
                time_range="3:00-3:30 PM",
                nutrition_tip="Energy maintenance and recovery",
                meals=[Meal(
                    name="Recovery Snack",
                    details="Apple with almond butter",
                    calories=200,
                    protein=8,
                    macros=MealMacros(carbs=25, fat=12)
                )]
            ),
            Dinner=NutritionMealBlock(
                time_range="6:00-6:30 PM",
                nutrition_tip="Evening nutrition for recovery",
                meals=[Meal(
                    name="Recovery Dinner",
                    details="Salmon with sweet potato and vegetables",
                    calories=500,
                    protein=40,
                    macros=MealMacros(carbs=45, fat=20)
                )]
            ),
            Evening_Snack=NutritionMealBlock(
                time_range="8:30-9:00 PM",
                nutrition_tip="Light nutrition for sleep support",
                meals=[Meal(
                    name="Sleep Support",
                    details="Herbal tea with small portion of nuts",
                    calories=100,
                    protein=3,
                    macros=MealMacros(carbs=5, fat=8)
                )]
            )
        )
    
    async def _handle_user_update(self, data: dict) -> dict:
        """Handle user data updates"""
        try:
            user_id = data.get("user_id")
            update_type = data.get("update_type", "general")
            
            logger.info(f"Processing user update for {user_id}: {update_type}")
            
            return {"status": "success", "message": "User update processed"}
            
        except Exception as e:
            logger.error(f"Error handling user update: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _log_input_data(self, user_id: str, user_context, behavior_analysis=None):
        """Log input data for debugging and analysis (preserving existing pattern)"""
        try:
            # Get next input file number (preserving existing numbering system)
            input_file_number = await self._get_next_file_number("input")
            
            input_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_type": "nutrition_plan",
                "user_id": user_id,
                "user_context_summary": {
                    "date_range": str(user_context.date_range) if hasattr(user_context, 'date_range') else "N/A",
                    "scores_count": len(user_context.scores) if hasattr(user_context, 'scores') else 0,
                    "biomarkers_count": len(user_context.biomarkers) if hasattr(user_context, 'biomarkers') else 0
                },
                "behavior_analysis_available": behavior_analysis is not None,
                "system_prompt_length": len(self.system_prompt)
            }
            
            # Write to input file (preserving existing pattern)
            input_file_path = f"/mnt/c/dev_skoth/health-agent-main/holisticos-mvp/logs/input_{input_file_number}.txt"
            os.makedirs(os.path.dirname(input_file_path), exist_ok=True)
            
            with open(input_file_path, 'w') as f:
                f.write(json.dumps(input_data, indent=2, default=str))
            
            logger.info(f"Input data logged to {input_file_path}")
            
        except Exception as e:
            logger.error(f"Error logging input data: {str(e)}")
    
    async def _log_output_data(self, user_id: str, nutrition_result: NutritionPlanResult):
        """Log output data for debugging and analysis"""
        try:
            # Get corresponding output file number
            output_file_number = await self._get_next_file_number("output")
            
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "agent_type": "nutrition_plan", 
                "user_id": user_id,
                "nutrition_plan": nutrition_result.dict(),
                "agent_id": self.agent_id
            }
            
            # Write to output file
            output_file_path = f"/mnt/c/dev_skoth/health-agent-main/holisticos-mvp/logs/output_{output_file_number}.txt"
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            with open(output_file_path, 'w') as f:
                f.write(json.dumps(output_data, indent=2, default=str))
            
            logger.info(f"Output data logged to {output_file_path}")
            
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
    """Run the nutrition agent in standalone mode for testing"""
    agent = HolisticNutritionAgent()
    
    print("🥗 HolisticOS Nutrition Agent Started")
    print("Waiting for events...")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Nutrition Agent")

if __name__ == "__main__":
    asyncio.run(main())