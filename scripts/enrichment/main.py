#!/usr/bin/env python3
"""
Main enrichment function and CLI entry point.
"""

import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .config import KNOWN_SPEAKERS, TOPIC_TAXONOMY
from .entities import extract_entities_spacy, normalize_entities_ollama
from .hosts import detect_hosts_from_intro, detect_hosts_from_entities
from .keywords import extract_keywords
from .topics import (
    classify_topics_huggingface,
    classify_topics_ollama,
    extract_episode_date,
    detect_chapters_ollama,
)
from .diarization import diarize_audio, merge_diarization_with_transcript
from .llm_utils import generate_summary_ollama, classify_content_segments


def enrich_transcript(
    transcript_path: Path,
    audio_path: Optional[Path] = None,
    podcast_name: Optional[str] = None,
    skip_diarization: bool = False,
    skip_ollama: bool = False,
) -> Dict:
    """
    Main enrichment function - combines all enrichment methods.

    Args:
        transcript_path: Path to .txt transcript file
        audio_path: Path to audio file (for diarization)
        podcast_name: Name of podcast (for known speakers)
        skip_diarization: Skip speaker diarization
        skip_ollama: Skip Ollama-based enrichments

    Returns:
        Enriched metadata dictionary
    """
    print(f"\nEnriching: {transcript_path.name}")
    start_time = time.time()

    # Load transcript text
    transcript_text = transcript_path.read_text(encoding='utf-8')

    # Load detailed JSON if available (for timestamps)
    detailed_path = transcript_path.with_name(
        transcript_path.stem + '_detailed.json'
    )
    whisper_segments = []
    if detailed_path.exists():
        with open(detailed_path) as f:
            detailed = json.load(f)
            whisper_segments = detailed.get('segments', [])

    # Initialize enrichment data
    enrichment = {
        'source_file': transcript_path.name,
        'enrichment_version': '1.0',
        'enriched_at': datetime.now().isoformat(),
        'podcast_name': podcast_name,
    }

    # === TIER 1: Fast Local NLP ===
    print("  [1/7] Extracting entities with spaCy...")
    try:
        enrichment['entities'] = extract_entities_spacy(transcript_text)
        print(f"        Found {len(enrichment['entities']['people'])} people, "
              f"{len(enrichment['entities']['organizations'])} orgs, "
              f"{len(enrichment['entities']['locations'])} locations")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['entities'] = {}

    # === Dynamic host detection ===
    print("  [2/7] Detecting hosts from intro...")
    enrichment['detected_hosts'] = _detect_hosts(
        podcast_name, transcript_text, enrichment.get('entities', {})
    )

    print("  [3/7] Extracting keywords with KeyBERT...")
    try:
        enrichment['keywords'] = extract_keywords(transcript_text)
        print(f"        Found {len(enrichment['keywords'])} keywords")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['keywords'] = []

    # === TIER 2: Speaker Diarization ===
    enrichment['speaker_segments'] = _run_diarization(
        audio_path, podcast_name, whisper_segments, skip_diarization
    )

    # === TIER 3: LLM-based Enrichment ===
    if not skip_ollama:
        _run_ollama_enrichment(enrichment, transcript_text)
    else:
        _skip_ollama_enrichment(enrichment)

    # Keep known speakers as fallback reference
    if podcast_name and podcast_name in KNOWN_SPEAKERS:
        enrichment['known_speakers_reference'] = KNOWN_SPEAKERS[podcast_name]

    elapsed = time.time() - start_time
    print(f"\n  Enrichment complete in {elapsed:.1f}s")

    return enrichment


def _detect_hosts(
    podcast_name: Optional[str],
    transcript_text: str,
    entities: Dict
) -> Dict:
    """Detect hosts using multiple strategies."""
    try:
        # Priority 1: Use known speakers if available
        if podcast_name and podcast_name in KNOWN_SPEAKERS:
            result = {
                'hosts': KNOWN_SPEAKERS[podcast_name]['hosts'],
                'producer': KNOWN_SPEAKERS[podcast_name].get('producer'),
                'source': 'known_speakers'
            }
            print(f"        Using known hosts: {result['hosts']}")
            return result

        # Priority 2: Try intro detection
        detected_hosts = detect_hosts_from_intro(transcript_text)
        if detected_hosts and detected_hosts.get('hosts'):
            print(f"        Detected: {detected_hosts.get('hosts', [])}")
            return detected_hosts

        # Priority 3: Use entity frequency analysis
        if entities:
            freq_hosts = detect_hosts_from_entities(entities, transcript_text)
            if freq_hosts:
                result = {'hosts': freq_hosts, 'source': 'entity_frequency'}
                print(f"        Fallback (frequency): {freq_hosts}")
                return result

    except Exception as e:
        print(f"        ERROR: {e}")

    return {}


def _run_diarization(
    audio_path: Optional[Path],
    podcast_name: Optional[str],
    whisper_segments: list,
    skip_diarization: bool
) -> list:
    """Run speaker diarization if audio is available."""
    if audio_path and audio_path.exists() and not skip_diarization:
        print("  [4/7] Running speaker diarization...")
        try:
            # Determine number of speakers from known hosts
            num_speakers = None
            if podcast_name and podcast_name in KNOWN_SPEAKERS:
                num_speakers = len(KNOWN_SPEAKERS[podcast_name]['hosts'])

            diarization = diarize_audio(audio_path, num_speakers)

            if diarization and whisper_segments:
                enriched_segments = merge_diarization_with_transcript(
                    diarization, whisper_segments
                )
                speakers = set(s['speaker'] for s in enriched_segments)
                print(f"        Found {len(speakers)} speakers, "
                      f"{len(enriched_segments)} segments")
                return enriched_segments
        except Exception as e:
            print(f"        ERROR: {e}")
    else:
        print("  [4/7] Skipping diarization (no audio or disabled)")

    return []


def _run_ollama_enrichment(enrichment: Dict, transcript_text: str) -> None:
    """Run Ollama-based enrichments."""
    print("  [5/7] Generating summary with Ollama...")
    try:
        enrichment['summary'] = generate_summary_ollama(transcript_text)
        if enrichment['summary']:
            print(f"        Generated {len(enrichment['summary'])} char summary")
        else:
            print("        No summary generated")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['summary'] = ""

    print("  [6/7] Classifying topics & content structure...")
    try:
        # Extract episode year for context grounding
        episode_year = extract_episode_date(transcript_text)
        if episode_year:
            enrichment['episode_year'] = episode_year
            print(f"        Episode year detected: {episode_year}")

        # Try HuggingFace zero-shot for broad topics
        print("        Using HuggingFace zero-shot classification...")
        hf_topics = classify_topics_huggingface(transcript_text, TOPIC_TAXONOMY)
        if hf_topics:
            enrichment['topics_broad'] = hf_topics
            print(f"        Broad topics (HF): {hf_topics}")
        else:
            # Fallback to Ollama
            topic_result = classify_topics_ollama(
                transcript_text, TOPIC_TAXONOMY, episode_year=episode_year
            )
            enrichment['topics_broad'] = topic_result.get('broad', [])
            print(f"        Broad topics (Ollama): {enrichment['topics_broad']}")

        # Use Ollama for specific topics
        topic_result = classify_topics_ollama(
            transcript_text, TOPIC_TAXONOMY, episode_year=episode_year
        )
        enrichment['topics_specific'] = topic_result.get('specific', [])
        print(f"        Specific topics: {enrichment['topics_specific']}")

        # Classify content structure
        content_structure = classify_content_segments(transcript_text)
        if content_structure:
            enrichment['content_structure'] = content_structure
            intro_topics = content_structure.get('intro_topics', [])
            main_topics = content_structure.get('main_topics', [])
            print(f"        Intro banter: {intro_topics}")
            print(f"        Main content: {main_topics}")
        else:
            enrichment['content_structure'] = {}
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['topics_broad'] = []
        enrichment['topics_specific'] = []
        enrichment['content_structure'] = {}

    print("  [7/7] Normalizing entities & detecting chapters...")
    try:
        # Normalize entity variants
        if enrichment.get('entities'):
            enrichment['entities'] = normalize_entities_ollama(
                enrichment['entities']
            )
            if enrichment['entities'].get('entity_mapping'):
                mapping_count = len(enrichment['entities']['entity_mapping'])
                print(f"        Normalized {mapping_count} entity variants")

        # Chapter detection
        enrichment['chapters'] = detect_chapters_ollama(transcript_text)
        if enrichment['chapters']:
            print(f"        Detected {len(enrichment['chapters'])} chapters")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['chapters'] = []


def _skip_ollama_enrichment(enrichment: Dict) -> None:
    """Set empty values when Ollama is skipped."""
    print("  [5/7] Skipping Ollama summary (disabled)")
    print("  [6/7] Skipping Ollama topics (disabled)")
    print("  [7/7] Skipping entity normalization (disabled)")
    enrichment['summary'] = ""
    enrichment['topics_broad'] = []
    enrichment['topics_specific'] = []
    enrichment['content_structure'] = {}
    enrichment['chapters'] = []


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Enrich podcast transcript with metadata'
    )
    parser.add_argument('transcript', help='Path to transcript .txt file')
    parser.add_argument('--audio', help='Path to audio file for diarization')
    parser.add_argument('--podcast', help='Podcast name (for known speakers)')
    parser.add_argument(
        '--skip-diarization',
        action='store_true',
        help='Skip speaker diarization'
    )
    parser.add_argument(
        '--skip-ollama',
        action='store_true',
        help='Skip Ollama-based enrichment'
    )
    parser.add_argument('--output', help='Output path for enriched JSON')

    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        print(f"ERROR: Transcript not found: {transcript_path}")
        sys.exit(1)

    audio_path = Path(args.audio) if args.audio else None

    # Auto-detect podcast name from path
    podcast_name = args.podcast
    if not podcast_name:
        # Try to extract from path like transcripts/TRUE ANON/episode.txt
        parts = transcript_path.parts
        if 'transcripts' in parts:
            idx = parts.index('transcripts')
            if idx + 1 < len(parts):
                podcast_name = parts[idx + 1]

    # Run enrichment
    enrichment = enrich_transcript(
        transcript_path,
        audio_path=audio_path,
        podcast_name=podcast_name,
        skip_diarization=args.skip_diarization,
        skip_ollama=args.skip_ollama,
    )

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = transcript_path.with_name(
            transcript_path.stem + '_enriched.json'
        )

    # Atomic write: write to temp file first, then rename
    temp_fd, temp_path = tempfile.mkstemp(
        suffix='.json',
        dir=output_path.parent,
        prefix='.enriching_'
    )
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(enrichment, f, indent=2)
        # Atomic rename (on same filesystem)
        os.rename(temp_path, output_path)
        print(f"\nSaved enrichment to: {output_path}")
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

    # Print summary
    _print_summary(enrichment)


def _print_summary(enrichment: Dict) -> None:
    """Print enrichment summary."""
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)

    # Hosts
    hosts = enrichment.get('detected_hosts', {})
    if hosts.get('hosts'):
        print(f"Detected Hosts: {hosts['hosts']}")

    # Entities
    entities = enrichment.get('entities', {})
    entity_count = sum(
        len(v) for k, v in entities.items() if k != 'entity_mapping'
    )
    print(f"Entities: {entity_count} total")
    if entities.get('entity_mapping'):
        print(f"  Normalized variants: {len(entities['entity_mapping'])}")

    # Keywords
    print(f"Keywords: {len(enrichment.get('keywords', []))}")

    # Topics
    print(f"Broad Topics: {enrichment.get('topics_broad', [])}")
    print(f"Specific Topics: {enrichment.get('topics_specific', [])}")

    # Content structure
    content = enrichment.get('content_structure', {})
    if content:
        print("Content Structure:")
        if content.get('intro_topics'):
            print(f"  Intro banter: {content['intro_topics']}")
        if content.get('main_topics'):
            print(f"  Main content: {content['main_topics']}")
        if content.get('tangents'):
            print(f"  Tangents: {content['tangents']}")

    # Other
    print(f"Speaker segments: {len(enrichment.get('speaker_segments', []))}")
    print(f"Chapters: {len(enrichment.get('chapters', []))}")

    if enrichment.get('summary'):
        print(f"Summary: {enrichment['summary'][:200]}...")


if __name__ == '__main__':
    main()
