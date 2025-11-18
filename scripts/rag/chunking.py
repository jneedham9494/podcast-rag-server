"""
Text chunking utilities for RAG indexing.

Provides sentence-aware chunking to improve semantic coherence.
"""

import re
from typing import List


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Uses simple regex-based splitting on sentence-ending punctuation.

    Args:
        text: Input text to split

    Returns:
        List of sentence strings
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text_sentence_aware(
    text: str,
    chunk_size: int = 1000,
    overlap_sentences: int = 3
) -> List[str]:
    """
    Chunk text while respecting sentence boundaries.

    Builds chunks from complete sentences rather than splitting mid-sentence.
    Provides overlap between chunks for better context preservation.

    Args:
        text: Input text to chunk
        chunk_size: Target characters per chunk
        overlap_sentences: Number of sentences to overlap between chunks

    Returns:
        List of text chunks
    """
    sentences = split_into_sentences(text)
    chunks: List[str] = []
    current_chunk = ""
    recent_sentences: List[str] = []

    for sentence in sentences:
        # Would adding this sentence exceed chunk size?
        if current_chunk and len(current_chunk) + len(sentence) > chunk_size:
            # Save current chunk
            chunks.append(current_chunk.strip())

            # Start new chunk with overlap from recent sentences
            overlap_text = ' '.join(recent_sentences[-overlap_sentences:]) if recent_sentences else ""
            current_chunk = overlap_text + (' ' if overlap_text else '') + sentence
            recent_sentences = [sentence]
        else:
            # Add sentence to current chunk
            current_chunk += (' ' if current_chunk else '') + sentence
            recent_sentences.append(sentence)

    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
