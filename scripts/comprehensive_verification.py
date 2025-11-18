#!/usr/bin/env python3
"""
Comprehensive 3-way verification for ALL feeds:
1. RSS feed entries
2. Downloaded audio files
3. Transcript files
"""

import xml.etree.ElementTree as ET
import feedparser
from pathlib import Path
import re
from collections import defaultdict

def normalize_title(title):
    """Normalize title for comparison"""
    title = re.sub(r'\[PREVIEW\]', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*-\s*TRUE ANON.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\(.*?\)', '', title)
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip().lower()

def get_rss_count(feed_url, feed_name):
    """Get count from RSS feed"""
    try:
        feed = feedparser.parse(feed_url)

        # Count unique titles
        titles = set()
        for entry in feed.entries:
            normalized = normalize_title(entry.title)
            titles.add(normalized)

        return len(feed.entries), len(titles)
    except Exception as e:
        return 0, 0

def get_downloaded_count(feed_name):
    """Get count of downloaded files"""
    episodes_dir = Path('..') / 'episodes' / feed_name

    if not episodes_dir.exists():
        return 0

    # Count all audio files
    audio_files = []
    for ext in ['*.mp3', '*.m4a', '*.wav']:
        audio_files.extend(list(episodes_dir.glob(ext)))

    return len(audio_files)

def get_transcript_count(feed_name):
    """Get count of transcript files"""
    transcripts_dir = Path('..') / 'transcripts' / feed_name

    if not transcripts_dir.exists():
        return 0

    txt_files = list(transcripts_dir.glob('*.txt'))
    return len(txt_files)

def get_unmatched_files(feed_name):
    """Find audio files without transcripts and vice versa"""
    episodes_dir = Path('..') / 'episodes' / feed_name
    transcripts_dir = Path('..') / 'transcripts' / feed_name

    # Get audio file stems
    audio_stems = set()
    if episodes_dir.exists():
        for ext in ['*.mp3', '*.m4a', '*.wav']:
            for f in episodes_dir.glob(ext):
                audio_stems.add(f.stem)

    # Get transcript stems
    transcript_stems = set()
    if transcripts_dir.exists():
        for f in transcripts_dir.glob('*.txt'):
            transcript_stems.add(f.stem)

    # Find mismatches
    audio_no_transcript = audio_stems - transcript_stems
    transcript_no_audio = transcript_stems - audio_stems

    return audio_no_transcript, transcript_no_audio

def main():
    print("=" * 100)
    print("COMPREHENSIVE 3-WAY VERIFICATION - ALL FEEDS")
    print("=" * 100)
    print()

    # Parse OPML
    opml_path = Path('..') / 'podocasts.opml'
    tree = ET.parse(opml_path)
    root = tree.getroot()

    results = []
    issues = []

    for outline in root.findall('.//outline[@type="rss"]'):
        feed_name = outline.get('text', 'Unknown')
        feed_url = outline.get('xmlUrl', '')

        print(f"Checking: {feed_name}...")

        # Get counts
        rss_total, rss_unique = get_rss_count(feed_url, feed_name)
        downloaded = get_downloaded_count(feed_name)
        transcribed = get_transcript_count(feed_name)

        # Get mismatches
        audio_no_trans, trans_no_audio = get_unmatched_files(feed_name)

        result = {
            'name': feed_name,
            'rss_total': rss_total,
            'rss_unique': rss_unique,
            'downloaded': downloaded,
            'transcribed': transcribed,
            'audio_no_transcript': len(audio_no_trans),
            'transcript_no_audio': len(trans_no_audio),
            'rss_duplicates': rss_total - rss_unique,
        }

        results.append(result)

        # Check for issues
        if downloaded != transcribed:
            issue = {
                'feed': feed_name,
                'type': 'transcription_incomplete',
                'downloaded': downloaded,
                'transcribed': transcribed,
                'missing': downloaded - transcribed,
                'audio_no_trans': list(audio_no_trans)[:5],  # First 5 examples
                'trans_no_audio': list(trans_no_audio)[:5]
            }
            issues.append(issue)

        if rss_total != rss_unique:
            issues.append({
                'feed': feed_name,
                'type': 'rss_duplicates',
                'total': rss_total,
                'unique': rss_unique,
                'duplicates': rss_total - rss_unique
            })

    # Print summary
    print()
    print("=" * 100)
    print("SUMMARY BY FEED")
    print("=" * 100)
    print()

    header = f"{'Feed':<40} {'RSS':>6} {'DL':>6} {'Trans':>6} {'Miss':>5} {'%':>6}"
    print(header)
    print("-" * 100)

    for r in sorted(results, key=lambda x: x['downloaded'] - x['transcribed'], reverse=True):
        missing = r['downloaded'] - r['transcribed']
        pct = (r['transcribed'] / r['downloaded'] * 100) if r['downloaded'] > 0 else 0

        status = ""
        if missing > 0:
            status = "⚠️"
        elif r['downloaded'] > 0:
            status = "✓"

        print(f"{r['name'][:40]:<40} {r['rss_total']:6} {r['downloaded']:6} {r['transcribed']:6} {missing:5} {pct:5.1f}% {status}")

    # Print detailed issues
    print()
    print("=" * 100)
    print("DETAILED ISSUES")
    print("=" * 100)

    if not issues:
        print("\n✅ No issues found! All feeds verified successfully.")
    else:
        for issue in issues:
            print()
            if issue['type'] == 'transcription_incomplete':
                print(f"⚠️  {issue['feed']}")
                print(f"   Downloaded: {issue['downloaded']}")
                print(f"   Transcribed: {issue['transcribed']}")
                print(f"   Missing: {issue['missing']}")

                if issue['audio_no_trans']:
                    print(f"   Audio without transcript ({len(issue['audio_no_trans'])} files):")
                    for f in issue['audio_no_trans']:
                        print(f"      - {f}")

                if issue['trans_no_audio']:
                    print(f"   Transcript without audio ({len(issue['trans_no_audio'])} files):")
                    for f in issue['trans_no_audio']:
                        print(f"      - {f}")

            elif issue['type'] == 'rss_duplicates':
                print(f"ℹ️  {issue['feed']}")
                print(f"   RSS has {issue['duplicates']} duplicate entries")
                print(f"   Total: {issue['total']}, Unique: {issue['unique']}")

    # Overall stats
    print()
    print("=" * 100)
    print("OVERALL STATISTICS")
    print("=" * 100)

    total_feeds = len(results)
    total_downloaded = sum(r['downloaded'] for r in results)
    total_transcribed = sum(r['transcribed'] for r in results)
    total_missing = total_downloaded - total_transcribed
    overall_pct = (total_transcribed / total_downloaded * 100) if total_downloaded > 0 else 0

    feeds_complete = sum(1 for r in results if r['downloaded'] == r['transcribed'] and r['downloaded'] > 0)

    print(f"Total feeds: {total_feeds}")
    print(f"Feeds complete: {feeds_complete}")
    print(f"Total downloaded: {total_downloaded}")
    print(f"Total transcribed: {total_transcribed}")
    print(f"Total missing: {total_missing}")
    print(f"Overall completion: {overall_pct:.2f}%")
    print()
    print("=" * 100)

if __name__ == '__main__':
    main()
