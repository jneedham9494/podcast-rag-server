"""
Metadata loading and processing for podcast transcripts.

Handles loading podcast metadata JSON files and extracting episode information.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


def load_podcast_metadata(metadata_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load all podcast metadata from JSON files in a directory.

    Args:
        metadata_dir: Directory containing podcast metadata JSON files

    Returns:
        Dictionary mapping podcast names to their metadata
    """
    metadata: Dict[str, Dict[str, Any]] = {}

    if not metadata_dir.exists():
        logger.warning(f"Metadata directory not found: {metadata_dir}")
        return metadata

    for json_file in metadata_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                podcast_name = json_file.stem
                metadata[podcast_name] = data
        except Exception as e:
            logger.warning(f"Could not load {json_file.name}: {e}")

    return metadata


def get_episode_metadata(
    podcast_metadata: Dict[str, Dict[str, Any]],
    podcast_name: str,
    episode_filename: str
) -> Dict[str, str]:
    """
    Extract episode metadata from podcast metadata.

    Matches episode by filename using exact or partial matching.

    Args:
        podcast_metadata: Loaded podcast metadata dictionary
        podcast_name: Name of the podcast
        episode_filename: Filename of the episode transcript

    Returns:
        Dictionary of episode metadata fields
    """
    if podcast_name not in podcast_metadata:
        return {}

    episode_stem = Path(episode_filename).stem
    podcast_data = podcast_metadata[podcast_name]
    episodes = podcast_data.get('episodes', [])

    for episode in episodes:
        episode_title = episode.get('title', '')

        # Try exact match first
        if episode_stem == episode_title:
            return extract_episode_fields(episode)

        # Try partial match (remove special characters)
        clean_stem = re.sub(r'[^\w\s]', '', episode_stem.lower())
        clean_title = re.sub(r'[^\w\s]', '', episode_title.lower())

        if clean_stem and clean_title and (
            clean_stem in clean_title or clean_title in clean_stem
        ):
            return extract_episode_fields(episode)

    return {}


def extract_episode_fields(episode: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract and format episode fields for indexing.

    Args:
        episode: Episode dictionary from metadata

    Returns:
        Formatted episode metadata
    """
    return {
        'title': episode.get('title', ''),
        'description': episode.get('description', '')[:500],  # Limit length
        'publish_date': episode.get('published', ''),
        'duration': str(episode.get('duration', '')),
        'link': episode.get('link', '')
    }


def load_detailed_transcript(
    transcript_dir: Path,
    episode_stem: str
) -> Optional[Dict[str, Any]]:
    """
    Load detailed Whisper transcript with timestamps.

    Args:
        transcript_dir: Directory containing the transcript
        episode_stem: Episode filename without extension

    Returns:
        Detailed transcript data or None if not found
    """
    detailed_file = transcript_dir / f"{episode_stem}_detailed.json"

    if not detailed_file.exists():
        return None

    try:
        with open(detailed_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load detailed transcript: {e}")
        return None


def find_chunk_timestamps(
    chunk_text: str,
    detailed_transcript: Optional[Dict[str, Any]]
) -> Tuple[float, float]:
    """
    Find start and end timestamps for a chunk by matching text to segments.

    Args:
        chunk_text: Text content of the chunk
        detailed_transcript: Detailed transcript with segments

    Returns:
        Tuple of (start_time, end_time) in seconds
    """
    if not detailed_transcript or 'segments' not in detailed_transcript:
        return (0.0, 0.0)

    segments = detailed_transcript['segments']

    # Find first segment that overlaps with chunk start
    chunk_words = chunk_text.split()[:10]  # First 10 words
    chunk_start_text = ' '.join(chunk_words).lower()

    start_time = 0.0
    end_time = 0.0
    found_start = False

    for segment in segments:
        segment_text = segment.get('text', '').lower().strip()

        if not found_start:
            # Look for chunk start
            if chunk_start_text[:50] in segment_text or segment_text in chunk_start_text:
                start_time = float(segment.get('start', 0))
                found_start = True

        if found_start:
            # Continue until we've covered the chunk length
            end_time = float(segment.get('end', 0))

            # Rough estimate: ~200 chars per second of speech
            if end_time - start_time > len(chunk_text) / 200:
                break

    return (start_time, end_time)


def format_timestamp(seconds: float) -> str:
    """
    Format seconds as MM:SS or HH:MM:SS.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    if seconds == 0:
        return "00:00"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
