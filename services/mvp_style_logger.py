"""
MVP-Style Direct File Logger - Enhanced for Complete System Flow
Completely independent of database operations - ensures logs are always created
Captures: Raw Health Data, AI Prompts/Responses, Agent Handoffs, Complete System Flow
"""

import json
import os
import glob
from datetime import datetime
from typing import Dict, Any, Optional, List

# Environment-aware logging
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_DEVELOPMENT = ENVIRONMENT in ["development", "dev"]

class MVPStyleLogger:
    """
    Enhanced direct file logger that captures complete multi-agent system flow
    Never depends on database operations - always creates logs
    """

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        # Ensure logs directory exists
        os.makedirs(logs_dir, exist_ok=True)

        # Create subdirectories for different log types
        self.raw_data_dir = os.path.join(logs_dir, "raw_data")
        self.agent_handoffs_dir = os.path.join(logs_dir, "agent_handoffs")
        self.ai_interactions_dir = os.path.join(logs_dir, "ai_interactions")

        for dir_path in [self.raw_data_dir, self.agent_handoffs_dir, self.ai_interactions_dir]:
            os.makedirs(dir_path, exist_ok=True)

    def get_next_analysis_number(self) -> int:
        """Get next analysis number by checking existing files"""
        try:
            # Look for existing input files to determine next number
            existing_files = glob.glob(f"{self.logs_dir}/input_*.txt")

            if not existing_files:
                return 1

            numbers = []
            for filename in existing_files:
                try:
                    # Extract number from filename like "input_5.txt"
                    basename = os.path.basename(filename)
                    number_part = basename.replace("input_", "").replace(".txt", "")
                    number = int(number_part)
                    numbers.append(number)
                except (ValueError, IndexError):
                    continue

            return max(numbers) + 1 if numbers else 1

        except Exception as e:
            print(f"[MVP_LOGGER_ERROR] Error getting analysis number: {e}")
            return 1

    def log_input_data(self, analysis_number: int, input_data: Dict[str, Any]) -> bool:
        """Log input data to input_N.txt file - MVP style"""
        try:
            input_file = f"{self.logs_dir}/input_{analysis_number}.txt"

            # Add metadata
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "log_type": "input",
                "data": input_data
            }

            # Write directly to file (MVP approach)
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

            if IS_DEVELOPMENT:
                pass  # Production: Verbose print removed
            return True

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to log input data: {e}")
            return False

    def log_output_data(self, analysis_number: int, output_data: Dict[str, Any]) -> bool:
        """Log output data to output_N.txt file - MVP style"""
        try:
            output_file = f"{self.logs_dir}/output_{analysis_number}.txt"

            # Add metadata
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "log_type": "output",
                "data": output_data
            }

            # Write directly to file (MVP approach)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

            if IS_DEVELOPMENT:
                pass  # Production: Verbose print removed
            return True

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to log output data: {e}")
            return False

    def log_insights_data(self, analysis_number: int, insights_data: Dict[str, Any]) -> bool:
        """Log insights data to insights_N.txt file - MVP style"""
        try:
            insights_file = f"{self.logs_dir}/insights_{analysis_number}.txt"

            # Add metadata
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "log_type": "insights",
                "data": insights_data
            }

            # Write directly to file (MVP approach)
            with open(insights_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

            if IS_DEVELOPMENT:
                pass  # Production: Verbose print removed
            return True

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to log insights data: {e}")
            return False

    def log_raw_health_data(self, analysis_number: int, raw_data: Dict[str, Any]) -> bool:
        """Log raw health data fetched from APIs"""
        try:
            raw_data_file = os.path.join(self.raw_data_dir, f"raw_health_{analysis_number}.json")

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "log_type": "raw_health_data",
                "data_sources": {
                    "sahha_scores": raw_data.get("sahha_scores", []),
                    "sahha_biomarkers": raw_data.get("sahha_biomarkers", []),
                    "sahha_archetypes": raw_data.get("sahha_archetypes", []),
                    "supabase_fallback_scores": raw_data.get("supabase_scores", []),
                    "supabase_fallback_biomarkers": raw_data.get("supabase_biomarkers", [])
                },
                "data_summary": {
                    "total_scores": len(raw_data.get("sahha_scores", [])),
                    "total_biomarkers": len(raw_data.get("sahha_biomarkers", [])),
                    "total_archetypes": len(raw_data.get("sahha_archetypes", [])),
                    "date_range": raw_data.get("date_range", {}),
                    "user_id": raw_data.get("user_id", "unknown")
                },
                "api_responses": raw_data.get("api_responses", {})
            }

            with open(raw_data_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

            if IS_DEVELOPMENT:
                pass  # Production: Verbose print removed
            return True

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to log raw health data: {e}")
            return False

    def log_ai_interaction(self, analysis_number: int, interaction_data: Dict[str, Any]) -> bool:
        """Log AI prompt/response interactions"""
        try:
            ai_file = os.path.join(self.ai_interactions_dir, f"ai_interaction_{analysis_number}_{interaction_data.get('sequence', 1)}.json")

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "sequence": interaction_data.get("sequence", 1),
                "agent_id": interaction_data.get("agent_id", "unknown"),
                "interaction_type": interaction_data.get("interaction_type", "openai_completion"),
                "prompt": {
                    "system_prompt": interaction_data.get("system_prompt", ""),
                    "user_prompt": interaction_data.get("user_prompt", ""),
                    "total_prompt_tokens": len(str(interaction_data.get("system_prompt", "")) + str(interaction_data.get("user_prompt", "")).split()),
                    "raw_health_data_included": interaction_data.get("includes_raw_data", False)
                },
                "response": {
                    "content": interaction_data.get("response_content", ""),
                    "total_response_tokens": len(str(interaction_data.get("response_content", "")).split()),
                    "finish_reason": interaction_data.get("finish_reason", "unknown"),
                    "model": interaction_data.get("model", "unknown")
                },
                "metadata": {
                    "request_time": interaction_data.get("request_time", "unknown"),
                    "response_time": interaction_data.get("response_time", "unknown"),
                    "processing_duration_ms": interaction_data.get("processing_duration_ms", 0)
                }
            }

            with open(ai_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

            pass  # Production: Verbose print removed
            return True

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to log AI interaction: {e}")
            return False

    def log_agent_handoff(self, analysis_number: int, handoff_data: Dict[str, Any]) -> bool:
        """Log agent-to-agent handoffs"""
        try:
            handoff_file = os.path.join(self.agent_handoffs_dir, f"handoff_{analysis_number}_{handoff_data.get('sequence', 1)}.json")

            log_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis_number": analysis_number,
                "sequence": handoff_data.get("sequence", 1),
                "handoff_flow": {
                    "from_agent": handoff_data.get("from_agent", "unknown"),
                    "to_agent": handoff_data.get("to_agent", "unknown"),
                    "handoff_type": handoff_data.get("handoff_type", "sequential")
                },
                "input_data": {
                    "data": handoff_data.get("input_data", {}),
                    "data_size_bytes": len(str(handoff_data.get("input_data", {}))),
                    "data_keys": list(handoff_data.get("input_data", {}).keys()) if isinstance(handoff_data.get("input_data"), dict) else []
                },
                "output_data": {
                    "data": handoff_data.get("output_data", {}),
                    "data_size_bytes": len(str(handoff_data.get("output_data", {}))),
                    "data_keys": list(handoff_data.get("output_data", {}).keys()) if isinstance(handoff_data.get("output_data"), dict) else []
                },
                "processing_metadata": {
                    "processing_time_ms": handoff_data.get("processing_time_ms", 0),
                    "success": handoff_data.get("success", True),
                    "error": handoff_data.get("error", None),
                    "memory_used": handoff_data.get("memory_used", False),
                    "cache_used": handoff_data.get("cache_used", False)
                },
                "system_context": {
                    "user_id": handoff_data.get("user_id", "unknown"),
                    "archetype": handoff_data.get("archetype", "unknown"),
                    "analysis_mode": handoff_data.get("analysis_mode", "unknown")
                }
            }

            with open(handoff_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, default=str, ensure_ascii=False)

            print(f"🔄 [MVP_LOGGER] Agent handoff logged: {os.path.basename(handoff_file)}")
            return True

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to log agent handoff: {e}")
            return False

    def log_complete_analysis(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        insights_data: Optional[Dict[str, Any]] = None,
        raw_health_data: Optional[Dict[str, Any]] = None,
        ai_interactions: Optional[List[Dict[str, Any]]] = None,
        agent_handoffs: Optional[List[Dict[str, Any]]] = None,
        user_id: str = None,
        archetype: str = None
    ) -> Dict[str, Any]:
        """Log complete analysis cycle with enhanced system flow data"""
        try:
            # Get next analysis number
            analysis_number = self.get_next_analysis_number()

            results = {
                "analysis_number": analysis_number,
                "input_success": False,
                "output_success": False,
                "insights_success": False,
                "raw_health_data_success": False,
                "ai_interactions_success": 0,
                "agent_handoffs_success": 0,
                "user_id": user_id,
                "archetype": archetype
            }

            # Add context to input data
            enriched_input = {
                **input_data,
                "_metadata": {
                    "user_id": user_id,
                    "archetype": archetype,
                    "analysis_number": analysis_number,
                    "timestamp": datetime.now().isoformat(),
                    "has_raw_health_data": bool(raw_health_data),
                    "has_ai_interactions": bool(ai_interactions),
                    "has_agent_handoffs": bool(agent_handoffs)
                }
            }

            # Add context to output data
            enriched_output = {
                **output_data,
                "_metadata": {
                    "user_id": user_id,
                    "archetype": archetype,
                    "analysis_number": analysis_number,
                    "timestamp": datetime.now().isoformat()
                }
            }

            # Log main analysis files
            results["input_success"] = self.log_input_data(analysis_number, enriched_input)
            results["output_success"] = self.log_output_data(analysis_number, enriched_output)

            # Log insights data if provided
            if insights_data:
                enriched_insights = {
                    **insights_data,
                    "_metadata": {
                        "user_id": user_id,
                        "archetype": archetype,
                        "analysis_number": analysis_number,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                results["insights_success"] = self.log_insights_data(analysis_number, enriched_insights)

            # Log raw health data if provided
            if raw_health_data:
                results["raw_health_data_success"] = self.log_raw_health_data(analysis_number, {
                    **raw_health_data,
                    "user_id": user_id,
                    "analysis_number": analysis_number
                })

            # Log AI interactions if provided
            if ai_interactions:
                for i, interaction in enumerate(ai_interactions, 1):
                    interaction_with_context = {
                        **interaction,
                        "sequence": i,
                        "user_id": user_id,
                        "analysis_number": analysis_number
                    }
                    if self.log_ai_interaction(analysis_number, interaction_with_context):
                        results["ai_interactions_success"] += 1

            # Log agent handoffs if provided
            if agent_handoffs:
                for i, handoff in enumerate(agent_handoffs, 1):
                    handoff_with_context = {
                        **handoff,
                        "sequence": i,
                        "user_id": user_id,
                        "archetype": archetype,
                        "analysis_number": analysis_number
                    }
                    if self.log_agent_handoff(analysis_number, handoff_with_context):
                        results["agent_handoffs_success"] += 1

            # Enhanced summary
            base_files = sum([results["input_success"], results["output_success"]])
            optional_files = sum([
                results.get("insights_success", False),
                results.get("raw_health_data_success", False),
                results["ai_interactions_success"],
                results["agent_handoffs_success"]
            ])
            total_files = base_files + optional_files

            if IS_DEVELOPMENT:
                pass  # Production: Verbose print removed

            if IS_DEVELOPMENT and insights_data:
                pass  # Production: Verbose print removed

            if IS_DEVELOPMENT and raw_health_data:
                pass  # Production: Verbose print removed

            if IS_DEVELOPMENT and ai_interactions:
                pass  # Production: Verbose print removed

            if IS_DEVELOPMENT and agent_handoffs:
                print(f"   🔄 Agent Handoffs: {results['agent_handoffs_success']}/{len(agent_handoffs)} logged in logs/agent_handoffs/")

            return results

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Complete analysis logging failed: {e}")
            return {
                "error": str(e),
                "analysis_number": -1,
                "input_success": False,
                "output_success": False,
                "insights_success": False
            }

    def get_recent_logs(self, limit: int = 5) -> Dict[str, Any]:
        """Get information about recent log files including enhanced system flow data"""
        try:
            # Find all log files
            input_files = glob.glob(f"{self.logs_dir}/input_*.txt")
            output_files = glob.glob(f"{self.logs_dir}/output_*.txt")
            insights_files = glob.glob(f"{self.logs_dir}/insights_*.txt")

            # Find enhanced log files
            raw_data_files = glob.glob(f"{self.raw_data_dir}/*.json")
            ai_interaction_files = glob.glob(f"{self.ai_interactions_dir}/*.json")
            agent_handoff_files = glob.glob(f"{self.agent_handoffs_dir}/*.json")

            # Sort by modification time
            all_files = input_files + output_files + insights_files + raw_data_files + ai_interaction_files + agent_handoff_files
            all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            recent_info = []
            for file_path in all_files[:limit * 5]:  # Get more to group by analysis number
                try:
                    file_name = os.path.basename(file_path)
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    file_size = os.path.getsize(file_path)

                    # Determine file type based on location and name
                    if "raw_data" in file_path:
                        file_type = "raw_health_data"
                    elif "ai_interactions" in file_path:
                        file_type = "ai_interaction"
                    elif "agent_handoffs" in file_path:
                        file_type = "agent_handoff"
                    else:
                        file_type = file_name.split('_')[0]  # input, output, or insights

                    recent_info.append({
                        "file": file_name,
                        "full_path": file_path,
                        "modified": mtime.isoformat(),
                        "size_bytes": file_size,
                        "type": file_type
                    })
                except Exception as e:
                    continue

            return {
                "total_files": len(all_files),
                "basic_logs": {
                    "input_files": len(input_files),
                    "output_files": len(output_files),
                    "insights_files": len(insights_files)
                },
                "enhanced_logs": {
                    "raw_data_files": len(raw_data_files),
                    "ai_interaction_files": len(ai_interaction_files),
                    "agent_handoff_files": len(agent_handoff_files)
                },
                "recent_files": recent_info[:limit],
                "directories": {
                    "main_logs": os.path.abspath(self.logs_dir),
                    "raw_data": os.path.abspath(self.raw_data_dir),
                    "ai_interactions": os.path.abspath(self.ai_interactions_dir),
                    "agent_handoffs": os.path.abspath(self.agent_handoffs_dir)
                }
            }

        except Exception as e:
            print(f"❌ [MVP_LOGGER_ERROR] Failed to get recent logs info: {e}")
            return {"error": str(e)}

# Create global singleton instance
mvp_logger = MVPStyleLogger()