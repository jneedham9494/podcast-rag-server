# Feature: Book Recommendations

## Status
Retroactive specification for existing feature

## Overview
Extracts book recommendations mentioned in podcast transcripts using pattern matching.

## Current Behavior
- Scans transcript text for book mention patterns
- Extracts book titles and authors when possible
- Aggregates recommendations by podcast
- Outputs structured JSON analysis

## Technical Implementation
- **Location**: [extract_book_recommendations.py](scripts/extract_book_recommendations.py) (~6KB)
- **Dependencies**: Standard library (re, json)
- **Dependents**: None (analysis tool)
- **Output**: `data/podcast_book_analysis.json`

## Acceptance Criteria (Current State)

### Book Extraction
- GIVEN transcript mentioning "the book [Title]"
  WHEN extracted
  THEN returns book title

- GIVEN transcript mentioning "[Title] by [Author]"
  WHEN extracted
  THEN returns title and author

### Analysis
- GIVEN all transcripts processed
  WHEN analysis complete
  THEN groups books by podcast

- GIVEN podcast
  WHEN analyzed
  THEN calculates "book score" (density of recommendations)

### Output
- GIVEN extraction complete
  WHEN saving
  THEN creates podcast_book_analysis.json with all books

## Known Issues / Tech Debt

- [ ] **Pattern limitations** - Regex patterns miss many mention styles
- [ ] **False positives** - May extract non-book mentions
- [ ] **No deduplication** - Same book may appear multiple times
- [ ] **No book validation** - Titles not verified against database
- [ ] **No author normalization** - Same author with different spellings
- [ ] **No tests** - Pattern matching has no test coverage

## Future Improvements

- [ ] Use NLP for better book detection
- [ ] Validate against book database (OpenLibrary, Google Books)
- [ ] Implement title/author deduplication
- [ ] Add confidence scores
- [ ] Track context (who recommended, why)
- [ ] Add pytest tests with sample transcripts
- [ ] Create API endpoint for book queries
- [ ] Add ISBN lookup where possible
