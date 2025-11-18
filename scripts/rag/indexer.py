"""
Enhanced RAG indexer for podcast transcripts.

Provides sentence-aware chunking with episode metadata and timestamps.
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from loguru import logger
from sentence_transformers import SentenceTransformer

from .chunking import chunk_text_sentence_aware
from .metadata import (
    find_chunk_timestamps,
    format_timestamp,
    get_episode_metadata,
    load_detailed_transcript,
    load_podcast_metadata,
)


class EnhancedTranscriptIndexer:
    """
    Indexer for podcast transcripts with enhanced metadata and timestamps.

    Features:
    - Sentence-aware chunking for better semantic coherence
    - Episode metadata (dates, descriptions, duration)
    - Timestamps from detailed Whisper transcripts
    - High-quality embeddings with sentence-transformers
    """

    def __init__(
        self,
        transcripts_dir: Path,
        metadata_dir: Path,
        db_path: Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_better_model: bool = True
    ):
        """
        Initialize enhanced indexer.

        Args:
            transcripts_dir: Directory containing transcript files
            metadata_dir: Directory containing podcast metadata JSON files
            db_path: Path to ChromaDB persistent storage
            chunk_size: Target characters per chunk
            chunk_overlap: Characters to overlap between chunks
            use_better_model: Use all-mpnet-base-v2 (better) vs all-MiniLM-L6-v2 (faster)
        """
        self.transcripts_dir = transcripts_dir
        self.metadata_dir = metadata_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collection
        collection_name = "podcast_transcripts_v2"
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Enhanced podcast transcripts with metadata and timestamps"}
        )

        # Initialize embedding model
        model_name = 'all-mpnet-base-v2' if use_better_model else 'all-MiniLM-L6-v2'
        logger.info(f"Loading embedding model: {model_name}")
        if use_better_model:
            logger.info("Using better quality model (2x larger embeddings)")
        self.model = SentenceTransformer(model_name)
        logger.info(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        # Load podcast metadata
        logger.info("Loading podcast metadata...")
        self.podcast_metadata = load_podcast_metadata(metadata_dir)
        logger.info(f"Loaded metadata for {len(self.podcast_metadata)} podcasts")

    def _generate_chunk_id(
        self,
        podcast_name: str,
        episode_filename: str,
        chunk_idx: int
    ) -> str:
        """Generate unique ID for a chunk."""
        content = f"{podcast_name}::{episode_filename}::{chunk_idx}"
        return hashlib.md5(content.encode()).hexdigest()

    def index_transcript(self, transcript_file: Path) -> int:
        """
        Index a single transcript file with enhanced metadata.

        Args:
            transcript_file: Path to the transcript file

        Returns:
            Number of chunks created
        """
        podcast_name = transcript_file.parent.name
        episode_filename = transcript_file.name
        episode_stem = transcript_file.stem

        # Read transcript
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading {transcript_file}: {e}")
            return 0

        if not text.strip():
            logger.debug(f"Skipping empty transcript: {episode_filename}")
            return 0

        # Chunk with sentence awareness
        chunks = chunk_text_sentence_aware(text, self.chunk_size)

        if not chunks:
            logger.debug(f"No chunks generated for: {episode_filename}")
            return 0

        # Get episode metadata
        episode_meta = get_episode_metadata(
            self.podcast_metadata, podcast_name, episode_filename
        )

        # Load detailed transcript for timestamps
        transcript_dir = self.transcripts_dir / podcast_name
        detailed_transcript = load_detailed_transcript(transcript_dir, episode_stem)

        # Prepare batch data
        chunk_ids: List[str] = []
        chunk_texts: List[str] = []
        chunk_metadata: List[Dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(podcast_name, episode_filename, idx)

            # Check if already indexed
            try:
                existing = self.collection.get(ids=[chunk_id])
                if existing and existing['ids']:
                    continue  # Skip already indexed chunk
            except Exception:
                pass

            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk)

            # Build metadata
            metadata: Dict[str, Any] = {
                'podcast_name': podcast_name,
                'episode_filename': episode_filename,
                'chunk_index': idx,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk)
            }

            # Add episode metadata
            if episode_meta:
                metadata.update({
                    'episode_title': episode_meta.get('title', ''),
                    'episode_description': episode_meta.get('description', ''),
                    'publish_date': episode_meta.get('publish_date', ''),
                    'duration': episode_meta.get('duration', ''),
                    'link': episode_meta.get('link', '')
                })

            # Add timestamps
            if detailed_transcript:
                start_time, end_time = find_chunk_timestamps(chunk, detailed_transcript)
                metadata['start_time_seconds'] = start_time
                metadata['end_time_seconds'] = end_time
                metadata['start_time'] = format_timestamp(start_time)
                metadata['end_time'] = format_timestamp(end_time)

            chunk_metadata.append(metadata)

        if not chunk_ids:
            return 0  # All chunks already indexed

        # Generate embeddings
        logger.debug(f"Generating embeddings for {len(chunk_ids)} chunks...")
        embeddings = self.model.encode(chunk_texts, show_progress_bar=False).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=chunk_metadata
        )

        return len(chunk_ids)

    def index_all_transcripts(self) -> Dict[str, int]:
        """
        Index all transcripts in the transcripts directory.

        Returns:
            Dictionary with indexing statistics
        """
        logger.info("=" * 80)
        logger.info("ENHANCED TRANSCRIPT INDEXING")
        logger.info("=" * 80)

        # Find all transcript directories
        podcast_dirs = [d for d in self.transcripts_dir.iterdir() if d.is_dir()]

        if not podcast_dirs:
            logger.warning("No podcast directories found!")
            return {'podcasts': 0, 'transcripts': 0, 'chunks': 0}

        logger.info(f"Found {len(podcast_dirs)} podcast directories")

        total_transcripts = 0
        total_chunks = 0
        processed_podcasts = 0

        for podcast_dir in sorted(podcast_dirs):
            podcast_name = podcast_dir.name
            transcript_files = list(podcast_dir.glob("*.txt"))

            # Filter out diarized transcripts
            transcript_files = [f for f in transcript_files if '_diarized' not in f.name]

            if not transcript_files:
                continue

            logger.info(f"Processing: {podcast_name} ({len(transcript_files)} transcripts)")

            podcast_chunks = 0
            for i, transcript_file in enumerate(transcript_files, 1):
                # Progress indicator
                if i % 50 == 0 or i == len(transcript_files):
                    logger.debug(f"Progress: {i}/{len(transcript_files)}")

                chunks_added = self.index_transcript(transcript_file)
                podcast_chunks += chunks_added

            total_transcripts += len(transcript_files)
            total_chunks += podcast_chunks
            processed_podcasts += 1

            logger.info(f"Added {podcast_chunks} chunks from {len(transcript_files)} transcripts")

        logger.info("=" * 80)
        logger.info("INDEXING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Podcasts processed: {processed_podcasts}")
        logger.info(f"Transcripts indexed: {total_transcripts}")
        logger.info(f"Total chunks created: {total_chunks}")
        logger.info(f"Collection size: {self.collection.count()} documents")
        logger.info(f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        return {
            'podcasts': processed_podcasts,
            'transcripts': total_transcripts,
            'chunks': total_chunks
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get indexer statistics."""
        return {
            'collection_size': self.collection.count(),
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'podcasts_loaded': len(self.podcast_metadata),
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }
