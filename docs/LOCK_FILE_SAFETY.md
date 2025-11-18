# Lock File Safety & Cleanup

## How Lock Files Work

When a worker transcribes a file, it creates a `.transcribing` lock file:
- **File**: `episode.mp3.transcribing`
- **Lock Type**: `fcntl.flock()` (advisory file lock)
- **Contents**: PID and timestamp

### Two-Level Locking:

1. **File System Lock** (`fcntl.flock`):
   - Automatically released when process dies
   - Even if process crashes or is killed
   - OS handles cleanup automatically

2. **Lock File** (`.transcribing`):
   - Used as a visual indicator
   - Contains process info
   - May be left behind if process crashes

## What Happens If Workers Crash?

### Scenario: Worker Dies Mid-Transcription

**Problem:**
- `.transcribing` file remains on disk
- Next worker sees the file and might skip the episode

**Solution: Automatic Stale Lock Detection**
The transcriber now automatically checks if locks are stale:

1. **Check if process still holds the lock:**
   - Tries to acquire the lock
   - If successful = original process died (stale)
   - If fails = process is still working (active)

2. **Check file age:**
   - Locks older than 4 hours are considered stale
   - Conservative (longest episodes ~2-3 hours max)
   - Automatically cleaned up

3. **Automatic cleanup:**
   - Stale locks are removed before transcription starts
   - No manual intervention needed!

## Manual Cleanup (If Needed)

### Check for Stale Locks

```bash
cd scripts
python3 cleanup_stale_locks.py
```

This will show:
- ✅ **Active locks**: Currently being transcribed
- ⚠️ **Stale locks**: Left behind by crashed workers

### Remove Stale Locks

```bash
python3 cleanup_stale_locks.py --delete
```

This safely removes only stale locks (not active ones).

## Example Output

```
================================================================================
STALE LOCK CLEANUP
================================================================================

Found 3 lock files
================================================================================

✅ ACTIVE LOCKS (1 files):
--------------------------------------------------------------------------------
  Episode 123 - Some Title.mp3
    Age: 0.3 hours
    Status: Being transcribed by active worker

⚠️  STALE LOCKS (2 files):
--------------------------------------------------------------------------------
  Episode 456 - Old File.mp3
    Age: 12.5 hours
    Status: Process died, lock is stale

  Episode 789 - Another File.mp3
    Age: 5.2 hours
    Status: Process died, lock is stale

💡 DRY RUN MODE - No files deleted
   Run with --delete to remove stale locks
```

## Safety Features

### 1. **Stale Lock Detection**
- Checks if process actually holds the lock
- Uses `fcntl.flock()` to test lock status
- Only removes locks not held by any process

### 2. **Age Check**
- Locks older than 4 hours = likely stale
- Conservative safety (longest episodes ~2-3 hours)
- Primary check is process lock status, age is backup

### 3. **Automatic Cleanup**
- Workers automatically detect and clean stale locks
- No manual intervention needed in normal operation

### 4. **Dry Run by Default**
- Manual cleanup script shows what would be deleted
- Must explicitly use `--delete` to remove files

## When to Manually Clean Locks

You only need manual cleanup if:
1. ❌ Monitor crashes hard (kill -9, power loss)
2. ❌ Multiple workers killed abruptly
3. ❌ You see transcriptions not progressing

Otherwise, the **automatic cleanup handles everything**.

## Monitor Crashes

If the monitor dies:
- ✅ Worker processes keep running (they're independent)
- ✅ Workers will complete their current transcriptions
- ✅ Lock files cleaned up automatically
- ✅ Just restart the monitor - it will detect existing workers

## Best Practices

### Before Killing Workers:
```bash
# Gentle shutdown (let them finish current file)
pkill podcast_transcriber.py

# Wait 30 seconds for graceful shutdown
sleep 30

# Force kill if needed (creates stale locks)
pkill -9 podcast_transcriber.py

# Clean up stale locks
python3 scripts/cleanup_stale_locks.py --delete
```

### After System Crash:
```bash
# Check for stale locks
python3 scripts/cleanup_stale_locks.py

# Remove stale locks if found
python3 scripts/cleanup_stale_locks.py --delete

# Restart monitor (will auto-detect work to do)
python3 scripts/monitor_progress.py
```

## Technical Details

**Lock File Contents:**
```
PID: 12345
Locked at 2025-11-14T18:30:00.123456
```

**Stale Detection Logic:**
1. Try to acquire `LOCK_EX | LOCK_NB` (non-blocking exclusive lock)
2. If successful: original process died, lock is stale
3. If fails: process still holds lock, keep it
4. Also check: if >24 hours old, definitely stale

**Why This Works:**
- `fcntl` locks are tied to process lifetime
- When process dies, OS automatically releases the lock
- We can test if lock is held without disrupting active workers

## Summary

✅ **Automatic stale lock cleanup** - no action needed normally
✅ **Manual cleanup available** - for edge cases
✅ **Safe by design** - won't remove active locks
✅ **Crash resistant** - workers keep going if monitor dies
✅ **Zero maintenance** - just works

Lock files won't cause nightmares! 🎉
