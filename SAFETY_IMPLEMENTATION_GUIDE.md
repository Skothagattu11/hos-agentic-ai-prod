# Safety Guardrails Implementation Guide

## 📋 Overview

This guide documents the implementation of **safety guardrails** for the HolisticOS routine generation system. The goal is to ensure AI-generated plans contain:
- ✅ **Generalized routines** (e.g., "have lunch", "morning meditation")
- ❌ **NO medical advice** (medications, supplements, dosages)
- ❌ **NO specific meal plans** (e.g., "eat grilled salmon with quinoa")

---

## 🎯 What Changed

### ✅ What We Allow (General Wellness)

| Category | Examples |
|----------|----------|
| **General Activities** | "Have lunch", "Eat dinner", "Morning meal" |
| **General Nutrition** | "Protein-rich meal", "Balanced meal", "Nutritious snack" |
| **General Guidance** | "Eat vegetables", "Include whole grains", "Stay hydrated" |
| **Wellness Practices** | "Morning meditation (10 min)", "Evening walk (30 min)" |

### ❌ What We Prohibit (Medical/Prescriptive)

| Category | Examples (Prohibited) |
|----------|----------------------|
| **Medications** | "Take aspirin", "Ibuprofen 400mg", "Prescription medication" |
| **Supplements** | "Vitamin D 2000 IU", "Omega-3 supplement", "Fish oil capsules" |
| **Dosages** | "500mg", "2 tablets", "1 cup of...", "6 oz salmon" |
| **Specific Foods** | "Grilled salmon", "Chicken breast", "Quinoa bowl with kale" |
| **Medical Referrals** | "Consult your doctor", "See a physician" |

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│  1. Safety Validator Service (services/safety_validator.py) │
│     - Pattern detection (medical terms, specific foods)     │
│     - Violation logging and tracking                        │
│     - Plan sanitization (fallback)                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. AI Prompt Integration (openai_main.py)                  │
│     - Safety guidelines injected into system prompt         │
│     - Instructs AI on allowed/prohibited content            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Post-Generation Validation (openai_main.py)             │
│     - Validates plan after AI generation                    │
│     - Logs violations for monitoring                        │
│     - Optional: Sanitizes plan (Phase 3)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 3-Phase Rollout Strategy

### **Phase 1: Integration (Non-Breaking) - ✅ COMPLETE**

**Goal**: Add safety system without affecting current behavior

**Status**: ✅ Implemented

**What Was Done**:
1. ✅ Created `SafetyValidator` service with pattern detection
2. ✅ Added safety guidelines to AI prompt
3. ✅ Integrated validation into routine generation
4. ✅ Added configuration flags (`.env`)
5. ✅ Created test suites

**Configuration** (`.env`):
```bash
SAFE_ROUTINE_MODE=true              # System enabled
VALIDATE_GENERATED_PLANS=true       # Validate all plans
BLOCK_UNSAFE_PLANS=false            # Don't block yet (monitor only)
LOG_SAFETY_VIOLATIONS=true          # Log for monitoring
```

**Behavior**: Plans are generated normally, violations are LOGGED but NOT blocked.

---

### **Phase 2: Monitoring (Current Phase) - 🔄 IN PROGRESS**

**Goal**: Monitor AI behavior and gather violation statistics

**Duration**: 1-2 weeks

**What to Do**:
1. **Start the server**:
   ```bash
   cd hos-agentic-ai-prod
   python start_openai.py
   ```

2. **Generate plans normally** (via API or Flutter app)

3. **Monitor logs** for `[SAFETY]` messages:
   ```bash
   # View safety logs
   grep "\[SAFETY\]" logs/server_*.log | tail -50

   # Count violations
   grep "\[SAFETY\].*violation" logs/server_*.log | wc -l

   # See violation types
   grep "\[SAFETY\].*medical_advice" logs/server_*.log | wc -l
   grep "\[SAFETY\].*specific_meal" logs/server_*.log | wc -l
   ```

4. **Run comprehensive tests** (multiple archetypes):
   ```bash
   # Test all archetypes (15 plans: 5 archetypes × 3 users × 1 iteration)
   python testing/test_safety_integration_endpoint.py

   # Test specific archetype only
   python testing/test_safety_integration_endpoint.py --archetype "Foundation Builder"

   # Quick test (single plan)
   python testing/test_safety_integration_endpoint.py --quick

   # Custom iteration count
   python testing/test_safety_integration_endpoint.py --iterations 5
   ```

5. **Review generated report**:
   ```bash
   # Report saved to: testing/safety_test_report.json
   cat testing/safety_test_report.json | python -m json.tool
   ```

**Expected Results**:
- **Target**: 95%+ plans should pass validation (0 violations)
- **Acceptable**: 5% plans may have minor violations (specific food mentions)
- **Concerning**: >10% plans with medical advice violations

**If Violations Are High**:
- Review AI prompt guidelines (too vague?)
- Add more prohibited patterns to `SafetyValidator`
- Adjust AI temperature (currently 0.2 for routine generation)

---

### **Phase 3: Enforcement (Future) - 📅 PLANNED**

**Goal**: Automatically sanitize or reject unsafe plans

**Trigger**: After Phase 2 shows <5% violation rate

**What to Do**:
1. **Update `.env`**:
   ```bash
   BLOCK_UNSAFE_PLANS=true  # Enable auto-sanitization
   ```

2. **Restart server**:
   ```bash
   python start_openai.py
   ```

3. **Test enforcement**:
   ```bash
   python testing/test_safety_integration_endpoint.py --quick
   ```

**Behavior**:
- Plans with violations are automatically sanitized
- Specific foods → Generic alternatives ("grilled salmon" → "protein-rich meal")
- Medical terms → Removed or generalized

---

## 🧪 Testing

### **Unit Tests** (Test validator logic)

```bash
cd hos-agentic-ai-prod
python3 testing/test_safety_validation.py
```

**Expected Output**:
```
🎉 All tests passed! Safety validator is working correctly.

Tests Passed: 5/5
  Unsafe Detection: ✅ PASS
  Safe Acceptance: ✅ PASS
  Sanitization: ✅ PASS
  Guidelines: ✅ PASS
  Configuration: ✅ PASS
```

---

### **Integration Tests** (Test actual endpoint)

**Start the server first**:
```bash
cd hos-agentic-ai-prod
python start_openai.py
```

**In another terminal, run tests**:

#### Quick Test (1 plan):
```bash
python testing/test_safety_integration_endpoint.py --quick
```

#### Full Test (45 plans: 5 archetypes × 3 users × 3 iterations):
```bash
python testing/test_safety_integration_endpoint.py
```

#### Test Specific Archetype:
```bash
python testing/test_safety_integration_endpoint.py --archetype "Peak Performer"
```

#### Test with Custom Iteration Count:
```bash
python testing/test_safety_integration_endpoint.py --iterations 10
```

**Expected Output**:
```
================================================================================
  SAFETY INTEGRATION TEST SUMMARY
================================================================================

Total Plans Generated: 45
Safe Plans: 43 (95.6%)
Unsafe Plans: 2 (4.4%)
Total Violations: 3
Average Violations per Plan: 0.07

✅ SUCCESS: Most plans passed safety validation!

Violations by Category:
  • specific_meal: 2 violations
  • medical_advice: 1 violation

📄 Detailed report saved to: testing/safety_test_report.json
```

---

## 📁 Files Modified/Created

### **New Files**:
- ✅ `services/safety_validator.py` - Core validation logic
- ✅ `testing/test_safety_validation.py` - Unit tests
- ✅ `testing/test_safety_integration_endpoint.py` - Integration tests
- ✅ `SAFETY_IMPLEMENTATION_GUIDE.md` - This document

### **Modified Files**:
- ✅ `services/api_gateway/openai_main.py` - Added safety integration
- ✅ `.env` - Added safety configuration
- ✅ `.env.example` - Documented safety configuration

---

## 🔧 Configuration Reference

### Environment Variables (`.env`)

```bash
# =============================================================================
# SAFETY VALIDATOR CONFIGURATION
# =============================================================================

# Enable/Disable Safety Guardrails
# Set to "true" to enable (RECOMMENDED)
SAFE_ROUTINE_MODE=true

# Validate Generated Plans
# Set to "true" to check all plans (RECOMMENDED)
VALIDATE_GENERATED_PLANS=true

# Block Unsafe Plans
# Phase 2: Set to "false" (monitor only)
# Phase 3: Set to "true" (enforce)
BLOCK_UNSAFE_PLANS=false

# Log Safety Violations
# Set to "true" to track violations (RECOMMENDED)
LOG_SAFETY_VIOLATIONS=true
```

### Disable Safety Checks (Not Recommended)

If you need to temporarily disable:
```bash
SAFE_ROUTINE_MODE=false           # Disables entire system
# OR
VALIDATE_GENERATED_PLANS=false    # Skips validation step
```

---

## 📊 Monitoring

### **View Safety Logs**

All violations are logged with `[SAFETY]` prefix:

```bash
# View recent safety logs
grep "\[SAFETY\]" logs/server_*.log | tail -50

# Count total violations today
grep "\[SAFETY\].*violation" logs/server_$(date +%Y%m%d)*.log | wc -l

# See violation details
grep "\[SAFETY\].*medical_advice" logs/server_*.log
grep "\[SAFETY\].*specific_meal" logs/server_*.log
```

### **Example Log Output**:

```
[SAFETY] [abc12345] Plan passed safety validation
[SAFETY] [def67890] Plan validation found 2 violation(s)
[SAFETY]   - specific_meal (medium): plan_items[3].title - Contains specific food item: 'grilled salmon'
[SAFETY]   - medical_advice (high): plan_items[5].description - Contains medical term: 'Vitamin D'
```

---

## 🛠️ Troubleshooting

### **Issue**: Plans still contain specific meals

**Diagnosis**: AI not following prompt guidelines

**Solution**:
1. Check `SAFE_ROUTINE_MODE=true` in `.env`
2. Restart server: `python start_openai.py`
3. Verify safety guidelines in logs (look for `[AI-PROMPT-DEBUG]` if enabled)
4. Add more patterns to `SafetyValidator.SPECIFIC_FOOD_PROHIBITED`

---

### **Issue**: Too many false positives (safe content flagged)

**Diagnosis**: Validator patterns too aggressive

**Solution**:
1. Review flagged content: `grep "\[SAFETY\].*violation" logs/server_*.log`
2. Adjust patterns in `services/safety_validator.py`
3. Add to `ALLOWED_GENERAL` patterns
4. Re-run tests: `python testing/test_safety_validation.py`

---

### **Issue**: Performance degradation

**Diagnosis**: Validation adds latency

**Solution**:
- Validation adds ~10-50ms per plan (negligible)
- If needed, disable in dev: `VALIDATE_GENERATED_PLANS=false`
- Keep enabled in production

---

## 📈 Success Metrics

### **Phase 2 Goals** (Monitoring):

| Metric | Target | Action If Not Met |
|--------|--------|-------------------|
| **Safe Plans** | >95% | Improve AI prompt guidelines |
| **Medical Advice Violations** | <2% | Add more prohibited patterns |
| **Specific Meal Violations** | <5% | Review task library |
| **False Positives** | <1% | Adjust validator patterns |

### **Phase 3 Goals** (Enforcement):

| Metric | Target | Action If Not Met |
|--------|--------|-------------------|
| **Safe Plans (Post-Sanitization)** | 100% | Improve sanitization logic |
| **User Complaints** | <1% | Review sanitized content quality |

---

## 🚀 Next Steps

### **Immediate (Do Now)**:
1. ✅ Configuration already added to `.env`
2. ✅ Tests created and passing
3. ✅ System integrated and ready

### **This Week (Phase 2)**:
1. **Start server**: `python start_openai.py`
2. **Run comprehensive tests**: `python testing/test_safety_integration_endpoint.py`
3. **Generate plans** normally via API or Flutter app
4. **Monitor logs** for `[SAFETY]` violations
5. **Review report**: `testing/safety_test_report.json`

### **Next 1-2 Weeks**:
1. **Collect statistics** on violation rates
2. **Review flagged content** - Is it truly unsafe?
3. **Adjust patterns** if false positives occur
4. **Share results** with team

### **After 2 Weeks (Phase 3)**:
1. If violation rate <5%: **Enable enforcement** (`BLOCK_UNSAFE_PLANS=true`)
2. **Test enforcement** with integration tests
3. **Monitor sanitized plans** for quality
4. **Remove old system** if new system proven stable

---

## 📞 Support

### **Questions?**
- Review this guide
- Check `services/safety_validator.py` code comments
- Run `python testing/test_safety_validation.py` to verify setup

### **Issues?**
- Check logs: `grep "\[SAFETY\]" logs/server_*.log`
- Run tests: `python testing/test_safety_integration_endpoint.py --quick`
- Review `.env` configuration

---

## 📝 Summary

This implementation provides:
1. ✅ **Non-breaking integration** - Current system still works
2. ✅ **Comprehensive validation** - Detects medical advice and specific meals
3. ✅ **Flexible configuration** - Easy to toggle features
4. ✅ **Monitoring capabilities** - Track violations over time
5. ✅ **Automatic enforcement** - Optional sanitization (Phase 3)
6. ✅ **Full testing suite** - Unit + integration tests

**Status**: Ready for Phase 2 (Monitoring) ✅

**Next Milestone**: After 1-2 weeks of monitoring → Phase 3 (Enforcement)

---

**Last Updated**: November 10, 2025
**Author**: HolisticOS Team
**Version**: 1.0
