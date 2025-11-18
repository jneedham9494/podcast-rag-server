"""
JSON repair and parsing utilities for handling LLM output.
"""

import json
import re
from typing import Any


def repair_json(text: str) -> str:
    """
    Attempt to repair common JSON formatting issues from LLM output.

    Fixes:
    - Single quotes -> double quotes
    - Trailing commas
    - Missing quotes around keys
    - Unescaped newlines in strings

    Args:
        text: Raw text containing JSON

    Returns:
        Repaired JSON string
    """
    # Strip any preamble before the JSON
    start = text.find('{')
    end = text.rfind('}') + 1
    if start < 0 or end <= start:
        return text

    json_str = text[start:end]

    # Replace single quotes with double quotes (but not inside strings)
    json_str = re.sub(r"'([^']*)'(?=\s*:)", r'"\1"', json_str)  # Keys
    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)  # String values

    # Remove trailing commas before } or ]
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)

    # Fix missing colons (e.g., "key" "value" -> "key": "value")
    json_str = re.sub(r'"\s+"', '": "', json_str)

    # Replace actual newlines in string values with \n
    lines = json_str.split('\n')
    json_str = ' '.join(line.strip() for line in lines)

    return json_str


def parse_json_safely(text: str, default: Any = None) -> Any:
    """
    Parse JSON from LLM output with repair attempts.

    Args:
        text: Raw text containing JSON
        default: Default value on failure (defaults to empty dict)

    Returns:
        Parsed JSON or default value on failure
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
