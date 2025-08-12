"""
Supabase Adapter for AsyncPG compatibility
This adapter allows existing asyncpg code to work with Supabase client
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from supabase import create_client, Client
import os
from pathlib import Path
from dotenv import load_dotenv


class SupabaseAsyncPGAdapter:
    """
    Adapter that provides AsyncPG-like interface using Supabase client
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        # Load environment variables if not provided
        if not supabase_url or not supabase_key:
            self._load_env()
            
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be provided or set in environment")
            
        self.client: Optional[Client] = None
        self._connected = False

    def _load_env(self):
        """Load environment variables from .env file"""
        current_dir = Path(__file__).parent.parent
        parent_dir = current_dir.parent
        env_locations = [
            current_dir / ".env",
            parent_dir / ".env",
            Path.cwd() / ".env"
        ]

        for env_path in env_locations:
            if env_path.exists():
                load_dotenv(env_path)
                break

    async def connect(self):
        """Initialize Supabase client (mimics asyncpg.connect)"""
        try:
            print(f"[🔍] Attempting Supabase connection...")
            print(f"[🔍] URL: {self.supabase_url[:30]}..." if self.supabase_url else "[🔍] URL: None")
            print(f"[🔍] Key: {'Present' if self.supabase_key else 'Missing'}")
            
            self.client = create_client(self.supabase_url, self.supabase_key)
            self._connected = True
            print(f"[✅] Connected to Supabase successfully - client type: {type(self.client)}")
            return self
        except Exception as e:
            print(f"[❌] Supabase connection failed: {e}")
            self._connected = False
            self.client = None
            raise

    async def close(self):
        """Close connection (mimics asyncpg connection.close)"""
        self._connected = False
        self.client = None
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected"""
        return self._connected and self.client is not None

    def _ensure_connected(self):
        """Ensure we have an active connection"""
        if not self._connected or not self.client:
            raise RuntimeError("Not connected to Supabase. Call connect() first.")

    async def execute(self, query: str, *args) -> str:
        """
        Execute a query (INSERT, UPDATE, DELETE)
        Returns status message like asyncpg
        """
        self._ensure_connected()
        
        try:
            # Parse the SQL query and convert to Supabase operations
            parsed_query = self._parse_query(query, args)
            
            if parsed_query['operation'] == 'INSERT':
                result = self.client.table(parsed_query['table']).insert(parsed_query['data']).execute()
                return f"INSERT 0 {len(result.data)}"
                
            elif parsed_query['operation'] == 'UPDATE':
                update_data = parsed_query['data'].copy()
                
                # Special handling for total_analyses increment
                if 'total_analyses' in update_data:
                    print(f"[MEMORY] Handling total_analyses increment for {parsed_query['where_value']}")
                    # First get current value
                    current_record = self.client.table(parsed_query['table']).select('total_analyses').eq(
                        parsed_query['where_column'], parsed_query['where_value']
                    ).execute()
                    
                    current_count = 0
                    if current_record.data:
                        current_count = current_record.data[0].get('total_analyses', 0)
                    
                    # Update with incremented value
                    update_data['total_analyses'] = current_count + 1
                    print(f"[MEMORY] Incrementing total_analyses from {current_count} to {current_count + 1}")
                
                print(f"[MEMORY] Updating {parsed_query['table']} with {len(update_data)} fields")
                for field, value in update_data.items():
                    if isinstance(value, (dict, list)):
                        print(f"[MEMORY] {field}: JSON data with {len(value) if isinstance(value, (dict, list)) else 'unknown'} items")
                    else:
                        print(f"[MEMORY] {field}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
                
                # Debug WHERE clause
                print(f"[MEMORY] WHERE {parsed_query.get('where_column')} = {parsed_query.get('where_value')}")
                
                result = self.client.table(parsed_query['table']).update(update_data).eq(
                    parsed_query['where_column'], parsed_query['where_value']
                ).execute()
                
                print(f"[MEMORY] Update successful: {len(result.data)} rows affected")
                return f"UPDATE {len(result.data)}"
                
            elif parsed_query['operation'] == 'DELETE':
                result = self.client.table(parsed_query['table']).delete().eq(
                    parsed_query['where_column'], parsed_query['where_value']
                ).execute()
                return f"DELETE {len(result.data)}"
                
            else:
                raise ValueError(f"Unsupported operation: {parsed_query['operation']}")
                
        except Exception as e:
            print(f"[❌] Query execution failed: {e}")
            print(f"[📝] Query: {query}")
            print(f"[📝] Args: {args}")
            raise

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Fetch multiple rows (SELECT queries)
        Returns list of dictionaries like asyncpg
        """
        self._ensure_connected()
        
        try:
            parsed_query = self._parse_query(query, args)
            self._validate_query(parsed_query, 'SELECT')
            
            # Handle COUNT queries specially
            if 'COUNT' in query.upper():
                return await self._handle_count_query(parsed_query, args)
            
            # Build Supabase query
            supabase_query = self.client.table(parsed_query['table']).select(parsed_query['columns'])
            
            # Add WHERE clause if present
            # Apply WHERE conditions
            if parsed_query.get('where_conditions'):
                for condition in parsed_query['where_conditions']:
                    column = condition['column']
                    operator = condition['operator']
                    value = condition['value']
                    
                    if operator == 'eq':
                        supabase_query = supabase_query.eq(column, value)
                    elif operator == 'gte':
                        supabase_query = supabase_query.gte(column, value)
                    elif operator == 'lte':
                        supabase_query = supabase_query.lte(column, value)
            
            # Fallback for legacy single where condition
            elif parsed_query.get('where_column') and parsed_query.get('where_value'):
                supabase_query = supabase_query.eq(parsed_query['where_column'], parsed_query['where_value'])
            
            # Add ORDER BY if present
            if parsed_query.get('order_by'):
                supabase_query = supabase_query.order(parsed_query['order_by']['column'], 
                                                    desc=parsed_query['order_by'].get('desc', False))
            
            # Add LIMIT if present
            if parsed_query.get('limit'):
                supabase_query = supabase_query.limit(parsed_query['limit'])
            
            result = supabase_query.execute()
            return result.data
            
        except Exception as e:
            print(f"[ERROR] Query fetch failed: {e}")
            self._log_query_debug(query, args, parsed_query if 'parsed_query' in locals() else None)
            raise

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Fetch single row (SELECT queries or INSERT with RETURNING)
        Returns dictionary or None like asyncpg
        """
        self._ensure_connected()  # ADD THIS CHECK - same as execute() has
        
        try:
            # Handle INSERT with RETURNING specially
            if 'INSERT' in query.upper() and 'RETURNING' in query.upper():
                return await self._handle_insert_returning(query, args)
            
            rows = await self.fetch(query, *args)
            return rows[0] if rows else None
        except Exception as e:
            print(f"[❌] Query fetchrow failed: {e}")
            raise

    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch single value from single row
        Returns the value or None like asyncpg
        """
        try:
            row = await self.fetchrow(query, *args)
            if row and len(row) > 0:
                return list(row.values())[0]
            return None
        except Exception as e:
            print(f"[❌] Query fetchval failed: {e}")
            raise

    def _parse_query(self, query: str, args: tuple) -> Dict[str, Any]:
        """
        Parse SQL query and convert to Supabase operations
        Enhanced parser with proper SQL clause separation
        """
        import re
        
        query = query.strip()
        query_upper = query.upper()
        
        # Replace parameter placeholders ($1, $2, etc.) with actual values
        processed_query = query
        for i, arg in enumerate(args, 1):
            placeholder = f"${i}"
            if isinstance(arg, str):
                # Clean string args to remove null terminators
                cleaned_arg = arg.rstrip('\x00').strip()
                # Escape single quotes in strings
                escaped_arg = cleaned_arg.replace("'", "''")
                processed_query = processed_query.replace(placeholder, f"'{escaped_arg}'")
            elif hasattr(arg, 'isoformat'):  # datetime object
                # Format datetime for PostgreSQL compatibility
                processed_query = processed_query.replace(placeholder, f"'{arg.isoformat()}'")
            else:
                processed_query = processed_query.replace(placeholder, str(arg))

        result = {
            'original_query': processed_query,
            'raw_args': args
        }

        # Parse INSERT queries
        if query_upper.startswith('INSERT'):
            result['operation'] = 'INSERT'
            
            # Extract table name
            table_match = query_upper.find('INTO ') + 5
            table_end = query.find('(', table_match)
            if table_end == -1:
                table_end = query.find(' ', table_match)
            result['table'] = query[table_match:table_end].strip()
            
            # For memory table INSERTs, create data dict from args
            if 'memory' in result['table'] or result['table'] in ['analysis_memory', 'memory', 'holistic_analysis_results']:
                result['data'] = self._create_generic_insert_data(query, args)
            
        # Parse UPDATE queries  
        elif query_upper.startswith('UPDATE'):
            result['operation'] = 'UPDATE'
            
            # Extract table name
            table_start = query_upper.find('UPDATE ') + 7
            table_end = query.find(' SET', table_start)
            result['table'] = query[table_start:table_end].strip()
            
            # Extract WHERE clause with parameter replacement
            where_pos = query_upper.find('WHERE ')
            if where_pos != -1:
                where_clause = query[where_pos + 6:].strip()
                if '=' in where_clause:
                    where_parts = where_clause.split('=')
                    result['where_column'] = where_parts[0].strip()
                    where_value_raw = where_parts[1].strip()
                    
                    # Handle parameter placeholders in WHERE clause
                    if where_value_raw.startswith('$'):
                        param_num = int(where_value_raw[1:])
                        if param_num <= len(args):
                            result['where_value'] = args[param_num - 1]
                        else:
                            result['where_value'] = where_value_raw.replace("'", "")
                    else:
                        result['where_value'] = where_value_raw.replace("'", "")
            
            # For analysis_memory and memory table UPDATEs, create data dict from query
            if result['table'] == 'analysis_memory':
                result['data'] = self._create_analysis_memory_update_data(query, args)
            elif result['table'] == 'memory':
                result['data'] = self._create_memory_update_data(query, args)
                
        # Parse SELECT queries
        elif query_upper.startswith('SELECT'):
            result['operation'] = 'SELECT'
            result.update(self._parse_select_query(processed_query, query_upper))

        # Parse DELETE queries
        elif query_upper.startswith('DELETE'):
            result['operation'] = 'DELETE'
            
            # Extract table name
            from_pos = query_upper.find(' FROM ') + 6
            where_pos = query_upper.find(' WHERE ')
            table_end = where_pos if where_pos != -1 else len(query)
            result['table'] = query[from_pos:table_end].strip()
            
            # Extract WHERE clause
            if where_pos != -1:
                where_clause = query[where_pos + 7:].strip()
                if '=' in where_clause:
                    where_parts = where_clause.split('=')
                    result['where_column'] = where_parts[0].strip()
                    result['where_value'] = where_parts[1].strip().replace("'", "")

        return result
    
    def _parse_select_query(self, query: str, query_upper: str) -> Dict[str, Any]:
        """Parse SELECT query with proper clause separation"""
        result = {}
        
        # Extract columns
        from_pos = query_upper.find(' FROM ')
        if from_pos == -1:
            return result
            
        columns_part = query[6:from_pos].strip()  # Skip "SELECT"
        result['columns'] = columns_part if columns_part != '*' else '*'
        
        # Extract table name
        table_start = from_pos + 6
        table_end = self._find_next_keyword_pos(query_upper, table_start, [' WHERE ', ' ORDER BY ', ' LIMIT ', ' GROUP BY '])
        result['table'] = query[table_start:table_end].strip()
        
        # Extract WHERE clause
        where_pos = query_upper.find(' WHERE ')
        if where_pos != -1:
            where_start = where_pos + 7  # Skip past " WHERE "
            where_end = self._find_next_keyword_pos(query_upper, where_start, [' ORDER BY ', ' LIMIT ', ' GROUP BY '])
            where_clause = query[where_start:where_end].strip()
            result['where_conditions'] = self._parse_where_clause(where_clause)
        
        # Extract ORDER BY - Fixed parsing for multi-column and complex ordering
        order_pos = query_upper.find(' ORDER BY ')
        if order_pos != -1:
            # Get everything after ORDER BY
            order_start = order_pos + 10  # Skip past " ORDER BY "
            order_end = self._find_next_keyword_pos(query_upper, order_start, [' LIMIT ', ' GROUP BY '])
            order_clause = query[order_start:order_end].strip()
            
            # Clean the order clause - remove newlines and extra spaces
            order_clause = ' '.join(order_clause.split())
            
            # Parse ORDER BY clause - Handle complex cases
            if order_clause:
                # Split by comma to handle multiple columns (take first one for Supabase)
                first_column = order_clause.split(',')[0].strip()
                
                # Check for DESC/ASC
                is_desc = 'DESC' in first_column.upper()
                
                # Extract column name by removing DESC/ASC and any extra text
                column_name = first_column.upper().replace(' DESC', '').replace(' ASC', '').strip()
                
                # Handle case where column name has been truncated/mangled - use original column from SELECT
                if len(column_name) < 3 or "'" in column_name:
                    # Fallback: extract column from ORDER BY in original query more carefully
                    import re
                    order_match = re.search(r'ORDER BY\s+([a-zA-Z_][a-zA-Z0-9_]*)', query_upper)
                    if order_match:
                        column_name = order_match.group(1).lower()
                    else:
                        column_name = 'created_at'  # Safe default
                else:
                    column_name = column_name.lower()
                
                result['order_by'] = {
                    'column': column_name,
                    'desc': is_desc
                }
        
        # Extract LIMIT
        limit_pos = query_upper.find(' LIMIT ')
        if limit_pos != -1:
            limit_end = self._find_next_keyword_pos(query_upper, limit_pos, [' GROUP BY ', ' ORDER BY '])
            limit_value = query[limit_pos + 7:limit_end].strip()
            try:
                result['limit'] = int(limit_value)
            except ValueError:
                pass
        
        return result
    
    def _create_generic_insert_data(self, query: str, args: tuple) -> Dict[str, Any]:
        """Create INSERT data dict from query and args - generic parser"""
        import re
        
        # Extract column names from INSERT query
        values_match = re.search(r'\((.*?)\)\s+VALUES', query, re.IGNORECASE | re.DOTALL)
        if not values_match:
            print(f"[ERROR] Could not parse column names from INSERT query")
            return {}
        
        columns_text = values_match.group(1)
        columns = [col.strip() for col in columns_text.split(',')]
        
        # Create data dict from columns and args
        data = {}
        for i, col in enumerate(columns):
            if i < len(args):
                value = args[i]
                # Handle JSON serialization for complex types
                if isinstance(value, dict):
                    data[col] = value
                elif hasattr(value, 'isoformat'):  # datetime
                    data[col] = value.isoformat()
                else:
                    data[col] = value
        
        return data
    
    def _find_next_keyword_pos(self, query_upper: str, start_pos: int, keywords: list) -> int:
        """Find the position of the next SQL keyword"""
        min_pos = len(query_upper)
        for keyword in keywords:
            pos = query_upper.find(keyword, start_pos)
            if pos != -1 and pos < min_pos:
                min_pos = pos
        return min_pos
    
    def _parse_where_clause(self, where_clause: str) -> list:
        """Parse WHERE clause into conditions for Supabase - Fixed boundary detection"""
        conditions = []
        
        # Clean the where clause - remove any ORDER BY, LIMIT, GROUP BY that leaked in
        clean_where = where_clause
        for keyword in [' ORDER BY', ' LIMIT', ' GROUP BY']:
            if keyword in clean_where.upper():
                clean_where = clean_where[:clean_where.upper().find(keyword)]
        
        # Split by AND (simple parsing)
        and_parts = clean_where.split(' AND ')
        
        for part in and_parts:
            part = part.strip()
            if not part:  # Skip empty parts
                continue
                
            # Handle different operators
            if '>=' in part:
                column, value = part.split('>=', 1)
                conditions.append({
                    'column': column.strip(),
                    'operator': 'gte',
                    'value': value.strip().replace("'", "")
                })
            elif '<=' in part:
                column, value = part.split('<=', 1)
                conditions.append({
                    'column': column.strip(),
                    'operator': 'lte', 
                    'value': value.strip().replace("'", "")
                })
            elif '=' in part:
                column, value = part.split('=', 1)
                conditions.append({
                    'column': column.strip(),
                    'operator': 'eq',
                    'value': value.strip().replace("'", "")
                })
        
        return conditions

    def _create_analysis_memory_insert_data(self, args: tuple) -> Dict[str, Any]:
        """Create data dict for analysis_memory table INSERT"""
        if len(args) >= 7:
            # Clean profile_id to remove any null terminators or unwanted characters
            profile_id = str(args[0]).rstrip('\x00').strip() if args[0] else ''
            
            return {
                'profile_id': profile_id,
                'analysis_type': args[1],
                'archetype': args[2],
                'previous_analysis_id': args[3] if args[3] else None,
                'behavior_analysis': json.loads(args[4]) if args[4] and isinstance(args[4], str) else args[4],
                'nutrition_plan': json.loads(args[5]) if args[5] and isinstance(args[5], str) else args[5],
                'routine_plan': json.loads(args[6]) if args[6] and isinstance(args[6], str) else args[6]
            }
        return {}

    def _create_memory_insert_data(self, args: tuple) -> Dict[str, Any]:
        """Create data dict for memory table INSERT"""
        if len(args) >= 6:
            # Clean profile_id to remove any null terminators or unwanted characters
            profile_id = str(args[0]).rstrip('\x00').strip() if args[0] else ''
            
            return {
                'profile_id': profile_id,
                'user_preferences': json.loads(args[1]) if isinstance(args[1], str) else args[1],
                'health_goals': json.loads(args[2]) if isinstance(args[2], str) else args[2],
                'dietary_restrictions': json.loads(args[3]) if isinstance(args[3], str) else args[3],
                'lifestyle_context': json.loads(args[4]) if isinstance(args[4], str) else args[4],
                'medical_conditions': json.loads(args[5]) if isinstance(args[5], str) else args[5]
            }
        return {}

    def _create_analysis_memory_update_data(self, query: str, args: tuple) -> Dict[str, Any]:
        """Create data dict for analysis_memory table UPDATE"""
        import json
        from datetime import datetime
        
        data = {}
        
        # Parse SET clause
        set_pos = query.upper().find(' SET ') + 5
        where_pos = query.upper().find(' WHERE ')
        if where_pos == -1:
            where_pos = len(query)
            
        set_clause = query[set_pos:where_pos].strip()
        
        # Simple parsing for analysis_memory UPDATE - handle common patterns
        assignments = [assign.strip() for assign in set_clause.split(',')]
        
        for assignment in assignments:
            if '=' not in assignment:
                continue
                
            field_part, value_part = assignment.split('=', 1)
            field_name = field_part.strip()
            value_part = value_part.strip()
            
            # Handle parameter placeholders like $1, $2
            if value_part.startswith('$'):
                param_num = int(value_part[1:])
                if param_num <= len(args):
                    raw_value = args[param_num - 1]
                    # Handle JSON fields
                    if field_name in ['engagement_metrics', 'performance_metrics', 'behavior_analysis', 'nutrition_plan', 'routine_plan']:
                        if isinstance(raw_value, str):
                            try:
                                data[field_name] = json.loads(raw_value)
                            except json.JSONDecodeError:
                                data[field_name] = raw_value
                        else:
                            data[field_name] = raw_value
                    else:
                        data[field_name] = raw_value
                        
            elif value_part.upper() == 'NOW()':
                # Special case for NOW() function
                data[field_name] = datetime.now().isoformat()
        
        return data

    def _create_memory_update_data(self, query: str, args: tuple) -> Dict[str, Any]:
        """Create data dict for memory table UPDATE with generic parsing and JSON handling"""
        import json
        import re
        from datetime import datetime
        
        data = {}
        
        # Parse SET clause generically
        set_pos = query.upper().find(' SET ') + 5
        where_pos = query.upper().find(' WHERE ')
        if where_pos == -1:
            where_pos = len(query)
            
        set_clause = query[set_pos:where_pos].strip()
        
        # Enhanced JSON serialization helper
        def serialize_json_field(field_name: str, value):
            # Known JSONB fields that need JSON serialization
            jsonb_fields = {
                'last_analysis_result', 'analysis_insights', 'last_nutrition_plan', 
                'last_routine_plan', 'last_behavior_analysis', 'user_preferences',
                'health_goals', 'dietary_restrictions', 'lifestyle_context', 
                'medical_conditions', 'behavioral_signature', 'sophistication_assessment',
                'primary_goal', 'adaptive_parameters', 'recommendations'
            }
            
            # Also handle archetype-specific plan fields (dynamic names ending with '_plan')
            if field_name.endswith('_plan') or field_name in jsonb_fields:
                if isinstance(value, str):
                    try:
                        # If it's already a JSON string, parse and re-serialize to ensure validity
                        parsed = json.loads(value)
                        return parsed
                    except json.JSONDecodeError:
                        # If not valid JSON, return as string
                        return value
                elif isinstance(value, (dict, list)):
                    # Ensure complex objects are JSON serializable
                    return json.loads(json.dumps(value, default=str))
                else:
                    return value
            else:
                # Non-JSON fields, return as-is
                return value
        
        # Generic SET clause parser - handles any field assignments
        # Parse assignments like "field1 = $1, field2 = $2, field3 = NOW()"
        assignments = []
        current_assignment = ""
        paren_count = 0
        
        for char in set_clause:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                assignments.append(current_assignment.strip())
                current_assignment = ""
                continue
            current_assignment += char
        
        if current_assignment.strip():
            assignments.append(current_assignment.strip())
        
        # Process each assignment
        for assignment in assignments:
            if '=' not in assignment:
                continue
                
            field_part, value_part = assignment.split('=', 1)
            field_name = field_part.strip()
            value_part = value_part.strip()
            
            # Handle different value types
            if value_part.startswith('$'):
                # Parameter placeholder like $1, $2
                param_num = int(value_part[1:])
                if param_num <= len(args):
                    raw_value = args[param_num - 1]  # $1 = args[0]
                    data[field_name] = serialize_json_field(field_name, raw_value)
                    
            elif value_part.upper() == 'NOW()':
                # Special case for NOW() function
                data[field_name] = datetime.now().isoformat()
                
            elif value_part.startswith("'") and value_part.endswith("'"):
                # String literal
                data[field_name] = value_part[1:-1]  # Remove quotes
                
            elif value_part.isdigit():
                # Numeric literal
                data[field_name] = int(value_part)
                
            elif 'total_analyses + 1' in value_part:
                # Special case for incrementing total_analyses
                data[field_name] = 1  # Will be handled by upsert logic
        
        print(f"[MEMORY DEBUG] Parsed {len(assignments)} assignments into {len(data)} data fields")
        for key, value in data.items():
            value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            print(f"[MEMORY DEBUG] {key}: {value_preview}")
        
        return data
    
    def _validate_query(self, parsed_query: Dict[str, Any], expected_operation: str = None) -> None:
        """Validate parsed query structure"""
        if not parsed_query.get('operation'):
            raise ValueError("Query operation not recognized")
        
        if expected_operation and parsed_query['operation'] != expected_operation:
            raise ValueError(f"Expected {expected_operation} query, got {parsed_query['operation']}")
        
        if parsed_query['operation'] in ['SELECT', 'UPDATE', 'DELETE'] and not parsed_query.get('table'):
            raise ValueError(f"{parsed_query['operation']} query missing table name")
    
    async def _handle_count_query(self, parsed_query: Dict[str, Any], args: tuple) -> List[Dict[str, Any]]:
        """Handle COUNT queries using Supabase's count parameter"""
        try:
            # Use Supabase's count functionality
            supabase_query = self.client.table(parsed_query['table']).select('*', count='exact', head=True)
            
            # Apply WHERE conditions
            if parsed_query.get('where_conditions'):
                for condition in parsed_query['where_conditions']:
                    column = condition['column']
                    operator = condition['operator']
                    value = condition['value']
                    
                    if operator == 'eq':
                        supabase_query = supabase_query.eq(column, value)
                    elif operator == 'gte':
                        supabase_query = supabase_query.gte(column, value)
                    elif operator == 'lte':
                        supabase_query = supabase_query.lte(column, value)
            
            # Execute query
            result = supabase_query.execute()
            count_value = result.count if result.count is not None else 0
            
            # Return in format expected by fetchval
            return [{"count": count_value}]
            
        except Exception as e:
            print(f"[ERROR] Count query failed: {e}")
            return [{"count": 0}]
    
    async def _handle_insert_returning(self, query: str, args: tuple) -> Optional[Dict[str, Any]]:
        """Handle INSERT with RETURNING using Supabase's correct insert pattern"""
        try:
            # Parse the INSERT query
            parsed_query = self._parse_query(query, args)
            
            if parsed_query['operation'] != 'INSERT':
                raise ValueError(f"Expected INSERT query, got {parsed_query['operation']}")
            
            # Use the correct Supabase client pattern for insert with return
            result = self.client.table(parsed_query['table']).insert(parsed_query['data']).execute()
            
            # Return the first inserted record
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"[ERROR] INSERT RETURNING failed: {e}")
            raise
    
    def _log_query_debug(self, query: str, args: tuple, parsed_query: Dict[str, Any] = None) -> None:
        """Enhanced debug logging for query issues"""
        print(f"[DEBUG] Original Query: {query}")
        print(f"[DEBUG] Query Args: {args}")
        
        if parsed_query:
            print(f"[DEBUG] Parsed Operation: {parsed_query.get('operation', 'UNKNOWN')}")
            print(f"[DEBUG] Target Table: {parsed_query.get('table', 'UNKNOWN')}")
            print(f"[DEBUG] Processed Query: {parsed_query.get('original_query', 'N/A')}")
            
            if parsed_query.get('where_conditions'):
                print(f"[DEBUG] WHERE Conditions: {parsed_query['where_conditions']}")
            if parsed_query.get('order_by'):
                print(f"[DEBUG] ORDER BY: {parsed_query['order_by']}")


# Factory function to create adapter connection (mimics asyncpg.connect)
async def connect_supabase_adapter(supabase_url: str = None, supabase_key: str = None, **kwargs) -> SupabaseAsyncPGAdapter:
    """
    Create and connect a Supabase adapter
    Mimics asyncpg.connect() signature
    """
    adapter = SupabaseAsyncPGAdapter(supabase_url, supabase_key)
    await adapter.connect()
    return adapter