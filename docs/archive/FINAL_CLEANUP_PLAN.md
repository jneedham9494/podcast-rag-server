# Final Cleanup Plan - Remaining Clutter

## Issues Found

### 1. **RAG Database Mismatch** ⚠️ CRITICAL
- `build_rag_index_v2.py` creates `rag_db_v2/` (5.6GB) ← NEW
- `rag_server.py` uses `rag_db/` (1.6GB) ← OLD

**Problem:** Server is using old database!

**Fix:** Update `rag_server.py` to use `rag_db_v2`

### 2. **Old Backup Folder**
- `transcripts.old.backup/` (214MB)

**Action:** DELETE (old backup from earlier work)

### 3. **Hidden Clutter**
- `.archived_files/` (empty folder from cleanup)
- `.manual_download_progress.txt` (old progress tracker)

**Action:** DELETE both

### 4. **Old RAG Database**
- `rag_db/` (1.6GB old database)

**Action:** DELETE after fixing server to use rag_db_v2

### 5. **Temporary Reports**
- `PATH_VALIDATION_REPORT.md` (just created, can archive)

**Action:** Move to docs/archive/

---

## Cleanup Actions

### Step 1: Fix RAG Server (CRITICAL)
```bash
# Update rag_server.py to use rag_db_v2
sed -i.bak 's/db_path = Path("rag_db")/db_path = Path("rag_db_v2")/' scripts/rag_server.py
```

### Step 2: Delete Old Clutter
```bash
# Remove old backup
rm -rf transcripts.old.backup

# Remove hidden clutter
rm -rf .archived_files
rm .manual_download_progress.txt

# Remove old RAG database (AFTER fixing server!)
rm -rf rag_db
```

### Step 3: Archive Temp Reports
```bash
mv PATH_VALIDATION_REPORT.md docs/archive/
```

---

## Space Savings

| Item | Size | Action |
|------|------|--------|
| transcripts.old.backup | 214MB | DELETE |
| rag_db (old) | 1.6GB | DELETE |
| .archived_files | ~0MB | DELETE |
| .manual_download_progress.txt | ~1KB | DELETE |
| **Total savings** | **~1.8GB** | |

---

## After Cleanup

**Root directory will contain:**
```
reading-list/
├── README.md
├── podocasts.opml
├── patreon_cookies.txt
├── requirements.txt
├── book_recommendations_raw.json
│
├── docs/
├── data/
├── scripts/
├── podcast_metadata/
├── episodes/
├── transcripts/
├── logs/
└── rag_db_v2/        # ← Only this RAG DB!
```

Clean and professional! ✨
