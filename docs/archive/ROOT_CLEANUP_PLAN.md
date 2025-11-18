# Root Directory Cleanup Plan

## Current Problems

### ❌ README.md is OUTDATED
- References **deleted scripts** (recommendation_extractor.py, download_monitor.py)
- Doesn't mention **monitor_progress.py** (the main tool!)
- No mention of **RAG server** (major feature!)
- Shows manual 3-step workflow (now automated)
- References old directory structure

### ❌ Too Many .md Files in Root (9 files!)
```
ANALYSIS_TOOLS_REVIEW.md       (3.4K) - Cleanup analysis
AUDIO_ANALYSIS_README.md       (8.1K) - Audio tools docs
CLEANUP_PLAN.md                (4.8K) - Cleanup plan
LOCK_FILE_SAFETY.md            (5.1K) - Lock file docs
MISSING_EPISODES.md            (2.5K) - Episode tracking
MONITOR_SMART_WORKERS.md       (3.3K) - Monitor docs
PATREON_BROWSER_METHOD.md      (2.6K) - Patreon auth
PATREON_COOKIE_GUIDE.md        (1.0K) - Patreon auth
RAG_SERVER_README.md           (7.4K) - RAG docs
```

### ❌ Temporary Files in Root
```
cleanup_repo.sh                (2.4K) - Cleanup script
missing_episodes.txt          (15K) - Old report
```

### ❌ Large Data File in Root
```
book_recommendations_raw.json  (2.3M) - Should be in data/
```

---

## Proposed Structure

```
reading-list/
├── README.md                    # ⭐ NEW: Comprehensive, up-to-date guide
│
├── docs/                        # 📚 All documentation
│   ├── GETTING_STARTED.md       # Quick start guide
│   ├── MONITOR_GUIDE.md         # Using monitor_progress.py
│   ├── RAG_GUIDE.md             # RAG server setup & usage
│   ├── AUDIO_TOOLS.md           # Audio analysis tools
│   ├── PATREON_AUTH.md          # Patreon authentication methods
│   ├── LOCK_FILE_SAFETY.md      # Lock file documentation
│   ├── MISSING_EPISODES.md      # Episode tracking
│   └── archive/                 # Historical cleanup reports
│       ├── CLEANUP_COMPLETION_SUMMARY.md
│       ├── FALSE_POSITIVE_CLEANUP_REPORT.md
│       └── OPTIMIZATION_LEARNINGS.md
│
├── data/                        # 💾 All data files
│   ├── book_recommendations_raw.json  # ← MOVE HERE
│   ├── guest_directory_complete.json
│   ├── podcast_book_analysis.json
│   └── download_state.json
│
├── scripts/                     # 🐍 All Python scripts
├── podcast_metadata/            # 📋 RSS metadata
├── episodes/                    # 🎵 Audio files
├── transcripts/                 # 📝 Transcriptions
│
├── podocasts.opml              # Feed list
├── patreon_cookies.txt         # Auth (gitignored)
└── requirements.txt            # Dependencies
```

---

## Actions to Take

### 1. **Update README.md**
Rewrite to reflect current system:
- ✅ Main tool: `monitor_progress.py` (automated orchestration)
- ✅ RAG server for semantic search
- ✅ Multi-worker transcription
- ✅ Patreon authentication methods
- ✅ Current directory structure
- ✅ Link to detailed docs in docs/

### 2. **Organize Documentation**
Move all .md files to `docs/` with better names:

```bash
# Create consolidated docs
MONITOR_GUIDE.md ← MONITOR_SMART_WORKERS.md + relevant sections
RAG_GUIDE.md ← RAG_SERVER_README.md
AUDIO_TOOLS.md ← AUDIO_ANALYSIS_README.md
PATREON_AUTH.md ← PATREON_COOKIE_GUIDE.md + PATREON_BROWSER_METHOD.md (merge!)

# Move to docs/
mv LOCK_FILE_SAFETY.md docs/
mv MISSING_EPISODES.md docs/

# Archive cleanup reports
mv CLEANUP_PLAN.md docs/archive/
mv ANALYSIS_TOOLS_REVIEW.md docs/archive/
```

### 3. **Clean Up Temp Files**
```bash
rm cleanup_repo.sh                # Already executed
rm missing_episodes.txt           # Old report (replaced by MISSING_EPISODES.md)
```

### 4. **Move Data Files**
```bash
mv book_recommendations_raw.json data/
```

### 5. **Create docs/README.md**
Index of all documentation with descriptions:
```markdown
# Documentation Index

## Getting Started
- [Getting Started Guide](GETTING_STARTED.md) - Quick start
- [Monitor Guide](MONITOR_GUIDE.md) - Main orchestration tool

## Advanced Features
- [RAG Guide](RAG_GUIDE.md) - Semantic search setup
- [Audio Tools](AUDIO_TOOLS.md) - Audio analysis features
- [Patreon Auth](PATREON_AUTH.md) - Patreon authentication

## Technical Reference
- [Lock File Safety](LOCK_FILE_SAFETY.md) - Multi-worker coordination
- [Missing Episodes](MISSING_EPISODES.md) - Episode tracking status
```

---

## Result

**Before:** 9 .md files in root, outdated README, scattered docs
**After:** Clean root, comprehensive README, organized docs/ folder

**Root directory:**
```
README.md           # ⭐ Modern, comprehensive guide
docs/               # 📚 All documentation organized
data/               # 💾 All data files
scripts/            # 🐍 All scripts
podocasts.opml      # Feed list
patreon_cookies.txt # Auth
requirements.txt    # Dependencies
```

Clean and professional! ✨
