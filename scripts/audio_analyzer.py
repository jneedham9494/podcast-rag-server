#!/usr/bin/env python3
"""
Audio Feature Extraction for Podcast Episodes
Extracts metadata: duration, audio quality, music/speech segments, etc.
"""

from pathlib import Path
import librosa
import numpy as np
import json
import sys
from typing import Dict
import subprocess

class AudioAnalyzer:
    def __init__(self, sample_rate: int = 22050):
        """
        Initialize audio analyzer

        Args:
            sample_rate: Sample rate for analysis (lower = faster, higher = more accurate)
        """
        self.sample_rate = sample_rate

    def extract_basic_info(self, audio_file: Path) -> Dict:
        """Extract basic audio information using ffprobe"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error',
                 '-show_entries', 'format=duration,bit_rate,size:stream=codec_name,sample_rate,channels',
                 '-of', 'json',
                 str(audio_file)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {}

            data = json.loads(result.stdout)

            format_info = data.get('format', {})
            stream_info = data.get('streams', [{}])[0]

            return {
                'duration_seconds': float(format_info.get('duration', 0)),
                'duration_readable': self._format_duration(float(format_info.get('duration', 0))),
                'file_size_bytes': int(format_info.get('size', 0)),
                'file_size_mb': round(int(format_info.get('size', 0)) / 1024 / 1024, 2),
                'bitrate_kbps': round(int(format_info.get('bit_rate', 0)) / 1000, 0),
                'codec': stream_info.get('codec_name', 'unknown'),
                'sample_rate': int(stream_info.get('sample_rate', 0)),
                'channels': int(stream_info.get('channels', 0))
            }

        except Exception as e:
            print(f"  Warning: Could not extract basic info: {e}")
            return {}

    def _format_duration(self, seconds: float) -> str:
        """Format duration as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def analyze_audio_features(self, audio_file: Path) -> Dict:
        """
        Analyze audio features using librosa

        Features extracted:
        - Tempo (BPM)
        - Energy/loudness
        - Spectral characteristics
        - Zero crossing rate (speech/music indicator)
        """
        print(f"  Loading audio: {audio_file.name}")

        try:
            # Load audio file (this takes time for long files)
            # Use duration limit for faster processing on long podcasts
            y, sr = librosa.load(str(audio_file), sr=self.sample_rate, duration=300)  # First 5 minutes

            print(f"  Analyzing features...")

            # Extract features
            features = {}

            # 1. Tempo (beats per minute)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo_bpm'] = float(tempo)

            # 2. RMS Energy (loudness)
            rms = librosa.feature.rms(y=y)[0]
            features['rms_mean'] = float(np.mean(rms))
            features['rms_std'] = float(np.std(rms))

            # 3. Zero Crossing Rate (speech vs music indicator)
            # Higher ZCR = more speech-like, lower = more music-like
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zero_crossing_rate_mean'] = float(np.mean(zcr))
            features['zero_crossing_rate_std'] = float(np.std(zcr))

            # 4. Spectral Centroid (brightness of sound)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_std'] = float(np.std(spectral_centroids))

            # 5. Spectral Rolloff (frequency below which X% of energy is contained)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['spectral_rolloff_mean'] = float(np.mean(spectral_rolloff))

            # 6. Mel-frequency cepstral coefficients (MFCC) - voice characteristics
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = [float(np.mean(mfcc)) for mfcc in mfccs]

            # 7. Classify content type based on features
            features['content_type'] = self._classify_content(features)

            return features

        except Exception as e:
            print(f"  Warning: Could not analyze features: {e}")
            return {}

    def _classify_content(self, features: Dict) -> str:
        """
        Classify audio content type based on features

        Returns: "speech", "music", "mixed", or "unknown"
        """
        if not features:
            return "unknown"

        zcr = features.get('zero_crossing_rate_mean', 0)
        tempo = features.get('tempo_bpm', 0)

        # Simple heuristics (can be improved)
        if zcr > 0.1 and tempo < 100:
            return "speech"
        elif zcr < 0.05 and tempo > 100:
            return "music"
        elif zcr > 0.05:
            return "mixed"
        else:
            return "unknown"

    def detect_silence_segments(self, audio_file: Path, threshold: float = -40) -> Dict:
        """
        Detect silence segments in audio

        Args:
            threshold: Silence threshold in dB (default: -40 dB)

        Returns: Silence statistics
        """
        try:
            y, sr = librosa.load(str(audio_file), sr=self.sample_rate, duration=300)

            # Detect non-silent intervals
            intervals = librosa.effects.split(y, top_db=-threshold)

            # Calculate silence percentage
            total_frames = len(y)
            non_silent_frames = sum(interval[1] - interval[0] for interval in intervals)
            silent_frames = total_frames - non_silent_frames

            return {
                'silence_percentage': round(100 * silent_frames / total_frames, 2),
                'non_silent_intervals': len(intervals),
                'analyzed_duration_seconds': len(y) / sr
            }

        except Exception as e:
            print(f"  Warning: Could not detect silence: {e}")
            return {}

    def analyze_episode(self, audio_file: Path, output_dir: Path) -> Dict:
        """
        Perform complete analysis on an episode

        Returns: Complete analysis results
        """
        episode_name = audio_file.stem

        print(f"\n{'='*80}")
        print(f"Analyzing: {episode_name}")
        print('='*80)

        # Check if already analyzed
        output_file = output_dir / f"{episode_name}_audio_analysis.json"
        if output_file.exists():
            print(f"  ✓ Already analyzed")
            with open(output_file, 'r') as f:
                return json.load(f)

        results = {
            'episode': episode_name,
            'audio_file': audio_file.name
        }

        # Extract basic info (fast)
        print("  Extracting basic information...")
        results['basic_info'] = self.extract_basic_info(audio_file)

        # Analyze audio features (slower)
        print("  Analyzing audio features...")
        results['audio_features'] = self.analyze_audio_features(audio_file)

        # Detect silence (medium speed)
        print("  Detecting silence segments...")
        results['silence_analysis'] = self.detect_silence_segments(audio_file)

        # Save results
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"  ✓ Analysis complete")
        print(f"     Duration: {results['basic_info'].get('duration_readable', 'unknown')}")
        print(f"     Size: {results['basic_info'].get('file_size_mb', 0)} MB")
        print(f"     Content Type: {results['audio_features'].get('content_type', 'unknown')}")

        return results

    def analyze_podcast(self, podcast_name: str, episodes_dir: Path, output_base_dir: Path):
        """Analyze all episodes in a podcast"""
        podcast_dir = episodes_dir / podcast_name

        if not podcast_dir.exists():
            print(f"Podcast not found: {podcast_name}")
            return

        # Find audio files
        audio_files = list(podcast_dir.glob('*.mp3')) + list(podcast_dir.glob('*.m4a'))

        if not audio_files:
            print(f"No audio files found in: {podcast_name}")
            return

        print(f"\n{'='*80}")
        print(f"ANALYZING: {podcast_name}")
        print(f"Episodes: {len(audio_files)}")
        print('='*80)

        output_dir = output_base_dir / podcast_name
        output_dir.mkdir(parents=True, exist_ok=True)

        analyzed = 0
        for i, audio_file in enumerate(sorted(audio_files), 1):
            print(f"\n[{i}/{len(audio_files)}]")
            try:
                self.analyze_episode(audio_file, output_dir)
                analyzed += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")

        print(f"\n{'='*80}")
        print(f"RESULTS: {podcast_name}")
        print(f"  Analyzed: {analyzed}/{len(audio_files)}")
        print('='*80)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze audio features of podcast episodes')
    parser.add_argument('podcast', nargs='?', help='Podcast name to analyze')
    parser.add_argument('--list', action='store_true', help='List available podcasts')
    parser.add_argument('--sample-rate', type=int, default=22050,
                        help='Sample rate for analysis (default: 22050)')

    args = parser.parse_args()

    episodes_dir = Path('episodes')
    output_dir = Path('audio_analysis')

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
        print("Usage: python3 scripts/audio_analyzer.py <podcast_name>")
        print("       python3 scripts/audio_analyzer.py --list")
        print()
        print("Example: python3 scripts/audio_analyzer.py \"Hello Internet\"")
        sys.exit(1)

    # Initialize analyzer
    analyzer = AudioAnalyzer(sample_rate=args.sample_rate)

    # Analyze podcast
    analyzer.analyze_podcast(args.podcast, episodes_dir, output_dir)


if __name__ == '__main__':
    main()
