# Podcast Archive & Analysis System

Automated system for downloading, transcribing, and semantically searching podcast archives. Currently managing **37 feeds**, **6,488 episodes**, and **6,592 transcripts**.

## Features

- 🎵 **Automated Download & Transcription** - Monitor orchestrates parallel workers
- 🔍 **Semantic Search** - RAG (Retrieval-Augmented Generation) server with vector embeddings
- 🎯 **Smart Worker Allocation** - Automatically scales workers based on workload
- 🔒 **Multi-Worker Safety** - File locking prevents duplicate work
- 📊 **Progress Monitoring** - Real-time dashboard of downloads and transcriptions
- 🔐 **Patreon Support** - Browser automation for premium content

## Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install feedparser requests openai-whisper

# For RAG server
pip install sentence-transformers chromadb flask numpy

# For Patreon (optional)
pip install playwright
~/Library/Python/3.9/bin/playwright install chromium

# ffmpeg (required for Whisper)
brew install ffmpeg  # macOS
```

### 2. Add Your Podcast Feeds

Edit `podocasts.opml` to add RSS feed URLs for podcasts you want to track.

### 3. Start the Monitor

```bash
cd scripts
python3 monitor_progress.py
```

**What the monitor does:**
- ✅ Downloads missing episodes from all feeds
- ✅ Transcribes downloaded audio (6 parallel workers by default)
- ✅ Tracks progress in real-time dashboard
- ✅ Automatically scales workers to feeds with most work
- ✅ Handles Patreon authentication automatically
- ✅ Safely coordinates multiple workers with file locking

The monitor handles everything - just start it and walk away!

### 4. Search Transcripts with RAG (Optional)

```bash
# Build the RAG index (one-time)
python3 scripts/build_rag_index_v2.py

# Start the RAG server
python3 scripts/rag_server.py

# Query from another terminal or code
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "book recommendations about psychology", "n_results": 10}'
```

The RAG server enables semantic search across all transcripts - find topics, quotes, recommendations, etc.

---

## Core Tools

### Monitor (Main Tool)

```bash
python3 scripts/monitor_progress.py
```

**Features:**
- Real-time progress dashboard (updates every 10s)
- Automatically launches download workers for incomplete feeds
- Automatically launches transcription workers (up to 6 parallel)
- Smart worker allocation (more workers on feeds with more episodes)
- File locking prevents duplicate work
- Shows completion percentages, book scores, worker counts

**Configuration:**
- `TARGET_TRANSCRIBERS = 6` - Max parallel transcription workers
- `MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50` - Threshold for multi-worker allocation

### Manual Tools

If you need to run components individually:

**Download episodes:**
```bash
python3 scripts/podcast_downloader.py "Podcast Name"
```

**Transcribe audio:**
```bash
python3 scripts/podcast_transcriber.py episodes/PodcastName/ base
```

**Models:** `tiny` (fast), `base` (default), `small`, `medium`, `large` (best quality)

**Clean stale locks** (if workers crash):
```bash
python3 scripts/cleanup_stale_locks.py
python3 scripts/cleanup_stale_locks.py --delete  # Actually remove them
```

---

## Patreon Authentication

For premium podcasts (e.g., Chapo Trap House, TrueAnon):

**Method 1: Browser Automation (Recommended)**

```bash
# One-time setup
pip3 install playwright
~/Library/Python/3.9/bin/playwright install chromium

# Log into Patreon in Chrome (once)
# Then the monitor handles authentication automatically!
```

**Method 2: Manual Cookies** (expires quickly)

See [docs/PATREON_AUTH.md](docs/PATREON_AUTH.md) for details.

---

## RAG Server

The RAG server enables semantic search across all transcripts using sentence transformers and vector embeddings.

**Build index:**
```bash
python3 scripts/build_rag_index_v2.py
```

**Start server:**
```bash
python3 scripts/rag_server.py
```

**Query from code:**
```python
import requests

response = requests.post('http://localhost:8000/search', json={
    'query': 'book recommendations about psychology',
    'n_results': 10
})

for result in response.json()['results']:
    print(f"Podcast: {result['metadata']['podcast_name']}")
    print(f"Text: {result['text']}")
    print(f"Similarity: {result['similarity']:.3f}")
```

See [docs/RAG_GUIDE.md](docs/RAG_GUIDE.md) for details.

---

## Directory Structure

```
reading-list/
├── README.md                    # This file
├── podocasts.opml              # Your podcast feed list
├── requirements.txt            # Python dependencies
│
├── docs/                       # 📚 Documentation
│   ├── MONITOR_GUIDE.md       # Monitor usage & configuration
│   ├── RAG_GUIDE.md           # RAG server setup
│   ├── AUDIO_TOOLS.md         # Audio analysis tools
│   ├── PATREON_AUTH.md        # Patreon authentication
│   ├── LOCK_FILE_SAFETY.md    # File locking details
│   └── MISSING_EPISODES.md    # Episode tracking status
│
├── scripts/                    # 🐍 All Python scripts
│   ├── monitor_progress.py    # ⭐ Main orchestrator
│   ├── podcast_downloader.py  # RSS feed downloader
│   ├── podcast_transcriber.py # Whisper transcription
│   ├── patreon_downloader.py  # Patreon downloads (cookies)
│   ├── patreon_browser_downloader.py  # Patreon (browser automation)
│   ├── build_rag_index_v2.py  # Build RAG index
│   ├── rag_server.py          # RAG query server
│   ├── cleanup_stale_locks.py # Lock file cleanup
│   └── ... (analysis tools)
│
├── data/                       # 💾 Generated data
│   ├── guest_directory_complete.json  # 2,058 guests
│   ├── podcast_book_analysis.json     # Book recommendations
│   └── download_state.json            # Download progress
│
├── podcast_metadata/           # 📋 RSS feed metadata (37 feeds)
├── episodes/                   # 🎵 Downloaded audio (6,488 episodes)
└── transcripts/                # 📝 Whisper transcriptions (6,592 transcripts)
```

---

## Documentation

- **[Getting Started](docs/MONITOR_GUIDE.md)** - Comprehensive monitor guide
- **[RAG Setup](docs/RAG_GUIDE.md)** - Semantic search with RAG
- **[Patreon Auth](docs/PATREON_AUTH.md)** - Premium podcast authentication
- **[Audio Tools](docs/AUDIO_TOOLS.md)** - Audio analysis features
- **[Lock File Safety](docs/LOCK_FILE_SAFETY.md)** - Multi-worker coordination
- **[Episode Tracking](docs/MISSING_EPISODES.md)** - Current status & adjustments

---

## System Stats

- **Feeds tracked:** 37 podcasts
- **Episodes downloaded:** 6,488 audio files
- **Transcripts generated:** 6,592 transcriptions
- **Transcription workers:** Up to 6 parallel (configurable)
- **Storage:** ~50MB per hour of audio + ~1MB transcript

---

## Configuration

**Monitor Settings** (in `monitor_progress.py`):

```python
TARGET_TRANSCRIBERS = 6  # Max parallel transcription workers
MIN_EPISODES_FOR_MULTIPLE_WORKERS = 50  # Threshold for multiple workers per feed
```

**Adjust based on your system:**
- 4-8 GB RAM: 3-4 workers
- 8-16 GB RAM: 5-6 workers
- 16+ GB RAM: 8-10 workers

Each Whisper `base` model worker uses ~2-3 GB RAM during transcription.

---

## Tips

1. **Start with the monitor** - It handles everything automatically
2. **Let it run** - Transcription takes time (6,488 episodes at ~30 mins each = weeks)
3. **Storage** - Plan for ~300GB for 6,000 episodes + transcripts
4. **Patreon** - Use browser automation method for reliability
5. **RAG server** - Build index after transcriptions complete for semantic search

---

## Troubleshooting

**Workers not starting:**
- Check `ps aux | grep podcast_transcriber.py` to see active workers
- Check for `.transcribing` lock files in episodes directories
- Run `python3 scripts/cleanup_stale_locks.py` if workers crashed

**Patreon downloads failing:**
- Make sure you're logged into Patreon in Chrome
- See [docs/PATREON_AUTH.md](docs/PATREON_AUTH.md) for authentication methods

**Transcription errors:**
- Ensure ffmpeg is installed: `brew install ffmpeg`
- Check audio file isn't corrupted
- Try smaller Whisper model: `base` instead of `large`

**Out of memory:**
- Reduce `TARGET_TRANSCRIBERS` in monitor_progress.py
- Use smaller Whisper model (`tiny` or `base`)

---

## License

Personal project for archiving and analyzing podcast content.
