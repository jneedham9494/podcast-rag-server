#!/usr/bin/env python3
"""
CLI entry point for enhanced RAG index builder.

Usage:
    python -m scripts.rag.main [--fast] [--db-path PATH]
"""

import argparse
import sys
from pathlib import Path

from loguru import logger

from .indexer import EnhancedTranscriptIndexer


def main() -> int:
    """
    Build enhanced RAG index from podcast transcripts.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description='Enhanced RAG index builder for podcast transcripts'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Use faster/smaller model (all-MiniLM-L6-v2)'
    )
    parser.add_argument(
        '--db-path',
        default='rag_db_v2',
        help='Path to ChromaDB directory (default: rag_db_v2)'
    )
    parser.add_argument(
        '--transcripts',
        default='transcripts',
        help='Path to transcripts directory (default: transcripts)'
    )
    parser.add_argument(
        '--metadata',
        default='podcast_metadata',
        help='Path to metadata directory (default: podcast_metadata)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Target characters per chunk (default: 1000)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Characters to overlap between chunks (default: 200)'
    )

    args = parser.parse_args()

    # Configuration
    transcripts_dir = Path(args.transcripts)
    metadata_dir = Path(args.metadata)
    db_path = Path(args.db_path)

    # Validate directories
    if not transcripts_dir.exists():
        logger.error(f"Transcripts directory not found: {transcripts_dir}")
        logger.error("Please run this script from the project root directory")
        return 1

    # Create indexer and build index
    try:
        indexer = EnhancedTranscriptIndexer(
            transcripts_dir=transcripts_dir,
            metadata_dir=metadata_dir,
            db_path=db_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            use_better_model=not args.fast
        )

        stats = indexer.index_all_transcripts()

        if stats['chunks'] == 0:
            logger.warning("No chunks were indexed")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
