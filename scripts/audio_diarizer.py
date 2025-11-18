#!/usr/bin/env python3
"""
Speaker Diarization for Podcast Episodes
Adds "who is speaking when" labels to existing transcripts using pyannote.audio
"""

from pathlib import Path
from pyannote.audio import Pipeline
import torch
import json
import sys
from typing import Dict, List, Tuple
import os

class AudioDiarizer:
    def __init__(self, episodes_dir: Path, transcripts_dir: Path, huggingface_token: str = None):
        """
        Initialize diarizer

        Args:
            episodes_dir: Directory containing audio files
            transcripts_dir: Directory containing transcripts
            huggingface_token: HuggingFace token for pyannote models
        """
        self.episodes_dir = episodes_dir
        self.transcripts_dir = transcripts_dir

        # Check if token is provided
        if not huggingface_token:
            huggingface_token = os.environ.get('HUGGINGFACE_TOKEN')

        if not huggingface_token:
            raise ValueError(
                "HuggingFace token required. Set HUGGINGFACE_TOKEN environment variable or pass token.\n"
                "Get token from: https://huggingface.co/settings/tokens\n"
                "Accept terms: https://huggingface.co/pyannote/speaker-diarization-3.1"
            )

        print("Loading diarization pipeline...")
        print("Note: First run will download ~1GB model files")

        # Load the diarization pipeline
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=huggingface_token
        )

        # Use GPU if available
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
            print("✓ Using GPU acceleration")
        else:
            print("✓ Using CPU (slower but works)")

        print("✓ Diarization pipeline loaded")

    def diarize_audio(self, audio_file: Path) -> Dict:
        """
        Perform speaker diarization on an audio file

        Returns: Dictionary with speaker segments
        """
        print(f"  Diarizing: {audio_file.name}")

        # Run diarization
        diarization = self.pipeline(str(audio_file))

        # Convert to structured format
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker,
                'duration': turn.end - turn.start
            })

        # Get speaker statistics
        speaker_times = {}
        for segment in segments:
            speaker = segment['speaker']
            duration = segment['duration']
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

        return {
            'segments': segments,
            'speaker_count': len(speaker_times),
            'speaker_times': speaker_times,
            'total_segments': len(segments)
        }

    def align_with_transcript(self, diarization: Dict, transcript_file: Path) -> Dict:
        """
        Align diarization with existing Whisper transcript

        Returns: Enhanced transcript with speaker labels
        """
        # Load existing Whisper transcript
        if not transcript_file.exists():
            return None

        with open(transcript_file, 'r', encoding='utf-8') as f:
            whisper_data = json.load(f)

        # Get segments from Whisper
        whisper_segments = whisper_data.get('segments', [])
        diarization_segments = diarization['segments']

        # Align each Whisper segment with the closest speaker
        enhanced_segments = []

        for wseg in whisper_segments:
            w_start = wseg['start']
            w_end = wseg['end']
            w_mid = (w_start + w_end) / 2

            # Find overlapping speaker
            speaker = None
            max_overlap = 0

            for dseg in diarization_segments:
                d_start = dseg['start']
                d_end = dseg['end']

                # Calculate overlap
                overlap_start = max(w_start, d_start)
                overlap_end = min(w_end, d_end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    speaker = dseg['speaker']

            # Add speaker to segment
            enhanced_seg = wseg.copy()
            enhanced_seg['speaker'] = speaker if speaker else 'UNKNOWN'
            enhanced_segments.append(enhanced_seg)

        # Create enhanced transcript
        enhanced = whisper_data.copy()
        enhanced['segments'] = enhanced_segments
        enhanced['diarization'] = {
            'speaker_count': diarization['speaker_count'],
            'speaker_times': diarization['speaker_times']
        }

        return enhanced

    def create_readable_transcript(self, enhanced_data: Dict) -> str:
        """
        Create human-readable transcript with speaker labels

        Format:
        [SPEAKER_00]: Hello, this is the podcast...
        [SPEAKER_01]: Thanks for having me!
        """
        lines = []
        current_speaker = None
        current_text = []

        for segment in enhanced_data['segments']:
            speaker = segment.get('speaker', 'UNKNOWN')
            text = segment['text'].strip()

            if speaker != current_speaker:
                # New speaker - write previous speaker's text
                if current_text:
                    lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
                    current_text = []

                current_speaker = speaker

            current_text.append(text)

        # Write final speaker's text
        if current_text:
            lines.append(f"[{current_speaker}]: {' '.join(current_text)}")

        return '\n\n'.join(lines)

    def process_episode(self, audio_file: Path) -> bool:
        """
        Process a single episode: diarize and enhance transcript

        Returns: True if successful
        """
        podcast_name = audio_file.parent.name
        episode_name = audio_file.stem

        # Find corresponding transcript
        transcript_dir = self.transcripts_dir / podcast_name
        detailed_transcript = transcript_dir / f"{episode_name}_detailed.json"

        if not detailed_transcript.exists():
            print(f"  ⚠️  No transcript found: {detailed_transcript.name}")
            return False

        # Check if already processed
        output_file = transcript_dir / f"{episode_name}_diarized.json"
        readable_file = transcript_dir / f"{episode_name}_diarized.txt"

        if output_file.exists():
            print(f"  ✓ Already processed: {episode_name}")
            return True

        try:
            # Perform diarization
            diarization = self.diarize_audio(audio_file)

            # Align with transcript
            enhanced = self.align_with_transcript(diarization, detailed_transcript)

            if not enhanced:
                print(f"  ⚠️  Failed to align transcript")
                return False

            # Save enhanced JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced, f, indent=2, ensure_ascii=False)

            # Save readable transcript
            readable = self.create_readable_transcript(enhanced)
            with open(readable_file, 'w', encoding='utf-8') as f:
                f.write(readable)

            print(f"  ✓ Processed: {episode_name}")
            print(f"     Speakers: {enhanced['diarization']['speaker_count']}")
            print(f"     Segments: {len(enhanced['segments'])}")

            return True

        except Exception as e:
            print(f"  ❌ Error processing {episode_name}: {e}")
            return False

    def process_podcast(self, podcast_name: str):
        """Process all episodes in a podcast directory"""
        podcast_dir = self.episodes_dir / podcast_name

        if not podcast_dir.exists():
            print(f"Podcast not found: {podcast_name}")
            return

        # Find audio files
        audio_files = list(podcast_dir.glob('*.mp3')) + list(podcast_dir.glob('*.m4a'))

        if not audio_files:
            print(f"No audio files found in: {podcast_name}")
            return

        print(f"\n{'='*80}")
        print(f"Processing: {podcast_name}")
        print(f"Episodes: {len(audio_files)}")
        print('='*80)

        processed = 0
        failed = 0

        for i, audio_file in enumerate(sorted(audio_files), 1):
            print(f"\n[{i}/{len(audio_files)}]")

            if self.process_episode(audio_file):
                processed += 1
            else:
                failed += 1

        print(f"\n{'='*80}")
        print(f"RESULTS: {podcast_name}")
        print(f"  Processed: {processed}")
        print(f"  Failed: {failed}")
        print('='*80)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Add speaker diarization to podcast transcripts')
    parser.add_argument('podcast', nargs='?', help='Podcast name to process (or "all")')
    parser.add_argument('--token', help='HuggingFace API token')
    parser.add_argument('--list', action='store_true', help='List available podcasts')

    args = parser.parse_args()

    episodes_dir = Path('episodes')
    transcripts_dir = Path('transcripts')

    if not episodes_dir.exists():
        print("Error: episodes/ directory not found")
        sys.exit(1)

    # List podcasts
    if args.list:
        podcasts = sorted([d.name for d in episodes_dir.iterdir() if d.is_dir()])
        print(f"\nAvailable podcasts ({len(podcasts)}):")
        for podcast in podcasts:
            print(f"  - {podcast}")
        print()
        return

    if not args.podcast:
        print("Usage: python3 scripts/audio_diarizer.py <podcast_name>")
        print("       python3 scripts/audio_diarizer.py --list")
        print()
        print("Example: python3 scripts/audio_diarizer.py \"Hello Internet\"")
        sys.exit(1)

    # Initialize diarizer
    try:
        diarizer = AudioDiarizer(
            episodes_dir=episodes_dir,
            transcripts_dir=transcripts_dir,
            huggingface_token=args.token
        )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Process podcasts
    if args.podcast.lower() == 'all':
        podcasts = sorted([d.name for d in episodes_dir.iterdir() if d.is_dir()])
        print(f"Processing all {len(podcasts)} podcasts...")

        for podcast in podcasts:
            diarizer.process_podcast(podcast)
    else:
        diarizer.process_podcast(args.podcast)


if __name__ == '__main__':
    main()
