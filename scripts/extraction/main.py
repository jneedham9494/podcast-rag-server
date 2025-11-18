#!/usr/bin/env python3
"""
Main entry point for guest and Twitter extraction.

Orchestrates extraction from all podcast metadata files.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

from .episode_detector import is_non_guest_episode
from .name_cleaner import clean_guest_name
from .twitter_finder import extract_twitter_handles
from .title_extractor import extract_guest_from_title
from .description_extractor import extract_guest_from_description


def extract_guests_with_twitter() -> None:
    """
    Extract guests and Twitter handles from all podcast metadata.

    Reads metadata from podcast_metadata/ directory and outputs
    a comprehensive guest directory to guest_directory_complete.json.
    """
    metadata_dir = Path("podcast_metadata")
    if not metadata_dir.exists():
        print("podcast_metadata directory not found")
        return

    guests = defaultdict(lambda: {
        'appearances': 0,
        'podcasts': set(),
        'episodes': [],
        'twitter_handles': set(),
        'twitter_from_metadata': False
    })

    stats = _ExtractionStats()

    for metadata_file in sorted(metadata_dir.glob("*.json")):
        podcast_name = metadata_file.stem
        print(f"\nProcessing: {podcast_name}")

        try:
            podcast_stats = _process_podcast(
                metadata_file, podcast_name, guests, stats
            )
            _print_podcast_stats(podcast_name, podcast_stats)
        except Exception as e:
            print(f"  Error: {e}")

    _print_summary(stats, guests)
    _save_results(guests, stats)


class _ExtractionStats:
    """Track extraction statistics."""

    def __init__(self):
        self.total_episodes = 0
        self.total_extracted = 0
        self.total_twitter_handles = 0
        self.total_non_guest_episodes = 0
        self.non_guest_by_type: Dict[str, int] = defaultdict(int)
        self.podcast_stats: Dict[str, Dict[str, Any]] = {}


def _process_podcast(
    metadata_file: Path,
    podcast_name: str,
    guests: Dict,
    stats: _ExtractionStats
) -> Dict[str, Any]:
    """
    Process a single podcast's metadata.

    Args:
        metadata_file: Path to podcast metadata JSON
        podcast_name: Name of the podcast
        guests: Guest dictionary to update
        stats: Statistics tracker

    Returns:
        Dictionary of podcast-specific stats
    """
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    episodes = metadata.get('episodes', [])
    episode_count = len(episodes)
    extracted_count = 0
    twitter_count = 0
    non_guest_count = 0

    for episode in episodes:
        title = episode.get('title', '')
        description = episode.get('description', '')
        stats.total_episodes += 1

        # Check if non-guest episode
        is_non_guest, episode_type = is_non_guest_episode(
            title, description, podcast_name
        )

        if is_non_guest:
            non_guest_count += 1
            stats.total_non_guest_episodes += 1
            stats.non_guest_by_type[episode_type] += 1
            continue

        # Extract guest
        guest_name = _extract_guest(
            title, description, podcast_name
        )

        # Extract Twitter handles
        twitter_handles = extract_twitter_handles(title + ' ' + description)

        if guest_name:
            guest_name = clean_guest_name(guest_name)

            if guest_name:
                guests[guest_name]['appearances'] += 1
                guests[guest_name]['podcasts'].add(podcast_name)
                guests[guest_name]['episodes'].append({
                    'title': title,
                    'podcast': podcast_name
                })

                if twitter_handles:
                    for handle in twitter_handles:
                        guests[guest_name]['twitter_handles'].add(handle)
                        guests[guest_name]['twitter_from_metadata'] = True
                    twitter_count += len(twitter_handles)

                extracted_count += 1
                stats.total_extracted += 1

    stats.total_twitter_handles += twitter_count

    guest_episodes = episode_count - non_guest_count
    extraction_rate = (
        (extracted_count / guest_episodes * 100)
        if guest_episodes > 0 else 0
    )

    podcast_stats = {
        'total': episode_count,
        'extracted': extracted_count,
        'non_guest': non_guest_count,
        'guest_episodes': guest_episodes,
        'missing': guest_episodes - extracted_count,
        'extraction_rate': extraction_rate,
        'twitter_count': twitter_count
    }

    stats.podcast_stats[podcast_name] = podcast_stats
    return podcast_stats


def _extract_guest(
    title: str,
    description: str,
    podcast_name: str
) -> str:
    """
    Extract guest name from title and description.

    For Chapo, prefers title (feat. format is reliable).
    For others, prefers description (more complete).

    Args:
        title: Episode title
        description: Episode description
        podcast_name: Name of the podcast

    Returns:
        Extracted guest name or None
    """
    guest_from_desc = extract_guest_from_description(description, podcast_name)
    guest_from_title = extract_guest_from_title(title, podcast_name)

    if 'chapo' in podcast_name.lower():
        return guest_from_title if guest_from_title else guest_from_desc
    else:
        return guest_from_desc if guest_from_desc else guest_from_title


def _print_podcast_stats(podcast_name: str, stats: Dict[str, Any]) -> None:
    """Print statistics for a single podcast."""
    print(
        f"  Extracted {stats['extracted']} guests, "
        f"{stats['non_guest']} non-guest episodes "
        f"({stats['extraction_rate']:.1f}% of guest episodes), "
        f"{stats['twitter_count']} Twitter handles"
    )


def _print_summary(stats: _ExtractionStats, guests: Dict) -> None:
    """Print overall extraction summary."""
    total_guest_episodes = stats.total_episodes - stats.total_non_guest_episodes

    print(f"\nTotal: {stats.total_extracted} guest appearances "
          f"from {stats.total_episodes} episodes")
    print(f"Non-guest episodes: {stats.total_non_guest_episodes} "
          f"(compilations, trailers, etc.)")
    print(f"Guest episodes: {total_guest_episodes}")

    overall_rate = (
        (stats.total_extracted / total_guest_episodes * 100)
        if total_guest_episodes > 0 else 0
    )
    print(f"Overall extraction rate: {overall_rate:.1f}% of guest episodes")
    print(f"Unique guests: {len(guests)}")
    print(f"Twitter handles found: {stats.total_twitter_handles}")

    # Non-guest episode breakdown
    if stats.total_non_guest_episodes > 0:
        print(f"\nNon-Guest Episode Breakdown:")
        sorted_types = sorted(
            stats.non_guest_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for episode_type, count in sorted_types:
            print(f"   {episode_type}: {count} episodes")

    # Top extraction rates
    print(f"\nTop Extraction Rates (Guest Episodes Only):")
    sorted_podcasts = sorted(
        stats.podcast_stats.items(),
        key=lambda x: x[1]['extraction_rate'],
        reverse=True
    )
    for podcast_name, pstats in sorted_podcasts[:10]:
        if pstats['guest_episodes'] > 0:
            print(
                f"   {podcast_name}: {pstats['extraction_rate']:.1f}% "
                f"({pstats['extracted']}/{pstats['guest_episodes']} guest episodes, "
                f"{pstats['non_guest']} non-guest)"
            )

    # Podcasts with most missing
    print(f"\nPodcasts with Most Missing Guest Episodes:")
    sorted_missing = sorted(
        stats.podcast_stats.items(),
        key=lambda x: x[1]['missing'],
        reverse=True
    )
    for podcast_name, pstats in sorted_missing[:5]:
        if pstats['missing'] > 0 and pstats['guest_episodes'] > 10:
            print(
                f"   {podcast_name}: {pstats['missing']} missing "
                f"({pstats['extraction_rate']:.1f}% of "
                f"{pstats['guest_episodes']} guest episodes)"
            )


def _save_results(guests: Dict, stats: _ExtractionStats) -> None:
    """Save extraction results to JSON file."""
    guests_list: List[Dict[str, Any]] = []
    metadata_twitter_count = 0

    for name, data in guests.items():
        guest_entry = {
            'name': name,
            'appearances': data['appearances'],
            'podcasts': sorted(list(data['podcasts'])),
            'episodes': data['episodes']
        }

        if data['twitter_handles']:
            handles_list = list(data['twitter_handles'])
            guest_entry['twitter'] = {
                'potential_handles': handles_list,
                'verified': False,
                'from_metadata': True
            }
            metadata_twitter_count += 1

        guests_list.append(guest_entry)

    guests_list.sort(key=lambda x: x['appearances'], reverse=True)

    output = {
        'total_guests': len(guests_list),
        'total_episodes': stats.total_episodes,
        'guests_with_twitter_from_metadata': metadata_twitter_count,
        'guests': guests_list
    }

    with open('guest_directory_complete.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to guest_directory_complete.json")
    print(f"Guests with Twitter handles from metadata: {metadata_twitter_count}")

    # Show sample guests with Twitter
    print(f"\nSample guests with Twitter handles from metadata:")
    count = 0
    for guest in guests_list:
        if guest.get('twitter', {}).get('from_metadata'):
            handles = guest['twitter']['potential_handles']
            print(f"  {guest['name']}: @{', @'.join(handles)}")
            count += 1
            if count >= 15:
                break


if __name__ == "__main__":
    extract_guests_with_twitter()
