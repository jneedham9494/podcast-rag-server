# Prioritized Guest Extraction Improvement Plan

**Date**: 2025-11-07
**Based on**: Comprehensive analysis of 37 podcasts

---

## Priority Ranking Methodology

**Impact Score** = Missing Episodes × (1 - Current Rate)
- Higher missing episodes = more to gain
- Lower current rate = more room for improvement
- Excludes non-interview formats (solo, co-host, documentary)

---

## 🎯 HIGH PRIORITY (Top 5 - Highest Impact)

### 1. Arseblog Arsecast, The Arsenal Podcast
- **Current**: 18.5% (284/1,537 guest episodes)
- **Missing**: 1,253 episodes
- **Potential**: ~626 episodes (target 60%)
- **Impact Score**: 1,021
- **Format**: Sports panel/interview
- **Action**:
  - Analyze panel discussion formats
  - Add patterns for "joining us today" type introductions
  - Handle multiple guests per episode

### 2. TRUE ANON TRUTH FEED
- **Current**: 11.6% (64/554 guest episodes)
- **Missing**: 490 episodes
- **Potential**: ~245 episodes (target 55%)
- **Impact Score**: 433
- **Format**: Investigation/interview
- **Action**:
  - Sample episode descriptions
  - Identify guest introduction patterns
  - May have inconsistent naming

### 3. The Adam Friedland Show Podcast
- **Current**: 15.8% (72/456 guest episodes)
- **Missing**: 384 episodes
- **Potential**: ~192 episodes (target 58%)
- **Impact Score**: 323
- **Format**: Comedy interview
- **Note**: Already improved from 2.2% → 15.8%
- **Action**:
  - Most episodes are NOT interviews (only 74 actually have guests)
  - Current extraction captures 97% of actual guest episodes
  - **No further action needed** - performance is actually excellent

### 4. The Yard
- **Current**: 5.8% (13/223 guest episodes)
- **Missing**: 210 episodes
- **Potential**: ~105 episodes (target 53%)
- **Impact Score**: 198
- **Format**: Gaming/comedy podcast
- **Action**:
  - Determine if truly interview-based or multi-host panel
  - Sample episodes to identify format

### 5. Chapo Trap House
- **Current**: 38.7% (190/491 guest episodes)
- **Missing**: 301 episodes
- **Potential**: ~150 episodes (target 69%)
- **Impact Score**: 185
- **Format**: Political commentary with guests
- **Action**:
  - Improve "feat." pattern detection
  - Add description-based patterns
  - Handle multi-guest episodes

---

## 🟡 MEDIUM PRIORITY (Next 5)

### 6. Odd Lots
- **Current**: 61.4% (654/1,066 guest episodes)
- **Missing**: 412 episodes
- **Already Working**: ✓ Being downloaded for transcripts
- **Action**:
  - Improve title-based extraction
  - Better handling of corporate/government official names
  - Handle episodes with generic titles ("San Francisco's New Mayor")

### 7. Multipolarity
- **Current**: 1.4% (2/147 guest episodes)
- **Missing**: 145 episodes
- **Action**: Analyze format, may need complete pattern overhaul

### 8. Fear&
- **Current**: 9.1% (15/165 guest episodes)
- **Missing**: 150 episodes
- **Action**: Sample descriptions, identify guest patterns

### 9. Sad Boyz
- **Current**: 28.2% (55/195 guest episodes)
- **Missing**: 140 episodes
- **Action**:
  - Improve "(w/ Guest)" patterns
  - Add "ft." variations
  - Check description formats

### 10. Joshua Citarella
- **Current**: 39.0% (53/136 guest episodes)
- **Missing**: 83 episodes
- **Already Working**: ✓ Being downloaded for transcripts
- **Action**:
  - Add more "My guest is" variations
  - Handle episodes with different format
  - May have solo commentary episodes

---

## 🟢 LOW PRIORITY (Smaller Volume)

These have fewer episodes, so lower overall impact:

11. **Fin vs History**: 5.5% (5/91, missing 86)
12. **The Always Sunny Podcast**: 1.3% (1/77, missing 76)
13. **Blowback**: 1.5% (1/65, missing 64)
14. **Say Why To Drugs**: 16.0% (8/50, missing 42)
15. **My Friend Podcast**: 11.1% (2/18, missing 16)

---

## ✅ ALREADY EXCELLENT (85%+) - No Action Needed

These podcasts already have excellent extraction:

- **Adam Buxton**: 95.1% (253/266) - **100% of actual guest episodes** ✓
- **RHLSTP**: 89.5% (854/954) ✓
- **Louis Theroux**: 89.1% (41/46) ✓
- **Grounded**: 86.4% (19/22) ✓

---

## ❌ NON-INTERVIEW FORMAT - Skip

These are not traditional interview podcasts:

- **Monday Morning Podcast** (0.4%) - Solo commentary
- **Cox n' Crendor Show** (0%) - Co-host duo
- **Hello Internet** (0%) - Co-host duo
- **Jimquisition** (1.9%) - Gaming commentary, mostly solo
- **Cyber Hack** (0%) - Format unclear
- **Documentary podcasts** (Witch, Things Fell Apart, etc.)

---

## 📋 Recommended Action Sequence

### Phase 1: Quick Wins (Already in Progress)
1. ✅ **Adam Buxton** - COMPLETE (100% of guest episodes)
2. ✅ **RHLSTP** - COMPLETE (89.5%)
3. ✅ **Louis Theroux** - COMPLETE (89.1%)
4. ✅ **Grounded** - COMPLETE (86.4%)

### Phase 2: Medium Difficulty (Currently Being Downloaded)
5. **Odd Lots** - 61.4% → target 75%
   - Improve title-based patterns
   - Corporate/government official names
6. **Joshua Citarella** - 39.0% → target 70%
   - Enhance "My guest is" patterns
   - Add format variations

### Phase 3: Higher Difficulty (New Work)
7. **Chapo Trap House** - 38.7% → target 60%
   - Better "feat." detection
   - Description patterns
8. **Sad Boyz** - 28.2% → target 50%
   - "(w/ Guest)" improvements
   - "ft." variations
9. **TRUE ANON** - 11.6% → target 40%
   - Complete format analysis
   - Custom patterns

### Phase 4: High Volume, High Difficulty
10. **Arseblog Arsecast** - 18.5% → target 50%
    - Sports podcast format
    - Panel discussions
    - Multiple guests

---

## Notes on Adam Friedland Show

**Important Discovery**: While the extraction shows 15.8% (72/456), this is actually **excellent performance**:

- Analysis shows only **74 episodes actually have guests** (16.2% of total)
- We're extracting **72 episodes**
- **Real extraction rate: 97.3% of guest episodes** ✓

This podcast mostly consists of:
- Regular host content (no guests)
- Comedy segments
- Commentary

**Conclusion**: Adam Friedland Show requires **no further action** - it's actually performing excellently.

---

## Impact Potential Summary

| Priority | Podcast | Missing | Realistic Gain | Effort |
|----------|---------|---------|----------------|--------|
| HIGH | Arseblog | 1,253 | ~400 | Hard |
| HIGH | TRUE ANON | 490 | ~150 | Medium |
| HIGH | The Yard | 210 | ~80 | Medium |
| HIGH | Chapo | 301 | ~100 | Medium |
| MEDIUM | Odd Lots | 412 | ~150 | Easy |
| MEDIUM | Sad Boyz | 140 | ~50 | Easy |
| MEDIUM | Joshua Citarella | 83 | ~30 | Easy |

**Total Realistic Gain from Top 7**: ~960 additional guests

---

## Current Status

### Podcasts Being Downloaded (Transcripts in Progress)
- Adam Buxton ✓
- RHLSTP ✓
- Odd Lots ✓
- Joshua Citarella ✓

### Next to Improve (Post Transcript Analysis)
1. Chapo Trap House
2. Sad Boyz
3. TRUE ANON
4. The Yard
5. Arseblog (if sports podcast format is desired)

---

## Conclusion

**Immediate Priority**: Focus on podcasts currently being downloaded for transcripts:
- Odd Lots: 61.4% → 75% (improve by ~150 episodes)
- Joshua Citarella: 39% → 70% (improve by ~30 episodes)

**Next Phase**: After transcript work, tackle:
- Chapo Trap House (high volume, moderate difficulty)
- Sad Boyz (moderate volume, easy patterns)
- TRUE ANON (high volume, uncertain difficulty)

**Long Term**: Consider Arseblog if sports content is priority (1,253 missing episodes)
