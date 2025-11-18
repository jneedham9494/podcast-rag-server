"""
Speaker diarization utilities for podcast audio.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional


def diarize_audio(
    audio_path: Path,
    num_speakers: Optional[int] = None
) -> List[Dict]:
    """
    Perform speaker diarization using pyannote.audio.

    Args:
        audio_path: Path to audio file
        num_speakers: Optional number of speakers (if known)

    Returns:
        List of segments with speaker labels and timestamps
    """
    from pyannote.audio import Pipeline
    import torch

    # Check for HuggingFace token
    hf_token = None
    token_file = Path.home() / '.huggingface' / 'token'
    if token_file.exists():
        hf_token = token_file.read_text().strip()
    else:
        # Try environment variable
        hf_token = (
            os.environ.get('HF_TOKEN') or
            os.environ.get('HUGGING_FACE_HUB_TOKEN')
        )

    if not hf_token:
        print("  WARNING: No HuggingFace token found. "
              "Speaker diarization requires authentication.")
        print("  Run: huggingface-cli login")
        return []

    # Load pipeline
    print("  Loading pyannote diarization pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )

    # Use GPU if available
    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
    elif torch.backends.mps.is_available():
        pipeline.to(torch.device("mps"))

    # Run diarization
    print(f"  Running diarization on {audio_path.name}...")
    if num_speakers:
        diarization = pipeline(str(audio_path), num_speakers=num_speakers)
    else:
        diarization = pipeline(str(audio_path))

    # Extract segments
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            'start': turn.start,
            'end': turn.end,
            'speaker': speaker,
            'duration': turn.end - turn.start
        })

    return segments


def merge_diarization_with_transcript(
    diarization_segments: List[Dict],
    whisper_segments: List[Dict]
) -> List[Dict]:
    """
    Merge speaker diarization with Whisper transcript segments.

    Maps each transcript segment to a speaker based on time overlap.

    Args:
        diarization_segments: Speaker diarization output
        whisper_segments: Whisper transcript segments with timestamps

    Returns:
        Enriched segments with speaker labels
    """
    enriched_segments = []

    for w_seg in whisper_segments:
        w_start = w_seg.get('start', 0)
        w_end = w_seg.get('end', 0)

        # Find overlapping diarization segment
        best_speaker = 'UNKNOWN'
        best_overlap = 0

        for d_seg in diarization_segments:
            # Calculate overlap
            overlap_start = max(w_start, d_seg['start'])
            overlap_end = min(w_end, d_seg['end'])
            overlap = max(0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = d_seg['speaker']

        enriched_segments.append({
            'id': w_seg.get('id', 0),
            'start': w_start,
            'end': w_end,
            'text': w_seg.get('text', '').strip(),
            'speaker': best_speaker
        })

    return enriched_segments
