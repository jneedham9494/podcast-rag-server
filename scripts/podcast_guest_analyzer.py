#!/usr/bin/env python3
"""
Analyzes podcast metadata to find episodes with guests and book mentions.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Patterns to detect book-related content
BOOK_KEYWORDS = [
    r'\bnew book\b',
    r'\blatest book\b',
    r'\bbook called\b',
    r'\bbook titled\b',
    r'\bauthor of\b',
    r'\bwrote\b',
    r'\bwriting\b',
    r'\bpublished\b',
    r'\bnovel\b',
    r'\bmemoir\b',
    r'\bbiography\b',
    r'\bessay\b',
    r'\bdiscuss(?:es|ing)? (?:his|her|their) book\b',
]

# Patterns to detect guest names
GUEST_PATTERNS = [
    r'(?:with|featuring|ft\.?) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
    r'^([A-Z][a-z]+(?: [A-Z][a-z]+)+)(?:\s*[-:])',  # Name at start followed by dash/colon
    r'(?:interview with|talks? to|conversation with) ([A-Z][a-z]+(?: [A-Z][a-z]+)+)',
]

def analyze_episode(episode, podcast_title):
    """Analyze a single episode for guest and book indicators."""
    title = episode.get('title', '')
    description = episode.get('description', '')
    combined_text = f"{title} {description}".lower()

    # Check for book keywords
    book_mentions = []
    for pattern in BOOK_KEYWORDS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            book_mentions.append(pattern.strip(r'\b'))

    # Extract potential guest names
    guests = set()
    for pattern in GUEST_PATTERNS:
        matches = re.findall(pattern, title)
        guests.update(matches)

    return {
        'title': title,
        'published': episode.get('published', ''),
        'duration': episode.get('duration', ''),
        'guests': list(guests),
        'book_keywords': book_mentions,
        'book_score': len(book_mentions),
        'has_guest': len(guests) > 0,
    }

def analyze_all_metadata(metadata_dir="podcast_metadata"):
    """Analyze all podcast metadata files."""
    metadata_path = Path(metadata_dir)

    results = {
        'podcasts': {},
        'top_book_episodes': [],
        'podcasts_by_book_density': [],
    }

    # Skip index.json
    json_files = [f for f in metadata_path.glob("*.json") if f.name != "index.json"]

    print(f"Analyzing {len(json_files)} podcast feeds...\n")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                podcast_data = json.load(f)

            podcast_title = podcast_data.get('podcast_title', 'Unknown')
            episodes = podcast_data.get('episodes', [])

            if not episodes:
                continue

            # Analyze each episode
            analyzed_episodes = []
            total_book_score = 0
            episodes_with_books = 0
            episodes_with_guests = 0

            for episode in episodes:
                analysis = analyze_episode(episode, podcast_title)
                analyzed_episodes.append(analysis)

                total_book_score += analysis['book_score']
                if analysis['book_score'] > 0:
                    episodes_with_books += 1
                if analysis['has_guest']:
                    episodes_with_guests += 1

            # Calculate metrics
            book_density = (episodes_with_books / len(episodes) * 100) if episodes else 0
            guest_density = (episodes_with_guests / len(episodes) * 100) if episodes else 0

            results['podcasts'][podcast_title] = {
                'total_episodes': len(episodes),
                'episodes_with_books': episodes_with_books,
                'episodes_with_guests': episodes_with_guests,
                'book_density_pct': round(book_density, 1),
                'guest_density_pct': round(guest_density, 1),
                'avg_book_score': round(total_book_score / len(episodes), 2) if episodes else 0,
                'top_episodes': sorted(
                    [e for e in analyzed_episodes if e['book_score'] > 0],
                    key=lambda x: x['book_score'],
                    reverse=True
                )[:10],
            }

            # Add to overall top episodes
            for episode_analysis in analyzed_episodes:
                if episode_analysis['book_score'] > 0:
                    results['top_book_episodes'].append({
                        'podcast': podcast_title,
                        **episode_analysis
                    })

        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")

    # Sort podcasts by book density
    results['podcasts_by_book_density'] = sorted(
        [
            {'podcast': k, **v}
            for k, v in results['podcasts'].items()
        ],
        key=lambda x: (x['book_density_pct'], x['episodes_with_books']),
        reverse=True
    )

    # Sort top episodes
    results['top_book_episodes'] = sorted(
        results['top_book_episodes'],
        key=lambda x: x['book_score'],
        reverse=True
    )[:50]  # Top 50 episodes overall

    return results

def print_report(results):
    """Print formatted analysis report."""
    print("=" * 80)
    print("📚 PODCAST GUEST & BOOK ANALYSIS REPORT")
    print("=" * 80)
    print()

    # Top podcasts by book density
    print("🏆 TOP PODCASTS BY BOOK MENTION DENSITY")
    print("-" * 80)
    for i, podcast in enumerate(results['podcasts_by_book_density'][:15], 1):
        print(f"{i:2d}. {podcast['podcast']}")
        print(f"    Episodes: {podcast['total_episodes']} | "
              f"Book Mentions: {podcast['episodes_with_books']} ({podcast['book_density_pct']}%) | "
              f"Guest Density: {podcast['guest_density_pct']}%")
        print(f"    Avg Book Score: {podcast['avg_book_score']}")
        print()

    print()
    print("=" * 80)
    print("🎯 TOP 20 EPISODES WITH BOOK INDICATORS")
    print("-" * 80)
    for i, episode in enumerate(results['top_book_episodes'][:20], 1):
        print(f"{i:2d}. {episode['podcast']}")
        print(f"    📻 {episode['title']}")
        if episode['guests']:
            print(f"    👤 Guests: {', '.join(episode['guests'])}")
        print(f"    📖 Book Score: {episode['book_score']} | Keywords: {', '.join(episode['book_keywords'][:3])}")
        print()

    print()
    print("=" * 80)
    print("📊 SUMMARY STATISTICS")
    print("-" * 80)
    total_episodes = sum(p['total_episodes'] for p in results['podcasts_by_book_density'])
    total_book_episodes = sum(p['episodes_with_books'] for p in results['podcasts_by_book_density'])
    print(f"Total Episodes Analyzed: {total_episodes:,}")
    print(f"Episodes with Book Mentions: {total_book_episodes:,} ({total_book_episodes/total_episodes*100:.1f}%)")
    print(f"Podcasts Analyzed: {len(results['podcasts'])}")
    print()

def save_detailed_report(results, output_file="podcast_book_analysis.json"):
    """Save detailed results to JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    import sys

    metadata_dir = sys.argv[1] if len(sys.argv) > 1 else "podcast_metadata"

    print("🔍 Analyzing podcast metadata for guests and book mentions...\n")
    results = analyze_all_metadata(metadata_dir)

    print_report(results)
    save_detailed_report(results)
