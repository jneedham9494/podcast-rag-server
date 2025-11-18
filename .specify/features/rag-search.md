# Feature: RAG Search

## Status
Retroactive specification for existing feature

## Overview
Semantic search system using Retrieval-Augmented Generation (RAG) over podcast transcripts. Includes index builder and API server.

## Current Behavior

### Index Builder (build_rag_index_v2.py)
- Reads all transcript files
- Chunks text into segments
- Generates embeddings using sentence-transformers
- Stores in ChromaDB vector database

### API Server (rag_server.py)
- FastAPI server with REST endpoints
- Semantic search over indexed transcripts
- Filter by podcast name
- Returns similarity scores and metadata

## Technical Implementation
- **Locations**:
  - [build_rag_index_v2.py](scripts/build_rag_index_v2.py) (~16KB)
  - [rag_server.py](scripts/rag_server.py) (~8KB)
- **Dependencies**: sentence-transformers, chromadb, fastapi, uvicorn, pydantic
- **Dependents**: None (end-user service)
- **Database**: `rag_db_v2/` (ChromaDB)
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`

## Acceptance Criteria (Current State)

### Index Building
- GIVEN transcripts directory
  WHEN builder runs
  THEN creates ChromaDB with all transcript chunks

- GIVEN new transcripts added
  WHEN builder runs
  THEN adds new transcripts to existing index

### API Server

#### Health Check
- GIVEN server running
  WHEN GET /
  THEN returns status "online"

#### Search
- GIVEN search query
  WHEN POST /search with query text
  THEN returns ranked results with similarity scores

- GIVEN search with filter_podcast
  WHEN POST /search
  THEN returns only results from that podcast

#### Info Endpoints
- GIVEN server running
  WHEN GET /stats
  THEN returns document count, podcast count, embedding dimension

- GIVEN server running
  WHEN GET /podcasts
  THEN returns list of all indexed podcast names

- GIVEN podcast name
  WHEN GET /podcast/{name}
  THEN returns chunk count, episode count, sample episodes

### Error Handling
- GIVEN no ChromaDB index
  WHEN server starts
  THEN fails with clear error message

- GIVEN invalid search query
  WHEN POST /search with empty query
  THEN returns 422 validation error

## Known Issues / Tech Debt

- [ ] **Global state** - Uses global variables for DB/model
- [ ] **No pagination** - `/podcasts` loads all data into memory
- [ ] **CORS wide open** - Allows all origins (security concern)
- [ ] **No authentication** - API is completely open
- [ ] **No rate limiting** - Can be overwhelmed
- [ ] **No caching** - Same queries re-compute embeddings
- [ ] **No incremental index** - Full rebuild required for updates

## Future Improvements

- [ ] Add API authentication (API keys)
- [ ] Implement rate limiting
- [ ] Add result pagination
- [ ] Implement query caching
- [ ] Add incremental index updates
- [ ] Add date filtering (requires metadata enrichment)
- [ ] Restrict CORS for production
- [ ] Add pytest tests with sample index
- [ ] Add health check for ChromaDB connection
- [ ] Containerize with Docker
