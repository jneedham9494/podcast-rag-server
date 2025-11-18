# Patreon Authentication Guide

Patreon requires authentication to download premium podcast episodes. This guide covers two methods.

## Method 1: Manual Cookie Extraction (Simple)

**Best for:** Quick one-time downloads

### Setup

1. **Open Chrome/Firefox** and log into Patreon.com
2. **Open Developer Tools** (F12 or Right-click → Inspect)
3. **Go to the Network tab**
4. **Visit your RSS feed** in the browser (example):
   ```
   https://www.patreon.com/rss/TrueAnonPod?auth=YOUR_AUTH_TOKEN
   ```
5. **Click on the first request** in the Network tab
6. **Go to "Headers" section**, scroll to "Request Headers"
7. **Copy the entire "Cookie:" header value**

It will look like:
```
session_id=abc123...; __cf_bm=xyz789...; ...
```

### Save Cookies

Create `patreon_cookies.txt` in project root:

```bash
echo "YOUR_COOKIE_STRING_HERE" > patreon_cookies.txt
```

### Usage

```bash
cd scripts
python3 patreon_downloader.py --manual-cookies
```

**Limitations:**
- Cookies expire after ~30 minutes
- Cloudflare bot detection may block requests
- Good for small downloads only

---

## Method 2: Browser Automation (Recommended)

**Best for:** Reliable automated downloads, integration with monitor

### Why Browser Automation?

Patreon actively blocks automated downloads:
- Download URLs have time-limited signatures (expire in minutes)
- Cloudflare Bot Management cookies expire every 30 mins
- Non-browser requests get blocked

**Solution:** Use Playwright to control a real browser with your existing login session.

### Setup (One-Time)

1. **Install Playwright:**
```bash
pip3 install playwright --user
~/Library/Python/3.9/bin/playwright install chromium
```

2. **Log into Patreon in Chrome:**
   - Open Chrome
   - Go to patreon.com
   - Log in
   - Keep Chrome open (session persists)

### Usage

```bash
cd scripts
python3 patreon_browser_downloader.py 'https://www.patreon.com/rss/TrueAnonPod?auth=YOUR_AUTH_TOKEN'
```

**Options:**
- Limit episodes: `patreon_browser_downloader.py <url> 10`
- Custom Chrome profile: `--chrome-profile="/path/to/profile"`

### How It Works

1. Launches real Chrome browser
2. Uses your existing Patreon session (no re-login needed)
3. Handles all authentication automatically (cookies, signatures, Cloudflare)
4. Downloads using browser's native download mechanism
5. Closes when done

### Integration with Monitor

The monitor (`monitor_progress.py`) automatically uses browser automation for Patreon feeds - no configuration needed!

---

## Method Comparison

| Method | Status | Best For | Limitations |
|--------|--------|----------|-------------|
| **Manual cookies** | ⚠️ Limited | Quick tests | Expires in 30 mins, bot detection |
| **Browser automation** | ✅ Recommended | Automated downloads | Requires Chrome installed |
| yt-dlp with cookies | ❌ Failed | N/A | Patreon blocks it |
| browser-cookie3 | ❌ Failed | N/A | Cookies expire too quickly |

---

## Troubleshooting

### Browser Automation Issues

**Browser doesn't open:**
- Ensure Chrome is installed
- Run: `~/Library/Python/3.9/bin/playwright install chromium`

**403 Forbidden errors:**
- Verify you're logged into Patreon in Chrome
- Try logging out and back in
- Close all Chrome windows and retry

**Downloads fail:**
- Check Patreon subscription is active
- Test with 1 episode first: `patreon_browser_downloader.py <url> 1`
- Check RSS feed URL is correct

### Cookie Method Issues

**Cookies expired:**
- Extract fresh cookies from browser
- Consider switching to browser automation method

**Cloudflare blocking:**
- Use browser automation method instead
- Manual cookies are not reliable for large downloads

---

## Recommendation

**Use browser automation** (`patreon_browser_downloader.py`) for all Patreon downloads. It's more reliable, handles authentication automatically, and integrates with the monitor system.

Manual cookie extraction is only useful for quick debugging or one-off downloads.
