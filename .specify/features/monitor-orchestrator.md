# Feature: Monitor/Orchestrator

## Status
Retroactive specification for existing feature

## Overview
The main orchestrator that provides a real-time dashboard and automatically manages podcast downloads and transcription workers.

## Current Behavior
- Displays real-time progress dashboard (updates every 10s)
- Automatically launches download workers for incomplete feeds
- Automatically launches transcription workers (up to 6 parallel)
- Smart worker allocation based on feed size
- File locking prevents duplicate work
- Shows completion percentages, book scores, worker counts

## Technical Implementation
- **Location**: [monitor_progress.py](scripts/monitor_progress.py)
- **Dependencies**: All other scripts (downloader, transcriber)
- **Dependents**: None (top-level entry point)
- **Size**: ~38KB (large file)

## Configuration
```python
TARGET_TRANSCRIBERS = 6  # Max parallel transcription workers
MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50  # Threshold for multiple workers
```

## Acceptance Criteria (Current State)

### Dashboard Display
- GIVEN monitor is started
  WHEN dashboard updates
  THEN shows all feeds with download %, transcription %, worker counts

### Worker Management
- GIVEN feeds with missing episodes
  WHEN monitor detects incomplete feeds
  THEN automatically launches download workers for those feeds

- GIVEN audio files without transcripts
  WHEN transcription workers < TARGET_TRANSCRIBERS
  THEN launches additional transcription workers

- GIVEN feed with >50 episodes needing transcription
  WHEN allocating workers
  THEN assigns multiple workers to that feed

### Process Coordination
- GIVEN multiple workers
  WHEN accessing same resource
  THEN file locking prevents duplicate work

- GIVEN stale lock files (>1 hour old)
  WHEN monitor runs
  THEN identifies and reports stale locks

### Error Handling
- GIVEN worker crashes
  WHEN monitor checks status
  THEN detects and reports missing worker

## Known Issues / Tech Debt

- [ ] **Large file** - 38KB exceeds 300-line guideline, needs refactoring
- [ ] **No tests** - Critical functionality has no test coverage
- [ ] **Global state** - Uses globals for tracking workers
- [ ] **No graceful shutdown** - Ctrl+C may leave orphan processes
- [ ] **Hardcoded timeouts** - Lock staleness threshold hardcoded

## Future Improvements

- [ ] Split into smaller modules (dashboard, worker_manager, lock_manager)
- [ ] Add pytest tests for worker allocation logic
- [ ] Implement proper signal handling for graceful shutdown
- [ ] Add configuration file support (YAML/TOML)
- [ ] Add metrics/observability (Prometheus export)
- [ ] Add alerting for stale locks or failed workers
