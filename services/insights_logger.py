"""
Insights Logging Service
Handles logging of insights to both output files and dedicated insights files
"""
import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional

class InsightsLogger:
    """Logger for insights with integration into existing log system"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
    
    async def get_next_analysis_number(self) -> int:
        """Get next analysis number (same logic as main system)"""
        try:
            existing_files = glob.glob(f"{self.logs_dir}/input_*.txt")
            if not existing_files:
                return 1
            
            numbers = []
            for filename in existing_files:
                try:
                    number = int(filename.split('_')[1].split('.')[0])
                    numbers.append(number)
                except (ValueError, IndexError):
                    continue
            
            return max(numbers) + 1 if numbers else 1
        except Exception as e:
            # print(f"[INSIGHTS_LOGGER] Error getting analysis number: {e}")  # Commented for error-only mode
            return 1
    
    async def log_insights_to_output_file(self, 
                                        analysis_number: int, 
                                        insights: List[Dict[str, Any]], 
                                        source: str = "insights_api",
                                        user_id: str = None,
                                        archetype: str = None) -> bool:
        """Add insights to existing output file"""
        try:
            output_file = f"{self.logs_dir}/output_{analysis_number}.txt"
            
            # Read existing output file if it exists
            existing_data = {}
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = {}
            
            # Add insights section to existing data
            insights_section = {
                "timestamp": datetime.now().isoformat(),
                "source": source,
                "user_id": user_id,
                "archetype": archetype,
                "insights_count": len(insights),
                "insights": insights
            }
            
            # Add to existing data structure
            if "insights" not in existing_data:
                existing_data["insights"] = []
            existing_data["insights"].append(insights_section)
            
            # Write back to file
            with open(output_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            # print(f"📝 [INSIGHTS_LOGGER] Added {len(insights)} insights to output_{analysis_number}.txt")  # Commented for error-only mode
            return True
            
        except Exception as e:
            # print(f"❌ [INSIGHTS_LOGGER] Failed to log to output file: {e}")  # Commented for error-only mode
            return False
    
    async def create_dedicated_insights_log(self, 
                                          insights: List[Dict[str, Any]], 
                                          source: str = "insights_api",
                                          user_id: str = None,
                                          archetype: str = None,
                                          analysis_number: Optional[int] = None) -> bool:
        """Create dedicated insights log file"""
        try:
            if analysis_number is None:
                analysis_number = await self.get_next_analysis_number()
            
            insights_file = f"{self.logs_dir}/insights_{analysis_number}.txt"
            
            insights_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "source": source,
                "user_id": user_id,
                "archetype": archetype,
                "total_insights": len(insights),
                "insights": insights,
                "metadata": {
                    "generated_by": "HolisticOS Insights System",
                    "log_type": "insights",
                    "version": "1.0"
                }
            }
            
            with open(insights_file, 'w') as f:
                json.dump(insights_data, f, indent=2, default=str)
            
            # print(f"📝 [INSIGHTS_LOGGER] Created dedicated insights log: insights_{analysis_number}.txt")  # Commented for error-only mode
            return True
            
        except Exception as e:
            # print(f"❌ [INSIGHTS_LOGGER] Failed to create dedicated log: {e}")  # Commented for error-only mode
            return False
    
    async def log_insights_comprehensive(self, 
                                       insights: List[Dict[str, Any]], 
                                       source: str = "insights_api",
                                       user_id: str = None,
                                       archetype: str = None,
                                       add_to_output: bool = True,
                                       create_dedicated: bool = True) -> Dict[str, Any]:
        """Comprehensive insights logging - both to output file and dedicated file"""
        try:
            analysis_number = await self.get_next_analysis_number()
            results = {
                "analysis_number": analysis_number,
                "output_file_success": False,
                "dedicated_file_success": False,
                "insights_count": len(insights)
            }
            
            # Log to output file (append to existing analysis results)
            if add_to_output:
                results["output_file_success"] = await self.log_insights_to_output_file(
                    analysis_number, insights, source, user_id, archetype
                )
            
            # Create dedicated insights file
            if create_dedicated:
                results["dedicated_file_success"] = await self.create_dedicated_insights_log(
                    insights, source, user_id, archetype, analysis_number
                )
            
            # Summary log
            if results["output_file_success"] or results["dedicated_file_success"]:
                print(f"✅ [INSIGHTS_LOGGER] Successfully logged {len(insights)} insights (Analysis #{analysis_number})")
                if results["output_file_success"]:
                    print(f"   📄 Added to: logs/output_{analysis_number}.txt")
                if results["dedicated_file_success"]:
                    print(f"   📋 Created: logs/insights_{analysis_number}.txt")
            
            return results
            
        except Exception as e:
            # print(f"❌ [INSIGHTS_LOGGER] Comprehensive logging failed: {e}")  # Commented for error-only mode
            return {"error": str(e), "insights_count": len(insights)}
    
    async def get_recent_insights_logs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent insights from log files"""
        try:
            insights_files = glob.glob(f"{self.logs_dir}/insights_*.txt")
            insights_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            recent_insights = []
            for insights_file in insights_files[:limit]:
                try:
                    with open(insights_file, 'r') as f:
                        data = json.load(f)
                        recent_insights.append({
                            "file": os.path.basename(insights_file),
                            "timestamp": data.get("timestamp"),
                            "user_id": data.get("user_id"),
                            "insights_count": data.get("total_insights", 0),
                            "source": data.get("source")
                        })
                except Exception as e:
                    # print(f"⚠️ [INSIGHTS_LOGGER] Could not read {insights_file}: {e}")  # Commented for error-only mode
                    continue
            
            return recent_insights
            
        except Exception as e:
            print(f"❌ [INSIGHTS_LOGGER] Failed to get recent insights: {e}")
            return []

# Global instance
insights_logger = InsightsLogger()