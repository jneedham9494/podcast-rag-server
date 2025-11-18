#!/usr/bin/env python3
"""
Podcast Transcriber
Transcribes podcast audio files using OpenAI Whisper
"""

import os
import sys

# Add Homebrew paths to PATH for ffmpeg
homebrew_paths = [
    "/opt/homebrew/bin",
    "/usr/local/bin"
]
for path in homebrew_paths:
    if os.path.exists(path) and path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{path}:{os.environ['PATH']}"

import whisper
from pathlib import Path
import json
from datetime import datetime
import time
import fcntl


def is_lock_stale(lock_file, max_age_hours=4):
    """
    Check if a lock file is stale (older than max_age_hours)

    Default: 4 hours (longest episodes ~2-3 hours max)

    Returns:
        True if lock is stale and should be removed
    """
    if not lock_file.exists():
        return False

    try:
        # Try to acquire lock first to see if process still holds it
        # This is the primary check - if we can acquire it, the original process died
        try:
            test_handle = open(lock_file, 'r+')
            fcntl.flock(test_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # We got the lock! Original process is dead - this is stale
            fcntl.flock(test_handle.fileno(), fcntl.LOCK_UN)
            test_handle.close()
            return True  # Lock is stale (process died)
        except (IOError, OSError):
            # Lock is still held by another process
            # Check age as a backup - even if held, if >4 hours something is wrong
            mtime = lock_file.stat().st_mtime
            age_seconds = time.time() - mtime
            age_hours = age_seconds / 3600

            if age_hours > max_age_hours:
                print(f"  ⚠️  Warning: Lock held for {age_hours:.1f} hours (max {max_age_hours})")
                return True  # Suspiciously old, consider stale

            return False  # Active and not too old
    except Exception:
        return False

def acquire_file_lock(audio_file):
    """
    Try to acquire an exclusive lock for transcribing a file
    Cleans up stale locks automatically

    Returns:
        Lock file handle if successful, None if file is already locked
    """
    lock_file = Path(str(audio_file) + ".transcribing")

    # Check for stale lock and clean up
    if lock_file.exists():
        if is_lock_stale(lock_file):
            print(f"  ⚠️  Cleaning up stale lock file: {lock_file.name}")
            try:
                lock_file.unlink()
            except Exception as e:
                print(f"  ⚠️  Could not remove stale lock: {e}")

    try:
        # Try to create and lock the file
        lock_handle = open(lock_file, 'w')
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_handle.write(f"PID: {os.getpid()}\n")
        lock_handle.write(f"Locked at {datetime.now().isoformat()}\n")
        lock_handle.flush()
        return lock_handle
    except (IOError, OSError):
        # File is already locked by another process
        return None

def release_file_lock(lock_handle, audio_file):
    """Release the file lock"""
    try:
        if lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
            lock_handle.close()

        lock_file = Path(str(audio_file) + ".transcribing")
        if lock_file.exists():
            lock_file.unlink()
    except Exception as e:
        print(f"⚠️  Warning: Could not release lock: {e}")

def transcribe_audio(audio_file, model_size="base", output_dir="../transcripts"):
    """
    Transcribe an audio file using Whisper

    Args:
        audio_file: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        output_dir: Directory to save transcripts

    Returns:
        Path to transcript file or None if failed
    """
    audio_path = Path(audio_file)

    if not audio_path.exists():
        print(f"✗ Audio file not found: {audio_file}")
        return None

    # Try to acquire lock
    lock_handle = acquire_file_lock(audio_path)
    if not lock_handle:
        print(f"⏭️  Skipping (another worker is transcribing): {audio_path.name}")
        return "skipped"

    print(f"\nTranscribing: {audio_path.name}")
    print(f"Model: {model_size}")

    try:
        # Load Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model(model_size)

        # Transcribe
        print("Transcribing audio (this may take a while)...")
        result = model.transcribe(str(audio_path), verbose=True)

        # Create output directory structure matching episodes
        transcript_dir = Path(output_dir) / audio_path.parent.name
        transcript_dir.mkdir(parents=True, exist_ok=True)

        # Save full transcript
        transcript_file = transcript_dir / f"{audio_path.stem}.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])

        print(f"✓ Transcript saved: {transcript_file}")

        # Save detailed transcript with timestamps
        detailed_file = transcript_dir / f"{audio_path.stem}_detailed.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump({
                'text': result['text'],
                'segments': result['segments'],
                'language': result['language'],
                'audio_file': str(audio_path),
                'transcribed_at': datetime.now().isoformat(),
                'model': model_size
            }, f, indent=2, ensure_ascii=False)

        print(f"✓ Detailed transcript saved: {detailed_file}")

        # Try to load and save episode metadata if available
        metadata_file = audio_path.with_suffix('.json')
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            metadata['transcript_file'] = str(transcript_file)
            metadata['detailed_transcript_file'] = str(detailed_file)

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

        release_file_lock(lock_handle, audio_path)
        return transcript_file

    except Exception as e:
        print(f"✗ Error transcribing audio: {e}")
        release_file_lock(lock_handle, audio_path)
        return None


def transcribe_directory(directory, model_size="base", pattern="*.mp3"):
    """
    Transcribe all audio files in a directory

    Args:
        directory: Directory containing audio files
        model_size: Whisper model size
        pattern: File pattern to match (e.g., "*.mp3", "*.m4a")
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"✗ Directory not found: {directory}")
        return

    all_audio_files = list(dir_path.glob(pattern))

    # Filter out already-transcribed files
    transcript_dir = Path("../transcripts") / dir_path.name
    transcribed_names = set()
    if transcript_dir.exists():
        transcribed_names = {f.stem for f in transcript_dir.glob("*.txt")}

    audio_files = [f for f in all_audio_files if f.stem not in transcribed_names]

    if not audio_files:
        if transcribed_names:
            print(f"✓ All {len(all_audio_files)} audio files already transcribed in {directory}")
        else:
            print(f"✗ No audio files found matching '{pattern}' in {directory}")
        return

    print(f"Found {len(audio_files)} audio files to transcribe ({len(transcribed_names)} already done)")
    print("=" * 80)

    successful = []
    failed = []
    skipped = []

    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}]")
        result = transcribe_audio(audio_file, model_size)

        if result == "skipped":
            skipped.append(audio_file)
        elif result:
            successful.append(audio_file)
        else:
            failed.append(audio_file)

    print("\n" + "=" * 80)
    print(f"✓ Transcription complete!")
    print(f"  Successful: {len(successful)}")
    print(f"  Skipped (locked by another worker): {len(skipped)}")
    print(f"  Failed: {len(failed)}")
    if failed:
        print("\nFailed files:")
        for f in failed:
            print(f"  - {f.name}")
    print("=" * 80)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file: python podcast_transcriber.py <audio_file> [model_size]")
        print("  Directory:   python podcast_transcriber.py <directory> [model_size]")
        print("\nModel sizes: tiny, base, small, medium, large")
        print("  - tiny/base: Fast but less accurate")
        print("  - small/medium: Balanced (recommended)")
        print("  - large: Most accurate but slow")
        print("\nExamples:")
        print("  python podcast_transcriber.py episodes/The_Louis_Theroux_Podcast/episode.mp3")
        print("  python podcast_transcriber.py episodes/The_Louis_Theroux_Podcast/ base")
        return

    path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"

    path_obj = Path(path)

    if path_obj.is_file():
        transcribe_audio(path, model_size)
    elif path_obj.is_dir():
        transcribe_directory(path, model_size)
    else:
        print(f"✗ Path not found: {path}")


if __name__ == "__main__":
    main()
