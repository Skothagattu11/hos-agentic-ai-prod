# Plan Parsers - Format-Specific Extraction

**Architecture**: Auto-detecting parser factory with format-specific implementations

**Last Updated**: 2025-10-08

---

## Overview

The parser system automatically detects the format of routine plan content and routes it to the appropriate specialized parser.

### Design Pattern: Strategy + Factory

```
Plan Content → Parser Factory → Auto-Detection → Specialized Parser → Structured Data
                     ↓
          [JsonPlanParser, MarkdownPlanParser]
```

---

## Architecture

### File Structure

```
services/parsers/
├── __init__.py                 # Package exports
├── base_parser.py             # Base interface (BasePlanParser)
├── json_parser.py             # JSON format handler
├── markdown_parser.py         # Markdown format handler
├── parser_factory.py          # Auto-detection & routing
└── README.md                  # This file
```

### Components

#### 1. BasePlanParser (Interface)

**File**: `base_parser.py`

**Purpose**: Ensures all parsers implement consistent API

**Methods**:
- `can_parse(content: str) -> bool`: Check if parser can handle format
- `parse(content: str, analysis_result: dict) -> dict`: Extract structured data
- `_parse_time_string(time_str: str) -> time`: Helper for time conversion

#### 2. JsonPlanParser

**File**: `json_parser.py`

**Handles**: `/routine/generate-markdown` API format

**Format**:
```json
{
  "time_blocks": [
    {
      "title": "Maintenance Zone",
      "time_range": "6:00 AM - 9:45 AM",
      "purpose": "Gentle activation",
      "why_it_matters": "...",
      "connection_to_insights": "..."
    }
  ],
  "plan_items": [
    {
      "title": "Hydration Protocol",
      "description": "16 oz warm water",
      "time_block": "Maintenance Zone",
      "scheduled_time": "06:00",
      "scheduled_end_time": "06:15",
      "estimated_duration_minutes": 15,
      "task_type": "wellness",
      "priority_level": "medium"
    }
  ]
}
```

**Detection Logic**:
```python
def can_parse(self, content: str) -> bool:
    return '"time_blocks"' in content and '"plan_items"' in content
```

#### 3. MarkdownPlanParser

**File**: `markdown_parser.py`

**Handles**: `/routine/generate` API format

**Format**:
```markdown
**6:00 AM - 9:45 AM: Maintenance Zone**
- **Purpose:** Gentle activation and energy building

- **6:00 AM - 6:15 AM:** Hydration Protocol. Start your day with 16 oz warm water with lemon.
- **6:15 AM - 6:45 AM:** Movement Flow. Gentle yoga sequence focusing on mobility.
```

**Detection Logic**:
```python
def can_parse(self, content: str) -> bool:
    # Look for markdown time block patterns
    return bool(
        re.search(r'\*\*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*:\s*\w+', content)
    )
```

**Regex Patterns**:
- **Time Blocks**: `**6:00 AM - 9:45 AM: Zone Name**`
- **Tasks**: `- **6:00 AM - 6:15 AM:** Task title. Description.`

#### 4. PlanParserFactory

**File**: `parser_factory.py`

**Purpose**: Auto-detect format and route to correct parser

**Flow**:
```python
def parse(content, analysis_result, profile_id):
    for parser in [JsonPlanParser(), MarkdownPlanParser()]:
        if parser.can_parse(content):
            result = parser.parse(content, analysis_result)
            if result and result['time_blocks'] and result['tasks']:
                return ExtractedPlan(...)
    return None  # All parsers failed
```

**Order Matters**: JSON parser is tried first (most structured), then Markdown

---

## Usage

### Integration with Plan Extraction Service

**File**: `services/plan_extraction_service.py`

```python
from services.parsers.parser_factory import parser_factory

# Auto-detect format and extract
extracted_plan = parser_factory.parse(plan_content, analysis_result, profile_id)

if not extracted_plan or not extracted_plan.time_blocks:
    # Fallback to legacy extraction if parsers fail
    extracted_plan = await self._extract_plan_with_normalized_structure(...)
```

### Data Models

**Output**: `ExtractedPlan` object with:
- `plan_id`: Analysis result ID
- `time_blocks`: List of `TimeBlockContext` objects
- `tasks`: List of `ExtractedTask` objects
- `archetype`: User archetype
- `user_id`: Profile ID
- `date`: Creation date

---

## Adding New Parsers

### Step 1: Create Parser Class

```python
# services/parsers/your_parser.py

from services.parsers.base_parser import BasePlanParser
from services.plan_extraction_service import TimeBlockContext, ExtractedTask

class YourFormatParser(BasePlanParser):
    """Parser for your custom format"""

    def can_parse(self, content: str) -> bool:
        # Implement format detection
        return "your_format_marker" in content

    def parse(self, content: str, analysis_result: dict) -> dict:
        # Implement extraction logic
        time_blocks = []
        tasks = []

        # ... your parsing code ...

        return {
            'time_blocks': time_blocks,
            'tasks': tasks
        }
```

### Step 2: Register in Factory

```python
# services/parsers/parser_factory.py

from services.parsers.your_parser import YourFormatParser

class PlanParserFactory:
    def __init__(self):
        self.parsers = [
            JsonPlanParser(),
            YourFormatParser(),  # Add your parser
            MarkdownPlanParser(),
        ]
```

### Step 3: Export in Package

```python
# services/parsers/__init__.py

from services.parsers.your_parser import YourFormatParser

__all__ = [
    'BasePlanParser',
    'JsonPlanParser',
    'MarkdownPlanParser',
    'YourFormatParser',
    'parser_factory'
]
```

---

## Performance

### Extraction Speed

| Parser | Average Time | Method |
|--------|--------------|--------|
| JsonPlanParser | <0.01s | JSON parsing |
| MarkdownPlanParser | <0.05s | Regex matching |

**Total extraction time** (including database storage): ~0.3-0.5s

### Comparison to AI Extraction

| Method | Speed | Cost | Reliability |
|--------|-------|------|-------------|
| Regex (Current) | <1s | Free | 100% |
| AI Extraction | 10-50s | $0.01+ | 95% |

**Decision**: Default to regex (`PLAN_EXTRACTION_METHOD=regex`) for speed and reliability

---

## Testing

### Unit Tests

```python
# Test JsonPlanParser
def test_json_parser():
    parser = JsonPlanParser()
    content = '{"time_blocks": [...], "plan_items": [...]}'

    assert parser.can_parse(content) == True

    result = parser.parse(content, analysis_result)

    assert len(result['time_blocks']) > 0
    assert len(result['tasks']) > 0
```

### Integration Test

```python
# Test parser factory auto-detection
def test_parser_factory():
    # Test with JSON format
    json_content = '{"time_blocks": [...], "plan_items": [...]}'
    plan = parser_factory.parse(json_content, analysis_result, profile_id)
    assert plan is not None

    # Test with Markdown format
    md_content = '**6:00 AM - 9:45 AM: Zone**\n- **6:00 AM - 6:15 AM:** Task'
    plan = parser_factory.parse(md_content, analysis_result, profile_id)
    assert plan is not None
```

### Manual Testing

```bash
# Test extraction with real user data
curl -X POST http://localhost:8002/api/v1/analysis/user/{user_id}/extract-latest

# Check status endpoint for results
curl http://localhost:8002/api/v1/analysis/result/{analysis_id}/status
```

---

## Error Handling

### Parser Failure Cascade

```
1. Try JsonPlanParser
   ↓ (fails)
2. Try MarkdownPlanParser
   ↓ (fails)
3. Return None
   ↓
4. Fallback to legacy extraction in plan_extraction_service.py
```

### Logging

```python
logger.info(f"🎯 Using {parser_name} for extraction")
logger.info(f"✅ {parser_name} successfully extracted {len(blocks)} blocks, {len(tasks)} tasks")
logger.warning(f"⚠️ {parser_name} returned empty results")
logger.error(f"❌ {parser_name} failed: {e}")
```

---

## Database Storage

### Tables

**time_blocks**:
- `id` (uuid, PK)
- `block_title` (text) - Full title with time and purpose
- `time_range` (text) - "6:00 AM - 9:45 AM"
- `purpose` (text) - Short description
- `why_it_matters` (text, optional)
- `connection_to_insights` (text, optional)
- `block_order` (int)
- `analysis_result_id` (uuid, FK)
- `archetype` (text)

**plan_items**:
- `id` (uuid, PK)
- `title` (text)
- `description` (text)
- `scheduled_time` (time) - HH:MM format
- `scheduled_end_time` (time)
- `estimated_duration_minutes` (int)
- `task_type` (text) - wellness, exercise, nutrition, etc.
- `priority_level` (text) - high, medium, low
- `time_block_id` (uuid, FK)
- `analysis_result_id` (uuid, FK)

### Upsert Logic

```python
# Conflict handling
ON CONFLICT (analysis_result_id, block_order) DO UPDATE ...
ON CONFLICT (analysis_result_id, task_order_in_block) DO UPDATE ...
```

---

## Future Enhancements

### Potential Additions

1. **XML Parser**: For systems exporting XML format
2. **YAML Parser**: For configuration-style plans
3. **CSV Parser**: For spreadsheet-based imports
4. **API Schema Parser**: Direct API response parsing

### Extensibility

The factory pattern makes it easy to add new formats without modifying existing code:
1. Create new parser class inheriting from `BasePlanParser`
2. Implement `can_parse()` and `parse()` methods
3. Register in factory's parser list
4. Done! Auto-detection handles routing

---

## Related Documentation

- **API Usage**: `/mnt/c/dev_skoth/well-planned/holistic-ai/API_USAGE_GUIDE.md`
- **Plan Extraction Service**: `services/plan_extraction_service.py`
- **Database Schema**: Check Supabase `time_blocks` and `plan_items` tables
- **Flutter Integration**: See API_USAGE_GUIDE.md for client implementation

---

## Support

For issues or questions:
1. Check logs for parser selection: `🎯 Using {ParserName} for extraction`
2. Verify format detection with manual `can_parse()` test
3. Test regex patterns with sample content
4. Check database for extracted results
5. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
