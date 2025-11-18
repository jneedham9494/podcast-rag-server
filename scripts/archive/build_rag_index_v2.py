#!/usr/bin/env python3
"""
Enhanced RAG Index Builder for Podcast Transcripts (v2)
Improvements:
- Better embedding model (all-mpnet-base-v2: 768 dims vs 384)
- Episode metadata (dates, descriptions, duration)
- Timestamps from detailed transcripts
- Sentence-aware chunking
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import hashlib
import sys
from typing import List, Dict, Tuple, Optional
import re
from datetime import datetime

class EnhancedTranscriptIndexer:
    def __init__(self,
                 transcripts_dir: Path,
                 metadata_dir: Path,
                 db_path: Path,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 use_better_model: bool = True):
        """
        Initialize enhanced indexer

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
        print("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or get collection (new name to avoid conflicts)
        collection_name = "podcast_transcripts_v2"
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Enhanced podcast transcripts with metadata and timestamps"}
        )

        # Initialize embedding model
        model_name = 'all-mpnet-base-v2' if use_better_model else 'all-MiniLM-L6-v2'
        print(f"Loading embedding model: {model_name}...")
        if use_better_model:
            print("  (Better quality, 2x larger embeddings)")
        self.model = SentenceTransformer(model_name)
        print(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

        # Load podcast metadata
        print("Loading podcast metadata...")
        self.podcast_metadata = self._load_podcast_metadata()
        print(f"Loaded metadata for {len(self.podcast_metadata)} podcasts")

    def _load_podcast_metadata(self) -> Dict[str, Dict]:
        """Load all podcast metadata from JSON files"""
        metadata = {}

        if not self.metadata_dir.exists():
            print(f"Warning: Metadata directory not found: {self.metadata_dir}")
            return metadata

        for json_file in self.metadata_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    podcast_name = json_file.stem
                    metadata[podcast_name] = data
            except Exception as e:
                print(f"Warning: Could not load {json_file.name}: {e}")

        return metadata

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences (simple approach)"""
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _chunk_text_sentence_aware(self, text: str) -> List[str]:
        """
        Chunk text respecting sentence boundaries

        Strategy: Build chunks from complete sentences
        """
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""
        overlap_sentences = []

        for sentence in sentences:
            # Would adding this sentence exceed chunk size?
            if current_chunk and len(current_chunk) + len(sentence) > self.chunk_size:
                # Save current chunk
                chunks.append(current_chunk.strip())

                # Start new chunk with overlap
                overlap_text = ' '.join(overlap_sentences[-3:]) if overlap_sentences else ""
                current_chunk = overlap_text + (' ' if overlap_text else '') + sentence
                overlap_sentences = [sentence]
            else:
                # Add sentence to current chunk
                current_chunk += (' ' if current_chunk else '') + sentence
                overlap_sentences.append(sentence)

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _get_episode_metadata(self, podcast_name: str, episode_filename: str) -> Dict:
        """Extract episode metadata from podcast metadata"""

        if podcast_name not in self.podcast_metadata:
            return {}

        # Try to match episode by filename
        episode_stem = Path(episode_filename).stem

        podcast_data = self.podcast_metadata[podcast_name]
        episodes = podcast_data.get('episodes', [])

        # Search for matching episode
        for episode in episodes:
            episode_title = episode.get('title', '')

            # Try exact match first
            if episode_stem == episode_title:
                return self._extract_episode_fields(episode)

            # Try partial match (remove special characters)
            clean_stem = re.sub(r'[^\w\s]', '', episode_stem.lower())
            clean_title = re.sub(r'[^\w\s]', '', episode_title.lower())
            if clean_stem and clean_title and (
                clean_stem in clean_title or clean_title in clean_stem
            ):
                return self._extract_episode_fields(episode)

        return {}

    def _extract_episode_fields(self, episode: Dict) -> Dict:
        """Extract and format episode fields"""
        return {
            'title': episode.get('title', ''),
            'description': episode.get('description', '')[:500],  # Limit description length
            'publish_date': episode.get('published', ''),
            'duration': str(episode.get('duration', '')),
            'link': episode.get('link', '')
        }

    def _load_detailed_transcript(self, transcript_dir: Path, episode_stem: str) -> Optional[Dict]:
        """Load detailed Whisper transcript with timestamps"""
        detailed_file = transcript_dir / f"{episode_stem}_detailed.json"

        if not detailed_file.exists():
            return None

        try:
            with open(detailed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"  Warning: Could not load detailed transcript: {e}")
            return None

    def _find_chunk_timestamps(self, chunk_text: str, detailed_transcript: Dict) -> Tuple[float, float]:
        """
        Find start and end timestamps for a chunk by matching text to segments

        Returns: (start_time, end_time) in seconds
        """
        if not detailed_transcript or 'segments' not in detailed_transcript:
            return (0, 0)

        segments = detailed_transcript['segments']

        # Find first segment that overlaps with chunk start
        chunk_words = chunk_text.split()[:10]  # First 10 words
        chunk_start_text = ' '.join(chunk_words).lower()

        start_time = 0
        end_time = 0
        found_start = False

        for segment in segments:
            segment_text = segment.get('text', '').lower().strip()

            if not found_start:
                # Look for chunk start
                if chunk_start_text[:50] in segment_text or segment_text in chunk_start_text:
                    start_time = segment.get('start', 0)
                    found_start = True

            if found_start:
                # Continue until we've covered the chunk length
                end_time = segment.get('end', 0)

                # Rough estimate: if we've covered enough segments
                if end_time - start_time > len(chunk_text) / 200:  # ~200 chars per second of speech
                    break

        return (start_time, end_time)

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as MM:SS or HH:MM:SS"""
        if seconds == 0:
            return "00:00"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def index_transcript(self, transcript_file: Path) -> int:
        """
        Index a single transcript file with enhanced metadata

        Returns: Number of chunks created
        """
        podcast_name = transcript_file.parent.name
        episode_filename = transcript_file.name
        episode_stem = transcript_file.stem

        # Read transcript
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"  Error reading {transcript_file}: {e}")
            return 0

        if not text.strip():
            print(f"  Skipping empty transcript: {episode_filename}")
            return 0

        # Chunk with sentence awareness
        chunks = self._chunk_text_sentence_aware(text)

        if not chunks:
            print(f"  No chunks generated for: {episode_filename}")
            return 0

        # Get episode metadata
        episode_meta = self._get_episode_metadata(podcast_name, episode_filename)

        # Load detailed transcript for timestamps
        transcript_dir = self.transcripts_dir / podcast_name
        detailed_transcript = self._load_detailed_transcript(transcript_dir, episode_stem)

        # Prepare batch data
        chunk_ids = []
        chunk_texts = []
        chunk_metadata = []

        for idx, chunk in enumerate(chunks):
            chunk_id = self._generate_chunk_id(podcast_name, episode_filename, idx)

            # Check if already indexed
            try:
                existing = self.collection.get(ids=[chunk_id])
                if existing and existing['ids']:
                    continue  # Skip already indexed chunk
            except:
                pass

            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk)

            # Build metadata
            metadata = {
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
                start_time, end_time = self._find_chunk_timestamps(chunk, detailed_transcript)
                metadata['start_time_seconds'] = start_time
                metadata['end_time_seconds'] = end_time
                metadata['start_time'] = self._format_timestamp(start_time)
                metadata['end_time'] = self._format_timestamp(end_time)

            chunk_metadata.append(metadata)

        if not chunk_ids:
            return 0  # All chunks already indexed

        # Generate embeddings
        print(f"  Generating embeddings for {len(chunk_ids)} chunks...")
        embeddings = self.model.encode(chunk_texts, show_progress_bar=False).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=chunk_metadata
        )

        return len(chunk_ids)

    def _generate_chunk_id(self, podcast_name: str, episode_filename: str, chunk_idx: int) -> str:
        """Generate unique ID for a chunk"""
        content = f"{podcast_name}::{episode_filename}::{chunk_idx}"
        return hashlib.md5(content.encode()).hexdigest()

    def index_all_transcripts(self):
        """Index all transcripts in the transcripts directory"""
        print("\n" + "="*80)
        print("ENHANCED TRANSCRIPT INDEXING")
        print("="*80)
        print()

        # Find all transcript directories
        podcast_dirs = [d for d in self.transcripts_dir.iterdir() if d.is_dir()]

        if not podcast_dirs:
            print("No podcast directories found!")
            return

        print(f"Found {len(podcast_dirs)} podcast directories")
        print()

        total_transcripts = 0
        total_chunks = 0
        processed_podcasts = 0

        for podcast_dir in sorted(podcast_dirs):
            podcast_name = podcast_dir.name
            transcript_files = list(podcast_dir.glob("*.txt"))

            # Filter out diarized transcripts for now
            transcript_files = [f for f in transcript_files if '_diarized' not in f.name]

            if not transcript_files:
                continue

            print(f"Processing: {podcast_name}")
            print(f"  Found {len(transcript_files)} transcripts")

            podcast_chunks = 0
            for i, transcript_file in enumerate(transcript_files, 1):
                # Progress indicator
                if i % 50 == 0 or i == len(transcript_files):
                    print(f"  Progress: {i}/{len(transcript_files)}...", end='\r')

                chunks_added = self.index_transcript(transcript_file)
                podcast_chunks += chunks_added

            total_transcripts += len(transcript_files)
            total_chunks += podcast_chunks
            processed_podcasts += 1

            print(f"  ✓ Added {podcast_chunks} chunks from {len(transcript_files)} transcripts")

        print()
        print("="*80)
        print("INDEXING COMPLETE")
        print("="*80)
        print(f"  Podcasts processed: {processed_podcasts}")
        print(f"  Transcripts indexed: {total_transcripts}")
        print(f"  Total chunks created: {total_chunks}")
        print(f"  ChromaDB location: {self.client._settings.persist_directory}")
        print()

        # Collection stats
        collection_count = self.collection.count()
        print(f"  Collection size: {collection_count} documents")
        print(f"  Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        print()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced RAG index builder')
    parser.add_argument('--fast', action='store_true',
                        help='Use faster/smaller model (all-MiniLM-L6-v2)')
    parser.add_argument('--db-path', default='rag_db_v2',
                        help='Path to ChromaDB directory (default: rag_db_v2)')

    args = parser.parse_args()

    # Configuration
    transcripts_dir = Path('transcripts')
    metadata_dir = Path('podcast_metadata')
    db_path = Path(args.db_path)

    # Validate directories
    if not transcripts_dir.exists():
        print(f"Error: Transcripts directory not found: {transcripts_dir}")
        print("Please run this script from the project root directory")
        sys.exit(1)

    # Create indexer and build index
    indexer = EnhancedTranscriptIndexer(
        transcripts_dir=transcripts_dir,
        metadata_dir=metadata_dir,
        db_path=db_path,
        chunk_size=1000,
        chunk_overlap=200,
        use_better_model=not args.fast
    )

    indexer.index_all_transcripts()


if __name__ == '__main__':
    main()
