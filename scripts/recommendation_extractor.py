#!/usr/bin/env python3
"""
Recommendation Extractor
Extracts book, movie, and music recommendations from podcast transcripts
"""

import json
import re
from pathlib import Path
import sys
from collections import defaultdict


# Patterns for detecting recommendations
BOOK_PATTERNS = [
    r'(?:book|novel|memoir|biography|read(?:ing)?)\s+(?:called|titled|named)?\s*["\']([^"\']+)["\']',
    r'["\']([^"\']+)["\']\s+(?:by|written by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'(?:read|reading)\s+([A-Z][^.!?]{5,50})\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'the book\s+["\']?([^"\'\.!?]{5,50})["\']?',
]

MOVIE_PATTERNS = [
    r'(?:film|movie|documentary)\s+(?:called|titled|named)?\s*["\']([^"\']+)["\']',
    r'["\']([^"\']+)["\']\s+(?:the\s+)?(?:film|movie)',
    r'(?:watched|saw|seen)\s+["\']([^"\']+)["\']',
]

MUSIC_PATTERNS = [
    r'(?:album|song|track|record)\s+(?:called|titled|named)?\s*["\']([^"\']+)["\']',
    r'["\']([^"\']+)["\']\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    r'(?:listening to|listened to)\s+["\']?([^"\'\.!?]{5,50})["\']?',
    r'the (?:band|artist|musician)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
]


def extract_with_context(text, patterns, context_size=100):
    """
    Extract matches with surrounding context

    Args:
        text: Full text to search
        patterns: List of regex patterns
        context_size: Number of characters to include before/after match

    Returns:
        List of (match, context) tuples
    """
    findings = []

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Get the matched text
            matched_text = match.group(1) if match.groups() else match.group(0)

            # Get context
            start = max(0, match.start() - context_size)
            end = min(len(text), match.end() + context_size)
            context = text[start:end].strip()

            findings.append({
                'text': matched_text.strip(),
                'context': context,
                'position': match.start()
            })

    # Remove duplicates while preserving order
    seen = set()
    unique_findings = []
    for f in findings:
        text_lower = f['text'].lower()
        if text_lower not in seen and len(f['text']) > 3:
            seen.add(text_lower)
            unique_findings.append(f)

    return unique_findings


def extract_recommendations(transcript_file):
    """
    Extract book, movie, and music recommendations from a transcript

    Args:
        transcript_file: Path to transcript text file

    Returns:
        Dictionary with books, movies, and music lists
    """
    transcript_path = Path(transcript_file)

    if not transcript_path.exists():
        print(f"✗ Transcript file not found: {transcript_file}")
        return None

    print(f"\nAnalyzing: {transcript_path.name}")

    with open(transcript_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract recommendations
    books = extract_with_context(text, BOOK_PATTERNS)
    movies = extract_with_context(text, MOVIE_PATTERNS)
    music = extract_with_context(text, MUSIC_PATTERNS)

    results = {
        'transcript': str(transcript_path),
        'books': books,
        'movies': movies,
        'music': music,
        'total': len(books) + len(movies) + len(music)
    }

    return results


def save_recommendations(results, output_file):
    """Save recommendations to JSON file"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved recommendations: {output_path}")


def print_recommendations(results):
    """Pretty print recommendations"""
    print("\n" + "=" * 80)
    print(f"RECOMMENDATIONS FROM: {Path(results['transcript']).name}")
    print("=" * 80)

    print(f"\n📚 BOOKS ({len(results['books'])})")
    print("-" * 80)
    for i, book in enumerate(results['books'], 1):
        print(f"\n{i}. {book['text']}")
        print(f"   Context: ...{book['context']}...")

    print(f"\n🎬 MOVIES/FILMS ({len(results['movies'])})")
    print("-" * 80)
    for i, movie in enumerate(results['movies'], 1):
        print(f"\n{i}. {movie['text']}")
        print(f"   Context: ...{movie['context']}...")

    print(f"\n🎵 MUSIC ({len(results['music'])})")
    print("-" * 80)
    for i, music in enumerate(results['music'], 1):
        print(f"\n{i}. {music['text']}")
        print(f"   Context: ...{music['context']}...")

    print("\n" + "=" * 80)
    print(f"Total recommendations found: {results['total']}")
    print("=" * 80)


def process_directory(directory, output_file="all_recommendations.json"):
    """Process all transcripts in a directory"""
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"✗ Directory not found: {directory}")
        return

    transcript_files = list(dir_path.glob("**/*.txt"))
    transcript_files = [f for f in transcript_files if not f.name.endswith('_detailed.json')]

    if not transcript_files:
        print(f"✗ No transcript files found in {directory}")
        return

    print(f"Found {len(transcript_files)} transcript files")
    print("=" * 80)

    all_results = []
    aggregate = defaultdict(list)

    for i, transcript_file in enumerate(transcript_files, 1):
        print(f"\n[{i}/{len(transcript_files)}]")
        results = extract_recommendations(transcript_file)

        if results:
            all_results.append(results)

            # Aggregate unique recommendations
            for book in results['books']:
                if book not in aggregate['books']:
                    aggregate['books'].append(book)

            for movie in results['movies']:
                if movie not in aggregate['movies']:
                    aggregate['movies'].append(movie)

            for music in results['music']:
                if music not in aggregate['music']:
                    aggregate['music'].append(music)

            # Save individual results
            output_dir = Path("recommendations")
            output_dir.mkdir(exist_ok=True)
            individual_file = output_dir / f"{transcript_file.stem}_recommendations.json"
            save_recommendations(results, individual_file)

    # Save aggregate results
    aggregate_results = {
        'total_transcripts': len(all_results),
        'books': aggregate['books'],
        'movies': aggregate['movies'],
        'music': aggregate['music'],
        'total_recommendations': len(aggregate['books']) + len(aggregate['movies']) + len(aggregate['music'])
    }

    save_recommendations(aggregate_results, output_file)

    print("\n" + "=" * 80)
    print(f"✓ Processing complete!")
    print(f"  Transcripts analyzed: {len(all_results)}")
    print(f"  Total books found: {len(aggregate['books'])}")
    print(f"  Total movies found: {len(aggregate['movies'])}")
    print(f"  Total music found: {len(aggregate['music'])}")
    print(f"  Aggregate file: {output_file}")
    print("=" * 80)


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file: python recommendation_extractor.py <transcript_file>")
        print("  Directory:   python recommendation_extractor.py <transcript_directory>")
        print("\nExamples:")
        print("  python recommendation_extractor.py transcripts/The_Louis_Theroux_Podcast/episode.txt")
        print("  python recommendation_extractor.py transcripts/")
        return

    path = sys.argv[1]
    path_obj = Path(path)

    if path_obj.is_file():
        results = extract_recommendations(path)
        if results:
            print_recommendations(results)

            # Save to file
            output_file = f"recommendations/{path_obj.stem}_recommendations.json"
            save_recommendations(results, output_file)

    elif path_obj.is_dir():
        process_directory(path)
    else:
        print(f"✗ Path not found: {path}")


if __name__ == "__main__":
    main()
