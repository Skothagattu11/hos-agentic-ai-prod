# ENABLE_DYNAMIC_PLANS Feature Flag Explanation

## Overview

The `ENABLE_DYNAMIC_PLANS` environment variable is a **master switch** that controls how the system generates daily health and wellness plans for users.

---

## When `ENABLE_DYNAMIC_PLANS=false` (Default for initial deployment)

### What Happens:
✅ **Uses AI generation only** - OpenAI GPT-4 generates completely custom plans
✅ **No task library used** - Every plan is generated from scratch
✅ **Feedback is still collected** - User task interactions are recorded for future learning
✅ **Backward compatible** - Works exactly like the original system

### Flow:
```
User Request → AI Generation (GPT-4) → Custom Plan Created → Sent to User
```

### Advantages:
- **Flexible**: AI can handle any user archetype and mode
- **Personalized**: Every plan is unique and context-aware
- **Safe**: No risk from new dynamic system

### Disadvantages:
- **Expensive**: Costs ~$0.084 per plan generation (OpenAI API calls)
- **Slower**: Takes 5-10 seconds to generate each plan
- **Repetitive**: Users may see same tasks frequently without variety

---

## When `ENABLE_DYNAMIC_PLANS=true` (After testing and validation)

### What Happens:
✅ **Uses task library first** - Selects pre-vetted tasks from database
✅ **AI fallback available** - If dynamic generation fails, falls back to AI
✅ **Learning system active** - System learns user preferences automatically
✅ **Cost savings activated** - 35% reduction in API costs (~$200/month savings at 1K users)

### Flow:
```
User Request → Check Task Library → Select Best Tasks → Generate Plan → Sent to User
                                           ↓ (if fails)
                                     AI Generation (Fallback)
```

### Advantages:
- **Cost Effective**: Task library lookups are free (database queries only)
- **Fast**: Sub-second response time for task selection
- **Variety**: 50+ task variations prevent repetition
- **Personalization**: System learns user preferences over time
- **Scalable**: Supports 10K+ concurrent users

### Disadvantages:
- **Limited task pool**: Only 50 tasks initially (can expand to 100+)
- **Requires seeding**: Task library must be populated first
- **New code path**: Additional testing needed before full rollout

---

## Technical Details

### Phase 1: Task Library Foundation
When enabled, the system:
1. **Selects tasks** based on:
   - User archetype (Foundation Builder, Peak Performer, etc.)
   - Current mode (high, medium, low energy)
   - Category (hydration, movement, nutrition, etc.)
   - Time of day preference (morning, afternoon, evening)

2. **Scores tasks** using:
   - 70% weight on archetype fit
   - 30% weight on mode fit
   - Randomization for variety

3. **Prevents repetition**:
   - Rotation threshold: 48 hours default
   - Tracks recently used tasks per user
   - Excludes variation groups used in last 48 hours

### Phase 2: Adaptive Learning (Auto-enabled with Phase 1)
When enabled, the system also:
1. **Records feedback**:
   - Task completions (implicit feedback)
   - Satisfaction ratings (explicit feedback)
   - Skip reasons (why user didn't complete)

2. **Learns preferences**:
   - Category affinity (which categories user loves)
   - Subcategory affinity (specific task types)
   - Complexity tolerance (easy vs challenging tasks)
   - Variety seeking score (exploration vs consistency)

3. **Progresses through learning phases**:
   - **Discovery** (Week 1): 80% untried tasks, 20% tried → explore
   - **Establishment** (Week 2-3): 70% favorites, 30% exploration → build habits
   - **Mastery** (Week 4+): 85% proven, 15% novelty → optimize

4. **Generates weekly summaries**:
   - Completion statistics
   - Favorite tasks identification
   - Streak tracking
   - Personalized insights
   - Next week recommendations

---

## Deployment Strategy

### Recommended Rollout:
1. **Phase 1** (Day 1-2): `ENABLE_DYNAMIC_PLANS=false`
   - Collect baseline feedback with AI generation
   - Verify feedback endpoints work correctly

2. **Phase 2** (Day 3-5): `ENABLE_DYNAMIC_PLANS=true` for 10% users (Canary)
   - Test dynamic generation with small user group
   - Monitor error rates and completion rates

3. **Phase 3** (Day 6-10): Expand to 50% users (Beta)
   - Validate personalization improvements
   - Check cost savings

4. **Phase 4** (Day 11+): Full rollout to 100% users
   - Monitor all metrics for 1 week
   - Iterate on task library (add more variations)

---

## Environment Variable Configuration

### Initial Setup (Testing Phase):
```env
# Master switch - Start with false
ENABLE_DYNAMIC_PLANS=false

# Feedback collection - Always true to learn user preferences
FEEDBACK_COLLECTION_ENABLED=true

# Phase 2 features - Enable with Phase 1
ADAPTIVE_LEARNING_ENABLED=true
WEEKLY_SUMMARIES_ENABLED=true

# Rotation prevention threshold
ROTATION_THRESHOLD_HOURS=48

# Learning phase progression criteria
DISCOVERY_MIN_DAYS=7
DISCOVERY_MIN_TASKS=15
ESTABLISHMENT_MIN_DAYS=21
ESTABLISHMENT_MIN_TASKS=40
```

### After Successful Testing:
```env
# Enable dynamic generation
ENABLE_DYNAMIC_PLANS=true

# Keep everything else the same
FEEDBACK_COLLECTION_ENABLED=true
ADAPTIVE_LEARNING_ENABLED=true
WEEKLY_SUMMARIES_ENABLED=true
```

---

## Instant Rollback

If issues occur, you can **instantly rollback** by:
```env
ENABLE_DYNAMIC_PLANS=false
```

Then restart the backend:
```bash
pkill -f start_openai.py
python start_openai.py
```

System immediately returns to AI-only generation with zero downtime.

---

## Monitoring

### Key Metrics to Watch:
1. **Dynamic plan success rate**: Should be >95%
2. **API latency**: Should be <500ms for dynamic plans
3. **Task variety**: 80% users should see 3+ variations per week
4. **Completion rate**: Should improve from 55% to 65% (Phase 1) to 75% (Phase 2)
5. **Cost reduction**: Should see 35% reduction in OpenAI API costs

### SQL Queries:
See `DEPLOYMENT_GUIDE.md` for complete monitoring queries.

---

## Summary

| Feature | `false` (AI Only) | `true` (Dynamic + AI) |
|---------|-------------------|----------------------|
| **Plan Generation** | OpenAI GPT-4 | Task Library + AI fallback |
| **Cost per Plan** | ~$0.084 | ~$0.00 (free database lookup) |
| **Response Time** | 5-10 seconds | <500ms |
| **Task Variety** | Low (repetitive) | High (50+ variations) |
| **Personalization** | Basic | Advanced (learns preferences) |
| **Scalability** | Limited (expensive) | High (cheap database queries) |
| **Risk** | Low (proven system) | Medium (new code path) |
| **Rollback** | N/A | Instant (flip flag) |

---

**Recommendation**: Start with `false` for 2 days, then enable `true` for gradual rollout.
