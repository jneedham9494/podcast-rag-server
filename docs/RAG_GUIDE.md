# Podcast Transcript RAG Server

## Overview
A local RAG (Retrieval-Augmented Generation) server for semantic search across podcast transcripts. Built with ChromaDB, sentence-transformers, and FastAPI.

## System Architecture

```
Technology Stack:
├── Vector DB: ChromaDB (persistent, embedded)
├── Embeddings: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions, local)
├── API Framework: FastAPI with automatic OpenAPI docs
└── Data: 5,494+ podcast transcripts (3.6GB+)
```

## Quick Start

### 1. Building the Index

```bash
# Run the indexer to process all transcripts
python3 scripts/build_rag_index.py

# The indexer will:
# - Scan transcripts/ directory for all .txt files
# - Chunk transcripts (~1000 chars per chunk with 200 char overlap)
# - Generate embeddings using sentence-transformers
# - Store in ChromaDB at ./rag_db/
# - Resume from where it left off if interrupted
```

### 2. Starting the Server

```bash
# Start the RAG server
python3 scripts/rag_server.py

# Server will start on: http://localhost:8000
# API docs available at: http://localhost:8000/docs
```

### 3. Running in Background

```bash
# Start indexer in background
nohup python3 -u scripts/build_rag_index.py > logs/build_rag_index.log 2>&1 &

# Start server in background
nohup python3 -u scripts/rag_server.py > logs/rag_server.log 2>&1 &
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/
```

### Get Collection Statistics
```bash
curl http://localhost:8000/stats
```

**Response:**
```json
{
  "total_documents": 3471,
  "total_podcasts": 23,
  "collection_name": "podcast_transcripts",
  "embedding_dimension": 384
}
```

### List All Podcasts
```bash
curl http://localhost:8000/podcasts
```

**Response:**
```json
{
  "podcasts": [
    "5CAST w Andrew Callaghan",
    "Bad Bets",
    "Block Stars with David Schwartz",
    "Blowback",
    "Chapo Trap House",
    ...
  ],
  "total": 23
}
```

### Semantic Search
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cryptocurrency and blockchain technology",
    "n_results": 5
  }'
```

**Response:**
```json
{
  "query": "cryptocurrency and blockchain technology",
  "results": [
    {
      "id": "26b0d1fdfba9492cc88a8f0c6c69fbcb",
      "text": "Welcome to Blockstars. Ripple's podcast...",
      "score": 0.8234,
      "metadata": {
        "podcast_name": "Block Stars with David Schwartz",
        "episode_filename": "Episode_123.txt",
        "chunk_index": 0,
        "total_chunks": 5
      }
    },
    ...
  ],
  "total_results": 5
}
```

### Search with Filters
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "economic policy",
    "n_results": 3,
    "filter_podcast": "Odd Lots"
  }'
```

### Get Podcast Information
```bash
curl http://localhost:8000/podcast/Hello%20Internet
```

**Response:**
```json
{
  "podcast_name": "Hello Internet",
  "total_chunks": 76,
  "total_episodes": 76,
  "sample_episodes": ["H.I. #1 - ...", "H.I. #2 - ...", ...]
}
```

## Python Client Example

```python
import requests

# Search for content
response = requests.post('http://localhost:8000/search',
    json={
        'query': 'artificial intelligence and machine learning',
        'n_results': 10
    })

results = response.json()
for result in results['results']:
    print(f"Podcast: {result['metadata']['podcast_name']}")
    print(f"Score: {result['score']:.4f}")
    print(f"Text: {result['text'][:200]}...")
    print("-" * 80)
```

## Using with LLMs

The RAG server can be integrated with LLMs (Claude, GPT-4, etc.) to provide context-aware responses:

### Example: Claude Integration

```python
import anthropic
import requests

def search_podcasts(query):
    """Search podcast transcripts"""
    response = requests.post('http://localhost:8000/search',
        json={'query': query, 'n_results': 5})
    return response.json()['results']

def ask_claude_with_context(question):
    """Ask Claude with podcast transcript context"""
    # Search for relevant transcripts
    results = search_podcasts(question)

    # Build context from search results
    context = "\n\n".join([
        f"From {r['metadata']['podcast_name']}:\n{r['text']}"
        for r in results
    ])

    # Query Claude with context
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Based on the following podcast transcripts, please answer this question:

Question: {question}

Context from podcasts:
{context}

Please cite which podcast the information came from."""
        }]
    )

    return message.content

# Example usage
response = ask_claude_with_context(
    "What were the main points discussed about blockchain security?"
)
print(response)
```

## File Structure

```
.
├── rag_db/                          # ChromaDB persistent storage
├── transcripts/                     # Source transcript files
│   ├── Podcast Name 1/
│   │   ├── episode1.txt
│   │   ├── episode2.txt
│   │   └── ...
│   └── Podcast Name 2/
│       └── ...
├── scripts/
│   ├── build_rag_index.py          # Indexer script
│   └── rag_server.py                # FastAPI server
└── logs/
    ├── build_rag_index.log          # Indexer logs
    └── rag_server.log               # Server logs
```

## Configuration

### Chunk Size Tuning

Edit `scripts/build_rag_index.py`:

```python
indexer = TranscriptIndexer(
    transcripts_dir=transcripts_dir,
    metadata_dir=metadata_dir,
    db_path=db_path,
    chunk_size=1000,      # Adjust chunk size (default: 1000 chars)
    chunk_overlap=200     # Adjust overlap (default: 200 chars)
)
```

### Server Port

Edit `scripts/rag_server.py`:

```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,           # Change port here
    log_level="info"
)
```

## Performance

- **Embedding Generation**: ~50-100 transcripts/min (local CPU)
- **Search Latency**: ~100-300ms per query
- **Collection Size**: 3,471+ documents (growing)
- **Storage**: ~100MB for ChromaDB index

## Future Enhancements

1. **Speaker Diarization**: Add "who is speaking when" labels using pyannote.audio
2. **Timestamp Alignment**: Link chunks back to specific audio timestamps
3. **Multi-Modal Search**: Search by audio or image content
4. **Hybrid Search**: Combine semantic search with keyword filtering
5. **Production Deployment**: Add authentication, rate limiting, caching
6. **Advanced Filtering**: Date ranges, duration, episode metadata

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill <PID>
```

### Indexer Not Finding Transcripts
```bash
# Verify directory structure
ls -la transcripts/

# Check indexer is running from project root
pwd  # Should be /Users/jackdev/development/reading-list
```

### ChromaDB Not Found
```bash
# Rebuild the index
python3 scripts/build_rag_index.py
```

## Current Status

**As of Last Run:**
- ✅ 3,471+ documents indexed
- ✅ 23 podcasts available (38 total in progress)
- ✅ Server running on http://localhost:8000
- ✅ Interactive docs at http://localhost:8000/docs
- 🔄 Indexer continuing to process remaining transcripts

**Test Queries Verified:**
- "cryptocurrency and blockchain technology" ✓
- "Hello Internet podcast" with filters ✓
- General semantic search ✓
- Podcast-specific filtering ✓
