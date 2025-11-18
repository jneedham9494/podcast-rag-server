# Feature: Patreon Authentication

## Status
Retroactive specification for existing feature

## Overview
Handles authentication for premium podcast content on Patreon. Two methods: cookie-based and browser automation.

## Current Behavior

### Cookie Method (patreon_downloader.py)
- Uses cookies extracted from browser
- Quick but cookies expire frequently

### Browser Automation (patreon_browser_downloader.py)
- Uses Playwright to automate Chrome browser
- Loads user's existing Chrome profile for authentication
- More reliable but slower

## Technical Implementation
- **Locations**:
  - [patreon_downloader.py](scripts/patreon_downloader.py) (~13KB)
  - [patreon_browser_downloader.py](scripts/patreon_browser_downloader.py) (~9KB)
- **Dependencies**: playwright, requests
- **Dependents**: monitor_progress.py
- **Configuration**: `patreon_cookies.txt` in project root

## Acceptance Criteria (Current State)

### Cookie Authentication
- GIVEN valid Patreon cookies file
  WHEN downloading premium episode
  THEN downloads successfully with cookie auth

- GIVEN expired cookies
  WHEN downloading
  THEN fails with authentication error

### Browser Automation
- GIVEN user logged into Patreon in Chrome
  WHEN browser automation runs
  THEN loads existing Chrome profile and uses session

- GIVEN Patreon episode URL
  WHEN browser navigates to page
  THEN extracts and downloads audio file

### Integration
- GIVEN premium feed detected
  WHEN monitor runs
  THEN uses appropriate Patreon downloader

## Known Issues / Tech Debt

- [ ] **Cookie expiration** - Cookies expire frequently, no auto-refresh
- [ ] **Chrome profile hardcoded** - Path to Chrome profile may vary
- [ ] **No error recovery** - Browser crashes not handled gracefully
- [ ] **Playwright version** - May break with Playwright updates
- [ ] **No headless option** - Browser always visible
- [ ] **Two implementations** - Duplicate code between cookie and browser methods

## Future Improvements

- [ ] Implement automatic cookie refresh
- [ ] Add configurable Chrome profile path
- [ ] Add headless browser option
- [ ] Consolidate into single module with strategy pattern
- [ ] Add pytest tests with mock Patreon responses
- [ ] Add session caching to reduce browser launches
- [ ] Implement proper error recovery and retry
