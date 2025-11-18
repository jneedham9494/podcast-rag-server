#!/usr/bin/env python3
"""
Extract book recommendations from podcast transcripts using RAG + LLM
"""

import requests
import json
import sys
from typing import List, Dict

def search_rag_server(query: str, n_results: int = 50) -> List[Dict]:
    """Search the RAG server for relevant transcript chunks"""
    response = requests.post('http://localhost:8000/search',
        json={'query': query, 'n_results': n_results})
    return response.json()['results']


def extract_books_with_llm_prompt(results: List[Dict]) -> str:
    """
    Generate a prompt for an LLM to extract book recommendations

    You can paste this into Claude.ai, ChatGPT, or use with the Anthropic API
    """

    # Build context from search results
    context_sections = []
    for i, result in enumerate(results, 1):
        podcast = result['metadata']['podcast_name']
        episode = result['metadata'].get('episode_filename', 'Unknown')
        text = result['text']

        context_sections.append(f"""
### Segment {i} from {podcast}
Episode: {episode}
Content:
{text}
""")

    full_context = "\n".join(context_sections)

    prompt = f"""I have {len(results)} transcript segments from various podcasts. Please analyze them and extract all book recommendations mentioned.

For each book, provide:
1. Book title
2. Author (if mentioned)
3. Which podcast/episode mentioned it
4. Context (why was it recommended, what was said about it)

Please format as a markdown list.

TRANSCRIPT SEGMENTS:
{full_context}

Please extract and list all book recommendations found in these segments."""

    return prompt


def extract_books_quick_analysis(results: List[Dict]) -> Dict:
    """
    Quick local analysis to identify potential book mentions
    (without requiring an LLM API)
    """

    book_indicators = [
        'book', 'read', 'author', 'wrote', 'published',
        'novel', 'recommend', 'reading list', 'title'
    ]

    likely_book_mentions = []

    for result in results:
        text = result['text'].lower()

        # Check if text contains book indicators
        if any(indicator in text for indicator in book_indicators):
            likely_book_mentions.append({
                'podcast': result['metadata']['podcast_name'],
                'episode': result['metadata'].get('episode_filename', 'Unknown'),
                'text': result['text'][:500],  # First 500 chars
                'score': result['score']
            })

    return {
        'total_segments': len(results),
        'likely_book_mentions': len(likely_book_mentions),
        'segments': likely_book_mentions
    }


def main():
    """Main function to extract book recommendations"""

    print("="*80)
    print("BOOK RECOMMENDATION EXTRACTOR")
    print("="*80)
    print()

    # Check if RAG server is running
    try:
        response = requests.get('http://localhost:8000/')
        if response.status_code != 200:
            print("Error: RAG server not responding at http://localhost:8000/")
            print("Please start the server with: python3 scripts/rag_server.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to RAG server at http://localhost:8000/")
        print("Please start the server with: python3 scripts/rag_server.py")
        sys.exit(1)

    print("✓ Connected to RAG server")
    print()

    # Search for book-related content
    print("Searching for book recommendations...")
    search_queries = [
        "book recommendation I recommend reading",
        "author wrote book published",
        "reading list favorite books"
    ]

    all_results = []
    seen_ids = set()

    for query in search_queries:
        print(f"  Query: '{query}'")
        results = search_rag_server(query, n_results=20)

        # Deduplicate results
        for result in results:
            if result['id'] not in seen_ids:
                all_results.append(result)
                seen_ids.add(result['id'])

    print(f"✓ Found {len(all_results)} unique relevant segments")
    print()

    # Quick analysis
    print("Analyzing segments for book mentions...")
    analysis = extract_books_quick_analysis(all_results)

    print(f"✓ Found {analysis['likely_book_mentions']} segments with likely book mentions")
    print()

    # Show sample mentions
    print("="*80)
    print("SAMPLE BOOK MENTIONS")
    print("="*80)
    print()

    for i, segment in enumerate(analysis['segments'][:10], 1):
        print(f"{i}. {segment['podcast']}")
        print(f"   Episode: {segment['episode']}")
        print(f"   Relevance: {segment['score']:.4f}")
        print(f"   Text: {segment['text'][:250]}...")
        print()

    if len(analysis['segments']) > 10:
        print(f"... and {len(analysis['segments']) - 10} more segments")
        print()

    # Generate LLM prompt
    print("="*80)
    print("NEXT STEP: USE AN LLM TO EXTRACT BOOKS")
    print("="*80)
    print()
    print("The RAG server found relevant segments. Now you can:")
    print()
    print("1. Generate an LLM prompt to extract books:")
    print("   python3 scripts/extract_book_recommendations.py > llm_prompt.txt")
    print()
    print("2. Copy the prompt and paste it into:")
    print("   - Claude.ai (https://claude.ai)")
    print("   - ChatGPT (https://chat.openai.com)")
    print("   - Or use the Anthropic/OpenAI API")
    print()

    # Ask user if they want to generate the prompt
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-prompt':
        print("="*80)
        print("GENERATED LLM PROMPT")
        print("="*80)
        print()
        prompt = extract_books_with_llm_prompt(all_results)
        print(prompt)
        print()
        print("="*80)
        print("Copy the prompt above and paste it into your LLM")
        print("="*80)
    else:
        print("To generate the full LLM prompt, run:")
        print("  python3 scripts/extract_book_recommendations.py --generate-prompt")

    # Save results
    output_file = 'book_recommendations_raw.json'
    with open(output_file, 'w') as f:
        json.dump({
            'total_segments': len(all_results),
            'analysis': analysis,
            'raw_segments': [
                {
                    'podcast': r['metadata']['podcast_name'],
                    'episode': r['metadata'].get('episode_filename'),
                    'text': r['text'],
                    'score': r['score']
                }
                for r in all_results
            ]
        }, f, indent=2)

    print()
    print(f"✓ Raw data saved to: {output_file}")
    print()


if __name__ == '__main__':
    main()
