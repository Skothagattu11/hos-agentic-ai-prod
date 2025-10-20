# MVP Enhancement Plan: Rich Archetype-Specific Health Plans

## Overview

This plan outlines how to enhance the existing HolisticOS routine generation system to provide rich, personalized, archetype-specific health plans with minimal structural changes to the current implementation.

## Current System Strengths

- ✅ Time blocks extraction with metadata
- ✅ Plan items with task classification
- ✅ Archetype integration (6 archetypes)
- ✅ Intensity mode logic (recovery/productive/performance)
- ✅ Biomarker-driven mode selection
- ✅ Existing extraction service with time block relationships

## MVP Strategy: 70-80% Impact with Minimal Changes

### Phase 1: Prompt Enhancement (Week 1) - Immediate Impact

#### A. Enhanced System Prompts
Add intensity markers and archetype-specific language to existing prompts:

```python
# Add to existing system prompts
ENHANCED_PROMPT_SUFFIX = """
When generating tasks, include intensity hints in descriptions:
- For easy activities: use words like "gentle", "light", "comfortable"
- For moderate activities: use words like "steady", "moderate", "consistent"
- For intense activities: use words like "vigorous", "challenging", "intense"

Also include archetype-specific motivational language:
- Peak Performer: "optimization", "metrics", "performance"
- Foundation Builder: "gentle", "nurturing", "supportive"
- Resilience Rebuilder: "safe", "restorative", "self-compassion"
- Transformation Seeker: "breakthrough", "revolutionary", "transformation"
- Systematic Improver: "progress", "methodical", "systematic"
- Connected Explorer: "meaningful", "community", "exploration"
"""
```

#### B. Enhanced Task Classification
Modify existing `_classify_task_type` method:

```python
def _classify_task_type(self, title: str, description: str) -> str:
    """Enhanced classification with intensity hints"""
    combined_text = f"{title} {description}".lower()

    # Intensity detection
    if any(word in combined_text for word in ['gentle', 'light', 'easy', 'comfort']):
        intensity = 'easy_'
    elif any(word in combined_text for word in ['vigorous', 'intense', 'challenging', 'peak']):
        intensity = 'high_'
    else:
        intensity = 'moderate_'

    # Activity classification (existing logic enhanced)
    if any(keyword in combined_text for keyword in ['exercise', 'workout', 'walk', 'movement']):
        return f'{intensity}exercise'
    elif any(keyword in combined_text for keyword in ['meditation', 'mindfulness', 'breath']):
        return f'{intensity}mindfulness'
    elif any(keyword in combined_text for keyword in ['hydration', 'water', 'nutrition']):
        return f'{intensity}nutrition'
    # Continue with existing patterns...
```

### Phase 2: Tag Integration (Week 2) - Medium Impact

#### A. Add Optional Metadata Columns
Extend existing tables without breaking current structure:

```sql
-- Add to existing plan_items table
ALTER TABLE plan_items ADD COLUMN intensity_hint TEXT;
ALTER TABLE plan_items ADD COLUMN archetype_language TEXT;
ALTER TABLE plan_items ADD COLUMN scaling_info TEXT;
ALTER TABLE plan_items ADD COLUMN user_guidance TEXT;

-- Add to existing time_blocks table
ALTER TABLE time_blocks ADD COLUMN energy_guidance TEXT;
ALTER TABLE time_blocks ADD COLUMN archetype_messaging TEXT;
ALTER TABLE time_blocks ADD COLUMN motivational_context TEXT;
```

#### B. Enhanced Extraction Logic
Add to existing `_store_plan_items_with_time_blocks` method:

```python
def _extract_enhancement_metadata(self, task: ExtractedTask, archetype: str, mode: str) -> dict:
    """Extract intensity and archetype info from task text"""
    task_text = f"{task.title} {task.description}"

    # Extract intensity hints
    intensity_hint = self._classify_intensity_from_text(task_text)

    # Generate archetype-specific language
    archetype_language = self._generate_archetype_markers(task_text, archetype)

    # Create scaling information
    scaling_info = self._generate_scaling_guidance(task, intensity_hint, archetype)

    # Generate user-friendly guidance
    user_guidance = self._create_user_guidance(task, archetype, mode, intensity_hint)

    return {
        "intensity_hint": intensity_hint,
        "archetype_language": archetype_language,
        "scaling_info": scaling_info,
        "user_guidance": user_guidance
    }

# Add to item_data in storage method:
item_data = {
    # ... existing fields ...
    **self._extract_enhancement_metadata(task, archetype, current_mode)
}
```

#### C. Archetype-Specific Communication Maps

```python
INTENSITY_COMMUNICATION = {
    "Peak Performer": {
        "easy": "Deload protocol - maintain form, RPE 3-4/10",
        "moderate": "Standard optimization - RPE 6-7/10",
        "high": "Peak output - RPE 8-9/10, full metrics"
    },
    "Foundation Builder": {
        "easy": "Light and easy does it - gentle progress",
        "moderate": "Confident building energy - trust your growing strength",
        "high": "Strong foundation power - you're capable of more than you know"
    },
    "Resilience Rebuilder": {
        "easy": "Extra gentle - whisper-level effort, self-compassion first",
        "moderate": "Steady confidence - natural pace, honor your body",
        "high": "Full capacity with self-compassion - strong and stable"
    },
    "Transformation Seeker": {
        "easy": "Strategic rest for breakthrough - champions recover intentionally",
        "moderate": "Progressive growth mode - building power for transformation",
        "high": "Revolutionary intensity - rewrite your story with every action"
    },
    "Systematic Improver": {
        "easy": "Gentle progression - methodical foundation building",
        "moderate": "Systematic advancement - steady, measurable progress",
        "high": "Optimized performance - precision meets intensity"
    },
    "Connected Explorer": {
        "easy": "Mindful exploration - gentle discovery at your own pace",
        "moderate": "Meaningful engagement - connecting with purpose",
        "high": "Passionate pursuit - full engagement with community spirit"
    }
}

ARCHETYPE_TIME_BLOCK_MESSAGING = {
    "Foundation Builder": {
        "morning": "Building momentum - feel the power of consistency",
        "midday": "Steady progress - small steps create big changes",
        "evening": "Gentle closure - preparing tomorrow's foundation"
    },
    "Peak Performer": {
        "morning": "Optimization window - prime time for peak performance",
        "midday": "Performance maintenance - sustaining excellence",
        "evening": "Recovery protocol - preparing for tomorrow's optimization"
    }
    # ... continue for all archetypes
}
```

### Phase 3: Presentation Layer (Week 3) - High User Impact

#### A. Frontend Transformation Functions

```python
def enhance_plan_for_presentation(plan_items: List[Dict], archetype: str, mode: str) -> List[Dict]:
    """Transform extracted plan items into user-friendly format"""
    enhanced_items = []

    for item in plan_items:
        # Add user-friendly intensity communication
        intensity = item.get('intensity_hint', 'moderate')
        item['user_friendly_intensity'] = INTENSITY_COMMUNICATION[archetype][intensity]

        # Add time block messaging
        if 'time_blocks' in item:
            block_type = classify_time_block_type(item['time_blocks']['block_title'])
            item['time_blocks']['archetype_messaging'] = ARCHETYPE_TIME_BLOCK_MESSAGING[archetype][block_type]

        # Generate scaling information
        item['scaling_info'] = generate_scaling_guidance(item, archetype, intensity)

        enhanced_items.append(item)

    return enhanced_items
```

#### B. API Response Enhancement
Modify existing API responses to include enhanced presentation:

```python
# In get_current_plan_items_for_user method:
if plan_items:
    # Apply presentation enhancement
    enhanced_items = enhance_plan_for_presentation(plan_items, archetype, current_mode)
    return {
        "routine_plan": plan_info["routine_plan"],
        "items": enhanced_items,
        "presentation_metadata": {
            "archetype": archetype,
            "mode": current_mode,
            "enhancement_version": "mvp_v1"
        }
    }
```

## Expected MVP Output

### Current Output:
```json
{
  "title": "Take a 10-min Brisk Walk",
  "description": "Short walk boosts step count and metabolism",
  "task_type": "exercise",
  "time_blocks": {
    "block_title": "Morning Wake-up",
    "time_range": "6:30-7:15 AM"
  }
}
```

### Enhanced MVP Output:
```json
{
  "title": "Take a 10-min Brisk Walk",
  "description": "Short walk boosts step count and metabolism",
  "task_type": "moderate_exercise",
  "intensity_hint": "moderate",
  "archetype_language": "steady_progress",
  "user_friendly_intensity": "Confident building energy - trust your growing strength",
  "scaling_info": "If low energy: 5-min gentle walk. If high energy: 15-min brisk walk",
  "user_guidance": "This moderate-intensity walk builds your foundation while honoring your current capacity",
  "time_blocks": {
    "block_title": "Morning Wake-up",
    "time_range": "6:30-7:15 AM",
    "archetype_messaging": "Building momentum - feel the power of consistency",
    "energy_guidance": "Use this time to gently awaken your body and set positive intention"
  }
}
```

## Implementation Timeline

### Week 1: Prompt Enhancement
- [ ] Update system prompts with intensity and archetype markers
- [ ] Enhance task classification logic
- [ ] Add archetype communication maps
- [ ] Test prompt changes with existing system

### Week 2: Database & Extraction Enhancement
- [ ] Add optional metadata columns to existing tables
- [ ] Implement enhancement metadata extraction
- [ ] Update storage methods to populate new fields
- [ ] Test extraction with enhanced metadata

### Week 3: Presentation Layer
- [ ] Create presentation transformation functions
- [ ] Implement archetype-specific messaging
- [ ] Update API responses with enhanced format
- [ ] End-to-end testing and refinement

## Technical Requirements

### Dependencies
- No new external dependencies required
- Uses existing OpenAI API integration
- Builds on current Supabase schema
- Compatible with existing extraction service

### Database Changes
- Only additive changes (new optional columns)
- No breaking changes to existing structure
- Maintains backward compatibility
- Optional metadata can be null

### Code Changes
- Enhance existing methods rather than rewrite
- Add new helper functions for metadata extraction
- Extend current API responses
- Maintain existing error handling patterns

## Success Metrics

### User Experience Improvements
- Clear intensity communication for all tasks
- Archetype-specific motivational language
- Practical scaling guidance for different energy levels
- Rich time block context and purpose

### Technical Achievements
- 70-80% improvement in user experience
- Zero breaking changes to existing system
- Maintains current performance characteristics
- Scalable foundation for future enhancements

## Risk Mitigation

### Low-Risk Approach
- All changes are additive, not destructive
- Maintains existing API contracts
- Graceful degradation if enhancements fail
- Rollback capability at each phase

### Testing Strategy
- Phase-by-phase validation
- A/B testing of enhanced vs current outputs
- User feedback integration
- Performance monitoring

## Future Roadmap (Post-MVP)

Once MVP is successful, consider:
1. Dynamic time block structures
2. Expanded habit repertoire
3. Real-time intensity adjustments
4. Progressive difficulty tracking
5. Rich educational content generation

This MVP approach delivers significant value while preserving system stability and minimizing implementation risk.