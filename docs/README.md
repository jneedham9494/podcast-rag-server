# Documentation Index

Complete documentation for the Podcast Archive & Analysis System.

## Quick Start

- **[../README.md](../README.md)** - Main README with quick start guide

## Core Documentation

### Essential Guides

- **[MONITOR_GUIDE.md](MONITOR_GUIDE.md)** - Using the monitor (main orchestration tool)
  - Real-time progress dashboard
  - Automatic worker allocation
  - Configuration options
  - Worker coordination

- **[RAG_GUIDE.md](RAG_GUIDE.md)** - Semantic search with RAG server
  - Building the vector index
  - Starting the server
  - Querying transcripts
  - API reference

- **[PATREON_AUTH.md](PATREON_AUTH.md)** - Patreon authentication methods
  - Manual cookie extraction
  - Browser automation (recommended)
  - Troubleshooting

### Technical Reference

- **[LOCK_FILE_SAFETY.md](LOCK_FILE_SAFETY.md)** - Multi-worker file locking
  - How locks work
  - Stale lock detection
  - Crash recovery
  - Manual cleanup

- **[MISSING_EPISODES.md](MISSING_EPISODES.md)** - Episode tracking status
  - Current completion status
  - RSS adjustments explained
  - Known feed issues

- **[AUDIO_TOOLS.md](AUDIO_TOOLS.md)** - Audio analysis tools
  - Speaker diarization
  - Audio quality analysis
  - Processing utilities

## Archive

Historical documentation (for reference):

- **[archive/CLEANUP_COMPLETION_SUMMARY.md](archive/CLEANUP_COMPLETION_SUMMARY.md)** - Guest data cleanup report
- **[archive/FALSE_POSITIVE_CLEANUP_REPORT.md](archive/FALSE_POSITIVE_CLEANUP_REPORT.md)** - False positive analysis
- **[archive/OPTIMIZATION_LEARNINGS.md](archive/OPTIMIZATION_LEARNINGS.md)** - Pattern matching optimization insights
- **[archive/CLEANUP_PLAN.md](archive/CLEANUP_PLAN.md)** - Repository cleanup plan
- **[archive/ANALYSIS_TOOLS_REVIEW.md](archive/ANALYSIS_TOOLS_REVIEW.md)** - Analysis tools review (post-RAG)
- **[archive/ROOT_CLEANUP_PLAN.md](archive/ROOT_CLEANUP_PLAN.md)** - Root directory reorganization

---

## Document Organization

```
docs/
├── README.md                    # This index
│
├── MONITOR_GUIDE.md            # Main tool documentation
├── RAG_GUIDE.md                # Semantic search
├── PATREON_AUTH.md             # Authentication
├── AUDIO_TOOLS.md              # Audio analysis
├── LOCK_FILE_SAFETY.md         # File locking
├── MISSING_EPISODES.md         # Episode tracking
│
└── archive/                    # Historical documentation
    ├── CLEANUP_COMPLETION_SUMMARY.md
    ├── FALSE_POSITIVE_CLEANUP_REPORT.md
    ├── OPTIMIZATION_LEARNINGS.md
    ├── CLEANUP_PLAN.md
    ├── ANALYSIS_TOOLS_REVIEW.md
    └── ROOT_CLEANUP_PLAN.md
```

---

## Quick Links

### Getting Started
1. [Install dependencies](../README.md#1-install-dependencies)
2. [Add podcast feeds](../README.md#2-add-your-podcast-feeds)
3. [Start the monitor](../README.md#3-start-the-monitor)

### Common Tasks
- [Configure Patreon authentication](PATREON_AUTH.md)
- [Set up RAG for semantic search](RAG_GUIDE.md)
- [Adjust worker settings](MONITOR_GUIDE.md#configuration)
- [Clean up stale locks](LOCK_FILE_SAFETY.md#manual-cleanup-if-needed)

### Troubleshooting
- [Workers not starting](../README.md#troubleshooting)
- [Patreon downloads failing](PATREON_AUTH.md#troubleshooting)
- [Out of memory errors](../README.md#troubleshooting)
- [Stale lock files](LOCK_FILE_SAFETY.md#when-to-manually-clean-locks)

---

## Contributing to Documentation

When adding new documentation:
1. Place user-facing guides in `docs/`
2. Move historical/cleanup reports to `docs/archive/`
3. Update this index with new documents
4. Link to new docs from main README.md if relevant
