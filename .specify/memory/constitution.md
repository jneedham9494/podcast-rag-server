# Project Constitution: Podcast Archive & Analysis System

> Project standards extracted from existing codebase patterns. These define the conventions used throughout the project.

---

## Project Overview

**Purpose**: Automated system for downloading, transcribing, and semantically searching podcast archives.

**Scale**: 37 feeds, 6,488 episodes, 6,592 transcripts

**Primary Language**: Python 3.9+

---

## File Organization

### Directory Structure
```
reading-list/
├── scripts/              # All Python scripts (37 files)
│   └── archive/          # Old/deprecated versions
├── docs/                 # Markdown documentation
│   └── archive/          # Archived docs
├── data/                 # Generated data files
│   └── archive/          # Archived data
├── episodes/             # Downloaded audio files
├── transcripts/          # Whisper transcriptions
├── podcast_metadata/     # RSS feed metadata (JSON)
├── rag_db_v2/            # ChromaDB vector database
└── logs/                 # Log files
```

### File Naming Conventions
- **Scripts**: `snake_case.py` (e.g., `podcast_downloader.py`, `rag_server.py`)
- **Documentation**: `SCREAMING_SNAKE_CASE.md` (e.g., `RAG_GUIDE.md`, `PATREON_AUTH.md`)
- **Data files**: `snake_case.json` (e.g., `download_state.json`)
- **Episodes**: Sanitized title with original extension (e.g., `Episode 123 - Topic.mp3`)
- **Archive folders**: Old versions go in `archive/` subdirectories

---

## Code Style

### Python Standards
- **Shebang**: `#!/usr/bin/env python3`
- **Module docstring**: Required at top of every file
- **Imports order**: Standard library → Third-party → Local
- **Path handling**: Use `pathlib.Path` (not `os.path`)
- **String formatting**: f-strings preferred
- **Entry point**: `if __name__ == "__main__": main()`

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Files**: `snake_case.py`

### Type Hints
- **Current state**: Inconsistently used
- **Future direction**: Use type hints for all new code
- **Pydantic**: Use for API request/response models (see `rag_server.py`)

### Configuration
- Define constants at top of file
- Use environment variables for secrets
- Example:
```python
# Configuration
TARGET_TRANSCRIBERS = 6
MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50
```

---

## Documentation Style

### Module Docstrings
```python
"""
Podcast Downloader
Downloads and organizes podcast episodes from OPML feed list
"""
```

### Function Docstrings
```python
def fetch_episodes(rss_url, limit=None, start_index=None, end_index=None):
    """Fetch and parse RSS feed to get episode information

    Args:
        rss_url: RSS feed URL
        limit: Maximum episodes to fetch (deprecated, use start/end instead)
        start_index: Starting episode index (0-based, inclusive)
        end_index: Ending episode index (0-based, exclusive)

    Returns:
        tuple: (episodes list, session object or None)
    """
```

### User Feedback
Use emoji indicators for visual feedback in CLI output:
- `✓` - Success
- `✗` - Failure
- `⚠️` - Warning
- Progress bars for long operations

---

## Error Handling

### Current Patterns
- **Try/except**: Use specific exception types
- **User messages**: Friendly, emoji-prefixed
- **Logging**: Print to stdout (no formal logging framework yet)
- **Cleanup**: Remove partial files on failure

### Example
```python
try:
    response.raise_for_status()
    # ... processing
except Exception as e:
    print(f"\n✗ Error downloading episode: {e}")
    if filename.exists():
        filename.unlink()  # Remove partial download
    return None
```

### Gaps to Address
- No formal logging framework
- No structured error types
- Limited input validation

---

## Testing

### Current State
- **No test suite exists** - This is a critical gap
- Manual testing only
- No CI/CD pipeline

### Future Direction
- Add pytest test suite
- Unit tests for utility functions
- Integration tests for download/transcription workflow
- Mock external services (RSS feeds, Patreon)

---

## External Dependencies

### Core Dependencies
- `feedparser` - RSS feed parsing
- `requests` - HTTP client
- `openai-whisper` - Audio transcription

### RAG/Search
- `sentence-transformers` - Embeddings
- `chromadb` - Vector database
- `fastapi` / `uvicorn` - API server

### Patreon Integration
- `playwright` - Browser automation

### Audio Processing
- `ffmpeg` - Audio conversion (system dependency)

---

## Multi-Worker Safety

### File Locking Pattern
- Use `.lock` or `.transcribing` files for coordination
- Check lock age to detect stale locks
- Scripts: `cleanup_stale_locks.py`

### State Persistence
- JSON files for state (e.g., `download_state.json`)
- Atomic writes when possible

---

## API Design (RAG Server)

### Current Pattern
- FastAPI with Pydantic models
- CORS enabled for local development
- Standard REST endpoints
- Global state for DB connections

### Endpoints
- `GET /` - Health check
- `GET /stats` - Collection statistics
- `POST /search` - Semantic search
- `GET /podcasts` - List all podcasts
- `GET /podcast/{name}` - Podcast details

---

## Known Technical Debt

1. **No tests** - Critical gap
2. **Inconsistent type hints** - Some files use them, others don't
3. **No formal logging** - Using print statements
4. **Large files** - Some scripts exceed 300 lines
5. **Duplicate code** - Guest extraction has multiple versions in archive
6. **No input validation** - Limited validation on user inputs
7. **Global state** - RAG server uses global variables
8. **Hardcoded paths** - Some scripts use hardcoded paths

---

## Commit Guidelines

Since this is not a git repository, no formal commit guidelines exist yet.

**When git is initialized:**
- Use conventional commits (feat, fix, refactor, docs, test)
- Reference issue numbers
- Include "why" in commit messages

---

## Future Improvements (Roadmap Items)

1. Initialize git repository
2. Add comprehensive test suite
3. Implement formal logging (e.g., `loguru`)
4. Add input validation throughout
5. Refactor large scripts into modules
6. Create proper Python package structure
7. Add CI/CD pipeline
8. Containerize with Docker
9. Add rate limiting to API
10. Implement proper secrets management
