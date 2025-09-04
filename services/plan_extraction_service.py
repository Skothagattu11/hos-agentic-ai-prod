"""
Plan Extraction Service - Extract Trackable Tasks from Existing Plans

This service extracts individual trackable tasks from plans stored in 
holistic_analysis_results and populates the plan_items table for check-in tracking.
"""

import json
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time
from dataclasses import dataclass

from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from shared_libs.exceptions.holisticos_exceptions import HolisticOSException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TimeBlockContext:
    """Represents a time block with rich contextual metadata"""
    block_id: str
    title: str
    time_range: str
    purpose: Optional[str] = None
    why_it_matters: Optional[str] = None
    connection_to_insights: Optional[str] = None
    health_data_integration: Optional[str] = None
    block_order: int = 1
    parent_routine_id: Optional[str] = None
    archetype: Optional[str] = None

@dataclass 
class ExtractedTask:
    """Represents a single actionable task within a time block"""
    task_id: str
    title: str
    description: str
    scheduled_time: Optional[time]
    scheduled_end_time: Optional[time]
    estimated_duration_minutes: Optional[int]
    task_type: str
    priority_level: str
    task_order_in_block: int
    time_block_id: str  # Reference to parent time block
    parent_routine_id: Optional[str] = None

@dataclass
class ExtractedPlan:
    """Complete extracted plan with time blocks and tasks"""
    plan_id: str
    user_id: str
    date: str
    archetype: str
    time_blocks: List[TimeBlockContext]
    tasks: List[ExtractedTask]
    health_data_integration: Optional[str] = None
    extraction_metadata: Dict[str, Any] = None

class PlanExtractionService:
    """Service to extract trackable tasks from existing holistic_analysis_results"""
    
    def __init__(self):
        """Initialize the plan extraction service"""
        supabase_url = os.getenv('SUPABASE_URL')
        # Try service key first for better permissions, fallback to anon key
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        logger.info(f"SUPABASE_URL: {supabase_url[:50] if supabase_url else 'None'}...")
        logger.info(f"Using SERVICE_KEY: {bool(os.getenv('SUPABASE_SERVICE_KEY'))}")
        logger.info(f"SUPABASE_KEY: {'***' + supabase_key[-10:] if supabase_key else 'None'}")
        
        if not supabase_url or not supabase_key:
            raise HolisticOSException("Missing Supabase credentials. Please check SUPABASE_URL and SUPABASE_SERVICE_KEY/SUPABASE_KEY environment variables.")
        
        self.supabase = create_client(supabase_url, supabase_key)
        
    async def extract_and_store_plan_items(self, analysis_result_id: str, profile_id: str) -> List[Dict[str, Any]]:
        """
        Extract trackable tasks and time blocks from a plan and store them in normalized structure
        
        Args:
            analysis_result_id: ID from holistic_analysis_results table
            profile_id: User's profile ID
            
        Returns:
            List of extracted and stored plan items with time block relationships
        """
        try:
            # Get the analysis result
            analysis_result = await self._get_analysis_result(analysis_result_id)
            if not analysis_result:
                raise HolisticOSException(f"Analysis result not found: {analysis_result_id}")
            
            logger.info(f"Found analysis result: {analysis_result.get('analysis_type', 'unknown')} - {analysis_result.get('archetype', 'unknown')}")
            
            # Debug: Show analysis_result structure
            if 'analysis_result' in analysis_result:
                content_preview = str(analysis_result['analysis_result'])[:200]
                logger.info(f"Analysis content preview: {content_preview}...")
                
                # Show more of the content for debugging
                try:
                    import json
                    parsed_content = json.loads(analysis_result['analysis_result']) if isinstance(analysis_result['analysis_result'], str) else analysis_result['analysis_result']
                    if 'content' in parsed_content:
                        content_sample = parsed_content['content'][:2000]  # Show more content
                        logger.info(f"Plan content sample (2000 chars): {content_sample}...")
                except:
                    logger.info("Could not parse analysis_result as JSON")
            
            # Parse the plan content
            plan_content = self._parse_plan_content(analysis_result)
            if not plan_content:
                logger.warning(f"No extractable content found in analysis result: {analysis_result_id}")
                return []
            
            # Extract using normalized approach with time blocks
            extracted_plan = self._extract_plan_with_normalized_structure(plan_content, analysis_result, profile_id)
            logger.info(f"Extracted {len(extracted_plan.time_blocks)} time blocks with {len(extracted_plan.tasks)} tasks")
            
            # Store time blocks first
            stored_time_blocks = await self._store_time_blocks(analysis_result_id, profile_id, extracted_plan.time_blocks, analysis_result.get('archetype', 'Unknown'))
            
            # Create time block ID mapping - use block indices for proper matching
            time_block_id_map = {}
            for i, (tb, stored_tb) in enumerate(zip(extracted_plan.time_blocks, stored_time_blocks), 1):
                # Create the generated key that matches what tasks use
                analysis_block_key = f"{analysis_result_id}_block_{i}"
                time_block_id_map[analysis_block_key] = stored_tb['id']
                
                # Also add title-based keys for fallback
                time_block_id_map[tb.title] = stored_tb['id']
                
                # Add simplified title without time range for fuzzy matching
                simplified_title = re.sub(r'\([^)]*\)', '', tb.title).strip()
                simplified_title = re.sub(r':\s*.*$', '', simplified_title).strip()
                time_block_id_map[simplified_title] = stored_tb['id']
                
                logger.debug(f"Mapped block {i}: '{analysis_block_key}' -> {stored_tb['id']}")
                logger.debug(f"        Title: '{tb.title}' -> {stored_tb['id']}")
            
            # Store tasks with time block relationships
            stored_items = await self._store_plan_items_with_time_blocks(
                analysis_result_id, 
                profile_id, 
                extracted_plan.tasks,
                time_block_id_map
            )
            
            logger.info(f"Successfully stored {len(stored_time_blocks)} time blocks and {len(stored_items)} plan items for profile {profile_id}")
            return stored_items
            
        except Exception as e:
            logger.error(f"Error extracting plan items: {str(e)}")
            raise HolisticOSException(f"Plan extraction failed: {str(e)}")
    
    async def _get_analysis_result(self, analysis_result_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result from holistic_analysis_results table"""
        try:
            result = self.supabase.table("holistic_analysis_results")\
                .select("*")\
                .eq("id", analysis_result_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error fetching analysis result {analysis_result_id}: {str(e)}")
            return None
    
    def _parse_plan_content(self, analysis_result: Dict[str, Any]) -> Optional[str]:
        """Parse and extract the content from analysis_result"""
        try:
            # The analysis_result field contains double-escaped JSON string
            raw_analysis = analysis_result.get('analysis_result', '{}')
            logger.info(f"Raw analysis_result type: {type(raw_analysis)}")
            
            # First level of JSON parsing (removes outer quotes and unescapes)
            if isinstance(raw_analysis, str):
                try:
                    first_parse = json.loads(raw_analysis)
                    logger.info(f"First parse type: {type(first_parse)}")
                    
                    # If it's still a string, parse again (double-escaped)
                    if isinstance(first_parse, str):
                        analysis_data = json.loads(first_parse)
                    else:
                        analysis_data = first_parse
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from analysis_result")
                    return None
            else:
                analysis_data = raw_analysis
            
            # Extract the content field which contains the actual plan
            content = analysis_data.get('content', '')
            
            if not content:
                logger.warning("No content field found in analysis_result")
                return None
                
            return content
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing analysis_result JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting plan content: {str(e)}")
            return None
    
    def _extract_tasks_from_content(self, content: str) -> List[ExtractedTask]:
        """
        Extract tasks from plan content with rich context using hybrid approach
        
        Now captures:
        - Individual actionable tasks
        - Why it matters context
        - Connection to insights
        - Time block context
        - Health data integration
        
        Handles various formats like:
        Format 1: 1. **Morning Wake-up (6:00-7:00 AM):** - **Tasks:** - **3-Minute HRV (6:00-6:03 AM):** Description
        Format 2: 1. **Morning Wake-up (6:00-7:00 AM):** **Tasks:** - **6:00-6:10 AM: Morning Hydration:** Description  
        Format 3: Any other variations with time patterns and task descriptions
        """
        extracted_tasks = []
        
        try:
            # Multiple patterns for different formats
            time_block_patterns = [
                r'(\d+)\.\s+\*\*([^*]+?)\*\*',  # Standard: 1. **Block Title**
                r'(\d+)\.\s+\*\*([^:]+?):\s*([^*]*?)\*\*',  # With colon: 1. **Block Title: Description**
            ]
            
            # Focused task patterns - only actionable, trackable tasks
            task_patterns = [
                # Format 1: "     - **3-Minute HRV/Readiness Check (6:00-6:03 AM):** Description"
                r'\s+-\s+\*\*([^(]*?)\s*(?:\(([^)]+)\))?\s*:\*\*\s*([^\n]*)',
                # Format 2: "   - **6:00-6:10 AM: Morning Hydration and Reflection**"
                r'\s+-\s+\*\*([^*]+?)\*\*',  
                # Format 3: Any line with time pattern (actionable activities)
                r'\s*-\s*([^\n]*?(?:\d{1,2}:\d{2}[^:\n]*?:\d{2}|\d{1,2}:\d{2})[^\n]*)',
            ]
            
            # Noise filter - skip these non-actionable sections
            noise_patterns = [
                r'why\s+it\s+matters',
                r'connection\s+to\s+insights', 
                r'health\s+data\s+integration',
                r'readiness\s+metrics',
                r'sleep\s+metrics',
                r'mental\s+wellbeing\s+metrics',
                r'activity\s+metrics',
                r'wellbeing\s+metrics',
                r'tasks:?\s*$',  # Just the word "Tasks:" by itself
            ]
            
            # Try each time block pattern until we find matches
            time_blocks = []
            for pattern in time_block_patterns:
                time_blocks = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
                if time_blocks:
                    logger.info(f"Found {len(time_blocks)} time blocks with pattern: {pattern}")
                    break
            
            if not time_blocks:
                logger.warning("No time blocks found with any pattern")
                return []
            
            for block_idx, block_match in enumerate(time_blocks):
                block_number = block_match.group(1)
                block_title = block_match.group(2).strip()
                logger.info(f"Processing block {block_number}: {block_title[:50]}...")
                
                # Extract time range from block title if present
                time_range = self._extract_time_range(block_title)
                
                # Get the content after this block until the next block  
                block_start = block_match.end()
                if block_idx < len(time_blocks) - 1:
                    # Get content until next block
                    next_block = time_blocks[block_idx + 1]
                    block_end = next_block.start()
                else:
                    # This is the last block, get all remaining content
                    block_end = len(content)
                
                block_content = content[block_start:block_end]
                logger.info(f"Block content sample: {block_content[:200]}...")
                
                # Try each task pattern until we find matches
                tasks = []
                for task_pattern in task_patterns:
                    tasks = list(re.finditer(task_pattern, block_content, re.MULTILINE | re.DOTALL))
                    if tasks:
                        logger.info(f"Found {len(tasks)} tasks in block {block_number} with pattern: {task_pattern}")
                        break
                
                if not tasks:
                    logger.warning(f"No tasks found in block {block_number} with any pattern")
                    # Fallback: look for any line with time patterns in the block
                    fallback_pattern = r'([^\n]*(?:\d{1,2}:\d{2}.*?AM|PM|\d{1,2}:\d{2}.*?\d{1,2}:\d{2})[^\n]*)'
                    fallback_matches = re.findall(fallback_pattern, block_content, re.MULTILINE)
                    if fallback_matches:
                        logger.info(f"Found {len(fallback_matches)} potential tasks with fallback pattern")
                        # Convert matches to mock task objects for processing
                        tasks = []
                        for i, match in enumerate(fallback_matches):
                            # Create a mock match object
                            class MockMatch:
                                def __init__(self, text):
                                    self.text = text.strip()
                                def group(self, n):
                                    if n == 1: return self.text
                                    return ""
                            tasks.append(MockMatch(match))
                
                for task_idx, task_match in enumerate(tasks):
                    # Handle different regex patterns with varying group counts
                    try:
                        task_title = task_match.group(1).strip()
                        # Try to get time info and description, handling different group structures
                        try:
                            task_time_info = task_match.group(2) if len(task_match.groups()) > 1 and task_match.group(2) else ""
                        except (IndexError, AttributeError):
                            task_time_info = ""
                        
                        try:
                            task_description = task_match.group(3).strip() if len(task_match.groups()) > 2 and task_match.group(3) else ""
                        except (IndexError, AttributeError):
                            task_description = ""
                            
                        # If no separate time info, try to extract from title
                        if not task_time_info and ':' in task_title:
                            parts = task_title.split(':', 1)
                            if len(parts) == 2 and any(char.isdigit() for char in parts[0]):
                                task_time_info = parts[0].strip()
                                task_title = parts[1].strip()
                                
                    except (IndexError, AttributeError) as e:
                        logger.warning(f"Error processing task match: {e}")
                        continue
                    
                    # Filter out noise - skip non-actionable content
                    is_noise = False
                    for noise_pattern in noise_patterns:
                        if re.search(noise_pattern, task_title.lower(), re.IGNORECASE):
                            logger.debug(f"Skipping noise: {task_title[:30]}...")
                            is_noise = True
                            break
                    
                    if is_noise:
                        continue
                    
                    # Skip if no actionable content (no time info and too generic)
                    if not task_time_info and len(task_title.split()) < 3:
                        logger.debug(f"Skipping generic: {task_title}")
                        continue
                        
                    # Must contain actionable words or time information
                    actionable_keywords = ['walk', 'exercise', 'drink', 'eat', 'stretch', 'meditation', 'breathing', 'work', 'session', 'break', 'hydrat', 'check', 'visualiz', 'exposur', 'activit']
                    has_actionable_content = task_time_info or any(keyword in task_title.lower() for keyword in actionable_keywords)
                    
                    if not has_actionable_content:
                        logger.debug(f"Skipping non-actionable: {task_title[:30]}...")
                        continue
                    
                    # Extract timing information
                    start_time, end_time, duration = self._extract_task_timing(task_time_info)
                    
                    # Generate unique item ID
                    item_id = self._generate_item_id(block_title, task_title, block_idx, task_idx)
                    
                    # Determine task type
                    task_type = self._classify_task_type(task_title, task_description)
                    
                    extracted_task = ExtractedTask(
                        task_id=item_id,
                        title=task_title,
                        description=task_description,
                        scheduled_time=start_time,
                        scheduled_end_time=end_time,
                        estimated_duration_minutes=duration,
                        task_type=task_type,
                        priority_level="medium",
                        task_order_in_block=task_idx,
                        time_block_id=block_title
                    )
                    
                    extracted_tasks.append(extracted_task)
            
            # Summary logging
            total_blocks = len(time_blocks) if time_blocks else 0
            total_tasks = len(extracted_tasks)
            
            logger.info(f"📊 Extraction Summary:")
            logger.info(f"   🏗️  Time blocks processed: {total_blocks}")
            logger.info(f"   ✅ Actionable tasks extracted: {total_tasks}")
            logger.info(f"   🎯 Focus: Only trackable, time-bound activities")
            
            return extracted_tasks
            
        except Exception as e:
            logger.error(f"Error extracting tasks from content: {str(e)}")
            return []
    
    def _extract_time_range(self, text: str) -> Optional[Tuple[time, time]]:
        """Extract time range from text like 'Morning Wake-up (6:00-7:00 AM)'"""
        try:
            # Pattern for time range like (6:00-7:00 AM) or (6:00 AM - 7:00 AM)
            pattern = r'\((\d{1,2}):(\d{2})(?:\s*-\s*|\s+to\s+)(\d{1,2}):(\d{2})\s*(AM|PM)?\)'
            match = re.search(pattern, text, re.IGNORECASE)
            
            if match:
                start_hour = int(match.group(1))
                start_minute = int(match.group(2))
                end_hour = int(match.group(3))
                end_minute = int(match.group(4))
                period = match.group(5).upper() if match.group(5) else 'AM'
                
                # Convert to 24-hour format
                if period == 'PM' and start_hour != 12:
                    start_hour += 12
                elif period == 'AM' and start_hour == 12:
                    start_hour = 0
                
                # Handle end time
                if period == 'PM' and end_hour != 12:
                    end_hour += 12
                elif period == 'AM' and end_hour == 12:
                    end_hour = 0
                
                return time(start_hour, start_minute), time(end_hour, end_minute)
            
            return None
            
        except Exception:
            return None
    
    def _extract_task_timing(self, time_info: str) -> Tuple[Optional[time], Optional[time], Optional[int]]:
        """Extract start time, end time, and duration from task timing info"""
        if not time_info:
            return None, None, None
        
        try:
            # Pattern for time range like "6:00-6:03 AM"
            pattern = r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})\s*(AM|PM)?'
            match = re.search(pattern, time_info, re.IGNORECASE)
            
            if match:
                start_hour = int(match.group(1))
                start_minute = int(match.group(2))
                end_hour = int(match.group(3))
                end_minute = int(match.group(4))
                period = match.group(5).upper() if match.group(5) else 'AM'
                
                # Convert to 24-hour format
                if period == 'PM' and start_hour != 12:
                    start_hour += 12
                    end_hour += 12
                elif period == 'AM' and start_hour == 12:
                    start_hour = 0
                    if end_hour == 12:
                        end_hour = 0
                
                start_time = time(start_hour, start_minute)
                end_time = time(end_hour, end_minute)
                
                # Calculate duration in minutes
                start_minutes = start_hour * 60 + start_minute
                end_minutes = end_hour * 60 + end_minute
                duration = end_minutes - start_minutes
                
                return start_time, end_time, duration if duration > 0 else None
            
            return None, None, None
            
        except Exception:
            return None, None, None
    
    def _generate_item_id(self, time_block: str, task_title: str, block_idx: int, task_idx: int) -> str:
        """Generate a unique item ID for the task"""
        # Clean and normalize strings
        block_clean = re.sub(r'[^\w\s]', '', time_block.lower())
        block_clean = re.sub(r'\s+', '_', block_clean.strip())
        
        title_clean = re.sub(r'[^\w\s]', '', task_title.lower())
        title_clean = re.sub(r'\s+', '_', title_clean.strip())
        
        # Truncate if too long
        block_clean = block_clean[:30]
        title_clean = title_clean[:40]
        
        return f"{block_clean}_{title_clean}_{block_idx}_{task_idx}"
    
    def _classify_task_type(self, title: str, description: str) -> str:
        """Classify task type based on title and description"""
        combined_text = f"{title} {description}".lower()
        
        if any(keyword in combined_text for keyword in ['hrv', 'readiness', 'check', 'assessment', 'measure']):
            return 'assessment'
        elif any(keyword in combined_text for keyword in ['workout', 'exercise', 'strength', 'cardio', 'walk', 'movement']):
            return 'exercise'
        elif any(keyword in combined_text for keyword in ['meal', 'eat', 'nutrition', 'food', 'hydration', 'water']):
            return 'nutrition'
        elif any(keyword in combined_text for keyword in ['meditation', 'mindfulness', 'breath', 'visualization', 'relaxation']):
            return 'mindfulness'
        elif any(keyword in combined_text for keyword in ['prepare', 'setup', 'organize', 'plan']):
            return 'preparation'
        else:
            return 'general'
    
    async def _store_plan_items(self, analysis_result_id: str, profile_id: str, tasks: List[ExtractedTask]) -> List[Dict[str, Any]]:
        """Store extracted tasks in plan_items table"""
        if not tasks:
            return []
        
        try:
            # Prepare data for insertion
            insert_data = []
            for task in tasks:
                item_data = {
                    'analysis_result_id': analysis_result_id,
                    'profile_id': profile_id,
                    'item_id': task.task_id,
                    'time_block': task.time_block_id,
                    'title': task.title,
                    'description': task.description,
                    'scheduled_time': task.scheduled_time.strftime('%H:%M:%S') if task.scheduled_time else None,
                    'scheduled_end_time': task.scheduled_end_time.strftime('%H:%M:%S') if task.scheduled_end_time else None,
                    'estimated_duration_minutes': task.estimated_duration_minutes,
                    'task_type': task.task_type,
                    'time_block_order': task.task_order_in_block,  # Use task order as block order for now
                    'task_order_in_block': task.task_order_in_block,
                    'is_trackable': True,
                    'priority_level': task.priority_level
                }
                insert_data.append(item_data)
            
            # Insert into database (use upsert to handle duplicates)
            result = self.supabase.table("plan_items")\
                .upsert(insert_data, on_conflict="analysis_result_id,item_id")\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error storing plan items: {str(e)}")
            raise HolisticOSException(f"Failed to store plan items: {str(e)}")
    
    def get_plan_items_for_analysis(self, analysis_result_id: str, trackable_only: bool = True) -> List[Dict[str, Any]]:
        """Get all plan items for a specific analysis result"""
        try:
            query = self.supabase.table("plan_items")\
                .select("*")\
                .eq("analysis_result_id", analysis_result_id)\
                .order("time_block_order")\
                .order("task_order_in_block")
            
            if trackable_only:
                query = query.eq("is_trackable", True)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error fetching plan items: {str(e)}")
            return []

    async def get_current_plan_items_for_user(self, profile_id: str, date_str: str = None) -> Dict[str, Any]:
        """Get current active plan items for a user"""
        try:
            from datetime import date
            target_date = date.fromisoformat(date_str) if date_str else date.today()
            
            # Get latest analysis results for user (routine and nutrition)
            analysis_results = self.supabase.table("holistic_analysis_results")\
                .select("id, analysis_type, archetype, created_at, analysis_result")\
                .eq("user_id", profile_id)\
                .in_("analysis_type", ["routine_plan", "nutrition_plan"])\
                .order("created_at", desc=True)\
                .limit(2)\
                .execute()
            
            if not analysis_results.data:
                return {"routine_plan": None, "nutrition_plan": None, "items": []}
            
            # Get plan items for each analysis result
            all_items = []
            plan_info = {"routine_plan": None, "nutrition_plan": None}
            
            for analysis in analysis_results.data:
                analysis_id = analysis["id"]
                plan_type = analysis["analysis_type"]
                
                # Store plan info
                plan_info[plan_type] = {
                    "analysis_id": analysis_id,
                    "archetype": analysis.get("archetype"),
                    "created_at": analysis["created_at"]
                }
                
                # Get plan items
                items = await self.get_plan_items_for_analysis(analysis_id)
                
                # Add plan context to each item
                for item in items:
                    item["plan_type"] = plan_type
                    item["analysis_info"] = plan_info[plan_type]
                
                all_items.extend(items)
            
            return {
                "routine_plan": plan_info["routine_plan"],
                "nutrition_plan": plan_info["nutrition_plan"],
                "items": all_items,
                "date": target_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching current plan items: {str(e)}")
            return {"routine_plan": None, "nutrition_plan": None, "items": []}

    def extract_plan_with_time_blocks(self, content: str, analysis_result: Dict[str, Any]) -> ExtractedPlan:
        """
        Time-block-centric extraction method for hybrid approach
        
        Extracts:
        - Time blocks with rich contextual metadata
        - Individual tasks linked to their time blocks
        - Health data integration
        - Archetype information
        """
        time_blocks = []
        all_tasks = []
        
        try:
            # Extract metadata from analysis result
            archetype = analysis_result.get('archetype', 'Unknown')
            analysis_id = analysis_result.get('id', 'unknown')
            user_id = analysis_result.get('user_id', 'unknown')
            date = datetime.now().strftime('%Y-%m-%d')  # Default to today
            
            # Parse health data integration section
            health_data_pattern = r'\*\*Health Data Integration:\*\*\s*(.*?)(?=\n\n|\Z)'
            health_data_match = re.search(health_data_pattern, content, re.DOTALL | re.IGNORECASE)
            health_data_integration = health_data_match.group(1).strip() if health_data_match else None
            
            # Find all time blocks with enhanced parsing
            time_block_pattern = r'(\d+)\.\s+\*\*([^*]+?)\*\*\s*\n(.*?)(?=\n\d+\.\s+\*\*|\n\*\*Health Data Integration|\Z)'
            time_block_matches = re.finditer(time_block_pattern, content, re.DOTALL)
            
            for block_match in time_block_matches:
                block_number = block_match.group(1)
                block_title = block_match.group(2).strip()
                block_content = block_match.group(3).strip()
                
                logger.info(f"Processing time block {block_number}: {block_title}")
                
                # Extract time range and purpose from block title
                purpose = None
                if ':' in block_title:
                    title_parts = block_title.split(':', 1)
                    time_range_part = title_parts[0].strip()
                    purpose = title_parts[1].strip() if len(title_parts) > 1 else None
                else:
                    time_range_part = block_title
                
                # Extract time range from the full block title
                time_range = self._extract_time_range_string(block_title)
                
                # Parse block-level context
                why_it_matters = None
                connection_to_insights = None
                
                # Extract "Why It Matters" from block content
                why_pattern = r'-\s*\*\*Why It Matters:\*\*\s*([^-]*?)(?=\n\s*-\s*\*\*|\Z)'
                why_match = re.search(why_pattern, block_content, re.DOTALL | re.IGNORECASE)
                if why_match:
                    why_it_matters = why_match.group(1).strip()
                
                # Extract "Connection to Insights" from block content  
                insights_pattern = r'-\s*\*\*Connection to Insights:\*\*\s*([^-]*?)(?=\n\s*-\s*\*\*|\Z)'
                insights_match = re.search(insights_pattern, block_content, re.DOTALL | re.IGNORECASE)
                if insights_match:
                    connection_to_insights = insights_match.group(1).strip()
                
                # Create time block
                block_id = f"{analysis_id}_block_{block_number}"
                time_block = TimeBlockContext(
                    block_id=block_id,
                    title=block_title,
                    time_range=time_range or "Not specified",
                    purpose=purpose,
                    why_it_matters=why_it_matters,
                    connection_to_insights=connection_to_insights,
                    health_data_integration=health_data_integration,
                    block_order=int(block_number),
                    parent_routine_id=analysis_id,
                    archetype=archetype
                )
                time_blocks.append(time_block)
                
                # Extract tasks from this time block
                tasks_section_pattern = r'-\s*\*\*Tasks:\*\*\s*(.*?)(?=-\s*\*\*(?:Why It Matters|Connection to Insights)|\Z)'
                tasks_section_match = re.search(tasks_section_pattern, block_content, re.DOTALL | re.IGNORECASE)
                
                if tasks_section_match:
                    tasks_content = tasks_section_match.group(1).strip()
                    task_pattern = r'-\s+\*\*([^(]*?)\s*\(([^)]+)\)\s*:\*\*\s*([^\n]*?)(?=\n\s*-|\Z)'
                    task_matches = re.finditer(task_pattern, tasks_content, re.DOTALL | re.IGNORECASE)
                    
                    task_order = 1
                    for task_match in task_matches:
                        task_name = task_match.group(1).strip()
                        time_info = task_match.group(2).strip()
                        task_description = task_match.group(3).strip()
                        
                        if not task_name or not time_info or len(task_name) < 3:
                            continue
                        
                        # Parse timing information
                        start_time, end_time, duration = self._extract_task_timing(time_info)
                        
                        # Determine task type and priority
                        task_type = self._determine_task_type(task_name, task_description)
                        priority_level = self._determine_priority(task_name, task_description, archetype)
                        
                        # Create task linked to time block
                        task = ExtractedTask(
                            task_id=f"{block_id}_task_{task_order}",
                            title=task_name,
                            description=task_description,
                            scheduled_time=start_time,
                            scheduled_end_time=end_time,
                            estimated_duration_minutes=duration,
                            task_type=task_type,
                            priority_level=priority_level,
                            task_order_in_block=task_order,
                            time_block_id=block_id,
                            parent_routine_id=analysis_id
                        )
                        
                        all_tasks.append(task)
                        task_order += 1
                        
                        logger.info(f"  ✓ Extracted task: {task_name} ({time_info})")
            
            # Create the complete extracted plan
            extracted_plan = ExtractedPlan(
                plan_id=analysis_id,
                user_id=user_id,
                date=date,
                archetype=archetype,
                time_blocks=time_blocks,
                tasks=all_tasks,
                health_data_integration=health_data_integration,
                extraction_metadata={
                    "total_time_blocks": len(time_blocks),
                    "total_tasks": len(all_tasks),
                    "extraction_date": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Extracted plan: {len(time_blocks)} time blocks, {len(all_tasks)} tasks")
            return extracted_plan
            
        except Exception as e:
            logger.error(f"Error in time-block extraction: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return empty plan on error
            return ExtractedPlan(
                plan_id=analysis_result.get('id', 'error'),
                user_id=analysis_result.get('user_id', 'unknown'),
                date=datetime.now().strftime('%Y-%m-%d'),
                archetype=analysis_result.get('archetype', 'Unknown'),
                time_blocks=[],
                tasks=[],
                extraction_metadata={"error": str(e)}
            )
    
    def _determine_task_type(self, task_name: str, description: str) -> str:
        """Determine task type based on content"""
        task_lower = f"{task_name} {description}".lower()
        
        if any(word in task_lower for word in ['exercise', 'activity', 'walk', 'workout', 'movement', 'stretch']):
            return 'physical_activity'
        elif any(word in task_lower for word in ['breathing', 'meditation', 'mindful', 'reflection', 'gratitude']):
            return 'mental_wellness'
        elif any(word in task_lower for word in ['hydration', 'water', 'breakfast', 'snack', 'nutrition']):
            return 'nutrition_hydration'
        elif any(word in task_lower for word in ['sleep', 'wind-down', 'bed', 'rest']):
            return 'sleep_recovery'
        elif any(word in task_lower for word in ['work', 'focus', 'productive', 'planning']):
            return 'productivity'
        elif any(word in task_lower for word in ['light', 'outdoor', 'sunlight']):
            return 'circadian_support'
        else:
            return 'general_wellness'
    
    def _determine_priority(self, task_name: str, description: str, archetype: str) -> str:
        """Determine priority level based on task content and user archetype"""
        task_content = f"{task_name} {description}".lower()
        
        # High priority for archetype-specific activities
        if archetype == "Peak Performer":
            if any(word in task_content for word in ['activity', 'performance', 'focus', 'optimization']):
                return 'high'
        
        # High priority for foundational activities
        if any(word in task_content for word in ['hydration', 'sleep', 'breathing']):
            return 'high'
        
        # Medium priority for wellness activities
        if any(word in task_content for word in ['reflection', 'planning', 'movement']):
            return 'medium'
        
        return 'medium'  # Default priority
    
    def _extract_time_range_string(self, text: str) -> Optional[str]:
        """Extract time range as string from text"""
        # Look for patterns like "(6:00-7:00 AM)" or "6:00-7:00 AM" or (9:00-11:00 AM)
        patterns = [
            r'\((\d{1,2}:\d{2}-\d{1,2}:\d{2}\s*[AP]M)\)',  # (6:00-7:00 AM)
            r'\((\d{1,2}:\d{2}:\d{2}-\d{1,2}:\d{2}:\d{2})\)',  # (06:00:00-07:00:00)
            r'(\d{1,2}:\d{2}-\d{1,2}:\d{2}\s*[AP]M)',     # 6:00-7:00 AM
            r'(\d{1,2}:\d{2}\s*[AP]M-\d{1,2}:\d{2}\s*[AP]M)',  # 6:00 AM-7:00 AM
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_plan_with_normalized_structure(self, content: str, analysis_result: Dict[str, Any], profile_id: str) -> ExtractedPlan:
        """
        Extract plan with normalized time blocks and tasks structure
        """
        try:
            # Use the existing extract_plan_with_time_blocks method but enhance it
            extracted_plan = self.extract_plan_with_time_blocks(content, analysis_result)
            
            # Ensure profile_id is set correctly
            extracted_plan.user_id = profile_id
            
            return extracted_plan
            
        except Exception as e:
            logger.error(f"Error in normalized extraction: {str(e)}")
            # Fallback to legacy method
            legacy_tasks = self._extract_tasks_from_content(content)
            
            # Convert legacy tasks to new structure
            time_blocks = []
            converted_tasks = []
            
            # Group tasks by time block
            time_block_groups = {}
            for task in legacy_tasks:
                block_title = task.time_block_id  # This is actually the block title in legacy
                if block_title not in time_block_groups:
                    time_block_groups[block_title] = []
                time_block_groups[block_title].append(task)
            
            # Create time blocks and update tasks
            for block_idx, (block_title, tasks) in enumerate(time_block_groups.items()):
                # Extract time range from block title
                time_range = self._extract_time_range_string(block_title)
                
                # Create time block
                time_block = TimeBlockContext(
                    block_id=f"block_{block_idx}",
                    title=block_title,
                    time_range=time_range or "Not specified",
                    block_order=block_idx + 1,
                    archetype=analysis_result.get('archetype', 'Unknown')
                )
                time_blocks.append(time_block)
                
                # Update tasks to reference this time block
                for task in tasks:
                    task.time_block_id = time_block.block_id
                    converted_tasks.append(task)
            
            return ExtractedPlan(
                plan_id=analysis_result.get('id', 'unknown'),
                user_id=profile_id,
                date=datetime.now().strftime('%Y-%m-%d'),
                archetype=analysis_result.get('archetype', 'Unknown'),
                time_blocks=time_blocks,
                tasks=converted_tasks,
                extraction_metadata={
                    "extraction_method": "legacy_conversion",
                    "total_time_blocks": len(time_blocks),
                    "total_tasks": len(converted_tasks)
                }
            )
    
    async def _store_time_blocks(self, analysis_result_id: str, profile_id: str, time_blocks: List[TimeBlockContext], archetype: str) -> List[Dict[str, Any]]:
        """Store time blocks in the time_blocks table"""
        if not time_blocks:
            return []
        
        try:
            # Prepare time block data for insertion
            time_block_data = []
            for tb in time_blocks:
                block_data = {
                    'analysis_result_id': analysis_result_id,
                    'profile_id': profile_id,
                    'block_title': tb.title,
                    'time_range': tb.time_range,
                    'purpose': tb.purpose,
                    'why_it_matters': tb.why_it_matters,
                    'connection_to_insights': tb.connection_to_insights,
                    'health_data_integration': tb.health_data_integration,
                    'block_order': tb.block_order,
                    'archetype': archetype,
                    'plan_type': 'routine'
                }
                time_block_data.append(block_data)
            
            # Insert time blocks
            result = self.supabase.table("time_blocks")\
                .upsert(time_block_data, on_conflict="analysis_result_id,block_title")\
                .execute()
            
            logger.info(f"Stored {len(result.data)} time blocks")
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error storing time blocks: {str(e)}")
            raise HolisticOSException(f"Failed to store time blocks: {str(e)}")
    
    async def _store_plan_items_with_time_blocks(self, analysis_result_id: str, profile_id: str, tasks: List[ExtractedTask], time_block_id_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """Store plan items with time block relationships"""
        if not tasks:
            return []
        
        try:
            # Prepare data for insertion
            insert_data = []
            for task in tasks:
                # Find the time block ID - improved matching logic
                time_block_id = None
                task_block_key = task.time_block_id
                
                # Strategy 1: Direct exact match
                if task_block_key in time_block_id_map:
                    time_block_id = time_block_id_map[task_block_key]
                    logger.debug(f"✅ Direct match: '{task.title}' -> '{task_block_key}'")
                else:
                    # Strategy 2: Match core keywords from task's time_block_id
                    task_words = set(re.sub(r'[^\w\s]', '', task_block_key.lower()).split())
                    task_words.discard('') # Remove empty strings
                    
                    best_match = None
                    best_score = 0
                    
                    for block_key, block_id in time_block_id_map.items():
                        if not block_key:  # Skip empty keys
                            continue
                            
                        block_words = set(re.sub(r'[^\w\s]', '', block_key.lower()).split())
                        
                        # Calculate similarity score based on common words
                        common_words = task_words.intersection(block_words)
                        if common_words:
                            # Give higher score to more specific matches
                            score = len(common_words) / max(len(task_words), len(block_words))
                            if score > best_score:
                                best_score = score
                                best_match = (block_key, block_id)
                    
                    if best_match and best_score > 0.3:  # At least 30% similarity
                        time_block_id = best_match[1]
                        logger.debug(f"✅ Fuzzy match: '{task.title}' -> '{best_match[0]}' (score: {best_score:.2f})")
                    else:
                        logger.warning(f"❌ No match found for task '{task.title}' with time_block_id '{task_block_key}'")
                
                # Log the mapping for debugging
                if time_block_id:
                    logger.debug(f"Mapped task '{task.title}' to time block ID: {time_block_id}")
                else:
                    logger.warning(f"Could not map task '{task.title}' with time_block_id '{task.time_block_id}' to any time block")
                
                item_data = {
                    'analysis_result_id': analysis_result_id,
                    'profile_id': profile_id,
                    'item_id': task.task_id,
                    'time_block': task.time_block_id,  # Keep original for backward compatibility
                    'time_block_id': time_block_id,  # New foreign key
                    'title': task.title,
                    'description': task.description,
                    'scheduled_time': task.scheduled_time.strftime('%H:%M:%S') if task.scheduled_time else None,
                    'scheduled_end_time': task.scheduled_end_time.strftime('%H:%M:%S') if task.scheduled_end_time else None,
                    'estimated_duration_minutes': task.estimated_duration_minutes,
                    'task_type': task.task_type,
                    'time_block_order': task.task_order_in_block,  # Use task order as block order for now
                    'task_order_in_block': task.task_order_in_block,
                    'is_trackable': True,
                    'priority_level': task.priority_level
                }
                insert_data.append(item_data)
            
            # Insert into database (use upsert to handle duplicates)
            result = self.supabase.table("plan_items")\
                .upsert(insert_data, on_conflict="analysis_result_id,item_id")\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error storing plan items with time blocks: {str(e)}")
            raise HolisticOSException(f"Failed to store plan items: {str(e)}")

# Convenience function for external use
async def extract_plan_items(analysis_result_id: str, profile_id: str) -> List[Dict[str, Any]]:
    """
    Convenience function to extract plan items from an analysis result
    
    Args:
        analysis_result_id: ID from holistic_analysis_results
        profile_id: User's profile ID
        
    Returns:
        List of extracted plan items
    """
    service = PlanExtractionService()
    return await service.extract_and_store_plan_items(analysis_result_id, profile_id)