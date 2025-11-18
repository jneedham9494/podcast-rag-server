# Feature: Guest Extraction

## Status
Retroactive specification for existing feature

## Overview
Extracts guest names and Twitter handles from podcast episodes using pattern matching and metadata analysis.

## Current Behavior
- Parses episode titles for guest name patterns (e.g., "w/ Guest Name", "feat. Guest")
- Extracts potential Twitter handles from descriptions
- Outputs structured JSON with guest directory
- Multiple archived versions indicate iterative development

## Technical Implementation
- **Location**: [guest_and_twitter_extractor.py](scripts/guest_and_twitter_extractor.py) (~44KB)
- **Archived versions**: 9+ versions in `scripts/archive/`
- **Dependencies**: Standard library (re, json)
- **Dependents**: None (analysis tool)
- **Output**: `data/guest_directory_complete.json` (2,058 guests)

## Acceptance Criteria (Current State)

### Guest Name Extraction
- GIVEN episode title with "w/ Guest Name"
  WHEN extracted
  THEN returns "Guest Name"

- GIVEN episode title with "feat. Guest"
  WHEN extracted
  THEN returns "Guest"

- GIVEN episode with multiple guests
  WHEN extracted
  THEN returns list of all guests

### Twitter Handle Extraction
- GIVEN episode description with @handle
  WHEN extracted
  THEN associates handle with guest

### Output
- GIVEN all podcasts processed
  WHEN extraction complete
  THEN saves guest_directory_complete.json with guest list

## Known Issues / Tech Debt

- [ ] **Massive file** - 44KB far exceeds guidelines
- [ ] **Many archived versions** - 9+ versions indicate unstable implementation
- [ ] **Pattern brittleness** - Relies on regex patterns that may miss cases
- [ ] **No deduplication** - Same guest may appear multiple times
- [ ] **No validation** - Twitter handles not verified
- [ ] **No tests** - Complex pattern matching has no test coverage

## Future Improvements

- [ ] Refactor into smaller modules
- [ ] Consolidate archived versions
- [ ] Add comprehensive regex tests
- [ ] Implement guest deduplication
- [ ] Add Twitter handle validation
- [ ] Use NLP/ML for better name extraction
- [ ] Add confidence scores for extractions
- [ ] Create clean API for guest lookup
