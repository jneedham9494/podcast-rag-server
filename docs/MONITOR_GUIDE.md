# Smart Multi-Worker Allocation in Monitor

The monitor now intelligently launches **multiple transcription workers** on feeds with lots of remaining work!

## How It Works

### **Smart Allocation Rules:**

1. **Target**: 6 total transcription workers (adjustable via `TARGET_TRANSCRIBERS`)

2. **Multiple Workers Per Feed:**
   - Feeds with **50+ remaining episodes** can get multiple workers
   - Max workers per feed = `min(available_slots, remaining_episodes / 50)`
   - Example: RHLSTP with 301 episodes can get up to **6 workers** (301/50 = 6)

3. **Priority:**
   - Feeds sorted by **most remaining episodes first**
   - Then by download completion status
   - Then by book score

### **Example Scenario:**

**Current Status:**
- TRUE ANON: 5 episodes remaining
- RHLSTP: 301 episodes remaining
- Total worker slots: 6

**Monitor Will Launch:**
- TRUE ANON: **1 worker** (only 5 episodes, doesn't need multiple)
- RHLSTP: **5 workers** (301 episodes, can get 6 max, 5 slots remain)
- **Total: 6 workers**

Once TRUE ANON finishes, the monitor will:
- Launch **1 more worker on RHLSTP** (now 6 workers total on RHLSTP)

## Visual Indicators

The monitor will show worker counts:
```
RHLSTP with Richard Herring   8   301  [██░░░░] 685/986  69.5%    📝×5
```

The `📝×5` means **5 transcription workers** are running on this feed!

## Time Estimates with Smart Allocation

**RHLSTP (301 episodes remaining):**

| Workers | Auto-Launched By Monitor | Time to Complete |
|---------|--------------------------|------------------|
| 1 worker | When <50 remaining | 150 hours (6.3 days) |
| 3 workers | When 150+ remaining | 50 hours (2.1 days) |
| 5 workers | When 250+ remaining | 30 hours (1.3 days) |
| **6 workers** | **When 300+ remaining** | **25 hours (1.0 days)** ✅ |

## Monitor Behavior

### On Startup:
1. Counts existing workers (from previous runs)
2. Calculates remaining worker slots
3. Prioritizes feeds by remaining episodes
4. Launches workers to fill slots

### Every 10 Seconds:
1. Checks worker counts
2. If workers finish, launches new ones
3. Dynamically adjusts to workload

### When TRUE ANON Finishes:
- 1 worker becomes available
- Monitor sees RHLSTP still has 301 remaining
- Launches 1 more worker on RHLSTP
- Now 6 workers on RHLSTP!

## Configuration

Edit `scripts/monitor_progress.py`:

```python
TARGET_TRANSCRIBERS = 6  # Total workers (adjust for your system)
MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50  # Threshold for multiple workers
```

**System Recommendations:**
- **4-8 GB RAM**: 3-4 workers
- **8-16 GB RAM**: 5-6 workers
- **16+ GB RAM**: 8-10 workers

Each Whisper base model worker uses ~2-3 GB RAM during transcription.

## Benefits

✅ **Automatic load balancing** - no manual worker management
✅ **Fast completion** - multiple workers on big feeds
✅ **Resource efficient** - only 1 worker on small feeds
✅ **File locking** - no duplicate work
✅ **Zero configuration** - just start the monitor!

## How to Use

Just run the monitor as usual:
```bash
cd scripts
python3 monitor_progress.py
```

The monitor will automatically:
1. Detect RHLSTP has 301 episodes
2. Launch 5-6 workers on RHLSTP
3. Launch 1 worker on TRUE ANON
4. Coordinate all workers with file locking

**That's it!** Sit back and watch your transcriptions finish in ~1 day instead of 6! 🚀
