# Current State: Podcast Archive & Analysis System

> System-wide specification documenting the current architecture and behavior.

---

## System Overview

**Purpose**: Automated system for downloading, transcribing, and semantically searching podcast archives.

**Current Scale**:
- 37 podcast feeds tracked
- 6,488 episodes downloaded
- 6,592 transcripts generated
- 2,058 guests extracted
- ~50GB storage footprint

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│  ┌──────────────┐  ┌───────────┐  ┌─────────────────┐   │
│  │ CLI Scripts  │  │ Dashboard │  │ RAG API Server  │   │
│  └──────────────┘  └───────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  Core Services                           │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐   │
│  │ Downloader  │  │Transcriber │  │ Index Builder   │   │
│  │ (RSS/OPML)  │  │ (Whisper)  │  │ (ChromaDB)      │   │
│  └─────────────┘  └────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐   │
│  │ episodes/   │  │transcripts/│  │ rag_db_v2/      │   │
│  │ (Audio)     │  │ (Text)     │  │ (Vectors)       │   │
│  └─────────────┘  └────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Download Pipeline
1. User starts `monitor_progress.py`
2. Monitor reads `podocasts.opml` for feed list
3. Downloads episodes from RSS feeds
4. Saves audio to `episodes/{podcast_name}/`
5. Saves metadata to `podcast_metadata/`

### Transcription Pipeline
1. Monitor detects audio without transcript
2. Launches transcription worker
3. Worker claims episode with lock file
4. Whisper transcribes audio
5. Saves text to `transcripts/{podcast_name}/`

### Search Pipeline
1. User runs `build_rag_index_v2.py`
2. Builder reads all transcripts
3. Chunks and embeds text
4. Stores in ChromaDB at `rag_db_v2/`
5. User starts `rag_server.py`
6. Server accepts search queries via REST API

---

## Entry Points

| Script | Purpose | Usage |
|--------|---------|-------|
| `monitor_progress.py` | Main orchestrator | `python3 scripts/monitor_progress.py` |
| `podcast_downloader.py` | Manual download | `python3 scripts/podcast_downloader.py "Podcast"` |
| `podcast_transcriber.py` | Manual transcribe | `python3 scripts/podcast_transcriber.py episodes/Dir/ base` |
| `rag_server.py` | Search API | `python3 scripts/rag_server.py` |

---

## Key Files

### Configuration
- `podocasts.opml` - Podcast feed list
- `patreon_cookies.txt` - Patreon auth cookies
- `requirements.txt` - Python dependencies

### Data
- `data/download_state.json` - Download progress
- `data/guest_directory_complete.json` - Extracted guests
- `data/podcast_book_analysis.json` - Book recommendations

### Logs
- `logs/` - Script execution logs
- `.transcribing` files - Lock files for workers

---

## External Dependencies

### Python Packages
- `feedparser` - RSS parsing
- `requests` - HTTP client
- `openai-whisper` - Speech-to-text
- `sentence-transformers` - Embeddings
- `chromadb` - Vector database
- `fastapi` / `uvicorn` - API server
- `playwright` - Browser automation

### System Dependencies
- `ffmpeg` - Audio processing
- `chromium` - Browser for Playwright

---

## Current Limitations

1. **No version control** - Not a git repository
2. **No tests** - Manual testing only
3. **No CI/CD** - No automated pipeline
4. **Limited validation** - Inputs not thoroughly validated
5. **Print-based logging** - No structured logs
6. **No authentication** - RAG API is open
7. **No containerization** - Runs on bare metal

---

## Known Working State

As of specification date:
- All 37 feeds successfully download
- Transcription completes for all audio formats
- RAG search returns relevant results
- Monitor coordinates workers without conflicts
- Patreon authentication works with browser method

---

## Performance Characteristics

- **Download**: ~1 episode/second (limited by network)
- **Transcription**: ~30 min audio = ~5 min processing (base model)
- **Index build**: ~6,500 transcripts = ~30 min
- **Search latency**: <100ms per query
- **Memory per worker**: ~2-3GB (Whisper base model)

---

## Monitoring

Current monitoring is through CLI output:
- Monitor shows real-time dashboard
- Downloads show progress percentage
- Transcription shows file count progress

No external monitoring (Prometheus, etc.) is implemented.

---

## Disaster Recovery

### Backup Recommendations
- `podocasts.opml` - Feed configuration
- `data/*.json` - Extracted metadata
- `rag_db_v2/` - Search index
- `transcripts/` - Transcript text

### Recovery Steps
1. Restore OPML file
2. Re-run monitor to download missing episodes
3. Re-run transcriber for missing transcripts
4. Rebuild RAG index

Audio files can be re-downloaded; transcripts take significant time.

---

## Future State Vision

1. **Containerized** - Docker deployment
2. **Tested** - 80%+ coverage
3. **Typed** - Full type hints
4. **Monitored** - Prometheus metrics
5. **Authenticated** - API keys
6. **Queued** - Redis job queue
7. **Searchable** - Web UI for search
