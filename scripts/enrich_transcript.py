#!/usr/bin/env python3
"""
Transcript Enrichment Pipeline
Adds semantic metadata to podcast transcripts for better RAG search.

Features:
- Named Entity Recognition (people, orgs, places)
- Keyword/keyphrase extraction
- Speaker diarization
- Topic classification
- Episode summaries
- Conversation segmentation
"""

import json
import os
import re
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime


def repair_json(text: str) -> str:
    """
    Attempt to repair common JSON formatting issues from LLM output.

    Fixes:
    - Single quotes → double quotes
    - Trailing commas
    - Missing quotes around keys
    - Unescaped newlines in strings
    """
    # Strip any preamble before the JSON
    start = text.find('{')
    end = text.rfind('}') + 1
    if start < 0 or end <= start:
        return text

    json_str = text[start:end]

    # Replace single quotes with double quotes (but not inside strings)
    # This is a simplified approach - handles most cases
    json_str = re.sub(r"'([^']*)'(?=\s*:)", r'"\1"', json_str)  # Keys
    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # String values

    # Remove trailing commas before } or ]
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)

    # Fix missing colons (e.g., "key" "value" -> "key": "value")
    json_str = re.sub(r'"\s+"', '": "', json_str)

    # Replace actual newlines in string values with \n
    # This is tricky - we need to be careful not to break the JSON structure
    lines = json_str.split('\n')
    json_str = ' '.join(line.strip() for line in lines)

    return json_str


def parse_json_safely(text: str, default=None):
    """
    Parse JSON from LLM output with repair attempts.

    Returns parsed JSON or default value on failure.
    """
    if default is None:
        default = {}

    # Try direct parse first
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass

    # Try with repairs
    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    return default

# Known hosts/speakers per podcast
KNOWN_SPEAKERS = {
    'TRUE ANON TRUTH FEED': {
        'hosts': ['Brace Belden', 'Liz Franczak'],
        'producer': 'Yung Chomsky',
        'aliases': {
            'brace': 'Brace Belden',
            'liz': 'Liz Franczak',
            'chomsky': 'Yung Chomsky',
            'young chomsky': 'Yung Chomsky',
        }
    },
    'Chapo Trap House': {
        'hosts': ['Will Menaker', 'Matt Christman', 'Felix Biederman', 'Amber A\'Lee Frost', 'Virgil Texas'],
        'aliases': {
            'will': 'Will Menaker',
            'matt': 'Matt Christman',
            'felix': 'Felix Biederman',
            'amber': 'Amber A\'Lee Frost',
        }
    },
    'The Adam Friedland Show Podcast': {
        'hosts': ['Adam Friedland', 'Nick Mullen'],
        'aliases': {
            'adam': 'Adam Friedland',
            'nick': 'Nick Mullen',
        }
    },
    'Blowback': {
        'hosts': ['Brendan James', 'Noah Kulwin'],
        'aliases': {
            'brendan': 'Brendan James',
            'noah': 'Noah Kulwin',
        }
    },
    'Hello Internet': {
        'hosts': ['CGP Grey', 'Brady Haran'],
        'aliases': {
            'grey': 'CGP Grey',
            'brady': 'Brady Haran',
        }
    },
    'Multipolarity': {
        'hosts': ['Marshall Kosloff', 'Justin Ling'],
        'aliases': {}
    },
    'RHLSTP with Richard Herring': {
        'hosts': ['Richard Herring'],
        'aliases': {
            'richard': 'Richard Herring',
        }
    },
    'The Louis Theroux Podcast': {
        'hosts': ['Louis Theroux'],
        'aliases': {
            'louis': 'Louis Theroux',
        }
    },
}

# Topic taxonomy for classification
TOPIC_TAXONOMY = [
    "US Politics",
    "International Politics",
    "Media & Journalism",
    "History",
    "Conspiracy Theories",
    "Technology",
    "Economics & Finance",
    "Crime & Justice",
    "Culture & Entertainment",
    "Science",
    "Health",
    "Religion",
    "Military & Intelligence",
    "Environment",
    "Sports",
    "Personal Stories",
]


def extract_entities_spacy(text: str) -> dict:
    """Extract named entities using spaCy"""
    import spacy

    # Load model (will be cached after first load)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("  Downloading spaCy model...")
        subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                      capture_output=True)
        nlp = spacy.load("en_core_web_sm")

    # Process text in chunks to handle long transcripts
    max_length = 100000
    entities = {
        'people': set(),
        'organizations': set(),
        'locations': set(),
        'dates': set(),
        'events': set(),
    }

    # Process in chunks
    for i in range(0, len(text), max_length):
        chunk = text[i:i + max_length]
        doc = nlp(chunk)

        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['people'].add(ent.text)
            elif ent.label_ in ('ORG', 'NORP'):
                entities['organizations'].add(ent.text)
            elif ent.label_ in ('GPE', 'LOC', 'FAC'):
                entities['locations'].add(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].add(ent.text)
            elif ent.label_ == 'EVENT':
                entities['events'].add(ent.text)

    # Convert sets to sorted lists
    return {k: sorted(list(v)) for k, v in entities.items()}


def normalize_entities_ollama(entities: dict, model: str = "llama3:8b") -> dict:
    """Use LLM to normalize entity variants and remove noise"""

    if not entities.get('people'):
        return entities

    people_list = entities['people'][:50]  # Limit for context window

    prompt = f"""Here are person names extracted from a podcast transcript. Many are spelling variants of the same person (from speech-to-text errors).

Group these into canonical names. Return ONLY a JSON object mapping variants to canonical names.
Skip any that aren't actually people (like "Instagram", "COVID", etc.).

Names: {people_list}

Return format:
{{"variant1": "Canonical Name", "variant2": "Canonical Name", ...}}

JSON:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse JSON from response using safe parser
        response = result.stdout.strip()
        mapping = parse_json_safely(response, default={})

        if mapping:
            # Apply mapping - handle cases where value might be a list
            normalized_people = set()
            for person in entities['people']:
                canonical = mapping.get(person, person)
                # Handle case where LLM returns a list instead of string
                if isinstance(canonical, list):
                    canonical = canonical[0] if canonical else person
                # Ensure we only add strings
                if isinstance(canonical, str):
                    normalized_people.add(canonical)
                else:
                    normalized_people.add(person)

            entities['people'] = sorted(list(normalized_people))
            entities['entity_mapping'] = mapping

    except Exception as e:
        print(f"  WARNING: Entity normalization failed: {e}")

    return entities


def detect_hosts_from_intro(text: str, model: str = "llama3:8b") -> dict:
    """Dynamically detect podcast hosts from the episode intro"""

    # Get first ~3000 chars (intro section) - need more context
    intro = text[:3000]

    prompt = f"""Analyze this podcast intro and extract the hosts' names.

Look for phrases like:
- "My name is X" or "I'm X"
- "joined by X" or "with me is X"
- "This is X and Y"
- "your hosts X and Y"

Intro transcript:
{intro}

Based on the intro above, identify the actual names mentioned. If you cannot find specific names, return an empty hosts array.

Return ONLY valid JSON with no extra text:
{{"podcast_name": "name or null", "hosts": ["FirstName LastName", "FirstName LastName"], "producer": "name or null"}}

JSON:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )

        response = result.stdout.strip()
        detected = parse_json_safely(response, default={})

        # Validate that hosts are actual names, not placeholders
        if detected.get('hosts'):
            valid_hosts = []
            for host in detected['hosts']:
                # Skip placeholders and generic values
                if host and isinstance(host, str):
                    host_lower = host.lower()
                    if not any(placeholder in host_lower for placeholder in
                               ['name1', 'name2', 'firstname', 'lastname', 'host', 'unknown']):
                        valid_hosts.append(host)
            detected['hosts'] = valid_hosts
        return detected if detected else {}
    except Exception as e:
        print(f"  WARNING: Host detection failed: {e}")

    return {}


def detect_hosts_from_entities(entities: dict, text: str) -> list:
    """Fallback: detect likely hosts from most frequently mentioned people in transcript"""
    from collections import Counter

    if not entities.get('people'):
        return []

    # Negative filter: Common non-host names (politicians, celebrities, historical figures)
    # These are often episode subjects, not hosts
    NON_HOST_PATTERNS = [
        # US Politicians
        'trump', 'biden', 'obama', 'clinton', 'bush', 'reagan', 'nixon', 'kennedy',
        'pelosi', 'schumer', 'mcconnell', 'harris', 'pence', 'cheney', 'rumsfeld',
        'pompeo', 'blinken', 'sanders', 'warren', 'aoc', 'ocasio',
        # International figures
        'putin', 'xi', 'netanyahu', 'zelensky', 'saddam', 'hussein', 'castro',
        'kim jong', 'bin laden', 'gaddafi', 'assad', 'khamenei',
        # Historical figures
        'hitler', 'stalin', 'mao', 'churchill', 'fdr', 'lincoln', 'washington',
        'jefferson', 'napoleon', 'caesar', 'marx', 'lenin',
        # Media/celebrities often discussed
        'musk', 'bezos', 'zuckerberg', 'jobs', 'gates',
        'epstein', 'maxwell', 'weinstein', 'cosby',
        # Common false positives
        'god', 'jesus', 'christ', 'allah', 'buddha',
    ]

    # Count occurrences of each person in the text
    person_counts = Counter()
    text_lower = text.lower()

    for person in entities['people']:
        # Skip single-character or very short names (likely initials/errors)
        if len(person) < 3:
            continue

        # Skip names that are clearly not hosts
        person_lower = person.lower()
        if any(pattern in person_lower for pattern in NON_HOST_PATTERNS):
            continue

        # Prefer names with at least 2 words (first + last name)
        # But don't require it (some hosts go by single names)
        words = person.split()

        # Count occurrences (case-insensitive)
        count = text_lower.count(person_lower)
        if count > 0:
            # Boost score for full names (2+ words)
            if len(words) >= 2:
                count = int(count * 1.5)
            person_counts[person] = count

    # Get top candidates
    top_people = person_counts.most_common(5)

    # Filter: hosts are usually mentioned many times
    if not top_people:
        return []

    max_count = top_people[0][1]
    threshold = max_count * 0.3  # At least 30% as frequent as most mentioned

    likely_hosts = [person for person, count in top_people
                   if count >= threshold and count >= 5]  # Minimum 5 mentions

    return likely_hosts[:3]  # Maximum 3 hosts


def classify_content_segments(text: str, model: str = "llama3:8b") -> dict:
    """Classify transcript into content types: intro_banter, main_content, tangent, outro"""

    # Sample from different parts of transcript
    total_len = len(text)
    intro = text[:3000]
    middle = text[total_len//3:total_len//3 + 4000]
    end = text[-2000:]

    prompt = f"""Analyze this podcast transcript and identify the content structure.

INTRO (first part):
{intro}

MIDDLE (main content):
{middle}

OUTRO (end):
{end}

Return a JSON object describing:
1. "intro_topics" - casual/banter topics in the intro (if any)
2. "main_topics" - the primary subjects of the episode
3. "tangents" - off-topic diversions (if any)
4. "has_ads" - true/false if there are ad reads
5. "estimated_intro_length" - "short" (<5min), "medium" (5-15min), or "long" (>15min)

Return ONLY JSON:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90
        )

        response = result.stdout.strip()
        return parse_json_safely(response, default={})
    except Exception as e:
        print(f"  WARNING: Content classification failed: {e}")

    return {}


def extract_keywords(text: str, top_n: int = 20) -> list:
    """Extract keywords using KeyBERT"""
    from keybert import KeyBERT

    # Initialize KeyBERT with sentence-transformers
    kw_model = KeyBERT('all-MiniLM-L6-v2')

    # Extract keywords (limit text length for performance)
    max_chars = 50000
    if len(text) > max_chars:
        # Sample from beginning, middle, end
        sample = text[:max_chars//3] + text[len(text)//2 - max_chars//6:len(text)//2 + max_chars//6] + text[-max_chars//3:]
    else:
        sample = text

    keywords = kw_model.extract_keywords(
        sample,
        keyphrase_ngram_range=(1, 3),
        stop_words='english',
        top_n=top_n,
        use_mmr=True,  # Maximal Marginal Relevance for diversity
        diversity=0.5
    )

    return [kw for kw, score in keywords]


def classify_topics_huggingface(text: str, topics: list) -> list:
    """
    Use HuggingFace zero-shot classification for more accurate topic labeling.
    More reliable than LLM-based classification for predefined categories.
    """
    try:
        from transformers import pipeline
    except ImportError:
        print("  WARNING: transformers not installed, skipping HuggingFace classification")
        return []

    # Initialize zero-shot classifier (cached after first load)
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1  # CPU, use 0 for GPU
    )

    # Sample text for classification (limit for performance)
    max_chars = 10000
    if len(text) > max_chars:
        sample = text[:max_chars//2] + "\n\n" + text[-max_chars//2:]
    else:
        sample = text

    # Run classification
    result = classifier(
        sample,
        candidate_labels=topics,
        multi_label=True  # Allow multiple topics
    )

    # Return topics with score > 0.25 (lowered threshold for more coverage)
    classified = []
    for label, score in zip(result['labels'], result['scores']):
        if score > 0.25:
            classified.append(label)
        if len(classified) >= 5:  # Maximum 5 broad topics
            break

    # If we got less than 2 topics, include the top 2 regardless of score
    if len(classified) < 2:
        classified = result['labels'][:2]

    return classified


def extract_episode_date(text: str) -> str:
    """Try to extract episode date/year from transcript for context grounding"""
    import re

    # Look for year mentions in first part of transcript
    intro = text[:5000]

    # Common patterns: "January 2020", "2019", "this week in November"
    year_pattern = r'\b(20\d{2}|19\d{2})\b'
    years = re.findall(year_pattern, intro)

    if years:
        # Return most common year mentioned
        from collections import Counter
        year_counts = Counter(years)
        return year_counts.most_common(1)[0][0]

    return None


def diarize_audio(audio_path: Path, num_speakers: int = None) -> list:
    """
    Perform speaker diarization using pyannote.audio

    Returns list of segments with speaker labels and timestamps
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
        import os
        hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')

    if not hf_token:
        print("  WARNING: No HuggingFace token found. Speaker diarization requires authentication.")
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


def merge_diarization_with_transcript(diarization_segments: list, whisper_segments: list) -> list:
    """
    Merge speaker diarization with Whisper transcript segments

    Maps each transcript segment to a speaker based on time overlap
    """
    enriched_segments = []

    for w_seg in whisper_segments:
        w_start = w_seg.get('start', 0)
        w_end = w_seg.get('end', 0)
        w_mid = (w_start + w_end) / 2

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


def generate_summary_ollama(text: str, model: str = "llama3:8b") -> str:
    """Generate episode summary using Ollama"""

    # Truncate text to fit context window
    max_chars = 12000  # ~3000 tokens
    if len(text) > max_chars:
        # Take beginning and end
        truncated = text[:max_chars//2] + "\n\n[...]\n\n" + text[-max_chars//2:]
    else:
        truncated = text

    prompt = f"""Summarize this podcast episode transcript in 2-3 sentences. Focus on the main topics discussed and key points made.

Transcript:
{truncated}

Summary:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"  WARNING: Ollama summary failed: {e}")
        return ""


def classify_topics_ollama(text: str, topics: list, model: str = "llama3:8b", episode_year: str = None) -> dict:
    """Classify episode into topics using Ollama - returns both broad and specific topics"""

    # Truncate text
    max_chars = 8000
    if len(text) > max_chars:
        truncated = text[:max_chars//2] + "\n\n[...]\n\n" + text[-max_chars//2:]
    else:
        truncated = text

    topic_list = "\n".join(f"- {t}" for t in topics)

    # Add context grounding if we know the episode year
    context_note = ""
    if episode_year:
        context_note = f"\n\nIMPORTANT: This episode was recorded in {episode_year}. Only reference events that occurred on or before {episode_year}."

    # First get broad categories
    prompt_broad = f"""Based on this podcast transcript, select the 2-4 most relevant broad topics from this list.
Return ONLY the topic names, one per line, no explanations.

Available topics:
{topic_list}

Transcript excerpt:
{truncated}

Selected topics:"""

    broad_topics = []
    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt_broad,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse response - extract matching topics
        response = result.stdout.strip()
        for line in response.split('\n'):
            line = line.strip().strip('-').strip()
            for topic in topics:
                if topic.lower() in line.lower() or line.lower() in topic.lower():
                    if topic not in broad_topics:
                        broad_topics.append(topic)
        broad_topics = broad_topics[:4]
    except Exception as e:
        print(f"  WARNING: Ollama broad topic classification failed: {e}")

    # Now get specific/detailed topics (free-form)
    year_constraint = ""
    if episode_year:
        year_constraint = f"\nIMPORTANT: This episode was recorded in {episode_year}. Only mention events/topics that existed in or before {episode_year}. Do NOT reference future events."

    prompt_specific = f"""Based on this podcast transcript, list 5-8 SPECIFIC topics, events, or subjects discussed.
Be specific - instead of "Politics" say "Obama administration policy" or "2016 election coverage".
Instead of "Technology" say "YouTube algorithm changes" or "iPhone launch".
{year_constraint}

Return only the specific topics, one per line, no explanations or numbering.

Transcript excerpt:
{truncated}

Specific topics discussed:"""

    specific_topics = []
    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt_specific,
            capture_output=True,
            text=True,
            timeout=60
        )

        for line in result.stdout.strip().split('\n'):
            # Clean up formatting
            line = line.strip()
            line = line.strip('-*•').strip()
            line = line.strip('0123456789.').strip()
            line = line.strip('"\'').strip()

            # Skip preamble/instruction-like lines
            if any(skip in line.lower() for skip in ['here are', 'specific topics', 'transcript:', 'discussed:']):
                continue

            if line and len(line) < 100 and len(line) > 5:
                specific_topics.append(line)
        specific_topics = specific_topics[:8]
    except Exception as e:
        print(f"  WARNING: Ollama specific topic extraction failed: {e}")

    return {
        'broad': broad_topics,
        'specific': specific_topics
    }


def detect_chapters_ollama(text: str, model: str = "llama3:8b") -> list:
    """Detect natural topic breaks/chapters in the transcript"""

    # For long transcripts, just identify major sections
    max_chars = 10000
    if len(text) > max_chars:
        truncated = text[:max_chars]
    else:
        truncated = text

    prompt = f"""Identify 3-6 main topic sections in this podcast transcript.
For each section, provide a short title (3-5 words).
Return ONLY the section titles, one per line.

Transcript:
{truncated}

Section titles:"""

    try:
        result = subprocess.run(
            ['ollama', 'run', model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )

        chapters = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            line = line.strip('-*•').strip()
            line = line.strip('0123456789.').strip()
            line = line.strip('"\'').strip()

            # Skip preamble lines
            if any(skip in line.lower() for skip in ['here are', 'section titles', 'sections:', 'chapters:']):
                continue

            if line and len(line) < 100 and len(line) > 3:
                chapters.append(line)

        return chapters[:6]
    except Exception as e:
        print(f"  WARNING: Ollama chapter detection failed: {e}")
        return []


def enrich_transcript(
    transcript_path: Path,
    audio_path: Path = None,
    podcast_name: str = None,
    skip_diarization: bool = False,
    skip_ollama: bool = False,
) -> dict:
    """
    Main enrichment function - combines all enrichment methods

    Args:
        transcript_path: Path to .txt transcript file
        audio_path: Path to audio file (for diarization)
        podcast_name: Name of podcast (for known speakers)
        skip_diarization: Skip speaker diarization
        skip_ollama: Skip Ollama-based enrichments

    Returns:
        Enriched metadata dictionary
    """
    print(f"\nEnriching: {transcript_path.name}")
    start_time = time.time()

    # Load transcript text
    transcript_text = transcript_path.read_text(encoding='utf-8')

    # Load detailed JSON if available (for timestamps)
    detailed_path = transcript_path.with_name(
        transcript_path.stem + '_detailed.json'
    )
    whisper_segments = []
    if detailed_path.exists():
        with open(detailed_path) as f:
            detailed = json.load(f)
            whisper_segments = detailed.get('segments', [])

    # Initialize enrichment data
    enrichment = {
        'source_file': transcript_path.name,
        'enrichment_version': '1.0',
        'enriched_at': datetime.now().isoformat(),
        'podcast_name': podcast_name,
    }

    # === TIER 1: Fast Local NLP ===
    print("  [1/7] Extracting entities with spaCy...")
    try:
        enrichment['entities'] = extract_entities_spacy(transcript_text)
        print(f"        Found {len(enrichment['entities']['people'])} people, "
              f"{len(enrichment['entities']['organizations'])} orgs, "
              f"{len(enrichment['entities']['locations'])} locations")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['entities'] = {}

    # === Dynamic host detection ===
    print("  [2/7] Detecting hosts from intro...")
    try:
        # Priority 1: Use known speakers if available (most reliable)
        if podcast_name and podcast_name in KNOWN_SPEAKERS:
            enrichment['detected_hosts'] = {
                'hosts': KNOWN_SPEAKERS[podcast_name]['hosts'],
                'producer': KNOWN_SPEAKERS[podcast_name].get('producer'),
                'source': 'known_speakers'
            }
            print(f"        Using known hosts: {enrichment['detected_hosts']['hosts']}")
        else:
            # Priority 2: Try intro detection for unknown podcasts
            detected_hosts = detect_hosts_from_intro(transcript_text)
            if detected_hosts and detected_hosts.get('hosts'):
                enrichment['detected_hosts'] = detected_hosts
                print(f"        Detected: {detected_hosts.get('hosts', [])}")
            else:
                enrichment['detected_hosts'] = {}
                # Priority 3: Use entity frequency analysis (last resort)
                if enrichment.get('entities'):
                    freq_hosts = detect_hosts_from_entities(enrichment['entities'], transcript_text)
                    if freq_hosts:
                        enrichment['detected_hosts'] = {'hosts': freq_hosts, 'source': 'entity_frequency'}
                        print(f"        Fallback (frequency): {freq_hosts}")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['detected_hosts'] = {}

    print("  [3/7] Extracting keywords with KeyBERT...")
    try:
        enrichment['keywords'] = extract_keywords(transcript_text)
        print(f"        Found {len(enrichment['keywords'])} keywords")
    except Exception as e:
        print(f"        ERROR: {e}")
        enrichment['keywords'] = []

    # === TIER 2: Speaker Diarization ===
    if audio_path and audio_path.exists() and not skip_diarization:
        print("  [4/7] Running speaker diarization...")
        try:
            # Determine number of speakers from known hosts
            num_speakers = None
            if podcast_name and podcast_name in KNOWN_SPEAKERS:
                num_speakers = len(KNOWN_SPEAKERS[podcast_name]['hosts'])

            diarization = diarize_audio(audio_path, num_speakers)

            if diarization and whisper_segments:
                enriched_segments = merge_diarization_with_transcript(
                    diarization, whisper_segments
                )
                enrichment['speaker_segments'] = enriched_segments

                # Count speaker turns
                speakers = set(s['speaker'] for s in enriched_segments)
                print(f"        Found {len(speakers)} speakers, "
                      f"{len(enriched_segments)} segments")
            else:
                enrichment['speaker_segments'] = []
        except Exception as e:
            print(f"        ERROR: {e}")
            enrichment['speaker_segments'] = []
    else:
        print("  [4/7] Skipping diarization (no audio or disabled)")
        enrichment['speaker_segments'] = []

    # === TIER 3: LLM-based Enrichment ===
    if not skip_ollama:
        print("  [5/7] Generating summary with Ollama...")
        try:
            enrichment['summary'] = generate_summary_ollama(transcript_text)
            if enrichment['summary']:
                print(f"        Generated {len(enrichment['summary'])} char summary")
            else:
                print("        No summary generated")
        except Exception as e:
            print(f"        ERROR: {e}")
            enrichment['summary'] = ""

        print("  [6/7] Classifying topics & content structure...")
        try:
            # Extract episode year for context grounding (prevents hallucinations)
            episode_year = extract_episode_date(transcript_text)
            if episode_year:
                enrichment['episode_year'] = episode_year
                print(f"        Episode year detected: {episode_year}")

            # Try HuggingFace zero-shot for broad topics (more reliable)
            print("        Using HuggingFace zero-shot classification...")
            hf_topics = classify_topics_huggingface(transcript_text, TOPIC_TAXONOMY)
            if hf_topics:
                enrichment['topics_broad'] = hf_topics
                print(f"        Broad topics (HF): {hf_topics}")
            else:
                # Fallback to Ollama for broad topics
                topic_result = classify_topics_ollama(transcript_text, TOPIC_TAXONOMY, episode_year=episode_year)
                enrichment['topics_broad'] = topic_result.get('broad', [])
                print(f"        Broad topics (Ollama): {enrichment['topics_broad']}")

            # Use Ollama for specific topics (requires free-form generation)
            topic_result = classify_topics_ollama(transcript_text, TOPIC_TAXONOMY, episode_year=episode_year)
            enrichment['topics_specific'] = topic_result.get('specific', [])
            print(f"        Specific topics: {enrichment['topics_specific']}")

            # Classify content structure (banter vs main content)
            content_structure = classify_content_segments(transcript_text)
            if content_structure:
                enrichment['content_structure'] = content_structure
                intro_topics = content_structure.get('intro_topics', [])
                main_topics = content_structure.get('main_topics', [])
                print(f"        Intro banter: {intro_topics}")
                print(f"        Main content: {main_topics}")
            else:
                enrichment['content_structure'] = {}
        except Exception as e:
            print(f"        ERROR: {e}")
            enrichment['topics_broad'] = []
            enrichment['topics_specific'] = []
            enrichment['content_structure'] = {}

        print("  [7/7] Normalizing entities & detecting chapters...")
        try:
            # Normalize entity variants
            if enrichment.get('entities'):
                enrichment['entities'] = normalize_entities_ollama(enrichment['entities'])
                if enrichment['entities'].get('entity_mapping'):
                    print(f"        Normalized {len(enrichment['entities']['entity_mapping'])} entity variants")

            # Chapter detection
            enrichment['chapters'] = detect_chapters_ollama(transcript_text)
            if enrichment['chapters']:
                print(f"        Detected {len(enrichment['chapters'])} chapters")
        except Exception as e:
            print(f"        ERROR: {e}")
            enrichment['chapters'] = []
    else:
        print("  [5/7] Skipping Ollama summary (disabled)")
        print("  [6/7] Skipping Ollama topics (disabled)")
        print("  [7/7] Skipping entity normalization (disabled)")
        enrichment['summary'] = ""
        enrichment['topics_broad'] = []
        enrichment['topics_specific'] = []
        enrichment['content_structure'] = {}
        enrichment['chapters'] = []

    # Keep known speakers as fallback reference
    if podcast_name and podcast_name in KNOWN_SPEAKERS:
        enrichment['known_speakers_reference'] = KNOWN_SPEAKERS[podcast_name]

    elapsed = time.time() - start_time
    print(f"\n  Enrichment complete in {elapsed:.1f}s")

    return enrichment


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Enrich podcast transcript with metadata')
    parser.add_argument('transcript', help='Path to transcript .txt file')
    parser.add_argument('--audio', help='Path to audio file for diarization')
    parser.add_argument('--podcast', help='Podcast name (for known speakers)')
    parser.add_argument('--skip-diarization', action='store_true', help='Skip speaker diarization')
    parser.add_argument('--skip-ollama', action='store_true', help='Skip Ollama-based enrichment')
    parser.add_argument('--output', help='Output path for enriched JSON')

    args = parser.parse_args()

    transcript_path = Path(args.transcript)
    if not transcript_path.exists():
        print(f"ERROR: Transcript not found: {transcript_path}")
        sys.exit(1)

    audio_path = Path(args.audio) if args.audio else None

    # Auto-detect podcast name from path
    podcast_name = args.podcast
    if not podcast_name:
        # Try to extract from path like transcripts/TRUE ANON TRUTH FEED/episode.txt
        parts = transcript_path.parts
        if 'transcripts' in parts:
            idx = parts.index('transcripts')
            if idx + 1 < len(parts):
                podcast_name = parts[idx + 1]

    # Run enrichment
    enrichment = enrich_transcript(
        transcript_path,
        audio_path=audio_path,
        podcast_name=podcast_name,
        skip_diarization=args.skip_diarization,
        skip_ollama=args.skip_ollama,
    )

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = transcript_path.with_name(
            transcript_path.stem + '_enriched.json'
        )

    # Atomic write: write to temp file first, then rename
    # This prevents corrupt partial files if process is killed
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(
        suffix='.json',
        dir=output_path.parent,
        prefix='.enriching_'
    )
    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(enrichment, f, indent=2)
        # Atomic rename (on same filesystem)
        os.rename(temp_path, output_path)
        print(f"\nSaved enrichment to: {output_path}")
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

    # Print summary
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)

    # Hosts
    hosts = enrichment.get('detected_hosts', {})
    if hosts.get('hosts'):
        print(f"Detected Hosts: {hosts['hosts']}")

    # Entities
    entities = enrichment.get('entities', {})
    entity_count = sum(len(v) for k, v in entities.items() if k != 'entity_mapping')
    print(f"Entities: {entity_count} total")
    if entities.get('entity_mapping'):
        print(f"  Normalized variants: {len(entities['entity_mapping'])}")

    # Keywords
    print(f"Keywords: {len(enrichment.get('keywords', []))}")

    # Topics
    print(f"Broad Topics: {enrichment.get('topics_broad', [])}")
    print(f"Specific Topics: {enrichment.get('topics_specific', [])}")

    # Content structure
    content = enrichment.get('content_structure', {})
    if content:
        print(f"Content Structure:")
        if content.get('intro_topics'):
            print(f"  Intro banter: {content['intro_topics']}")
        if content.get('main_topics'):
            print(f"  Main content: {content['main_topics']}")
        if content.get('tangents'):
            print(f"  Tangents: {content['tangents']}")

    # Other
    print(f"Speaker segments: {len(enrichment.get('speaker_segments', []))}")
    print(f"Chapters: {len(enrichment.get('chapters', []))}")

    if enrichment.get('summary'):
        print(f"Summary: {enrichment['summary'][:200]}...")


if __name__ == '__main__':
    main()
