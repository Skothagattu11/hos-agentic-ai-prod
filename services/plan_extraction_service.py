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

# EXTRACTION METHOD TOGGLE - Simple configuration
EXTRACTION_METHOD = os.getenv('PLAN_EXTRACTION_METHOD', 'regex')  # 'regex' or 'ai'

# Production logging control - only errors and warnings in production
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
PRODUCTION_MODE = ENVIRONMENT == 'production'

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
        
    async def extract_and_store_plan_items(self, analysis_result_id: str, profile_id: str, override_plan_date: str = None) -> List[Dict[str, Any]]:
        """
        Extract trackable tasks and time blocks from a plan and store them in normalized structure
        
        Args:
            analysis_result_id: ID from holistic_analysis_results table
            profile_id: User's profile ID
            override_plan_date: Optional date to override the plan_date (YYYY-MM-DD format). If not provided, uses analysis_date from holistic_analysis_results.
            
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
            extracted_plan = await self._extract_plan_with_normalized_structure(plan_content, analysis_result, profile_id)
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
                time_block_id_map,
                override_plan_date
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
            
            # Production: Clean logging removed
            
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
    
    async def _store_plan_items(self, analysis_result_id: str, profile_id: str, tasks: List[ExtractedTask], override_plan_date: str = None) -> List[Dict[str, Any]]:
        """Store extracted tasks in plan_items table"""
        if not tasks:
            return []
        
        try:
            # Use override_plan_date if provided, otherwise get from holistic_analysis_results
            if override_plan_date:
                plan_date = override_plan_date
            else:
                # Get the analysis_date from holistic_analysis_results
                analysis_result = self.supabase.table("holistic_analysis_results")\
                    .select("analysis_date")\
                    .eq("id", analysis_result_id)\
                    .execute()
                
                if not analysis_result.data:
                    raise HolisticOSException(f"Analysis result not found: {analysis_result_id}")
                
                plan_date = analysis_result.data[0]["analysis_date"]
            
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
                    'priority_level': task.priority_level,
                    'plan_date': plan_date  # Add the plan date from analysis
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
        """Get all plan items for a specific analysis result with time block names"""
        try:
            # Get plan items
            query = self.supabase.table("plan_items")\
                .select("*")\
                .eq("analysis_result_id", analysis_result_id)\
                .order("time_block_order")\
                .order("task_order_in_block")

            if trackable_only:
                query = query.eq("is_trackable", True)

            result = query.execute()
            plan_items = result.data if result.data else []

            if plan_items:
                # Get time blocks for this analysis_result_id
                time_blocks_result = self.supabase.table("time_blocks")\
                    .select("id, block_title, time_range, purpose, block_order")\
                    .eq("analysis_result_id", analysis_result_id)\
                    .execute()

                time_blocks = time_blocks_result.data if time_blocks_result.data else []

                # Create mapping from time_block_id (UUID) to time block data
                time_block_mapping = {}
                for tb in time_blocks:
                    time_block_mapping[tb.get("id")] = tb

                # Match plan items to time blocks using time_block_id (UUID)
                for item in plan_items:
                    time_block_id = item.get("time_block_id")

                    if time_block_id and time_block_id in time_block_mapping:
                        item["time_blocks"] = time_block_mapping[time_block_id]
                    else:
                        # Fallback: try to extract block number from time_block string
                        time_block_str = item.get("time_block", "")
                        if "block_" in time_block_str:
                            try:
                                block_num = int(time_block_str.split("block_")[-1])
                                # Try to find by block_order as fallback
                                for tb in time_blocks:
                                    if tb.get("block_order") == block_num:
                                        item["time_blocks"] = tb
                                        break
                                else:
                                    # No match found, create fallback
                                    item["time_blocks"] = {
                                        "block_title": f"Time Block {block_num}",
                                        "time_range": "",
                                        "purpose": ""
                                    }
                            except (ValueError, IndexError):
                                item["time_blocks"] = None
                        else:
                            item["time_blocks"] = None

            return plan_items

        except Exception as e:
            logger.error(f"Error fetching plan items: {str(e)}")
            return []

    async def get_current_plan_items_for_user(self, profile_id: str, date_str: str = None, analysis_result_id: str = None) -> Dict[str, Any]:
        """Get plan items for a user - if analysis_result_id provided, use specific analysis, otherwise find most recent COMPLETE analysis"""
        try:
            from datetime import date
            target_date = date.fromisoformat(date_str) if date_str else date.today()
            target_date_str = target_date.isoformat()
            
            logger.info(f"Fetching plan items for profile_id: {profile_id}, date: {target_date_str}, analysis_result_id: {analysis_result_id}")
            
            complete_analysis = None
            
            # Step 1: If specific analysis_result_id provided, use that directly
            if analysis_result_id:
                logger.info(f"Using specific analysis_result_id: {analysis_result_id}")
                specific_analysis = self.supabase.table("holistic_analysis_results")\
                    .select("id, archetype, analysis_date, created_at, user_id")\
                    .eq("id", analysis_result_id)\
                    .eq("user_id", profile_id)\
                    .single()\
                    .execute()
                
                if specific_analysis.data:
                    # Verify this analysis has plan_items (no need to check time_blocks for specific requests)
                    plan_items_check = self.supabase.table("plan_items")\
                        .select("id")\
                        .eq("analysis_result_id", analysis_result_id)\
                        .limit(1)\
                        .execute()
                    
                    if plan_items_check.data:
                        complete_analysis = specific_analysis.data
                        logger.info(f"Using specific analysis: {complete_analysis['id']} ({complete_analysis['archetype']})")
                    else:
                        logger.warning(f"Specific analysis {analysis_result_id} has no plan_items")
                        return {"routine_plan": None, "nutrition_plan": None, "items": [], "date": target_date_str}
                else:
                    logger.warning(f"Specific analysis {analysis_result_id} not found for user {profile_id}")
                    return {"routine_plan": None, "nutrition_plan": None, "items": [], "date": target_date_str}
            
            # Step 2: If no specific analysis_result_id, find most recent COMPLETE analysis
            if not complete_analysis:
                logger.info("No specific analysis_result_id provided, finding most recent complete analysis")
                analyses_with_blocks = self.supabase.table("holistic_analysis_results")\
                    .select("id, archetype, analysis_date, created_at, user_id")\
                    .eq("user_id", profile_id)\
                    .in_("analysis_type", ["routine_plan", "nutrition_plan"])\
                    .order("created_at", desc=True)\
                    .execute()
                
                if not analyses_with_blocks.data:
                    logger.warning(f"No analyses found for user {profile_id}")
                    return {"routine_plan": None, "nutrition_plan": None, "items": [], "date": target_date_str}
                
                # Find the most recent analysis that has both time_blocks AND plan_items
                for analysis in analyses_with_blocks.data:
                    # Check if this analysis has time_blocks
                    time_blocks_check = self.supabase.table("time_blocks")\
                        .select("id")\
                        .eq("analysis_result_id", analysis["id"])\
                        .limit(1)\
                        .execute()
                    
                    # Check if this analysis has plan_items
                    plan_items_check = self.supabase.table("plan_items")\
                        .select("id")\
                        .eq("analysis_result_id", analysis["id"])\
                        .limit(1)\
                        .execute()
                    
                    if time_blocks_check.data and plan_items_check.data:
                        complete_analysis = analysis
                        logger.info(f"Found complete analysis: {analysis['id']} ({analysis['archetype']}, {analysis['analysis_date']})")
                        break
                
                if not complete_analysis:
                    logger.warning(f"No complete analyses found for user {profile_id}")
                    return {"routine_plan": None, "nutrition_plan": None, "items": [], "date": target_date_str}
            
            # Step 2: Get plan items using our new implementation
            plan_items = self.get_plan_items_for_analysis(complete_analysis["id"], trackable_only=True)

            logger.info(f"DEBUG: Retrieved {len(plan_items)} items for analysis {complete_analysis['id']}")
            if plan_items:
                logger.info(f"DEBUG: First item time_block: {plan_items[0].get('time_block')}")
                logger.info(f"DEBUG: First item time_blocks: {plan_items[0].get('time_blocks')}")

            # If no items for target date, try again with our new implementation (should not happen with current logic)
            if not plan_items:
                logger.info(f"No items found - trying fallback logic")
                plan_items = self.get_plan_items_for_analysis(complete_analysis["id"], trackable_only=False)
            
            # Step 3: Organize response
            all_items = []
            plan_info = {
                "routine_plan": {
                    "analysis_id": complete_analysis["id"],
                    "analysis_result_id": complete_analysis["id"],  # Add explicit analysis_result_id field
                    "archetype": complete_analysis.get("archetype"),
                    "created_at": complete_analysis["created_at"],
                    "analysis_date": complete_analysis["analysis_date"]
                },
                "nutrition_plan": None
            }
            
            for item in plan_items:
                # Add plan context to item
                item["plan_type"] = "routine_plan"
                item["analysis_info"] = plan_info["routine_plan"]
                all_items.append(item)
            
            logger.info(f"Returning {len(all_items)} plan items from analysis {complete_analysis['id']}")
            
            return {
                "routine_plan": plan_info["routine_plan"],
                "nutrition_plan": plan_info["nutrition_plan"],
                "items": all_items,
                "date": target_date_str,
                "analysis_used": complete_analysis["id"],
                "archetype": complete_analysis.get("archetype")
            }
            
        except Exception as e:
            logger.error(f"Error fetching current plan items: {str(e)}")
            # Use date_str if available, fallback to today
            fallback_date = date_str if date_str else date.today().isoformat()
            return {"routine_plan": None, "nutrition_plan": None, "items": [], "date": fallback_date}

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
            
            # Find all time blocks with enhanced parsing - try multiple patterns
            time_block_patterns = [
                # NEW FORMAT: **Block Name (Time Range): Purpose** (dynamic circadian timing)
                r'\*\*([^*]+?)\s*\(([^)]+)\)\s*:\s*([^*]+?)\*\*\s*\n(.*?)(?=\n\*\*[^*]+?\s*\([^)]+\)\s*:|\n\*\*Health Data Integration|\Z)',
                # Format: **1. Block Title (Time): Description**
                r'\*\*(\d+)\.\s+([^*]+?)\*\*\s*\n(.*?)(?=\n\*\*\d+\.|\n\*\*Health Data Integration|\Z)',
                # Format: 1. **Block Title**
                r'(\d+)\.\s+\*\*([^*]+?)\*\*\s*\n(.*?)(?=\n\d+\.\s+\*\*|\n\*\*Health Data Integration|\Z)',
                # Format: **Block Title (Time):** (legacy)
                r'\*\*([^*]+?)\s*\(([^)]+)\)\s*:[^*]*?\*\*\s*\n(.*?)(?=\n\*\*[^*]+?\s*\([^)]+\)\s*:|\n\*\*Health Data Integration|\Z)',
            ]
            
            time_block_matches = []
            successful_pattern = None
            
            # Try each pattern until we find matches
            for i, pattern in enumerate(time_block_patterns):
                logger.debug(f"Trying time block pattern {i+1}: {pattern[:50]}...")
                matches = list(re.finditer(pattern, content, re.DOTALL))
                if matches:
                    time_block_matches = matches
                    successful_pattern = pattern
                    pass  # Production: Remove verbose pattern logging
                    break
                else:
                    logger.debug(f"❌ Pattern {i+1} found 0 matches")
            
            if not time_block_matches:
                logger.warning("❌ No time blocks found with structured patterns - trying emergency fallback")
                # BULLETPROOF FALLBACK: Extract anything that looks like a time block
                return self._emergency_extraction_fallback(content, analysis_result, user_id, date, archetype)

            # Initialize global task counter to prevent duplicate task IDs
            global_task_order = 1

            for block_match in time_block_matches:
                # Handle different patterns - some patterns may have different group structures
                num_groups = len(block_match.groups())

                if num_groups == 4:
                    # NEW FORMAT: **Block Name (Time Range): Purpose** - 4 groups
                    block_name = block_match.group(1).strip()
                    time_range_extracted = block_match.group(2).strip()
                    purpose_extracted = block_match.group(3).strip()
                    block_content = block_match.group(4).strip()

                    # Use block name as title and generate sequential order number
                    block_title = f"{block_name} ({time_range_extracted}): {purpose_extracted}"
                    block_number = str(len(time_blocks) + 1)  # Sequential numbering

                    logger.info(f"NEW FORMAT - Processing time block {block_number}: {block_name}")
                elif num_groups >= 3:
                    # Standard pattern with 3 groups
                    block_number = block_match.group(1)
                    block_title = block_match.group(2).strip()
                    block_content = block_match.group(3).strip()
                elif num_groups == 2:
                    # Pattern with 2 groups (no explicit number)
                    block_title = block_match.group(1).strip()
                    block_content = block_match.group(2).strip()
                    # Extract block number from title if present
                    number_match = re.match(r'(\d+)\.\s*(.+)', block_title)
                    if number_match:
                        block_number = number_match.group(1)
                        block_title = number_match.group(2).strip()
                    else:
                        block_number = str(len(time_blocks) + 1)  # Auto-increment
                else:
                    logger.warning(f"Unexpected pattern structure with {num_groups} groups")
                    continue
                
                logger.info(f"Processing time block {block_number}: {block_title}")
                logger.debug(f"Block content length: {len(block_content)} characters")

                # Extract time range and purpose from block title (or use pre-extracted values for new format)
                if num_groups == 4:
                    # NEW FORMAT: Already extracted time_range and purpose
                    time_range = time_range_extracted
                    purpose = purpose_extracted
                else:
                    # LEGACY FORMAT: Extract from block title
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
                
                # Extract tasks from this time block with enhanced pattern matching
                tasks_section_patterns = [
                    # NEW FORMAT: - **Tasks:** ... - **Reasoning:**
                    r'-\s*\*\*Tasks:\*\*\s*(.*?)(?=-\s*\*\*(?:Reasoning|Why It Matters|Connection to Insights)|\Z)',
                    # Alternative: **Tasks:** ... **Reasoning:**
                    r'\*\*Tasks:\*\*\s*(.*?)(?=\*\*(?:Reasoning|Why It Matters|Connection to Insights)|\Z)',
                    # Legacy format: - **Tasks:** ... - **Why It Matters:**
                    r'-\s*\*\*Tasks:\*\*\s*(.*?)(?=-\s*\*\*(?:Why It Matters|Connection to Insights)|\Z)',
                ]
                
                tasks_content = None
                for tasks_pattern in tasks_section_patterns:
                    tasks_section_match = re.search(tasks_pattern, block_content, re.DOTALL | re.IGNORECASE)
                    if tasks_section_match:
                        tasks_content = tasks_section_match.group(1).strip()
                        break
                
                if tasks_content:
                    # First check if tasks_content is just one paragraph (new format)
                    if not re.search(r'\n\s*-', tasks_content):
                        # NEW FORMAT: Single paragraph of tasks, split by sentences
                        sentences = [s.strip() for s in re.split(r'[.!?]+', tasks_content) if s.strip()]

                        for sentence in sentences:
                            if len(sentence) > 10:  # Skip very short fragments
                                task_id = f"{analysis_id}_task_{global_task_order}"
                                task = ExtractedTask(
                                    task_id=task_id,
                                    title=sentence[:50] + "..." if len(sentence) > 50 else sentence,
                                    description=sentence,
                                    time_block_id=block_id,
                                    scheduled_time=None,
                                    scheduled_end_time=None,
                                    estimated_duration_minutes=None,
                                    task_type="general",
                                    priority_level="medium",
                                    task_order_in_block=global_task_order,
                                    parent_routine_id=analysis_id
                                )
                                all_tasks.append(task)
                                global_task_order += 1
                    else:
                        # LEGACY FORMAT: Individual task bullet points
                        task_patterns = [
                            # Format: - **Task Name (Time):** Description
                            r'-\s+\*\*([^(]*?)\s*\(([^)]+)\)\s*:\*\*\s*([^\n]*?)(?=\n\s*-|\Z)',
                            # Format: - **Time: Task Name:** Description
                            r'-\s+\*\*([^:]*?):\s*([^*]+?)\*\*\s*([^\n]*?)(?=\n\s*-|\Z)',
                            # Format: - **Task Name:** Description
                            r'-\s+\*\*([^*:]+?)\*\*\s*([^\n]*?)(?=\n\s*-|\Z)',
                            # Format: - Task with time pattern
                            r'-\s+([^*\n]*?(?:\d{1,2}:\d{2}[^*\n]*?)?)(?=\n\s*-|\Z)',
                        ]

                        task_matches = []
                        for i, task_pattern in enumerate(task_patterns):
                            matches = list(re.finditer(task_pattern, tasks_content, re.DOTALL | re.IGNORECASE))
                            if matches:
                                task_matches = matches
                                logger.debug(f"✅ Found {len(matches)} tasks using task pattern {i+1}")
                                break
                            else:
                                logger.debug(f"❌ Task pattern {i+1} found 0 matches")

                        for task_match in task_matches:
                            # Handle different task pattern formats
                            num_groups = len(task_match.groups())

                            if num_groups >= 3:
                                # Pattern with 3 groups: task_name, time_info, description
                                task_name = task_match.group(1).strip()
                                time_info = task_match.group(2).strip() if task_match.group(2) else ""
                                task_description = task_match.group(3).strip() if task_match.group(3) else ""
                            elif num_groups == 2:
                                # Pattern with 2 groups: task_name, description (or task_name, time_info)
                                task_name = task_match.group(1).strip()
                                # Check if second group looks like time info or description
                                second_group = task_match.group(2).strip()
                                if re.match(r'\d{1,2}:\d{2}', second_group):
                                    time_info = second_group
                                    task_description = ""
                                else:
                                    time_info = ""
                                    task_description = second_group
                            else:
                                # Pattern with 1 group: combined task info
                                full_text = task_match.group(1).strip()
                                # Try to extract time info from the text
                                time_match = re.search(r'\(([^)]*\d{1,2}:\d{2}[^)]*)\)', full_text)
                                if time_match:
                                    time_info = time_match.group(1).strip()
                                    task_name = re.sub(r'\([^)]*\d{1,2}:\d{2}[^)]*\)', '', full_text).strip()
                                    task_description = ""
                                else:
                                    task_name = full_text
                                    time_info = ""
                                    task_description = ""

                            # Clean up task name
                            task_name = re.sub(r'^[*\s:-]+|[*\s:-]+$', '', task_name).strip()

                            if not task_name or len(task_name) < 3:
                                logger.debug(f"Skipping task with insufficient name: '{task_name}'")
                                continue

                            # Parse timing information
                            start_time, end_time, duration = self._extract_task_timing(time_info)

                            # Determine task type and priority
                            task_type = self._determine_task_type(task_name, task_description)
                            priority_level = self._determine_priority(task_name, task_description, archetype)

                            # Create task linked to time block
                            task = ExtractedTask(
                                task_id=f"{analysis_id}_task_{global_task_order}",
                                title=task_name,
                                description=task_description,
                                scheduled_time=start_time,
                                scheduled_end_time=end_time,
                                estimated_duration_minutes=duration,
                                task_type=task_type,
                                priority_level=priority_level,
                                task_order_in_block=global_task_order,
                                time_block_id=block_id,
                                parent_routine_id=analysis_id
                            )

                            all_tasks.append(task)
                            global_task_order += 1

                            logger.info(f"  ✓ Extracted task: {task_name} ({time_info})")
                            logger.debug(f"    Task details - Name: '{task_name}', Time: '{time_info}', Description: '{task_description[:50]}...'")
                else:
                    logger.warning(f"❌ No tasks section found in block: {block_title}")
                    logger.debug(f"Block content preview (500 chars): {block_content[:500]}...")
            
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
    
    def _emergency_extraction_fallback(self, content: str, analysis_result: Dict[str, Any], user_id: str, date: str, archetype: str) -> ExtractedPlan:
        """
        BULLETPROOF FALLBACK: When structured patterns fail, extract ANYTHING useful
        This method NEVER fails - it always returns something
        """
        time_blocks = []
        all_tasks = []
        
        try:
            logger.info("🚨 EMERGENCY EXTRACTION: Using aggressive fallback patterns")
            
            # STEP 1: Find ANYTHING that looks like a time block (very loose patterns)
            emergency_patterns = [
                # Any line with ** and numbers and time patterns
                r'\*\*.*?(\d+).*?\*\*.*?(\d{1,2}:\d{2}.*?\d{1,2}:\d{2}|AM|PM).*?\n(.*?)(?=\n\*\*|\Z)',
                # Any header with ** and containing time info
                r'\*\*([^*]*(?:\d{1,2}:\d{2}[^*]*)?)\*\*\s*\n(.*?)(?=\n\*\*[^*]*(?:\d{1,2}:\d{2}|$)|\Z)',
                # Just lines starting with **
                r'\*\*([^*]+)\*\*\s*\n(.*?)(?=\n\*\*|\Z)',
                # Even markdown headers
                r'^#+\s*([^\n]*(?:\d{1,2}:\d{2}[^\n]*)?)\s*\n(.*?)(?=\n#+|\Z)',
            ]
            
            block_found = False
            for i, pattern in enumerate(emergency_patterns):
                matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
                if matches:
                    pass  # Production: Remove verbose emergency pattern logging
                    
                    for j, match in enumerate(matches):
                        groups = match.groups()
                        if len(groups) >= 2:
                            block_title = groups[0].strip()
                            block_content = groups[1].strip()
                            
                            # Skip if too short or likely noise
                            if len(block_title) < 5 or len(block_content) < 10:
                                continue
                                
                            # Create time block
                            time_range = self._extract_time_range_string(block_title) or "Time not specified"
                            time_block = TimeBlockContext(
                                block_id=f"emergency_block_{j+1}",
                                title=block_title,
                                time_range=time_range,
                                purpose=f"Emergency extraction from pattern {i+1}",
                                block_order=j+1,
                                archetype=archetype
                            )
                            time_blocks.append(time_block)
                            
                            # Extract tasks from this block content
                            tasks = self._emergency_extract_tasks(block_content, time_block.block_id, j+1)
                            all_tasks.extend(tasks)
                            block_found = True
                    
                    if block_found:
                        break
            
            # STEP 2: If still no blocks, create one big block from the entire content
            if not time_blocks:
                logger.info("🚨 CREATING SINGLE MEGA-BLOCK from entire content")
                time_block = TimeBlockContext(
                    block_id="mega_block_1",
                    title="Complete Plan Content",
                    time_range="Full day",
                    purpose="Emergency extraction - single block",
                    block_order=1,
                    archetype=archetype
                )
                time_blocks.append(time_block)
                
                # Extract ANY actionable items from the entire content
                all_tasks = self._emergency_extract_tasks(content, "mega_block_1", 1)
            
            # STEP 3: Ensure we have at least SOMETHING
            if not all_tasks:
                logger.info("🚨 NO TASKS FOUND - Creating placeholder tasks")
                # Create placeholder tasks from any bullet points or lines with keywords
                placeholder_tasks = self._create_placeholder_tasks(content, time_blocks[0].block_id if time_blocks else "fallback_block")
                all_tasks.extend(placeholder_tasks)
            
            # STEP 4: If we STILL have nothing, create absolute minimum
            if not time_blocks and not all_tasks:
                logger.warning("🚨 ABSOLUTE FALLBACK - Creating minimal structure")
                time_blocks = [TimeBlockContext(
                    block_id="absolute_fallback",
                    title="Plan Content (Structure not detected)",
                    time_range="Various times",
                    purpose="Fallback extraction",
                    block_order=1,
                    archetype=archetype
                )]
                all_tasks = [ExtractedTask(
                    task_id="fallback_task_1",
                    title="Review the generated plan",
                    description="Plan structure could not be parsed automatically",
                    scheduled_time=None,
                    scheduled_end_time=None,
                    estimated_duration_minutes=None,
                    task_type="general",
                    priority_level="medium",
                    task_order_in_block=1,
                    time_block_id="absolute_fallback"
                )]
            
            # Production: Verbose logging removed
            
            return ExtractedPlan(
                plan_id=analysis_result.get('id', 'emergency'),
                user_id=user_id,
                date=date,
                archetype=archetype,
                time_blocks=time_blocks,
                tasks=all_tasks,
                extraction_metadata={
                    "extraction_method": "emergency_fallback",
                    "total_time_blocks": len(time_blocks),
                    "total_tasks": len(all_tasks),
                    "content_length": len(content)
                }
            )
            
        except Exception as e:
            logger.error(f"🚨 EMERGENCY EXTRACTION FAILED: {e}")
            # ABSOLUTE LAST RESORT
            return ExtractedPlan(
                plan_id=analysis_result.get('id', 'error'),
                user_id=user_id,
                date=date,
                archetype=archetype,
                time_blocks=[TimeBlockContext(
                    block_id="error_block",
                    title="Extraction Error",
                    time_range="Unknown",
                    purpose="Error fallback",
                    block_order=1,
                    archetype=archetype
                )],
                tasks=[ExtractedTask(
                    task_id="error_task",
                    title="Plan extraction encountered an error",
                    description=f"Error: {str(e)[:100]}",
                    scheduled_time=None,
                    scheduled_end_time=None,
                    estimated_duration_minutes=None,
                    task_type="general",
                    priority_level="medium",
                    task_order_in_block=1,
                    time_block_id="error_block"
                )],
                extraction_metadata={"error": str(e), "method": "absolute_last_resort"}
            )
    
    def _emergency_extract_tasks(self, content: str, block_id: str, block_num: int) -> List[ExtractedTask]:
        """Extract tasks using very aggressive patterns - never fails"""
        tasks = []
        
        # Super aggressive task patterns
        task_patterns = [
            # Any line with ** and containing time info
            r'[-*]\s*\*\*([^*]*?(?:\d{1,2}:\d{2}[^*]*?)?)\*\*[:\s]*([^\n]*)',
            # Any bullet point
            r'[-*•]\s*([^\n]{10,})',
            # Any line containing time patterns
            r'([^\n]*\d{1,2}:\d{2}[^\n]*)',
            # Just capture anything after **
            r'\*\*([^*]{5,})\*\*',
        ]
        
        for pattern in task_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                for i, match in enumerate(matches[:10]):  # Limit to 10 tasks per pattern
                    if isinstance(match, tuple):
                        task_text = ' '.join([m for m in match if m]).strip()
                    else:
                        task_text = match.strip()
                    
                    if len(task_text) > 5:  # Must have some content
                        task = ExtractedTask(
                            task_id=f"emergency_task_{block_num}_{i+1}",
                            title=task_text[:100],  # Limit title length
                            description=task_text if len(task_text) > 100 else "",
                            scheduled_time=None,
                            scheduled_end_time=None,
                            estimated_duration_minutes=None,
                            task_type="general",
                            priority_level="medium",
                            task_order_in_block=i+1,
                            time_block_id=block_id
                        )
                        tasks.append(task)
                break  # Stop at first successful pattern
        
        return tasks
    
    def _create_placeholder_tasks(self, content: str, block_id: str) -> List[ExtractedTask]:
        """Create placeholder tasks when nothing else works"""
        # Split content by common separators and create tasks
        sections = re.split(r'\n\n+|\n---+\n|\n===+\n', content)
        tasks = []
        
        for i, section in enumerate(sections[:5]):  # Max 5 sections
            section = section.strip()
            if len(section) > 20:  # Must have reasonable content
                # Take first sentence or 100 chars
                title = section.split('.')[0][:100] if '.' in section else section[:100]
                task = ExtractedTask(
                    task_id=f"placeholder_task_{i+1}",
                    title=title.strip(),
                    description=section[:200] if len(section) > 100 else "",
                    scheduled_time=None,
                    scheduled_end_time=None,
                    estimated_duration_minutes=None,
                    task_type="general",
                    priority_level="medium",
                    task_order_in_block=i+1,
                    time_block_id=block_id
                )
                tasks.append(task)
        
        return tasks if tasks else [ExtractedTask(
            task_id="final_fallback_task",
            title="Review your personalized plan",
            description="Plan extraction used fallback method",
            scheduled_time=None,
            scheduled_end_time=None,
            estimated_duration_minutes=None,
            task_type="general",
            priority_level="medium",
            task_order_in_block=1,
            time_block_id=block_id
        )]
    
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
    
    async def _extract_plan_with_normalized_structure(self, content: str, analysis_result: Dict[str, Any], profile_id: str) -> ExtractedPlan:
        """
        Extract plan with normalized time blocks and tasks structure
        Supports both regex and AI extraction methods
        """
        try:
            # TOGGLE: Choose extraction method based on configuration
            if EXTRACTION_METHOD == 'ai':
                from services.ai_plan_extraction_service import extract_plan_with_ai
                extracted_plan = await extract_plan_with_ai(content, analysis_result)
            else:
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
    
    async def _store_plan_items_with_time_blocks(self, analysis_result_id: str, profile_id: str, tasks: List[ExtractedTask], time_block_id_map: Dict[str, str], override_plan_date: str = None) -> List[Dict[str, Any]]:
        """Store plan items with time block relationships"""
        if not tasks:
            return []
        
        try:
            # Use override_plan_date if provided, otherwise get from holistic_analysis_results
            if override_plan_date:
                plan_date = override_plan_date
            else:
                # Get the analysis_date from holistic_analysis_results for plan_date
                analysis_result = self.supabase.table("holistic_analysis_results")\
                    .select("analysis_date")\
                    .eq("id", analysis_result_id)\
                    .execute()
                
                if not analysis_result.data:
                    raise HolisticOSException(f"Analysis result {analysis_result_id} not found")
                
                plan_date = analysis_result.data[0]["analysis_date"]
            
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
                    'priority_level': task.priority_level,
                    'plan_date': plan_date  # Add the plan date from analysis
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