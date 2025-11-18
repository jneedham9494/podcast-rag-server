#!/bin/bash
# Launch multiple transcription workers for a podcast feed
# Usage: ./launch_transcription_workers.sh <feed_name> <num_workers> [model_size]

if [ $# -lt 2 ]; then
    echo "Usage: $0 <feed_name> <num_workers> [model_size]"
    echo ""
    echo "Examples:"
    echo "  $0 'RHLSTP with Richard Herring' 5"
    echo "  $0 'RHLSTP with Richard Herring' 5 small"
    echo ""
    echo "Available feeds with remaining transcriptions:"
    python3 - <<EOF
from pathlib import Path

episodes_dir = Path('../episodes')
transcripts_dir = Path('../transcripts')

for podcast_dir in sorted(episodes_dir.iterdir()):
    if not podcast_dir.is_dir():
        continue

    name = podcast_dir.name
    audio_files = list(podcast_dir.glob('*.mp3')) + list(podcast_dir.glob('*.m4a')) + list(podcast_dir.glob('*.wav'))
    valid_files = [f for f in audio_files if f.stat().st_size > 100 * 1024]
    downloaded = len(valid_files)

    if downloaded == 0:
        continue

    transcribed = 0
    trans_dir = transcripts_dir / name
    if trans_dir.exists():
        txt_files = list(trans_dir.glob('*.txt'))
        transcribed = len(txt_files)

    transcribed = min(transcribed, downloaded)
    remaining = downloaded - transcribed

    if remaining > 0:
        print(f"  '{name}' - {remaining} remaining")
EOF
    exit 1
fi

FEED_NAME="$1"
NUM_WORKERS="$2"
MODEL_SIZE="${3:-base}"

EPISODES_DIR="../episodes/$FEED_NAME"

if [ ! -d "$EPISODES_DIR" ]; then
    echo "❌ Feed directory not found: $EPISODES_DIR"
    exit 1
fi

LOG_DIR="../logs"
mkdir -p "$LOG_DIR"

echo "=================================================="
echo "LAUNCHING TRANSCRIPTION WORKERS"
echo "=================================================="
echo "Feed: $FEED_NAME"
echo "Workers: $NUM_WORKERS"
echo "Model: $MODEL_SIZE"
echo ""

for i in $(seq 1 $NUM_WORKERS); do
    LOG_FILE="$LOG_DIR/transcribe_${FEED_NAME//[^a-zA-Z0-9]/_}_worker${i}.log"

    echo "🚀 Launching worker $i..."
    python3 podcast_transcriber.py "$EPISODES_DIR" "$MODEL_SIZE" > "$LOG_FILE" 2>&1 &

    WORKER_PID=$!
    echo "   PID: $WORKER_PID"
    echo "   Log: $LOG_FILE"
done

echo ""
echo "✅ All $NUM_WORKERS workers launched!"
echo ""
echo "Monitor progress:"
echo "  tail -f $LOG_DIR/transcribe_${FEED_NAME//[^a-zA-Z0-9]/_}_worker*.log"
echo ""
echo "Stop all workers:"
echo "  pkill -f 'podcast_transcriber.py.*$FEED_NAME'"
