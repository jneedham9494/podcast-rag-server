# Missing Episodes Report

Generated: 2025-11-14
Updated: 2025-11-14 (all episodes downloaded!)

## ✅ ALL FEEDS COMPLETE!

---

## TRUE ANON TRUTH FEED - COMPLETE ✓ (Actually 100%+!)

**Final Status:**
- Total in RSS: 558 episodes
- Downloaded: 560 episodes
- Extra: 2 old episodes no longer in RSS feed but still on disk

**Previously "Missing" Episodes - NOW DOWNLOADED:**
1. ✅ `[9/11 Week] Bush Did 9/11 Part 3` → `Episode 58 Bush Did 911 Pt. 3.mp3`
2. ✅ `[9/11 Week] Bush Did 9/11 Part 2` → `Episode 44 Bush Did 911 (Part 2).mp3`
3. ✅ `You'd Never Guess (Theme From TrueAnon)` → `You'd Never Guess (Theme From TrueAnon).wav`

*Note: RSS titles don't match filenames exactly, which caused initial confusion. All episodes are downloaded.*

---

## Block Stars with David Schwartz - COMPLETE ✓

- The RSS feed has a generic "Block Stars" entry that matches multiple episode files
- All 27 actual episodes are downloaded
- No action needed

---

## Final Summary

All feeds are now showing correctly in the monitor:

### Feeds with Manual Overrides (Complete Collections):

- **Block Stars with David Schwartz**: 100% (27/27) ✓
  - RSS has generic "Block Stars" entry causing count issues

- **TRUE ANON TRUTH FEED**: 100% (560/560) ✓
  - Has 2 more files than current RSS (old episodes removed from feed)
  - Includes 5 .wav files (4 previews + 1 theme song)

- **Joshua Citarella**: 100% (166/166) ✓
  - Has 25 preview duplicates (same episode with `[PREVIEW]` tag and without)
  - 166 unique episodes (191 total files - 25 duplicates)
  - Run `python3 scripts/cleanup_joshua_citarella_duplicates.py` to remove duplicates (saves 336 MB)

- **Hello Internet**: 100% (126/126) ✓
  - Podcast ended, RSS truncated to 76 episodes
  - We have complete archive (126 episodes)

- **Hello Internet Archive**: 100% (126/126) ✓
  - Symlink to Hello Internet directory
  - Same 126 episodes

### Other Feeds:
- All other feeds verified complete via RSS duplicate detection
- RSS duplicates automatically subtracted from totals

**No missing episodes remain!** 🎉

---

## Technical Notes

**Why do some feeds have more files than RSS?**
- Podcasts remove old episodes from RSS feeds
- SoundCloud has episode limits
- Podcast hosts may rotate content
- We keep all downloaded files regardless of RSS changes

**Monitor Updates:**
- Now counts .mp3, .m4a, AND .wav files
- Detects and subtracts RSS duplicate entries
- Manual overrides for feeds with bad RSS data
- Shows correct completion % for all feeds
