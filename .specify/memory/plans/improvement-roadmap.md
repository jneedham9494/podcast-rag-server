# Improvement Roadmap

> Prioritized list of improvements identified during SpecKit retrofit analysis.

---

## Priority 1: Critical / Security

### 1.1 Add Test Suite
**Impact**: High | **Effort**: Medium | **Risk of Not Doing**: Critical bugs in production

- [ ] Initialize pytest in project
- [ ] Add unit tests for utility functions (sanitize_filename, parse_opml)
- [ ] Add integration tests for download workflow
- [ ] Add mock fixtures for RSS feeds and Patreon
- [ ] Target: 80% coverage on core modules

**Acceptance Criteria**:
- GIVEN any code change
  WHEN tests run
  THEN all tests pass before merge

### 1.2 Restrict CORS on RAG Server
**Impact**: Medium | **Effort**: Low | **Risk**: Security vulnerability

- [ ] Replace `allow_origins=["*"]` with specific origins
- [ ] Add environment variable for allowed origins
- [ ] Document CORS configuration

**Acceptance Criteria**:
- GIVEN RAG server in production
  WHEN request from unknown origin
  THEN request is rejected

### 1.3 Add API Authentication
**Impact**: High | **Effort**: Medium | **Risk**: Unauthorized access

- [ ] Implement API key authentication
- [ ] Add rate limiting per key
- [ ] Add audit logging for API calls

**Acceptance Criteria**:
- GIVEN request without API key
  WHEN hitting protected endpoint
  THEN returns 401 Unauthorized

---

## Priority 2: Technical Debt

### 2.1 Refactor Large Files
**Impact**: Medium | **Effort**: High | **Risk**: Maintenance difficulty

Files exceeding guidelines:
- `monitor_progress.py` (38KB) → Split into modules
- `guest_and_twitter_extractor.py` (44KB) → Consolidate and refactor

**Approach**:
```
scripts/
├── monitor/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── worker_manager.py
│   └── lock_manager.py
├── extraction/
│   ├── __init__.py
│   ├── guest_extractor.py
│   └── twitter_finder.py
```

### 2.2 Initialize Git Repository
**Impact**: High | **Effort**: Low | **Risk**: No version control

- [ ] `git init`
- [ ] Create `.gitignore` (episodes/, transcripts/, rag_db_v2/, logs/, *.pyc)
- [ ] Initial commit with current state
- [ ] Set up conventional commit hooks

### 2.3 Add Formal Logging
**Impact**: Medium | **Effort**: Medium | **Risk**: Debugging difficulty

- [ ] Replace print() with structured logging
- [ ] Use loguru or standard logging module
- [ ] Add log rotation
- [ ] Add log levels (DEBUG, INFO, WARNING, ERROR)

**Acceptance Criteria**:
- GIVEN any script execution
  WHEN logging
  THEN logs to file with timestamp, level, and context

### 2.4 Add Input Validation
**Impact**: Medium | **Effort**: Medium | **Risk**: Runtime errors

- [ ] Validate podcast names before lookup
- [ ] Validate episode ranges (start < end, positive integers)
- [ ] Validate file paths exist
- [ ] Add pydantic models for CLI inputs

---

## Priority 3: Enhancements

### 3.1 Implement Retry Logic
**Impact**: Medium | **Effort**: Low | **Risk**: Failed downloads

- [ ] Add exponential backoff for downloads
- [ ] Configure max retries (default: 3)
- [ ] Log retry attempts

**Acceptance Criteria**:
- GIVEN transient network error
  WHEN downloading
  THEN retries 3 times with backoff before failing

### 3.2 Add Progress Persistence
**Impact**: Medium | **Effort**: Medium | **Risk**: Lost progress on crash

- [ ] Store progress in SQLite or JSON
- [ ] Resume from last checkpoint after crash
- [ ] Track per-episode status

### 3.3 Add Queue System for Transcription
**Impact**: High | **Effort**: High | **Risk**: Inefficient resource use

- [ ] Implement Redis/RabbitMQ queue
- [ ] Workers pull from queue instead of scanning
- [ ] Add dead letter queue for failures

### 3.4 Add Transcript Output Formats
**Impact**: Low | **Effort**: Low | **Risk**: Limited usability

- [ ] Add SRT output for subtitles
- [ ] Add VTT output for web
- [ ] Add JSON output with timestamps

---

## Priority 4: Documentation

### 4.1 Add Type Hints Throughout
**Impact**: Medium | **Effort**: Medium | **Risk**: IDE support limited

- [ ] Add type hints to all functions
- [ ] Run mypy in CI
- [ ] Document complex types

### 4.2 Add Architecture Documentation
**Impact**: Low | **Effort**: Low | **Risk**: Onboarding difficulty

- [ ] Create architecture diagram
- [ ] Document data flow
- [ ] Document worker coordination

### 4.3 Consolidate Archive Files
**Impact**: Low | **Effort**: Low | **Risk**: Confusion

- [ ] Review `scripts/archive/` - 12 files
- [ ] Review `data/archive/` - 11 files
- [ ] Delete or document archived versions

---

## Priority 5: Future Features

### 5.1 Containerization
**Impact**: Medium | **Effort**: Medium

- [ ] Create Dockerfile for each service
- [ ] Create docker-compose.yml
- [ ] Add health checks

### 5.2 CI/CD Pipeline
**Impact**: Medium | **Effort**: Medium

- [ ] GitHub Actions workflow
- [ ] Run tests on PR
- [ ] Lint with ruff
- [ ] Type check with mypy

### 5.3 Incremental RAG Index
**Impact**: High | **Effort**: High

- [ ] Detect new transcripts
- [ ] Add only new documents to index
- [ ] Track indexed documents in metadata

### 5.4 Speaker Diarization
**Impact**: Medium | **Effort**: High

- [ ] Integrate pyannote.audio or similar
- [ ] Identify speakers in transcripts
- [ ] Tag transcript segments with speaker

### 5.5 Web Dashboard
**Impact**: Medium | **Effort**: High

- [ ] React/Vue frontend for monitor
- [ ] Real-time updates via WebSocket
- [ ] Search interface for RAG

---

## Implementation Timeline (Suggested)

### Phase 1: Foundation (Week 1-2)
- Initialize git
- Add test suite
- Add logging framework

### Phase 2: Security (Week 3)
- Restrict CORS
- Add API authentication
- Add input validation

### Phase 3: Refactoring (Week 4-5)
- Refactor monitor_progress.py
- Refactor guest_extractor.py
- Add type hints

### Phase 4: Enhancements (Week 6-8)
- Add retry logic
- Add progress persistence
- Add output formats

### Phase 5: Infrastructure (Week 9-10)
- Containerization
- CI/CD pipeline
- Queue system

---

## Success Metrics

- **Test Coverage**: ≥80%
- **Type Coverage**: ≥90%
- **File Size**: All files <300 lines
- **API Uptime**: ≥99%
- **Download Success Rate**: ≥95%
- **Transcription Throughput**: X episodes/day

---

## Notes

This roadmap was generated by analyzing the existing codebase during SpecKit retrofit. Priorities should be adjusted based on:
- Active development needs
- User feedback
- Resource availability
- Business requirements
