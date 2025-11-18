# Feature: Podcast Downloading

## Status
Retroactive specification for existing feature

## Overview
Downloads and organizes podcast episodes from RSS feeds defined in OPML file.

## Current Behavior
- Parses OPML file to get list of podcast RSS feeds
- Fetches RSS feed and extracts episode information
- Downloads audio files with progress indicator
- Saves metadata JSON alongside each audio file
- Detects and re-downloads partial/corrupted files (<1MB)
- Supports Patreon feeds with authentication

## Technical Implementation
- **Location**: [podcast_downloader.py](scripts/podcast_downloader.py)
- **Dependencies**: feedparser, requests, pathlib
- **Dependents**: monitor_progress.py, patreon_downloader.py
- **Size**: ~300 lines (within guidelines)

## Acceptance Criteria (Current State)

### OPML Parsing
- GIVEN valid OPML file
  WHEN parsed
  THEN extracts all RSS feed URLs and titles

- GIVEN search term matching podcast name
  WHEN looking up feed
  THEN returns matching feed (case-insensitive partial match)

### Episode Fetching
- GIVEN valid RSS feed URL
  WHEN fetched
  THEN returns list of episodes with title, date, audio URL, description

- GIVEN range parameters (start:end)
  WHEN fetching
  THEN returns only episodes in that range

### Downloading
- GIVEN episode with audio URL
  WHEN downloading
  THEN shows progress percentage and MB downloaded

- GIVEN episode already downloaded (>1MB)
  WHEN downloading
  THEN skips with success message

- GIVEN partial download (<1MB)
  WHEN downloading
  THEN deletes and re-downloads

- GIVEN download failure
  WHEN error occurs
  THEN removes partial file and returns None

### Metadata
- GIVEN successful download
  WHEN completed
  THEN saves .json metadata file alongside audio

### Patreon Support
- GIVEN Patreon RSS feed URL
  WHEN fetching
  THEN uses authenticated session with proper headers

## Known Issues / Tech Debt

- [ ] **No input validation** - Doesn't validate episode_limit is positive integer
- [ ] **No retry logic** - Single failure causes episode to be skipped
- [ ] **No timeout configuration** - Hardcoded 60s timeout
- [ ] **No rate limiting** - Could overwhelm servers
- [ ] **Silent failures** - Some errors only printed, not propagated
- [ ] **No checksum validation** - Can't verify file integrity

## Future Improvements

- [ ] Add input validation for all parameters
- [ ] Implement retry with exponential backoff
- [ ] Add configurable timeout
- [ ] Implement rate limiting per domain
- [ ] Add checksum validation (if provided in RSS)
- [ ] Add pytest tests with mock RSS feeds
- [ ] Support resumable downloads for large files
