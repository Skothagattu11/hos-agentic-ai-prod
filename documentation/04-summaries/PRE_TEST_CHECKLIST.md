# Pre-Test Checklist - Phase 4 Integration Test

## ✅ Before Running `python run_phase4_test.py`

### 1. Environment Variables
```bash
# Check .env file exists
ls -la .env

# Verify required variables are set
cat .env | grep OPENAI_API_KEY
cat .env | grep SUPABASE_URL
cat .env | grep DATABASE_URL
```

**Required:**
- [ ] `OPENAI_API_KEY` - OpenAI API key (starts with sk-)
- [ ] `SUPABASE_URL` - Supabase project URL
- [ ] `SUPABASE_KEY` - Supabase anon key
- [ ] `DATABASE_URL` - PostgreSQL connection string

---

### 2. Data File
```bash
# Check JSON file exists
ls -la holistic_analysis_results_rows.json
```

**Required:**
- [ ] `holistic_analysis_results_rows.json` exists in project root
- [ ] Contains circadian_analysis entry
- [ ] Contains behavior_analysis entry
- [ ] Has user_id: a57f70b4-d0a4-4aef-b721-a4b526f64869

---

### 3. Database Tables

**Check if tables exist:**
```sql
-- Run in Supabase SQL editor or psql

-- Check task_library
SELECT COUNT(*) FROM task_library;
-- Expected: At least 6 tasks

-- Check holistic_analysis_results
SELECT COUNT(*) FROM holistic_analysis_results LIMIT 1;
-- Expected: No error (table exists)

-- Check plan_items
SELECT COUNT(*) FROM plan_items LIMIT 1;
-- Expected: No error (table exists)

-- Check time_blocks
SELECT COUNT(*) FROM time_blocks LIMIT 1;
-- Expected: No error (table exists)
```

**Required:**
- [ ] `task_library` table exists with ≥6 tasks
- [ ] `holistic_analysis_results` table exists
- [ ] `plan_items` table exists with Option B columns:
  - `source` (TEXT)
  - `task_library_id` (UUID)
  - `category` (TEXT)
  - `subcategory` (TEXT)
  - `variation_group` (TEXT)
- [ ] `time_blocks` table exists

---

### 4. Database Connection Test
```bash
# Quick connection test
python testing/check_env.py
```

**Required:**
- [ ] Database connection successful
- [ ] OpenAI API key valid
- [ ] No connection errors

---

### 5. Task Library Data

**Verify task_library has Peak Performer tasks:**
```sql
SELECT id, name, category, archetype_fit
FROM task_library
WHERE archetype_fit ? 'Peak Performer'
LIMIT 10;
```

**If empty, populate with sample tasks:**
```sql
INSERT INTO task_library (
    name, category, subcategory, variation_group,
    duration_minutes, time_preference, description,
    archetype_fit, mode_fit
) VALUES
    ('Morning Hydration', 'hydration', 'water', 'hydration_basic', 5, 'morning', 'Drink 16oz water upon waking', '{"Peak Performer": 0.9}', '{"high": 0.8, "medium": 0.9, "low": 0.7}'),
    ('Protein-Rich Breakfast', 'nutrition', 'breakfast', 'nutrition_breakfast', 20, 'morning', 'High-protein breakfast', '{"Peak Performer": 0.95}', '{"high": 0.9, "medium": 0.8, "low": 0.7}'),
    ('Mid-Morning Movement', 'movement', 'stretch', 'movement_light', 15, 'any', 'Light stretching', '{"Peak Performer": 0.85}', '{"high": 0.9, "medium": 0.8, "low": 0.6}'),
    ('Afternoon Energy Boost', 'nutrition', 'snack', 'nutrition_snack', 10, 'afternoon', 'Healthy snack', '{"Peak Performer": 0.8}', '{"high": 0.7, "medium": 0.8, "low": 0.9}'),
    ('Evening Wind-Down', 'mindfulness', 'meditation', 'mindfulness_meditation', 10, 'evening', 'Evening meditation', '{"Peak Performer": 0.75}', '{"high": 0.6, "medium": 0.8, "low": 0.9}'),
    ('Sleep Hygiene Routine', 'sleep', 'preparation', 'sleep_hygiene', 15, 'evening', 'Pre-sleep routine', '{"Peak Performer": 0.9}', '{"high": 0.8, "medium": 0.9, "low": 0.95}');
```

**Required:**
- [ ] At least 6 tasks in task_library
- [ ] Tasks have archetype_fit containing "Peak Performer"
- [ ] Tasks have valid categories (hydration, nutrition, movement, etc.)

---

### 6. Plan Items Schema Verification

**Verify plan_items has Option B columns:**
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'plan_items'
AND column_name IN ('source', 'task_library_id', 'category', 'subcategory', 'variation_group');
```

**Expected Output:**
```
column_name       | data_type
------------------+-----------
source            | text
task_library_id   | uuid
category          | text
subcategory       | text
variation_group   | text
```

**If columns missing, add them:**
```sql
ALTER TABLE plan_items
ADD COLUMN IF NOT EXISTS source TEXT,
ADD COLUMN IF NOT EXISTS task_library_id UUID REFERENCES task_library(id),
ADD COLUMN IF NOT EXISTS category TEXT,
ADD COLUMN IF NOT EXISTS subcategory TEXT,
ADD COLUMN IF NOT EXISTS variation_group TEXT;
```

**Required:**
- [ ] All 5 Option B columns exist in plan_items table

---

### 7. Python Dependencies
```bash
# Check required packages
pip list | grep openai
pip list | grep asyncpg
pip list | grep supabase
```

**Required packages:**
- [ ] `openai` - OpenAI Python client
- [ ] `asyncpg` - PostgreSQL async driver
- [ ] `supabase` - Supabase Python client

**If missing:**
```bash
pip install -r requirements.txt
```

---

## 🚀 Ready to Run?

**If all checkboxes are checked, run:**
```bash
python run_phase4_test.py
```

**Or:**
```bash
python testing/test_phase4_routine_extraction_real.py
```

---

## 📊 What to Expect

### Test Duration
- **Estimated time**: 30-60 seconds
- **API calls**: 1 OpenAI call (routine planning)
- **Database writes**: ~15 rows (plan + items + time blocks)

### Cost Estimate
- **OpenAI tokens**: ~2,000-4,000 tokens
- **Estimated cost**: $0.01-0.03 USD

### Output
- **Console**: Detailed step-by-step progress
- **Database**: New rows in holistic_analysis_results, plan_items, time_blocks

---

## ❌ If Test Fails

### Check Logs
1. Read error message carefully
2. Check which step failed
3. Review prerequisites for that step

### Common Issues
1. **OpenAI API error**: Invalid key or quota exceeded
2. **Database error**: Connection issue or missing tables
3. **Task library empty**: No tasks to select from
4. **Column missing**: plan_items schema not updated

### Get Help
- Review `testing/PHASE4_TEST_README.md` for troubleshooting
- Check Supabase logs for database errors
- Verify `.env` file configuration

---

## ✅ After Successful Test

### Verify Database
```sql
-- Check plan was saved
SELECT id, analysis_type, archetype
FROM holistic_analysis_results
WHERE analysis_type = 'routine_planning'
ORDER BY created_at DESC
LIMIT 1;

-- Check plan items
SELECT task_title, source, task_library_id, category
FROM plan_items
WHERE analysis_result_id = '<id-from-above>'
ORDER BY source DESC;
```

### Expected Results
- 1 new row in holistic_analysis_results
- 10-15 new rows in plan_items (6+ library, 4-9 AI)
- Library tasks: source='library', task_library_id populated
- AI tasks: source='ai', task_library_id=null

---

**Ready? Let's test!** 🚀
