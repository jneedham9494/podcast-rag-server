"""
Named entity extraction and normalization.
"""

import subprocess
import sys
from typing import Dict

from .json_utils import parse_json_safely


def extract_entities_spacy(text: str) -> Dict[str, list]:
    """
    Extract named entities using spaCy.

    Args:
        text: Transcript text

    Returns:
        Dictionary with entity categories as keys and lists of entities
    """
    import spacy

    # Load model (will be cached after first load)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("  Downloading spaCy model...")
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            capture_output=True
        )
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


def normalize_entities_ollama(
    entities: Dict[str, list],
    model: str = "llama3:8b"
) -> Dict[str, list]:
    """
    Use LLM to normalize entity variants and remove noise.

    Args:
        entities: Dictionary of entities by category
        model: Ollama model to use

    Returns:
        Entities with normalized names
    """
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
