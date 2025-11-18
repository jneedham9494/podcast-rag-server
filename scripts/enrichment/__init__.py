"""
Enrichment package for podcast transcript semantic metadata.

Adds semantic metadata to transcripts for better RAG search:
- Named Entity Recognition (people, orgs, places)
- Keyword/keyphrase extraction
- Speaker diarization
- Topic classification
- Episode summaries
- Conversation segmentation
"""

from .json_utils import repair_json, parse_json_safely
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
from .main import enrich_transcript

__all__ = [
    'repair_json',
    'parse_json_safely',
    'KNOWN_SPEAKERS',
    'TOPIC_TAXONOMY',
    'extract_entities_spacy',
    'normalize_entities_ollama',
    'detect_hosts_from_intro',
    'detect_hosts_from_entities',
    'extract_keywords',
    'classify_topics_huggingface',
    'classify_topics_ollama',
    'extract_episode_date',
    'detect_chapters_ollama',
    'diarize_audio',
    'merge_diarization_with_transcript',
    'generate_summary_ollama',
    'classify_content_segments',
    'enrich_transcript',
]
