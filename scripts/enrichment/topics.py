"""
Topic classification utilities for podcast transcripts.
"""

import re
import subprocess
from collections import Counter
from typing import Dict, List, Optional


def classify_topics_huggingface(text: str, topics: List[str]) -> List[str]:
    """
    Use HuggingFace zero-shot classification for topic labeling.

    More reliable than LLM-based classification for predefined categories.

    Args:
        text: Transcript text
        topics: List of candidate topic labels

    Returns:
        List of classified topics
    """
    try:
        from transformers import pipeline
    except ImportError:
        print("  WARNING: transformers not installed, skipping HuggingFace")
        return []

    # Initialize zero-shot classifier (cached after first load)
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1  # CPU, use 0 for GPU
    )

    # Sample text for classification
    max_chars = 10000
    if len(text) > max_chars:
        half = max_chars // 2
        sample = text[:half] + "\n\n" + text[-half:]
    else:
        sample = text

    # Run classification
    result = classifier(
        sample,
        candidate_labels=topics,
        multi_label=True
    )

    # Return topics with score > 0.25
    classified = []
    for label, score in zip(result['labels'], result['scores']):
        if score > 0.25:
            classified.append(label)
        if len(classified) >= 5:  # Maximum 5 broad topics
            break

    # If less than 2 topics, include top 2 regardless of score
    if len(classified) < 2:
        classified = result['labels'][:2]

    return classified


def extract_episode_date(text: str) -> Optional[str]:
    """
    Try to extract episode date/year from transcript for context grounding.

    Args:
        text: Transcript text

    Returns:
        Year string or None
    """
    # Look for year mentions in first part of transcript
    intro = text[:5000]

    # Common patterns: "January 2020", "2019", "this week in November"
    year_pattern = r'\b(20\d{2}|19\d{2})\b'
    years = re.findall(year_pattern, intro)

    if years:
        # Return most common year mentioned
        year_counts = Counter(years)
        return year_counts.most_common(1)[0][0]

    return None


def classify_topics_ollama(
    text: str,
    topics: List[str],
    model: str = "llama3:8b",
    episode_year: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Classify episode into topics using Ollama.

    Returns both broad and specific topics.

    Args:
        text: Transcript text
        topics: List of broad topic categories
        model: Ollama model to use
        episode_year: Year for context grounding

    Returns:
        Dictionary with 'broad' and 'specific' topic lists
    """
    # Truncate text
    max_chars = 8000
    if len(text) > max_chars:
        half = max_chars // 2
        truncated = text[:half] + "\n\n[...]\n\n" + text[-half:]
    else:
        truncated = text

    topic_list = "\n".join(f"- {t}" for t in topics)

    # Get broad categories
    prompt_broad = f"""Based on this podcast transcript, select the 2-4 most relevant broad topics from this list.
Return ONLY the topic names, one per line, no explanations.

Available topics:
{topic_list}

Transcript excerpt:
{truncated}

Selected topics:"""

    broad_topics = []
    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt_broad,
            capture_output=True,
            text=True,
            timeout=60
        )

        response = result.stdout.strip()
        for line in response.split('\n'):
            line = line.strip().strip('-').strip()
            for topic in topics:
                if topic.lower() in line.lower() or line.lower() in topic.lower():
                    if topic not in broad_topics:
                        broad_topics.append(topic)
        broad_topics = broad_topics[:4]
    except Exception as e:
        print(f"  WARNING: Ollama broad topic classification failed: {e}")

    # Get specific/detailed topics
    year_constraint = ""
    if episode_year:
        year_constraint = (
            f"\nIMPORTANT: This episode was recorded in {episode_year}. "
            f"Only mention events/topics that existed in or before {episode_year}. "
            "Do NOT reference future events."
        )

    prompt_specific = f"""Based on this podcast transcript, list 5-8 SPECIFIC topics, events, or subjects discussed.
Be specific - instead of "Politics" say "Obama administration policy" or "2016 election coverage".
Instead of "Technology" say "YouTube algorithm changes" or "iPhone launch".
{year_constraint}

Return only the specific topics, one per line, no explanations or numbering.

Transcript excerpt:
{truncated}

Specific topics discussed:"""

    specific_topics = []
    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt_specific,
            capture_output=True,
            text=True,
            timeout=60
        )

        for line in result.stdout.strip().split('\n'):
            # Clean up formatting
            line = line.strip()
            line = line.strip('-*•').strip()
            line = line.strip('0123456789.').strip()
            line = line.strip('"\'').strip()

            # Skip preamble/instruction-like lines
            skip_phrases = [
                'here are', 'specific topics', 'transcript:', 'discussed:'
            ]
            if any(skip in line.lower() for skip in skip_phrases):
                continue

            if line and 5 < len(line) < 100:
                specific_topics.append(line)
        specific_topics = specific_topics[:8]
    except Exception as e:
        print(f"  WARNING: Ollama specific topic extraction failed: {e}")

    return {
        'broad': broad_topics,
        'specific': specific_topics
    }


def detect_chapters_ollama(text: str, model: str = "llama3:8b") -> List[str]:
    """
    Detect natural topic breaks/chapters in the transcript.

    Args:
        text: Transcript text
        model: Ollama model to use

    Returns:
        List of chapter titles
    """
    # For long transcripts, just identify major sections
    max_chars = 10000
    if len(text) > max_chars:
        truncated = text[:max_chars]
    else:
        truncated = text

    prompt = f"""Identify 3-6 main topic sections in this podcast transcript.
For each section, provide a short title (3-5 words).
Return ONLY the section titles, one per line.

Transcript:
{truncated}

Section titles:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )

        chapters = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            line = line.strip('-*•').strip()
            line = line.strip('0123456789.').strip()
            line = line.strip('"\'').strip()

            # Skip preamble lines
            skip_phrases = [
                'here are', 'section titles', 'sections:', 'chapters:'
            ]
            if any(skip in line.lower() for skip in skip_phrases):
                continue

            if line and 3 < len(line) < 100:
                chapters.append(line)

        return chapters[:6]
    except Exception as e:
        print(f"  WARNING: Ollama chapter detection failed: {e}")
        return []
