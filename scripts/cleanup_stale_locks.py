#!/usr/bin/env python3
"""
Cleanup stale transcription lock files

Lock files (.transcribing) can be left behind if workers crash.
This script safely removes stale locks.
"""

from pathlib import Path
import time
import fcntl

def is_lock_active(lock_file):
    """
    Check if a lock file is actually held by a process

    Returns:
        True if lock is held, False if stale
    """
    try:
        # Try to acquire lock
        test_handle = open(lock_file, 'r+')
        fcntl.flock(test_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # We got the lock! Original process is dead
        fcntl.flock(test_handle.fileno(), fcntl.LOCK_UN)
        test_handle.close()
        return False  # Lock is stale (not held)
    except (IOError, OSError):
        # Lock is still held by another process
        return True
    except Exception:
        return False

def cleanup_stale_locks(episodes_dir, dry_run=True):
    """
    Find and clean up stale lock files

    Args:
        episodes_dir: Path to episodes directory
        dry_run: If True, only report stale locks without deleting
    """
    episodes_path = Path(episodes_dir)

    if not episodes_path.exists():
        print(f"❌ Directory not found: {episodes_dir}")
        return

    # Find all .transcribing files
    lock_files = list(episodes_path.glob('**/*.transcribing'))

    if not lock_files:
        print("✅ No lock files found")
        return

    print(f"Found {len(lock_files)} lock files")
    print("=" * 80)

    active_locks = []
    stale_locks = []

    for lock_file in lock_files:
        # Check file age
        mtime = lock_file.stat().st_mtime
        age_seconds = time.time() - mtime
        age_hours = age_seconds / 3600

        # Check if lock is held
        is_active = is_lock_active(lock_file)

        if is_active:
            active_locks.append((lock_file, age_hours))
        else:
            stale_locks.append((lock_file, age_hours))

    # Report active locks
    if active_locks:
        print(f"\n✅ ACTIVE LOCKS ({len(active_locks)} files):")
        print("-" * 80)
        for lock_file, age in active_locks:
            audio_file = lock_file.name.replace('.transcribing', '')
            print(f"  {audio_file[:60]}")
            print(f"    Age: {age:.1f} hours")
            print(f"    Status: Being transcribed by active worker")
            print()

    # Report stale locks
    if stale_locks:
        print(f"\n⚠️  STALE LOCKS ({len(stale_locks)} files):")
        print("-" * 80)
        for lock_file, age in stale_locks:
            audio_file = lock_file.name.replace('.transcribing', '')
            print(f"  {audio_file[:60]}")
            print(f"    Age: {age:.1f} hours")
            print(f"    Status: Process died, lock is stale")
            print()

        if not dry_run:
            print(f"\n🗑️  DELETING {len(stale_locks)} stale lock files...")
            deleted = 0
            for lock_file, age in stale_locks:
                try:
                    lock_file.unlink()
                    print(f"  ✓ Deleted: {lock_file.name}")
                    deleted += 1
                except Exception as e:
                    print(f"  ✗ Error deleting {lock_file.name}: {e}")

            print()
            print(f"✅ Deleted {deleted}/{len(stale_locks)} stale locks")
        else:
            print("\n💡 DRY RUN MODE - No files deleted")
            print("   Run with --delete to remove stale locks")

    if not stale_locks and not active_locks:
        print("✅ No lock files found")
    elif not stale_locks:
        print("\n✅ All locks are active (no cleanup needed)")

def main():
    import sys

    print("=" * 80)
    print("STALE LOCK CLEANUP")
    print("=" * 80)
    print()

    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--delete':
        dry_run = False
        print("⚠️  DELETE MODE: Stale locks will be removed")
    else:
        print("ℹ️  DRY RUN MODE: No files will be deleted")

    print()

    episodes_dir = Path(__file__).parent.parent / 'episodes'
    cleanup_stale_locks(episodes_dir, dry_run=dry_run)

    print()
    print("=" * 80)
    if dry_run:
        print("Run with --delete to remove stale locks:")
        print("  python3 cleanup_stale_locks.py --delete")

if __name__ == '__main__':
    main()
