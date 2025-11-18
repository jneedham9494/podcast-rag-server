"""
RAG (Retrieval-Augmented Generation) indexing package.

Provides utilities for building semantic search indexes from podcast transcripts.
"""

from .chunking import chunk_text_sentence_aware, split_into_sentences
from .indexer import EnhancedTranscriptIndexer
from .metadata import (
    extract_episode_fields,
    find_chunk_timestamps,
    format_timestamp,
    get_episode_metadata,
    load_detailed_transcript,
    load_podcast_metadata,
)

__all__ = [
    # Chunking
    'split_into_sentences',
    'chunk_text_sentence_aware',
    # Indexer
    'EnhancedTranscriptIndexer',
    # Metadata
    'load_podcast_metadata',
    'get_episode_metadata',
    'extract_episode_fields',
    'load_detailed_transcript',
    'find_chunk_timestamps',
    'format_timestamp',
]
