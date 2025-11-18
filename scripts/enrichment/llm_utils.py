"""
LLM-based utilities for transcript enrichment using Ollama.
"""

import subprocess
from typing import Dict

from .json_utils import parse_json_safely


def generate_summary_ollama(text: str, model: str = "llama3:8b") -> str:
    """
    Generate episode summary using Ollama.

    Args:
        text: Transcript text
        model: Ollama model to use

    Returns:
        Episode summary string
    """
    # Truncate text to fit context window
    max_chars = 12000  # ~3000 tokens
    if len(text) > max_chars:
        half = max_chars // 2
        truncated = text[:half] + "\n\n[...]\n\n" + text[-half:]
    else:
        truncated = text

    prompt = f"""Summarize this podcast episode transcript in 2-3 sentences. Focus on the main topics discussed and key points made.

Transcript:
{truncated}

Summary:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"  WARNING: Ollama summary failed: {e}")
        return ""


def classify_content_segments(text: str, model: str = "llama3:8b") -> Dict:
    """
    Classify transcript into content types.

    Identifies: intro_banter, main_content, tangent, outro

    Args:
        text: Transcript text
        model: Ollama model to use

    Returns:
        Dictionary with content structure analysis
    """
    # Sample from different parts of transcript
    total_len = len(text)
    intro = text[:3000]
    middle = text[total_len // 3:total_len // 3 + 4000]
    end = text[-2000:]

    prompt = f"""Analyze this podcast transcript and identify the content structure.

INTRO (first part):
{intro}

MIDDLE (main content):
{middle}

OUTRO (end):
{end}

Return a JSON object describing:
1. "intro_topics" - casual/banter topics in the intro (if any)
2. "main_topics" - the primary subjects of the episode
3. "tangents" - off-topic diversions (if any)
4. "has_ads" - true/false if there are ad reads
5. "estimated_intro_length" - "short" (<5min), "medium" (5-15min), or "long" (>15min)

Return ONLY JSON:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90
        )

        response = result.stdout.strip()
        return parse_json_safely(response, default={})
    except Exception as e:
        print(f"  WARNING: Content classification failed: {e}")

    return {}
