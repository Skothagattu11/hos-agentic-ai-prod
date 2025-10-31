# Remaining Implementation Phases - Hybrid System

## Current Status: Phase 3 Complete ✅

**Completed:**
- ✅ Phase 1: Foundation Setup (Database, Task Library, Basic Services)
- ✅ Phase 2: Dynamic Task Selector & Category Mapper
- ✅ Phase 3: Feature Switch Integration (API Endpoint Modified)

**What Works Now:**
- Feature switch controls hybrid vs AI-only flow
- Configuration loads with all new flags
- API endpoint has hybrid logic integrated
- Task replacement logic fully implemented
- 100% tests passing for integration

---

## Phase 4: Mode Support Implementation (1-2 days)

**Goal:** Add mode-specific filtering to task library for brain_power, travel, fasting, productivity, recovery modes.

### Tasks:

#### 4.1 Database Migration
- **File:** `supabase/migrations/007_add_mode_support.sql`
- **Changes:**
  - Add `preferred_mode` VARCHAR(50) column
  - Add `compatible_modes` TEXT[] column
  - Add `requires_equipment` BOOLEAN column
  - Add `intensity_level` VARCHAR(20) column (light, moderate, intense)
  - Add `energy_requirement` VARCHAR(20) column (low, moderate, high)
  - Create index on mode filtering columns

#### 4.2 Update Task Library Seed
- **File:** `services/seeding/task_library_seed.py`
- **Changes:**
  - Add mode metadata to all 50 tasks
  - Example: `{'preferred_mode': 'brain_power', 'compatible_modes': ['brain_power', 'productivity'], 'requires_equipment': False, 'intensity_level': 'light', 'energy_requirement': 'low'}`
  - Re-run seeding to update existing tasks

#### 4.3 Update Task Library Service
- **File:** `services/dynamic_personalization/task_library_service.py`
- **Method:** `get_tasks_for_category()`
- **Changes:**
  - Add mode parameter to query filters
  - Implement mode constraints:
    - `brain_power`: Avoid intense physical tasks
    - `travel`: Only portable tasks (requires_equipment=false)
    - `fasting`: Low energy requirements
    - `productivity`: Focus on work/wellness
    - `recovery`: Rest-focused categories

#### 4.4 Testing
- **File:** `testing/test_mode_filtering.py`
- **Tests:**
  - Test each mode returns appropriate tasks
  - Verify equipment filtering for travel mode
  - Verify intensity filtering for brain_power mode
  - Verify energy filtering for fasting mode

**Acceptance Criteria:**
- ✅ Migration applied successfully
- ✅ All 50 tasks have mode metadata
- ✅ Mode filtering works in task queries
- ✅ Travel mode only returns portable tasks
- ✅ Brain_power mode avoids intense workouts
- ✅ Tests pass for all 5 modes

**Estimated Time:** 1-2 days

---

## Phase 5: Shuffle Frequency & Plan Caching (1 day)

**Goal:** Implement AI plan caching and shuffle frequency logic to reduce AI costs.

### Tasks:

#### 5.1 Helper Functions in API Gateway
- **File:** `services/api_gateway/openai_main.py`
- **Functions to Add:**
  ```python
  async def _get_last_shuffle_date(user_id: str) -> Optional[str]
  async def _save_shuffle_date(user_id: str)
  async def _load_cached_ai_plan(user_id: str) -> Optional[Dict]
  async def _save_cached_ai_plan(user_id: str, plan: Dict)
  ```

#### 5.2 Update Routine Generation Logic
- **File:** `services/api_gateway/openai_main.py`
- **Method:** `generate_fresh_routine_plan()`
- **Changes:**
  - Check shuffle frequency before calling AI
  - Load cached plan if no shuffle needed
  - Save new AI plans to cache
  - Update last_shuffle_date after AI generation

#### 5.3 Testing
- **File:** `testing/test_shuffle_frequency.py`
- **Tests:**
  - First generation (no cache) → AI called
  - Second generation (within window) → Cache used
  - Third generation (outside window) → AI called, cache updated
  - Manual shuffle frequency → Never regenerates

**Acceptance Criteria:**
- ✅ Cached plans reused when within shuffle window
- ✅ AI only called when shuffle needed
- ✅ Cost reduction verified (fewer AI calls)
- ✅ Shuffle frequency configurable via .env

**Estimated Time:** 1 day

---

## Phase 6: End-to-End Testing (1-2 days)

**Goal:** Comprehensive multi-day user journey testing with real data.

### Tasks:

#### 6.1 Multi-Day Journey Test
- **File:** `testing/test_hybrid_system_journey.py`
- **Simulation:**
  - Day 1-7: Generate plans with hybrid system
  - Record task feedback (completions, ratings)
  - Verify preference evolution
  - Test learning phase transitions
  - Test mode switching (brain_power → productivity on day 4)
  - Verify shuffle frequency behavior

#### 6.2 Performance Testing
- **File:** `testing/test_hybrid_performance.py`
- **Tests:**
  - API latency < 2 seconds
  - Replacement rate > 70%
  - Memory usage acceptable
  - Concurrent user handling

#### 6.3 Integration with Flutter App
- **Manual Testing:**
  - Generate routine from Flutter app
  - Verify hybrid plan displays correctly
  - Test feedback submission
  - Verify plan caching behavior

**Acceptance Criteria:**
- ✅ 7-day journey completes successfully
- ✅ Task feedback recorded correctly
- ✅ Preferences evolve over time
- ✅ Learning phases transition
- ✅ Performance metrics within targets
- ✅ Flutter app integration works

**Estimated Time:** 1-2 days

---

## Phase 7: Gradual Rollout (1-2 weeks)

**Goal:** Safely deploy hybrid system to production users.

### 7.1 Alpha Testing (3-5 days)
- **Users:** 1 test user
- **Configuration:** `ENABLE_DYNAMIC_TASK_SELECTION=true`
- **Monitoring:**
  - Daily log review
  - Replacement rate tracking
  - Error rate monitoring
  - User feedback collection
- **Success Criteria:**
  - Zero crashes
  - Replacement rate > 70%
  - User satisfaction maintained

### 7.2 Beta Testing (1 week)
- **Users:** 10% of user base
- **Implementation:**
  - Add user-level feature flag
  - Percentage-based rollout (hash user_id % 100 < 10)
- **Monitoring:**
  - A/B comparison dashboard
  - Cost per plan tracking
  - Completion rate comparison
  - Skip reason analysis
- **Success Criteria:**
  - Completion rate ≥ AI baseline
  - 75% cost reduction confirmed
  - No quality degradation

### 7.3 Production Rollout (1 week)
- **Schedule:**
  - Day 1: 25% of users
  - Day 3: 50% of users
  - Day 5: 75% of users
  - Day 7: 100% of users
- **Monitoring:**
  - Real-time error tracking
  - API uptime monitoring
  - User support ticket volume
  - Database performance
- **Rollback Plan:**
  - Set `ENABLE_DYNAMIC_TASK_SELECTION=false`
  - Restart service (no deployment needed)

**Acceptance Criteria:**
- ✅ Alpha: No crashes, good user experience
- ✅ Beta: Metrics ≥ AI baseline
- ✅ Production: 100% rollout successful
- ✅ Cost savings confirmed
- ✅ User retention stable

**Estimated Time:** 1-2 weeks

---

## Phase 8: Post-Launch Optimization (Ongoing)

**Goal:** Continuously improve hybrid system based on real-world data.

### 8.1 Feedback Loop Refinement (Month 1)
- Analyze user feedback patterns
- Tune learning phase thresholds
- Adjust discovery → establishment criteria
- Optimize establishment → mastery transition

### 8.2 Task Library Expansion (Month 1-2)
- Add tasks based on skip reasons
- Target 100+ tasks by end of Month 2
- Fill coverage gaps (modes, archetypes, categories)
- Community-contributed tasks

### 8.3 Category Mapping Improvement (Month 2)
- Analyze unmapped AI tasks
- Add new patterns to CategoryMapper
- Increase replacement rate to 90%+
- Reduce "kept AI" task count

### 8.4 Circadian Analysis Fix (CRITICAL - Can do anytime)
- Fix broken circadian timing service
- Personalize time blocks based on sleep/wake
- Test with diverse user schedules
- Validate timing accuracy

### 8.5 AI Strategic Layer Optimization (Month 2-3)
- Analyze best-performing time block structures
- Update AI system prompts based on patterns
- Create mode-specific AI prompts
- Reduce shuffle frequency needs

### 8.6 Advanced Features (Month 3+)
- Weather-based task adaptation
- Calendar event integration
- Location-aware suggestions
- Social features (task recommendations from similar users)
- Multimodal input (images, voice)

**Acceptance Criteria:**
- ✅ Learning phases optimized
- ✅ 100+ tasks in library
- ✅ 90%+ replacement rate
- ✅ Circadian analysis working
- ✅ AI prompts improved

**Estimated Time:** Ongoing

---

## Optional/Future Phases

### Phase 9: Advanced Analytics Dashboard
- Replacement rate trends
- Cost savings visualization
- User engagement metrics
- Learning phase distribution
- Mode usage statistics

### Phase 10: AI Enhancement
- GPT-4 → GPT-4.5/GPT-5 migration
- Fine-tuned model for health plans
- Multi-agent coordination improvements
- Real-time adaptation during day

### Phase 11: Mobile App Enhancements
- In-app task library editor
- Custom task creation
- Plan preview before acceptance
- Real-time task swapping

---

## Summary Table

| Phase | Status | Estimated Time | Critical? |
|-------|--------|---------------|-----------|
| Phase 1: Foundation | ✅ Complete | - | Yes |
| Phase 2: Task Selector | ✅ Complete | - | Yes |
| Phase 3: Feature Switch | ✅ Complete | - | Yes |
| **Phase 4: Mode Support** | 🔜 Next | 1-2 days | **Recommended** |
| **Phase 5: Shuffle/Caching** | 🔜 Pending | 1 day | **Recommended** |
| **Phase 6: E2E Testing** | 🔜 Pending | 1-2 days | **Critical** |
| **Phase 7: Rollout** | 🔜 Pending | 1-2 weeks | **Critical** |
| Phase 8: Optimization | 🔜 Ongoing | Continuous | Optional |
| Phase 9: Analytics | 🔜 Future | 1 week | Optional |
| Phase 10: AI Enhancement | 🔜 Future | 2-3 weeks | Optional |
| Phase 11: Mobile Features | 🔜 Future | 2-3 weeks | Optional |

---

## Recommended Next Steps

### Option A: Complete Core Implementation (Recommended)
1. ✅ Phase 4: Mode Support (1-2 days)
2. ✅ Phase 5: Shuffle/Caching (1 day)
3. ✅ Phase 6: E2E Testing (1-2 days)
4. ✅ Phase 7: Gradual Rollout (1-2 weeks)

**Total Time:** ~2-3 weeks to production
**Result:** Fully functional hybrid system in production

### Option B: Skip to Testing (Faster)
1. ✅ Phase 6: E2E Testing (test current implementation)
2. ✅ Phase 7: Alpha Testing (1 user, 3-5 days)
3. 🔄 Iterate based on feedback

**Total Time:** ~1 week to alpha
**Result:** Quick validation, add features later

### Option C: Focus on Optimization
1. ✅ Phase 8.4: Fix Circadian Analysis (critical)
2. ✅ Phase 8.3: Improve Category Mapping
3. ✅ Phase 8.2: Expand Task Library
4. 🔄 Return to Phase 6/7 when ready

**Total Time:** Variable
**Result:** Higher quality before rollout

---

## Current System Capabilities

**What Works Now:**
- ✅ AI generates time block structure
- ✅ Dynamic selector can replace tasks (when enabled)
- ✅ Category mapping works (7/7 tests passing)
- ✅ Feature switch controls flow
- ✅ Configuration loads correctly
- ✅ Fallback to AI if library unavailable

**What Needs Work:**
- ⚠️ Mode filtering not yet implemented (Phase 4)
- ⚠️ Plan caching not yet implemented (Phase 5)
- ⚠️ Shuffle frequency partially implemented (needs helper functions)
- ⚠️ No end-to-end testing yet
- ⚠️ Not tested with real routine generation
- ⚠️ Circadian analysis broken (independent issue)

**Ready for Production?**
- 🔴 Not yet - needs Phase 4-7
- 🟡 Alpha-ready - can test with 1 user now
- 🟢 After Phase 6 - ready for beta testing

---

## Decision Point

**You should decide:**

1. **Continue building features?** → Start Phase 4 (Mode Support)
2. **Test what we have?** → Start Phase 6 (E2E Testing)
3. **Deploy to alpha user?** → Enable feature switch and monitor
4. **Focus on quality?** → Fix circadian, expand task library
5. **Something else?** → Tell me what you need

Let me know which path you want to take!
