# AI Context Generation Service - Integration Guide

## 🚀 **Overview**

The AI Context Generation Service replaces the complex 4-layer memory system with a simple, AI-powered approach that generates personalized context from real user engagement data.

## 📋 **Migration: Memory Service → AI Context Service**

### **Before (Memory Service):**
```python
from services.agents.memory.holistic_memory_service import HolisticMemoryService

# Complex memory system with 4 layers
memory_service = HolisticMemoryService()
context = await memory_service.get_working_memory(user_id)
enhanced_prompt = await memory_service.enhance_prompt_with_memory(base_prompt, user_id)
```

### **After (AI Context Service):**
```python
from services.ai_context_generation_service import AIContextGeneratorService

# Simple AI-powered context generation
context_service = AIContextGeneratorService()
context = await context_service.generate_user_context(user_id, archetype)
enhanced_prompt = await context_service.enhance_analysis_prompt(base_prompt, user_id, archetype)
```

---

## 🔧 **API Reference**

### **1. Initialize Service**

```python
from services.ai_context_generation_service import AIContextGeneratorService

# Initialize the service
context_service = AIContextGeneratorService()
```

**Environment Detection:**
- **Development**: Automatically uses Supabase REST API
- **Production**: Automatically uses database adapter
- **Based on**: `ENVIRONMENT` environment variable

---

### **2. Generate User Context**

**Method:** `generate_user_context(user_id, archetype=None, days=30)`

**Parameters:**
```python
user_id: str          # Required - User profile ID
archetype: str = None # Optional - User archetype for personalization
days: int = 30        # Optional - Number of days to analyze (default: 30)
```

**Usage Example:**
```python
# Generate context for systematic_improver archetype
context = await context_service.generate_user_context(
    user_id="35pDPUIfAoRl2Y700bFkxPKYjjf2",
    archetype="systematic_improver",
    days=30
)
```

**Response Format:**
```python
# Returns: str - AI-generated context summary
"""
### Context Summary for User ID: 35pDPUIf...

1. **Engagement Patterns**:
   - **Consistently Completed**: The user excels in productivity tasks,
     particularly "Focused Work Sessions," achieving high completion rates
     and satisfaction ratings (5/5).
   - **Struggles With**: The user has shown difficulty with tasks related
     to reflection and planning, often completing them partially.

2. **Timing Preferences**:
   - **Most Successful**: The user tends to perform best in the morning,
     particularly during the first half of the day.
   - **Afternoon Challenges**: There is a noted dip in energy and focus
     in the afternoon.

3. **Satisfaction Trends**:
   - **Highest Satisfaction**: Activities such as "Hydration and Light
     Stretching," "Evening Routine" yield the highest satisfaction ratings (5/5).

4. **Recent Changes**:
   - The user has recently adopted a more structured routine, which they
     report as being more aligned with their preferences.

5. **Optimization Opportunities**:
   - **Enhance Reflection Practices**: Given the user's struggle with
     reflection tasks, integrating shorter formats could improve completion.
   - **Afternoon Energy Management**: Implementing strategic breaks during
     afternoon could help mitigate energy dips.

6. **Avoid Patterns**:
   - **Skipped Tasks**: The user has consistently skipped "Focused Work
     Sessions" in the afternoon, indicating suboptimal timing.
   - **Complex Reflection Tasks**: Lengthy reflection tasks have not been
     effective; simplifying these could lead to better engagement.

### Actionable Insights:
- **Morning Focus**: Prioritize high-energy tasks in the morning
- **Reflection Simplification**: Streamline reflection tasks
- **Energy Management**: Introduce short breaks in the afternoon
"""
```

---

### **3. Enhance Analysis Prompts**

**Method:** `enhance_analysis_prompt(base_prompt, user_id, archetype=None)`

**Parameters:**
```python
base_prompt: str      # Required - Original analysis prompt
user_id: str          # Required - User profile ID
archetype: str = None # Optional - User archetype
```

**Usage Example:**
```python
# Original behavior analysis prompt
base_prompt = """
Analyze the user's health data and provide personalized behavior recommendations.
Focus on sustainable habits that align with their lifestyle and preferences.
"""

# Enhanced with user context
enhanced_prompt = await context_service.enhance_analysis_prompt(
    base_prompt=base_prompt,
    user_id="35pDPUIfAoRl2Y700bFkxPKYjjf2",
    archetype="systematic_improver"
)
```

**Response Format:**
```python
# Returns: str - Enhanced prompt with user personalization context
"""
Analyze the user's health data and provide personalized behavior recommendations.
Focus on sustainable habits that align with their lifestyle and preferences.

USER PERSONALIZATION CONTEXT:
### Context Summary for User ID: 35pDPUIf...

1. **Engagement Patterns**:
   - **Consistently Completed**: The user excels in productivity tasks...
   [Full context as shown above]

Use this context to personalize your analysis. Focus on:
- Building on what has worked for this user previously
- Avoiding patterns that have consistently failed
- Optimizing timing based on their successful patterns
- Adapting recommendations to their engagement style and preferences

Make your analysis specific to this user's proven patterns and preferences.
"""
```

---

### **4. Get Raw Engagement Data (Optional)**

**Method:** `engagement_service.get_raw_engagement_data(user_id, days=30)`

**Parameters:**
```python
user_id: str     # Required - User profile ID
days: int = 30   # Optional - Number of days to analyze
```

**Usage Example:**
```python
# Access raw data for custom analysis
raw_data = await context_service.engagement_service.get_raw_engagement_data(
    user_id="35pDPUIfAoRl2Y700bFkxPKYjjf2",
    days=30
)
```

**Response Format:**
```python
# Returns: Dict[str, Any]
{
    "calendar_selections": [
        {
            "title": "Morning Readiness Check-in",
            "task_type": "wellness",
            "time_block": "Morning Wake-up",
            "estimated_duration_minutes": 5,
            "selection_timestamp": "2025-09-29T06:00:00Z",
            "calendar_notes": "Added to morning routine"
        }
        # ... 31 items collected
    ],
    "task_checkins": [
        {
            "title": "Break and Reassessment",
            "task_type": "productivity",
            "time_block": "Focus Block",
            "completion_status": "completed",
            "satisfaction_rating": 5,
            "user_notes": "Very effective break",
            "planned_date": "2025-09-29",
            "completed_at": "2025-09-29T10:30:00Z"
        }
        # ... 20 items collected
    ],
    "daily_journals": [
        {
            "journal_date": "2025-09-29",
            "energy_level": 5,
            "mood_rating": 5,
            "sleep_quality": 3,
            "stress_level": 2,
            "nutrition_satisfaction": 4,
            "hydration_glasses": 12,
            "what_went_well": "New routine feels more personalized",
            "what_was_challenging": "Afternoon energy dip",
            "tomorrow_intentions": "Focus on morning productivity"
        }
        # ... 2 entries collected
    ],
    "recent_plan_items": [
        {
            "title": "Focused Work Session",
            "description": "High-priority tasks with deep focus",
            "task_type": "productivity",
            "time_block": "Focus Block",
            "estimated_duration_minutes": 90,
            "plan_date": "2025-09-29",
            "is_trackable": true
        }
        # ... 320 items collected
    ],
    "data_period": {
        "start_date": "2025-08-30T00:00:00Z",
        "end_date": "2025-09-29T00:00:00Z",
        "days_analyzed": 30
    }
}
```

---

### **5. Resource Cleanup**

**Method:** `cleanup()`

**Usage Example:**
```python
# Always cleanup after use
try:
    context = await context_service.generate_user_context(user_id, archetype)
    # Use context...
finally:
    await context_service.cleanup()
```

---

## 🔄 **Integration Examples**

### **Example 1: Behavior Analysis Integration**

```python
# OLD WAY - Memory Service
async def analyze_behavior_old(user_id: str, archetype: str):
    memory_service = HolisticMemoryService()
    base_prompt = "Analyze user behavior patterns..."
    enhanced_prompt = await memory_service.enhance_prompt_with_memory(base_prompt, user_id)
    # Complex memory operations...

# NEW WAY - AI Context Service
async def analyze_behavior_new(user_id: str, archetype: str):
    context_service = AIContextGeneratorService()
    try:
        base_prompt = "Analyze user behavior patterns..."
        enhanced_prompt = await context_service.enhance_analysis_prompt(
            base_prompt, user_id, archetype
        )

        # Use enhanced prompt with OpenAI
        response = await openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": enhanced_prompt}]
        )
        return response.choices[0].message.content
    finally:
        await context_service.cleanup()
```

### **Example 2: Circadian Analysis Integration**

```python
async def analyze_circadian_patterns(user_id: str, archetype: str):
    context_service = AIContextGeneratorService()
    try:
        base_prompt = """
        Analyze the user's circadian rhythm patterns and recommend optimal timing
        for sleep, meals, exercise, and cognitive tasks based on their chronotype.
        """

        enhanced_prompt = await context_service.enhance_analysis_prompt(
            base_prompt, user_id, archetype
        )

        # The enhanced prompt now includes:
        # - Morning productivity peaks
        # - Afternoon energy dips
        # - Evening routine preferences
        # - Timing-specific satisfaction data

        return await call_openai_analysis(enhanced_prompt)
    finally:
        await context_service.cleanup()
```

### **Example 3: Routine Generation Integration**

```python
async def generate_personalized_routine(user_id: str, archetype: str):
    context_service = AIContextGeneratorService()
    try:
        # Get user context for routine personalization
        user_context = await context_service.generate_user_context(
            user_id, archetype, days=30
        )

        routine_prompt = f"""
        Generate a personalized daily routine for a {archetype} user.

        USER CONTEXT:
        {user_context}

        Based on this context:
        - Schedule high-energy tasks during their proven peak times
        - Avoid task types they consistently struggle with
        - Include activities with highest satisfaction ratings
        - Account for their natural energy rhythms
        """

        return await call_openai_analysis(routine_prompt)
    finally:
        await context_service.cleanup()
```

---

## ⚡ **Performance Considerations**

### **Caching Strategy:**
- Context is automatically stored in `holistic_memory_analysis_context` table
- Subsequent calls within the same day may use cached context
- Manual cache invalidation available if needed

### **API Costs:**
- **Development**: Uses Supabase REST API (free tier friendly)
- **Production**: Uses database adapter (optimized queries)
- **OpenAI**: Single AI call vs multiple memory operations (cost reduction)

### **Error Handling:**
```python
async def safe_context_generation(user_id: str, archetype: str):
    context_service = AIContextGeneratorService()
    try:
        context = await context_service.generate_user_context(user_id, archetype)

        # Check if context generation failed
        if context.startswith("Failed to generate"):
            # Fallback to basic analysis without personalization
            return await basic_analysis_without_context(user_id, archetype)

        return context
    except Exception as e:
        logger.error(f"Context generation failed: {e}")
        # Graceful degradation
        return await basic_analysis_without_context(user_id, archetype)
    finally:
        await context_service.cleanup()
```

---

## 🎯 **Migration Checklist**

### **Step 1: Replace Memory Service Imports**
- [ ] Replace `HolisticMemoryService` imports with `AIContextGeneratorService`
- [ ] Update memory-related method calls

### **Step 2: Update Analysis Methods**
- [ ] Replace `memory.enhance_prompt_with_memory()` with `enhance_analysis_prompt()`
- [ ] Replace `memory.get_working_memory()` with `generate_user_context()`

### **Step 3: Test Integration**
- [ ] Verify context generation works with real user data
- [ ] Test enhanced prompts provide better personalization
- [ ] Confirm cleanup methods prevent resource leaks

### **Step 4: Deploy Database Migration**
- [ ] Run `create_holistic_memory_analysis_context_table.sql` in production
- [ ] Verify RLS policies work correctly

### **Step 5: Monitor Performance**
- [ ] Track context generation success rates
- [ ] Monitor AI analysis quality improvements
- [ ] Verify reduced complexity and maintenance overhead

---

## ✅ **Expected Benefits After Migration**

### **Technical Benefits:**
- **90% code reduction** - Simple AI calls vs complex memory layers
- **Better reliability** - Uses proven engagement APIs
- **Easier maintenance** - Single service vs multiple memory components
- **Cost optimization** - 1 AI call vs multiple memory operations

### **User Experience Benefits:**
- **Personalized insights** - Based on actual user behavior patterns
- **Actionable recommendations** - Specific timing and task guidance
- **Circadian optimization** - Real timing preferences identified
- **Behavior adaptation** - Builds on proven user successes

The AI Context Generation Service provides a modern, efficient replacement for the complex memory system while delivering significantly better user value through AI-powered personalization.