# Audio Analysis & Speaker Diarization

## Overview
Advanced audio processing tools to extract metadata and speaker information from podcast episodes.

## Features

### 1. Speaker Diarization ([scripts/audio_diarizer.py](scripts/audio_diarizer.py:1))
**What it does**: Identifies "who is speaking when" in podcast episodes

**Output formats:**
- JSON with speaker-labeled segments
- Readable transcripts with `[SPEAKER_00]:` labels
- Speaker statistics (talk time per speaker)

**Example output:**
```
[SPEAKER_00]: Hello and welcome to the podcast. Today we're discussing...

[SPEAKER_01]: Thanks for having me. It's great to be here.

[SPEAKER_00]: So let's dive right in. What do you think about...
```

### 2. Audio Feature Analysis ([scripts/audio_analyzer.py](scripts/audio_analyzer.py:1))
**What it extracts:**
- Duration, file size, bitrate, codec
- Tempo (BPM) and rhythm
- Audio energy/loudness characteristics
- Speech vs music classification
- Spectral features (brightness, timbre)
- Silence detection and percentage
- Voice characteristics (MFCC)

**Use cases:**
- Find high-energy vs calm episodes
- Detect music intros/outros
- Quality assurance
- Content classification

## Installation

### 1. Install Speaker Diarization Dependencies

```bash
# Install PyTorch (required for pyannote.audio)
pip3 install torch --user

# Install pyannote.audio
pip3 install pyannote.audio --user
```

### 2. Install Audio Analysis Dependencies

```bash
# Install librosa for audio feature extraction
pip3 install librosa --user

# Install additional audio processing libraries
pip3 install soundfile --user
```

### 3. Get HuggingFace Token (for speaker diarization)

1. Create account at https://huggingface.co/
2. Go to https://huggingface.co/settings/tokens
3. Create new token (read access)
4. Accept model terms at https://huggingface.co/pyannote/speaker-diarization-3.1

Set token as environment variable:
```bash
export HUGGINGFACE_TOKEN="hf_your_token_here"
```

Or pass directly to script:
```bash
python3 scripts/audio_diarizer.py "Hello Internet" --token hf_your_token_here
```

## Usage

### Speaker Diarization

**List available podcasts:**
```bash
python3 scripts/audio_diarizer.py --list
```

**Process single podcast:**
```bash
python3 scripts/audio_diarizer.py "Hello Internet"
```

**Process all podcasts:**
```bash
python3 scripts/audio_diarizer.py all
```

**Output files created:**
```
transcripts/Hello Internet/
  ├── episode_name.txt                    # Original plain transcript
  ├── episode_name_detailed.json          # Original Whisper output
  ├── episode_name_diarized.json          # Enhanced with speakers
  └── episode_name_diarized.txt           # Readable with [SPEAKER_X]
```

### Audio Feature Analysis

**Analyze single podcast:**
```bash
python3 scripts/audio_analyzer.py "Hello Internet"
```

**Custom sample rate (faster but less accurate):**
```bash
python3 scripts/audio_analyzer.py "Hello Internet" --sample-rate 16000
```

**Output files created:**
```
audio_analysis/Hello Internet/
  └── episode_name_audio_analysis.json    # All audio features
```

**Example output:**
```json
{
  "episode": "H.I. #1 - Hello",
  "basic_info": {
    "duration_seconds": 3245.6,
    "duration_readable": "00:54:05",
    "file_size_mb": 46.8,
    "bitrate_kbps": 128,
    "codec": "mp3",
    "channels": 2
  },
  "audio_features": {
    "tempo_bpm": 85.3,
    "rms_mean": 0.042,
    "zero_crossing_rate_mean": 0.087,
    "content_type": "speech"
  },
  "silence_analysis": {
    "silence_percentage": 12.4,
    "non_silent_intervals": 245
  }
}
```

## Performance Estimates

### Speaker Diarization
- **Speed**: ~5-10x faster than re-transcribing
- **Time for 5,494 episodes**: 50-80 hours total
- **Model size**: ~1GB download (first run only)
- **Accuracy**: 80-95% (varies by audio quality and overlap)

### Audio Feature Analysis
- **Speed**: ~2-5 minutes per episode
- **Time for 5,494 episodes**: ~10-20 hours total
- **Disk space**: ~50MB for all analyses

## Use Cases

### With RAG Server

Once you have speaker diarization, you can:

1. **Search by speaker:**
   ```python
   # Find all segments from SPEAKER_00 (usually the host)
   results = requests.post('http://localhost:8000/search',
       json={'query': 'economics discussion', 'n_results': 10})

   # Filter for specific speaker in post-processing
   host_segments = [r for r in results if r['metadata'].get('speaker') == 'SPEAKER_00']
   ```

2. **Analyze speaking patterns:**
   - Who speaks most/least?
   - Do certain topics correlate with specific speakers?
   - Identify frequent guests

3. **Enhanced transcripts:**
   - More readable with speaker labels
   - Better context for LLM queries
   - Easier to follow conversations

### Audio Features Use Cases

1. **Content discovery:**
   ```python
   # Find high-energy episodes
   # Find episodes with music
   # Find very long or very short episodes
   ```

2. **Quality control:**
   ```python
   # Detect episodes with excessive silence
   # Find low-quality audio (low bitrate)
   # Identify problematic recordings
   ```

3. **Analysis:**
   ```python
   # Compare speech patterns across podcasts
   # Detect intro/outro music timing
   # Analyze pacing and tempo trends
   ```

## Running at Scale

### Parallel Processing

For faster processing, run multiple podcasts in parallel:

```bash
# Terminal 1
python3 scripts/audio_diarizer.py "Podcast A"

# Terminal 2
python3 scripts/audio_diarizer.py "Podcast B"

# Terminal 3
python3 scripts/audio_diarizer.py "Podcast C"
```

### Background Processing

```bash
# Run in background
nohup python3 scripts/audio_diarizer.py "Hello Internet" > logs/diarize_hello_internet.log 2>&1 &

# Monitor progress
tail -f logs/diarize_hello_internet.log
```

## Updating RAG Index with Speaker Data

Once you have diarized transcripts, rebuild the RAG index to include speaker info:

```bash
# Rebuild index to include diarized transcripts
python3 scripts/build_rag_index.py
```

The indexer will detect `_diarized.txt` files and prioritize them over plain transcripts.

## Limitations

### Speaker Diarization
- Cannot identify speakers by name (only labels them as SPEAKER_00, SPEAKER_01, etc.)
- Accuracy decreases with:
  - Overlapping speech
  - Poor audio quality
  - Many speakers (>4)
  - Background noise
- May merge or split speakers inconsistently

### Audio Features
- First 5 minutes analyzed by default (configurable)
- Some features require good audio quality
- Music/speech classification is heuristic-based

## Future Enhancements

1. **Speaker identification**: Map SPEAKER_X to actual names using metadata or voice prints
2. **Real-time processing**: Process as episodes download
3. **Advanced features**:
   - Emotion detection
   - Accent/language detection
   - Topic segmentation
   - Chapter detection
4. **RAG integration**: Native speaker filtering in search queries

## Troubleshooting

### HuggingFace token issues
```bash
# Verify token is set
echo $HUGGINGFACE_TOKEN

# Test token manually
python3 -c "from huggingface_hub import HfApi; HfApi().whoami(token='$HUGGINGFACE_TOKEN')"
```

### Out of memory
```bash
# Use lower sample rate for audio analysis
python3 scripts/audio_analyzer.py "Podcast" --sample-rate 16000

# For diarization, process fewer episodes at once
```

### Slow processing
- Use GPU if available (pyannote.audio will auto-detect)
- Lower sample rates for audio analysis
- Process multiple podcasts in parallel
- Skip very long episodes

## Example Workflow

```bash
# 1. Transcribe episodes (already done)
# 2. Add speaker diarization
python3 scripts/audio_diarizer.py "Hello Internet"

# 3. Extract audio features
python3 scripts/audio_analyzer.py "Hello Internet"

# 4. Rebuild RAG index with new data
python3 scripts/build_rag_index.py

# 5. Query with enhanced context
python3 scripts/extract_book_recommendations.py --generate-prompt
```

## Cost Analysis

**Completely Free & Local:**
- No API costs (unlike OpenAI Whisper API)
- No cloud processing required
- All models run locally
- One-time HuggingFace token setup (free)

**Resource Requirements:**
- Disk: ~1GB for models, ~100MB for analyses
- RAM: 4-8GB recommended
- CPU: Works on any modern CPU (GPU speeds it up)
- Time: ~60-100 hours total for all episodes
