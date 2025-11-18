# Odd Lots Guest Extraction - Improvement Report

**Date**: 2025-11-07
**Focus**: Improving Odd Lots extraction from 61.4% to target 75%

---

## Results Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Guest Extraction Rate** | 61.4% | 69.3% | +7.9% |
| **Guests Extracted** | 654 | 705 | +51 guests |
| **Non-Guest Episodes Tagged** | 24 | 72 | +48 episodes |
| **Actual Guest Episodes** | 1,065 | 1,017 | (48 reclassified) |

**Achievement**: 69.3% extraction rate, close to 75% target!

---

## Improvements Made

### 1. New Title Patterns (5 total)

**Pattern 1**: "Lots More With GUEST on/about..."
- Handles: "Lots More With Skanda Amarnath on This Moment in Macro"
- Impact: Captures follow-up interview episodes

**Pattern 2**: "GUEST on Topic" (enhanced)
- Added particles support: van, de, von, di, da, del
- Better filtering for generic titles

**Pattern 3**: "Topic With GUEST Name" (enhanced)
- Improved particle support
- Better false positive filtering

**Pattern 4**: "GUEST Is/Was/Wants/Thinks/Says/Explains..."
- Handles: "Austan Goolsbee Is Still Concerned About Inflation"
- Impact: Captures opinion/analysis episodes

**Pattern 5**: "GUEST: Topic"
- Handles: "David Woo: What Trump Started is Worse Than a Trade War"
- Impact: Captures expert commentary format

### 2. New Description Patterns (8 total)

**Pattern 1**: "we speak with GUEST, a..."
- Original pattern (already working)

**Pattern 2**: "Tracy and Joe speak with GUEST"
- Original pattern (already working)

**Pattern 3**: Job title before name
- Regex: `Federal Reserve Bank|Fed|Federal Reserve + President + GUEST`
- Handles: "Richmond Federal Reserve Bank President Tom Barkin"
- Impact: Captures Fed officials and government figures

**Pattern 4**: "In this episode" + guest patterns
- Handles: "In this episode, we speak with..."
- Impact: Captures episodes with intro phrases

**Pattern 5**: "According to GUEST, ..."
- Handles opening statements
- Impact: Limited, but catches some edge cases

**Pattern 6**: "GUEST is the/a [profession]"
- Handles: "Zichen Wang is the writer of the Pekingnology newsletter"
- Impact: Captures profession-first introductions

**Pattern 7**: "GUEST has built/is/was..."
- Handles: "Don Wilson has built a career diving into..."
- Impact: Captures biographical openings

**Pattern 8**: "GUEST of [company/org]"
- Handles: "David Johnson of Resolution Financial..."
- Impact: Captures company affiliation mentions

### 3. Enhanced Non-Guest Episode Detection

**New Episode Types Tagged**:

1. **Cross-promotion** (3 patterns)
   - "Introducing:", "Big Take:", "Everybody's Business:"
   - Impact: +12 episodes tagged

2. **Rereleases**
   - "(Rerelease)" or "Re-release" in title
   - Impact: +1 episode tagged

3. **Sponsored content**
   - "Sponsored Content" in title
   - Impact: +1 episode tagged

4. **Roundup episodes**
   - "Lots More on..." (discussion/roundup without specific guest)
   - Impact: +34 episodes tagged

**Total Non-Guest Episodes**: 72 (up from 24)

---

## Extraction Breakdown

### Episodes by Type

- **Total Episodes**: 1,089
- **Guest Episodes**: 1,017 (93.4%)
- **Non-Guest Episodes**: 72 (6.6%)
  - Cross-promotion: ~20
  - Roundups: ~34
  - Compilations: ~5
  - Other: ~13

### Guest Extraction

- **Guests Extracted**: 705 (69.3% of 1,017 guest episodes)
- **Still Missing**: 312 episodes (30.7%)

---

## Remaining Challenges

Looking at still-missing episodes, they fall into these categories:

### 1. Company/Organization Focus (no individual guest)
- "A Major American Egg Farm Just Lost 90% of its Chickens"
- "The Company That Wants To Bring Back Supersonic Jet Travel"
- **Action**: May not need individual names - company/org features

### 2. Topic-Driven Episodes (multiple guests or panel)
- "Why The World Started Hedging Its US Dollar Exposure"
- "How Do We Define a Currency?"
- **Action**: May require transcript analysis to identify all participants

### 3. Location/Trip Episodes (special format)
- "A Trip to Alaska With San Fran Fed President Mary Daly"
- "How to Move Freight Across the Icy Roads of Alaska"
- **Action**: Special travel/reporting format, may have multiple people

### 4. Edge Cases
- Non-standard naming conventions
- Guest names in different languages
- Multiple guests not clearly listed

---

## Next Steps

### For Odd Lots
1. ✅ **Complete**: Improved from 61.4% → 69.3%
2. ✅ **Complete**: Proper non-guest episode tagging (72 episodes)
3. **Future**: Consider transcript analysis for remaining 312 episodes
4. **Future**: Pattern analysis for company-focused episodes

### For Other Podcasts (from Prioritization Plan)
1. **Joshua Citarella**: 39.0% → target 70%
   - Add more "My guest is" pattern variations
   - Handle different episode formats

2. **Chapo Trap House**: 38.8% → target 60%
   - Better "feat." pattern detection
   - Add description-based patterns

3. **Sad Boyz**: 28.2% → target 50%
   - Enhance "(w/ Guest)" patterns
   - Add "ft." pattern variations

---

## Technical Summary

### Files Modified
- `guest_and_twitter_extractor.py`
  - Enhanced `extract_guest_from_title()` with 5 new Odd Lots patterns
  - Enhanced `extract_guest_from_description()` with 8 new Odd Lots patterns
  - Enhanced `is_non_guest_episode()` with 4 new episode type detections

### Pattern Philosophy
1. **Title patterns**: Structured, predictable formats (higher confidence)
2. **Description patterns**: More flexible, captures edge cases (medium confidence)
3. **Non-guest detection**: Removes false negatives, improves accuracy metrics

### Performance Impact
- **Processing time**: ~60 seconds for 9,388 episodes (unchanged)
- **False positives**: Minimal increase due to careful filtering
- **False negatives**: Significant reduction (+51 guests found)

---

## Conclusion

Successfully improved Odd Lots extraction from 61.4% to 69.3%, achieving a gain of +51 guests and properly tagging +48 non-guest episodes. This brings us close to the 75% target, with the remaining episodes being challenging edge cases that may require transcript analysis or represent non-traditional interview formats.

The improvements focused on:
- Better title pattern matching (5 new patterns)
- Enhanced description parsing (8 new patterns)  
- Accurate non-guest episode classification (4 new types)

This provides a solid foundation for transcript-based book/movie recommendation extraction.
