# Server Logging Guide

Complete guide for capturing and analyzing server logs during development and testing.

## Quick Start

### Option 1: Server with Console + File Logging (Recommended)
```bash
./start_openai_with_logs.sh
```
- ✅ See logs in terminal
- ✅ Logs saved to file
- ✅ Best for debugging

### Option 2: Server with File-Only Logging (Quiet)
```bash
./start_openai_quiet_logs.sh
```
- ✅ No console clutter
- ✅ All logs saved to file
- ✅ View with `tail -f logs/server_*.log`

### Option 3: 7-Day Test with Logging
```bash
./run_7day_test_with_logs.sh
```
- ✅ Captures test output
- ✅ Separate from server logs
- ✅ Timestamped for comparison

---

## Log Files Location

All logs are saved to the `logs/` directory with timestamps:

```
logs/
├── server_20251030_123456.log     # Server logs
├── server_20251030_145612.log     # Another server session
├── 7day_test_20251030_150000.log  # Test run logs
└── ...
```

**Filename Format**: `{type}_{YYYYMMDD}_{HHMMSS}.log`

---

## Viewing Logs in Real-Time

### While Server is Running:
```bash
# In another terminal, watch logs live:
tail -f logs/server_*.log

# Or specifically:
tail -f logs/server_20251030_123456.log
```

### Search Logs:
```bash
# Find all TaskPreseeder messages:
grep "PRESEED" logs/server_*.log

# Find friction-related logs:
grep -i "friction" logs/server_*.log

# Find errors only:
grep "ERROR\|❌" logs/server_*.log

# Find specific plan generation:
grep "9b2cd15c-3ceb" logs/server_*.log
```

---

## Complete Workflow with Logging

### 1. Start Server with Logging
```bash
# Terminal 1: Start server
./start_openai_with_logs.sh
```

### 2. Monitor Logs in Real-Time
```bash
# Terminal 2: Watch logs
tail -f logs/server_*.log | grep -E "PRESEED|FRICTION|ERROR"
```

### 3. Run 7-Day Test
```bash
# Terminal 3: Run test
./run_7day_test_with_logs.sh
```

### 4. Analyze Results
```bash
# Check what TaskPreseeder found:
grep "feedback_count" logs/server_*.log

# Check friction scores:
grep "friction_score" logs/server_*.log

# Check if simplification happened:
grep "SIMPLIFIED\|micro-habit" logs/server_*.log
```

---

## What Each Log Contains

### Server Logs (`server_*.log`)
- All API requests (HTTP)
- TaskPreseeder operations
- FeedbackService calculations
- AI prompt generation
- Database queries
- Errors and warnings
- Plan extraction details

**Key Lines to Look For**:
```
✅ [PRESEED] Selected X tasks from Y days of feedback  # SUCCESS
⚪ [PRESEED] Cold start - using pure AI (0 completed tasks)  # BUG

INFO:httpx:HTTP Request: HEAD .../task_checkins?profile_id=eq.a57f70b4...  # CORRECT
INFO:httpx:HTTP Request: HEAD .../task_checkins?profile_id=eq.None  # BUG (BEFORE FIX)
```

### Test Logs (`7day_test_*.log`)
- Day-by-day plan generation
- Check-in creation
- Friction analysis summaries
- Category evolution tables
- Final validation results

---

## Debugging with Logs

### Problem: TaskPreseeder finds 0 check-ins

**Search**:
```bash
grep "feedback_count=0" logs/server_*.log
```

**Look for**:
```
INFO:...task_preseeder:[PRESEED] User a57f70b4: feedback_count=0, threshold=3
```

**Then check database query**:
```bash
grep "task_checkins" logs/server_*.log | grep "profile_id"
```

**Should see**:
```
# CORRECT (after fix):
profile_id=eq.a57f70b4-d0a4-4aef-b721-a4b526f64869

# WRONG (before fix):
profile_id=eq.None
```

### Problem: Tasks not simplifying

**Search**:
```bash
grep -A5 "nutrition" logs/7day_test_*.log | grep "Day [567]"
```

**Look for changes in task titles Day 1 → Day 7**:
- Day 1: "Balanced Breakfast"
- Day 7: "Take photo of breakfast plate" ✅ (simplified)
- Day 7: "Balanced Breakfast" ❌ (not simplified)

### Problem: Categories excluded instead of simplified

**Search**:
```bash
grep "MISSING from Day 7" logs/7day_test_*.log
```

**Should see**:
```
✅ PASS: All high-friction categories present in Day 7
```

**Not**:
```
❌ FAIL: High-friction categories MISSING from Day 7: ['exercise', 'sleep']
```

---

## Log Analysis Scripts

### Extract Key Metrics from Server Log
```bash
# Count API calls
grep "HTTP Request" logs/server_20251030_123456.log | wc -l

# Count TaskPreseeder selections
grep "Selected.*tasks from" logs/server_*.log | wc -l

# Count errors
grep "ERROR\|❌" logs/server_*.log | wc -l

# Get all friction scores
grep "friction_score" logs/server_*.log | awk '{print $NF}'
```

### Compare Before/After Fix
```bash
# Before fix (should show profile_id=None):
grep "task_checkins" logs/server_20251030_120000.log | head -1

# After fix (should show actual user_id):
grep "task_checkins" logs/server_20251030_150000.log | head -1
```

---

## Advanced: Custom Logging Levels

If you want to change what gets logged, edit `start_openai.py`:

```python
# Current (ULTRA-QUIET mode):
os.environ["LOG_LEVEL"] = "ERROR"

# For verbose debugging:
os.environ["LOG_LEVEL"] = "DEBUG"

# For important info:
os.environ["LOG_LEVEL"] = "INFO"
```

Then restart server:
```bash
./start_openai_with_logs.sh
```

---

## Cleanup Old Logs

```bash
# Delete logs older than 7 days:
find logs/ -name "*.log" -mtime +7 -delete

# Archive logs:
tar -czf logs_archive_$(date +%Y%m%d).tar.gz logs/*.log
rm logs/*.log

# Keep only last 10 logs:
ls -t logs/*.log | tail -n +11 | xargs rm -f
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./start_openai_with_logs.sh` | Start server with console + file logging |
| `./start_openai_quiet_logs.sh` | Start server with file-only logging |
| `./run_7day_test_with_logs.sh` | Run test with logging |
| `tail -f logs/server_*.log` | Watch server logs live |
| `grep "ERROR" logs/*.log` | Find all errors |
| `grep "PRESEED" logs/server_*.log` | Find TaskPreseeder operations |
| `ls -lt logs/` | List logs by date (newest first) |

---

## Troubleshooting

### Logs directory not created
```bash
mkdir -p logs
```

### Permission denied
```bash
chmod +x *.sh
```

### Too much output
Use the quiet version:
```bash
./start_openai_quiet_logs.sh
```

Then view in another terminal:
```bash
tail -f logs/server_*.log
```

### Want to grep multiple patterns
```bash
tail -f logs/server_*.log | grep -E "PRESEED|friction|ERROR"
```

---

## Status: ✅ READY TO USE

All logging scripts are ready. Start with:
```bash
./start_openai_with_logs.sh
```
