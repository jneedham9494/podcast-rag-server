"""
Keyword extraction utilities using KeyBERT.
"""

from typing import List


def extract_keywords(text: str, top_n: int = 20) -> List[str]:
    """
    Extract keywords using KeyBERT.

    Args:
        text: Transcript text
        top_n: Number of keywords to extract

    Returns:
        List of extracted keywords
    """
    from keybert import KeyBERT

    # Initialize KeyBERT with sentence-transformers
    kw_model = KeyBERT('all-MiniLM-L6-v2')

    # Limit text length for performance
    max_chars = 50000
    if len(text) > max_chars:
        # Sample from beginning, middle, end
        third = max_chars // 3
        mid_start = len(text) // 2 - third // 2
        mid_end = len(text) // 2 + third // 2
        sample = text[:third] + text[mid_start:mid_end] + text[-third:]
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
