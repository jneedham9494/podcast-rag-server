# Feature: Transcription

## Status
Retroactive specification for existing feature

## Overview
Transcribes podcast audio files to text using OpenAI Whisper, with multi-worker support and lock file coordination.

## Current Behavior
- Uses OpenAI Whisper for speech-to-text
- Supports multiple model sizes (tiny, base, small, medium, large)
- Creates lock files to coordinate multiple workers
- Outputs .txt transcript files alongside audio
- Default model: `base` (~2-3GB RAM per worker)

## Technical Implementation
- **Location**: [podcast_transcriber.py](scripts/podcast_transcriber.py) (~9KB)
- **Dependencies**: openai-whisper, ffmpeg (system)
- **Dependents**: monitor_progress.py
- **Output**: `transcripts/{podcast_name}/{episode}.txt`

## Configuration
```bash
python3 scripts/podcast_transcriber.py episodes/PodcastName/ base
# Models: tiny, base, small, medium, large
```

## Acceptance Criteria (Current State)

### Transcription
- GIVEN audio file without transcript
  WHEN transcriber runs
  THEN creates .txt file with same name in transcripts folder

- GIVEN Whisper model parameter
  WHEN transcribing
  THEN uses specified model (tiny/base/small/medium/large)

### Worker Coordination
- GIVEN multiple transcription workers
  WHEN same episode targeted
  THEN lock file prevents duplicate work

- GIVEN episode with .transcribing lock file
  WHEN another worker encounters it
  THEN skips that episode

- GIVEN stale lock file (>1 hour)
  WHEN detected
  THEN can be cleaned with cleanup_stale_locks.py

### Progress Tracking
- GIVEN directory of audio files
  WHEN transcriber runs
  THEN shows progress (X of Y files)

- GIVEN completed transcription
  WHEN file saved
  THEN shows success with timing info

### Error Handling
- GIVEN corrupted audio file
  WHEN Whisper fails
  THEN logs error and continues with next file

- GIVEN insufficient memory
  WHEN model loads
  THEN fails with memory error

## Known Issues / Tech Debt

- [ ] **No GPU detection** - Doesn't check for CUDA availability
- [ ] **Lock file race condition** - Small window for duplicate work
- [ ] **No queue system** - Each worker scans all files
- [ ] **No progress persistence** - Crashes lose progress info
- [ ] **Fixed output format** - Only outputs .txt, no SRT/VTT
- [ ] **No language detection** - Assumes English

## Future Improvements

- [ ] Add GPU detection and optimization
- [ ] Implement proper queue (Redis/RabbitMQ)
- [ ] Add output format options (SRT, VTT, JSON)
- [ ] Implement language detection
- [ ] Add progress persistence (SQLite/Redis)
- [ ] Add pytest tests with short audio samples
- [ ] Add diarization (speaker identification) integration
- [ ] Implement batch processing for small files
