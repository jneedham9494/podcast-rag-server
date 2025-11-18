# Comprehensive Implementation Plan

> Actionable plan to modernize the Podcast Archive & Analysis System based on SpecKit retrofit analysis.

---

## Executive Summary

**Current State**: 8,610 lines of Python across 37 scripts with no tests, no version control, and several files 3-4x over size guidelines.

**Goal**: Transform into a maintainable, tested, secure codebase with proper CI/CD.

**Timeline**: 12 weeks (can be parallelized with multiple developers)

**Critical Files Requiring Refactoring**:
| File | Lines | Guideline | Over By |
|------|-------|-----------|---------|
| enrich_transcript.py | 1,132 | 300 | 3.8x |
| guest_and_twitter_extractor.py | 959 | 300 | 3.2x |
| monitor_progress.py | 868 | 300 | 2.9x |
| build_rag_index_v2.py | 444 | 300 | 1.5x |
| patreon_downloader.py | 388 | 300 | 1.3x |

---

## Phase 1: Foundation (Week 1-2)

### 1.1 Initialize Version Control

**Todo: Initialize git repository with proper configuration**

Acceptance Criteria:
- GIVEN project root directory
  WHEN `git status` is run
  THEN shows clean working directory with proper .gitignore

- GIVEN .gitignore file
  WHEN checking ignored patterns
  THEN excludes: episodes/, transcripts/, rag_db_v2/, logs/, __pycache__/, *.pyc, .env, patreon_cookies.txt

- GIVEN initial commit
  WHEN viewing git history
  THEN shows conventional commit message with all current files

Definition of Done:
- [ ] `.gitignore` created with all exclusions
- [ ] Initial commit with message: "chore: initial commit with existing codebase"
- [ ] `.gitattributes` for line ending consistency
- [ ] Branch protection rules documented

---

### 1.2 Set Up Testing Infrastructure

**Todo: Initialize pytest with basic configuration and first tests**

Acceptance Criteria:
- GIVEN test command `pytest`
  WHEN run from project root
  THEN discovers and runs all tests in tests/ directory

- GIVEN utility function sanitize_filename()
  WHEN tested with edge cases (empty, special chars, too long)
  THEN all tests pass

- GIVEN conftest.py
  WHEN tests need fixtures
  THEN provides mock RSS feed, mock audio file fixtures

Definition of Done:
- [ ] `pytest.ini` or `pyproject.toml` [tool.pytest] configured
- [ ] `tests/` directory structure created
- [ ] `tests/conftest.py` with common fixtures
- [ ] `tests/unit/test_utils.py` with 10+ tests for utility functions
- [ ] Coverage configuration (target: 80%)
- [ ] Test command documented in README

**Test Directory Structure**:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_utils.py        # sanitize_filename, parse_opml
│   ├── test_downloader.py   # download logic
│   └── test_transcriber.py  # transcription logic
├── integration/
│   ├── test_download_flow.py
│   └── test_rag_server.py
└── fixtures/
    ├── sample.opml
    ├── sample_rss.xml
    └── sample_audio.mp3     # 5-second test audio
```

---

### 1.3 Add Logging Framework

**Todo: Replace print() statements with structured logging using loguru**

Acceptance Criteria:
- GIVEN any script execution
  WHEN logging occurs
  THEN writes to both console and rotating log file

- GIVEN log message
  WHEN written
  THEN includes timestamp, level, module, function, line number

- GIVEN log file exceeding 10MB
  WHEN new logs written
  THEN rotates to new file, keeps 5 backups

Definition of Done:
- [ ] loguru added to requirements.txt
- [ ] `scripts/utils/logging_config.py` created
- [ ] All print() replaced with logger calls in core scripts
- [ ] Log levels used appropriately (DEBUG, INFO, WARNING, ERROR)
- [ ] Log rotation configured (10MB, 5 backups)

---

## Phase 2: Security Hardening (Week 3-4)

### 2.1 Secure RAG Server API

**Todo: Add API key authentication and rate limiting to RAG server**

Acceptance Criteria:
- GIVEN request without X-API-Key header
  WHEN hitting /search endpoint
  THEN returns 401 Unauthorized with message "API key required"

- GIVEN request with invalid API key
  WHEN hitting any protected endpoint
  THEN returns 403 Forbidden with message "Invalid API key"

- GIVEN valid API key exceeding 100 requests/minute
  WHEN making additional requests
  THEN returns 429 Too Many Requests

- GIVEN valid request
  WHEN processed
  THEN audit log contains: timestamp, API key (masked), endpoint, response time

Definition of Done:
- [ ] API keys stored in environment variable (comma-separated list)
- [ ] Middleware validates X-API-Key header
- [ ] Rate limiting per API key (100 req/min default)
- [ ] Audit logging for all API calls
- [ ] Health endpoint (/) remains unauthenticated
- [ ] Tests cover all auth scenarios

---

### 2.2 Restrict CORS

**Todo: Configure CORS with environment-based allowed origins**

Acceptance Criteria:
- GIVEN CORS_ORIGINS environment variable set
  WHEN request from listed origin
  THEN request succeeds

- GIVEN request from unlisted origin
  WHEN hitting API
  THEN returns CORS error

- GIVEN no CORS_ORIGINS set
  WHEN server starts
  THEN defaults to localhost:3000 only

Definition of Done:
- [ ] CORS origins read from environment variable
- [ ] Default to restrictive list for production
- [ ] Documented in README

---

### 2.3 Add Input Validation

**Todo: Implement comprehensive input validation across all scripts**

Acceptance Criteria:
- GIVEN podcast_downloader.py called with invalid podcast name
  WHEN name contains path traversal (../)
  THEN rejects with validation error

- GIVEN episode range "10:5" (invalid - start > end)
  WHEN parsing range
  THEN rejects with clear error message

- GIVEN file path outside project directory
  WHEN attempting to write
  THEN rejects with security error

Definition of Done:
- [ ] `scripts/utils/validators.py` created
- [ ] All CLI inputs validated
- [ ] Path traversal prevention
- [ ] Range validation (start < end, positive integers)
- [ ] Tests for all validation functions

---

## Phase 3: Refactoring (Week 5-8)

### 3.1 Refactor monitor_progress.py (868 lines → ~4 modules)

**Todo: Split monitor_progress.py into focused modules**

Target Structure:
```
scripts/monitor/
├── __init__.py
├── main.py              # Entry point, main loop (~100 lines)
├── dashboard.py         # Display rendering (~150 lines)
├── worker_manager.py    # Process launching/tracking (~200 lines)
├── feed_analyzer.py     # Feed status calculation (~150 lines)
└── lock_manager.py      # Lock file operations (~100 lines)
```

Acceptance Criteria:
- GIVEN refactored monitor
  WHEN running `python3 scripts/monitor/main.py`
  THEN behaves identically to original

- GIVEN each new module
  WHEN checking line count
  THEN all modules ≤200 lines

- GIVEN worker_manager.py
  WHEN launching workers
  THEN proper signal handling for graceful shutdown

Definition of Done:
- [ ] All modules under 200 lines
- [ ] No circular imports
- [ ] Original functionality preserved (diff output before/after)
- [ ] Unit tests for each module
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions

---

### 3.2 Refactor guest_and_twitter_extractor.py (959 lines → ~3 modules)

**Todo: Split guest extractor into focused modules and consolidate archived versions**

Target Structure:
```
scripts/extraction/
├── __init__.py
├── guest_extractor.py   # Guest name extraction (~250 lines)
├── twitter_finder.py    # Twitter handle extraction (~200 lines)
├── patterns.py          # Regex patterns library (~100 lines)
└── deduplicator.py      # Guest deduplication (~100 lines)
```

Acceptance Criteria:
- GIVEN refactored extractor
  WHEN running extraction
  THEN produces identical output to original

- GIVEN guest name with multiple spellings
  WHEN deduplicated
  THEN merges into single canonical entry

- GIVEN archived versions in scripts/archive/
  WHEN refactoring complete
  THEN archive versions documented and can be deleted

Definition of Done:
- [ ] All modules under 300 lines
- [ ] Regex patterns extracted to separate file with tests
- [ ] Deduplication logic implemented
- [ ] Archive versions reviewed and documented
- [ ] Unit tests for pattern matching
- [ ] Integration test comparing output to baseline

---

### 3.3 Refactor enrich_transcript.py (1,132 lines → ~4 modules)

**Todo: Split transcript enrichment into focused modules**

Target Structure:
```
scripts/enrichment/
├── __init__.py
├── main.py              # Entry point (~100 lines)
├── entity_extractor.py  # NER extraction (~300 lines)
├── summarizer.py        # Summary generation (~200 lines)
├── formatter.py         # Output formatting (~150 lines)
└── cache.py             # Result caching (~100 lines)
```

Acceptance Criteria:
- GIVEN refactored enrichment
  WHEN processing transcript
  THEN produces identical enriched output

- GIVEN each module
  WHEN checking line count
  THEN all modules ≤300 lines

Definition of Done:
- [ ] All modules under 300 lines
- [ ] Type hints throughout
- [ ] Unit tests for each component
- [ ] Documentation for enrichment pipeline

---

### 3.4 Add Type Hints Throughout

**Todo: Add complete type hints to all Python files**

Acceptance Criteria:
- GIVEN any Python file
  WHEN running mypy
  THEN passes with no errors

- GIVEN function signature
  WHEN inspecting
  THEN has parameter types and return type

Definition of Done:
- [ ] mypy configuration in pyproject.toml
- [ ] All functions have type hints
- [ ] Custom types defined in `scripts/types.py`
- [ ] mypy passes with strict mode

---

## Phase 4: Reliability (Week 9-10)

### 4.1 Implement Retry Logic

**Todo: Add exponential backoff retry for network operations**

Acceptance Criteria:
- GIVEN transient network error (connection reset, timeout)
  WHEN downloading episode
  THEN retries 3 times with exponential backoff (1s, 2s, 4s)

- GIVEN permanent error (404, 403)
  WHEN downloading
  THEN fails immediately without retry

- GIVEN retry attempt
  WHEN logging
  THEN logs attempt number and wait time

Definition of Done:
- [ ] `scripts/utils/retry.py` with decorator
- [ ] Retry logic in podcast_downloader.py
- [ ] Retry logic in patreon_downloader.py
- [ ] Configurable retry count and backoff
- [ ] Tests with mock network errors

---

### 4.2 Add Progress Persistence

**Todo: Implement SQLite-based progress tracking**

Acceptance Criteria:
- GIVEN download or transcription in progress
  WHEN process crashes
  THEN can resume from last checkpoint after restart

- GIVEN episode status
  WHEN queried
  THEN returns: pending, downloading, downloaded, transcribing, transcribed, failed

- GIVEN failed episode
  WHEN viewed
  THEN shows error message and timestamp

Definition of Done:
- [ ] SQLite database schema defined
- [ ] Progress tracking for downloads
- [ ] Progress tracking for transcriptions
- [ ] Resume logic on restart
- [ ] CLI to query progress status
- [ ] Migration from JSON state files

---

### 4.3 Graceful Shutdown

**Todo: Implement proper signal handling for graceful shutdown**

Acceptance Criteria:
- GIVEN monitor running with workers
  WHEN Ctrl+C pressed
  THEN sends SIGTERM to all child workers, waits for completion

- GIVEN worker in middle of transcription
  WHEN SIGTERM received
  THEN completes current file before exiting

- GIVEN 30-second timeout exceeded
  WHEN waiting for workers
  THEN force kills remaining processes

Definition of Done:
- [ ] Signal handlers for SIGINT, SIGTERM
- [ ] Worker shutdown coordination
- [ ] Timeout for forced termination
- [ ] Lock file cleanup on exit
- [ ] Tests for shutdown scenarios

---

## Phase 5: Infrastructure (Week 11-12)

### 5.1 Containerization

**Todo: Create Docker configuration for all services**

Acceptance Criteria:
- GIVEN Dockerfile
  WHEN building image
  THEN creates working container with all dependencies

- GIVEN docker-compose.yml
  WHEN running `docker-compose up`
  THEN starts RAG server with ChromaDB volume

- GIVEN container
  WHEN checking health
  THEN health check endpoint responds

Definition of Done:
- [ ] Dockerfile for RAG server
- [ ] Dockerfile for worker (downloader/transcriber)
- [ ] docker-compose.yml with all services
- [ ] Volume mounts for episodes/, transcripts/, rag_db_v2/
- [ ] Health checks configured
- [ ] Documentation for Docker usage

---

### 5.2 CI/CD Pipeline

**Todo: Set up GitHub Actions for automated testing and linting**

Acceptance Criteria:
- GIVEN pull request
  WHEN opened
  THEN runs: tests, mypy, ruff lint

- GIVEN failing tests
  WHEN PR checked
  THEN blocks merge

- GIVEN all checks pass
  WHEN PR merged
  THEN updates coverage badge

Definition of Done:
- [ ] `.github/workflows/ci.yml` created
- [ ] Test job runs pytest with coverage
- [ ] Lint job runs ruff
- [ ] Type check job runs mypy
- [ ] Coverage report uploaded
- [ ] Branch protection requires CI pass

**CI Configuration**:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov=scripts --cov-report=xml
      - run: mypy scripts/
      - run: ruff check scripts/
```

---

### 5.3 Development Dependencies

**Todo: Create requirements-dev.txt with development tools**

Contents:
```
pytest>=7.0
pytest-cov>=4.0
pytest-mock>=3.0
mypy>=1.0
ruff>=0.1
loguru>=0.7
httpx>=0.25  # For testing FastAPI
```

---

## Phase 6: Documentation & Cleanup (Ongoing)

### 6.1 Update README

**Todo: Update README with new project structure and commands**

Sections to add:
- Development setup (venv, requirements-dev.txt)
- Running tests
- Type checking
- Docker usage
- API authentication

---

### 6.2 Archive Cleanup

**Todo: Review and document archived files**

Current archives:
- `scripts/archive/` - 12 files
- `data/archive/` - 11 files
- `docs/archive/` - 25 files

Decision for each:
- Delete if superseded
- Keep with documentation if historical value

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Test Coverage | 0% | ≥80% | `pytest --cov` |
| Type Coverage | ~10% | ≥90% | `mypy --txt-report` |
| Max File Size | 1,132 lines | ≤300 lines | `wc -l` |
| Lint Errors | Unknown | 0 | `ruff check` |
| API Auth | None | 100% | Manual review |
| CI Pipeline | None | All green | GitHub Actions |

---

## Risk Mitigation

### Risk: Refactoring breaks existing functionality
**Mitigation**:
- Create baseline output files before refactoring
- Compare output after refactoring
- Add integration tests that verify end-to-end behavior

### Risk: Test suite slows development
**Mitigation**:
- Start with fast unit tests
- Integration tests only for critical paths
- Use pytest markers to separate fast/slow tests

### Risk: Type hints reveal existing bugs
**Mitigation**:
- Add type hints incrementally
- Use `# type: ignore` with explanation for known issues
- Fix bugs as discovered

---

## Dependencies Between Tasks

```
Phase 1 (Foundation)
├── 1.1 Git → All other tasks depend on this
├── 1.2 Testing → Required before refactoring
└── 1.3 Logging → Can be parallel

Phase 2 (Security)
├── 2.1 API Auth → Requires 1.2 (tests)
├── 2.2 CORS → Parallel with 2.1
└── 2.3 Validation → Parallel with 2.1

Phase 3 (Refactoring)
├── 3.1 Monitor → Requires 1.2 (tests)
├── 3.2 Guest Extractor → Requires 1.2 (tests)
├── 3.3 Enrichment → Requires 1.2 (tests)
└── 3.4 Type Hints → After 3.1-3.3

Phase 4 (Reliability)
├── 4.1 Retry → Requires 1.3 (logging)
├── 4.2 Progress → Requires 3.1 (refactored monitor)
└── 4.3 Shutdown → Requires 3.1 (refactored monitor)

Phase 5 (Infrastructure)
├── 5.1 Docker → Requires 1.2, 3.x
└── 5.2 CI/CD → Requires 1.1, 1.2
```

---

## Quick Wins (Can Do Immediately)

1. **Initialize git** - 10 minutes
2. **Create .gitignore** - 5 minutes
3. **Add requirements-dev.txt** - 5 minutes
4. **Set up pytest boilerplate** - 30 minutes
5. **Write first 5 utility tests** - 1 hour
6. **Add loguru to one script** - 30 minutes

---

## Resource Requirements

- **Developer time**: ~200-300 hours total
- **No additional infrastructure** for Phases 1-4
- **CI/CD**: GitHub Actions (free for public repos)
- **Docker**: Local only initially

---

## Review Checkpoints

- **End of Week 2**: Git initialized, 10+ tests passing, logging in 3 scripts
- **End of Week 4**: API secured, input validation complete
- **End of Week 8**: All large files refactored, 80% coverage
- **End of Week 10**: Retry logic, progress persistence working
- **End of Week 12**: Docker and CI/CD operational

---

## Next Steps

1. Start with Phase 1.1 (Initialize Git) - **This unblocks everything**
2. Parallel: Set up pytest (1.2) while creating .gitignore
3. Write first tests for `sanitize_filename()` and `parse_opml()`
4. Add loguru to `monitor_progress.py` as pilot
5. Continue with security (Phase 2) while tests grow
