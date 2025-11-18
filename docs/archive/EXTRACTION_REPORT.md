# Guest Extraction Improvement Report

**Date**: 2025-11-07
**Total Episodes Processed**: 9,388
**Unique Guests Extracted**: 1,455
**Total Guest Appearances**: 2,250
**Guests with Twitter Handles**: 155

---

## Executive Summary

Successfully improved guest extraction across all podcasts, increasing unique guests from 1,409 to 1,455 (+46 guests). Key improvements focused on Adam Friedland Show, Joshua Citarella, and Odd Lots podcasts.

---

## Major Improvements

### Adam Friedland Show
- **Before**: 10 guests (2.2%)
- **After**: 73 guests (16.0%)
- **Improvement**: 630% increase
- **Achievement**: Now extracting 98.6% of episodes that actually have guests
- **Note**: Only 74 out of 457 episodes have guest interviews (16.2% of total)

### Joshua Citarella
- **Before**: 32 guests (23.2%)
- **After**: 55 guests (39.9%)
- **Improvement**: +71.9%

### Odd Lots
- **Before**: 254 guests (23.3%)
- **After**: 286 guests (26.3%)
- **Improvement**: +12.6%

### Twitter Handles
- **Before**: 145 guests with handles
- **After**: 155 guests with handles
- **Improvement**: +10 guests

---

## Pattern Fixes Applied

### Adam Friedland Show - 4 Format Patterns
1. **Format 1**: `GUEST NAME Talks Topic` (case-insensitive)
2. **Format 2**: `GUEST NAME | Topic` (pipe separator)
3. **Format 3**: `The Adam Friedland Show Podcast - Guest Name - Episode ##`
4. **Format 4**: `Episode ## Featuring Guest Name`

### Odd Lots - Enhanced Name Matching
- Added lowercase particle support: van, de, von, di, da, del
- Added alternative format: `Topic With Guest Name`
- Improved filtering for generic titles

### Joshua Citarella - Fixed Pattern
- Fixed missing colon: `Doomscroll ##: Guest Name`

### Generic Patterns
- Improved `(w/ Guest Name)` and `(with Guest Name)` patterns
- Enhanced `ft. Guest Name` pattern

---

## Extraction Quality by Podcast

| Podcast | Rate | Guests | Episodes | Quality |
|---------|------|--------|----------|---------|
| Grounded with Louis Theroux | 86.4% | 19 | 22 | Excellent |
| The Louis Theroux Podcast | 84.3% | 43 | 51 | Excellent |
| THE ADAM BUXTON PODCAST | 81.6% | 217 | 266 | Excellent |
| RHLSTP with Richard Herring | 57.8% | 568 | 982 | Good |
| Joshua Citarella | 24.6% | 34 | 138 | Improved |
| Odd Lots | 21.3% | 232 | 1,089 | Room for improvement |

---

## Top 30 Most Frequent Podcast Guests

1. **Andrew Allen** (39 appearances) - Arseblog Arsecast @JoeBrewinFFT
2. **Phil Costa** (26 appearances) - Arseblog Arsecast @okwonga
3. **Tim Stillman** (26 appearances) - Arseblog Arsecast @Stillberto
4. **Philippe Auclair** (22 appearances) - Arseblog Arsecast @AAllenSport
5. **Amy Lawrence** (18 appearances) - Arseblog Arsecast @charles_watts
6. **Alex Nichols** (17 appearances) - Chapo Trap House @Lowenaffchen
7. **James Benge** (16 appearances) - Arseblog Arsecast @Okwonga
8. **Lewis Ambrose** (15 appearances) - Arseblog Arsecast @YankeeGunner
9. **Charles Watts** (13 appearances) - Arseblog Arsecast @jeorgebird
10. **Adam Buxton** (12 appearances) - RHLSTP, Louis Theroux
11. **James Acaster** (9 appearances) - RHLSTP, Adam Buxton
12. **Louis Theroux** (9 appearances) - RHLSTP, Adam Buxton
13. **Ryan Hunn** (8 appearances) - Arseblog Arsecast @Stadio
14. **Jon Ronson** (8 appearances) - Grounded, RHLSTP, Adam Buxton
15. **Sara Pascoe** (8 appearances) - RHLSTP, Adam Buxton
16. **Tim Key** (8 appearances) - RHLSTP, Adam Buxton
17. **Joe Lycett** (8 appearances) - RHLSTP, Adam Buxton
18. **Kaya Kaynak** (7 appearances) - Arseblog Arsecast @kaykaynak97
19. **Tayo Popoola** (7 appearances) - Arseblog Arsecast @DJTayo
20. **David Mitchell** (7 appearances) - RHLSTP, Adam Buxton
21. **Ken Early** (6 appearances) - Arseblog Arsecast @kenearlys
22. **Brace Belden** (6 appearances) - Chapo, Joshua Citarella, Adam Friedland
23. **Viktor Shvets** (6 appearances) - Odd Lots
24. **Bob Mortimer** (6 appearances) - RHLSTP, Adam Buxton
25. **Armando Iannucci** (6 appearances) - RHLSTP
26. **Nish Kumar** (6 appearances) - RHLSTP, Adam Buxton
27. **Richard Osman** (6 appearances) - RHLSTP
28. **Sarah Millican** (6 appearances) - RHLSTP
29. **Mike Recine** (6 appearances) - Adam Friedland Show
30. **Harry Symeou** (5 appearances) - Arseblog Arsecast @arsenalpodcast

---

## Podcasts Requiring Further Work

These podcasts have low extraction rates and may benefit from description-based extraction or manual review:

- **I Like Films with Jonathan Ross**: 6.2% (1/16 episodes)
- **Jimquisition**: 1.7% (9/524 episodes)
- **Multipolarity**: 1.3% (2/151 episodes)
- **The Yard**: 5.7% (13/228 episodes)
- **Fear&**: 8.8% (15/171 episodes)

---

## Next Steps

1. **Verify Twitter Handles**: Review the 155 guests with potential Twitter handles from metadata
2. **Description-Based Extraction**: Implement for low-rate podcasts (I Like Films, Jimquisition, etc.)
3. **Begin Transcription Download**: Start with high-priority podcasts:
   - RHLSTP (568 unique guests, 18.0% book density)
   - Adam Buxton (217 unique guests, 15.4% book density)
   - Odd Lots (232 unique guests, 15.1% book density)
   - Joshua Citarella (34 unique guests, 18.8% book density)

---

## Technical Notes

### Files Updated
- `guest_and_twitter_extractor.py` - Main extraction script with improved patterns
- `guest_directory_complete.json` - Complete guest directory with 1,455 guests
- `EXTRACTION_REPORT.md` - This report

### Key Learnings
1. **Adam Friedland Show**: Most episodes don't have guest interviews - only 16.2% do
2. **Odd Lots**: Only 54% of episodes have guest names in titles (rest are topic-only)
3. **Twitter Handles**: Episode descriptions are valuable source (found 155 potential handles)
4. **Name Particles**: Important to support lowercase particles (van, de, von) for international names
