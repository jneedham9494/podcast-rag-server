# Repository Cleanup Plan

## Files to DELETE (Safe to Remove)

### 1. **Forensic/Debugging Scripts** (One-off analysis, no longer needed)
- `scripts/forensic_episode_check.py` - Created during episode count debugging
- `scripts/find_rss_duplicates.py` - Found RSS duplicates (already documented)
- `scripts/find_archived_true_anon.py` - Found TRUE ANON +2 explanation (just created)
- `scripts/cleanup_joshua_citarella_duplicates.py` - Already executed successfully
- `scripts/analyze_missing_episodes.py` - Old debugging script
- `scripts/find_missing_episodes.py` - Replaced by monitor_progress.py

### 2. **Temporary JSON Reports** (Generated during debugging)
- `forensic_episode_report.json` - Debugging output
- `rss_duplicates_report.json` - Debugging output
- `missing_episodes_analysis.json` - Old analysis
- `missing_episodes.json` - Old analysis
- `validation_report_rss.json` - Old validation
- `validation_report.json` - Old validation
- `scripts/download_state.json` - Duplicate (main one in data/)

### 3. **Redundant Launch Scripts** (Replaced by monitor_progress.py)
- `scripts/launch_all_parallel.py` - Old manual launcher
- `scripts/launch_all_transcribers.py` - Old manual launcher
- `scripts/launch_parallel_workers.py` - Old manual launcher
- `scripts/launch_priority_workers.py` - Old manual launcher
- `scripts/launch_smart_parallel.py` - Old manual launcher
- `scripts/launch_transcription_parallel.py` - Old manual launcher

### 4. **Redundant Validation Scripts** (monitor_progress.py does this now)
- `scripts/validate_all_feeds.py` - Old validation
- `scripts/validate_comprehensive.py` - Old validation
- `scripts/validate_feeds_with_rss.py` - Old validation
- `scripts/validate_transcriptions.py` - Old validation

### 5. **Redundant Download Scripts** (Replaced by monitor_progress.py)
- `scripts/auto_download_patreon.py` - Old automation attempt
- `scripts/mouse_auto_download.py` - Old automation attempt
- `scripts/manual_download_helper.py` - Old helper
- `scripts/download_monitor.py` - Replaced by monitor_progress.py

### 6. **Duplicate Patreon Scripts**
- `scripts/patreon_downloader_browser.py` - Duplicate of patreon_browser_downloader.py

### 7. **Old RAG Script**
- `scripts/build_rag_index.py` - Replaced by build_rag_index_v2.py

### 8. **Redundant Documentation** (Content merged into current docs)
- `TRANSCRIPTION_PARALLEL.md` - Merged into MONITOR_SMART_WORKERS.md
- `AUDIO_TOOLS_SUMMARY.md` - Redundant with AUDIO_ANALYSIS_README.md
- `SCRIPTS_ANALYSIS.md` - Outdated

---

## Files to KEEP (Active/Useful)

### Core Scripts
- ✅ `scripts/monitor_progress.py` - Main orchestrator
- ✅ `scripts/podcast_downloader.py` - RSS feed downloader
- ✅ `scripts/patreon_downloader.py` - Patreon downloader (cookies)
- ✅ `scripts/patreon_browser_downloader.py` - Patreon downloader (browser)
- ✅ `scripts/podcast_transcriber.py` - Whisper transcriber
- ✅ `scripts/cleanup_stale_locks.py` - Safety utility

### Analysis/Processing Scripts
- ✅ `scripts/audio_analyzer.py` - Audio analysis tool
- ✅ `scripts/audio_diarizer.py` - Speaker diarization
- ✅ `scripts/extract_book_recommendations.py` - Book extraction
- ✅ `scripts/guest_and_twitter_extractor.py` - Guest/Twitter extraction
- ✅ `scripts/podcast_guest_analyzer.py` - Guest analysis
- ✅ `scripts/podcast_metadata_scraper.py` - Metadata scraper
- ✅ `scripts/podcast_processor.py` - Processing pipeline
- ✅ `scripts/recommendation_extractor.py` - Recommendation extraction
- ✅ `scripts/twitter_finder.py` - Twitter finder

### RAG/Server Scripts
- ✅ `scripts/build_rag_index_v2.py` - RAG index builder (v2)
- ✅ `scripts/rag_server.py` - RAG query server
- ✅ `scripts/smart_orchestrator.py` - Smart orchestration

### Documentation to Keep
- ✅ `README.md` - Main README
- ✅ `LOCK_FILE_SAFETY.md` - Lock file documentation
- ✅ `MONITOR_SMART_WORKERS.md` - Monitor documentation
- ✅ `MISSING_EPISODES.md` - Episode tracking
- ✅ `PATREON_COOKIE_GUIDE.md` - Patreon auth guide
- ✅ `PATREON_BROWSER_METHOD.md` - Browser method guide
- ✅ `AUDIO_ANALYSIS_README.md` - Audio analysis docs
- ✅ `RAG_SERVER_README.md` - RAG server docs

### Data Files
- ✅ `book_recommendations_raw.json` - Book data
- ✅ `data/download_state.json` - Download state
- ✅ `data/guest_directory_complete.json` - Guest directory
- ✅ `data/podcast_book_analysis.json` - Book analysis
- ✅ `podcast_metadata/*.json` - All metadata files
- ✅ `podocasts.opml` - Feed list

### Docs to Keep
- ✅ `docs/CLEANUP_COMPLETION_SUMMARY.md` - Cleanup history
- ✅ `docs/FALSE_POSITIVE_CLEANUP_REPORT.md` - Cleanup report
- ✅ `docs/OPTIMIZATION_LEARNINGS.md` - Learnings
- ✅ `docs/podcast_priority_list.md` - Priority list

---

## Summary

**DELETE:** 28 files (forensic scripts, temp reports, redundant launchers)
**KEEP:** 40+ files (active scripts, docs, data)

This will make the repo much cleaner while keeping all actively used tools!
