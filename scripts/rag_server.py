#!/usr/bin/env python3
"""
RAG Server for Podcast Transcripts
Provides semantic search and retrieval endpoints via FastAPI
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import uvicorn
import os
import time
from collections import defaultdict
from loguru import logger

# Configure logging
logger.add(
    "logs/rag_server.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Security configuration from environment
API_KEYS = os.environ.get("RAG_API_KEYS", "").split(",")
API_KEYS = [k.strip() for k in API_KEYS if k.strip()]  # Clean empty strings
CORS_ORIGINS = os.environ.get("RAG_CORS_ORIGINS", "http://localhost:3000").split(",")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS if o.strip()]
RATE_LIMIT_REQUESTS = int(os.environ.get("RAG_RATE_LIMIT", "100"))  # requests per minute
REQUIRE_AUTH = os.environ.get("RAG_REQUIRE_AUTH", "false").lower() == "true"

# Rate limiting storage
rate_limit_storage: Dict[str, List[float]] = defaultdict(list)

# Global state with type hints
db_client: Optional[chromadb.ClientAPI] = None
collection: Optional[Collection] = None
embedding_model: Optional[SentenceTransformer] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan: startup and shutdown."""
    global db_client, collection, embedding_model

    # Startup
    db_path = Path("rag_db_v2")

    if not db_path.exists():
        raise RuntimeError(
            f"ChromaDB not found at {db_path}. "
            "Please run build_rag_index_v2.py first to create the index."
        )

    print("Initializing ChromaDB client...")
    db_client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False)
    )

    print("Loading collection...")
    try:
        collection = db_client.get_collection(name="podcast_transcripts")
        print(f"Collection loaded: {collection.count()} documents")
    except Exception as e:
        raise RuntimeError(f"Failed to load collection 'podcast_transcripts': {e}")

    print("Loading embedding model...")
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"Model loaded. Embedding dimension: {embedding_model.get_sentence_embedding_dimension()}")

    print("\n" + "=" * 80)
    print("RAG SERVER READY")
    print("=" * 80)
    print(f"Collection: {collection.count()} documents indexed")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Auth Required: {REQUIRE_AUTH}")
    print(f"API Keys Configured: {len(API_KEYS)}")
    print(f"CORS Origins: {CORS_ORIGINS}")
    print(f"Rate Limit: {RATE_LIMIT_REQUESTS} req/min")
    print("=" * 80 + "\n")

    logger.info(f"Server started - Auth: {REQUIRE_AUTH}, Keys: {len(API_KEYS)}, Rate: {RATE_LIMIT_REQUESTS}/min")

    yield  # Server runs here

    # Shutdown
    print("Shutting down RAG server...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Podcast Transcript RAG API",
    description="Semantic search and retrieval for podcast transcripts",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# API Key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def mask_api_key(key: str) -> str:
    """Mask API key for logging (show first 4 and last 4 chars)."""
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def check_rate_limit(client_id: str) -> bool:
    """
    Check if client has exceeded rate limit.

    Returns True if request is allowed, False if rate limited.
    """
    now = time.time()
    minute_ago = now - 60

    # Clean old entries
    rate_limit_storage[client_id] = [
        ts for ts in rate_limit_storage[client_id] if ts > minute_ago
    ]

    # Check limit
    if len(rate_limit_storage[client_id]) >= RATE_LIMIT_REQUESTS:
        return False

    # Record this request
    rate_limit_storage[client_id].append(now)
    return True


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[str]:
    """
    Verify API key and check rate limits.

    Returns the API key if valid, None if auth not required.
    Raises HTTPException for auth failures.
    """
    client_ip = request.client.host if request.client else "unknown"

    # If auth is not required and no key provided, allow but rate limit by IP
    if not REQUIRE_AUTH and not api_key:
        if not check_rate_limit(f"ip:{client_ip}"):
            logger.warning(f"Rate limit exceeded for IP {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        return None

    # If auth is required but no key provided
    if REQUIRE_AUTH and not api_key:
        logger.warning(f"Missing API key from {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="API key required. Include X-API-Key header."
        )

    # If key provided, validate it
    if api_key:
        if not API_KEYS:
            # No keys configured but one was provided - warn and allow
            logger.warning("API key provided but no keys configured")
        elif api_key not in API_KEYS:
            logger.warning(f"Invalid API key {mask_api_key(api_key)} from {client_ip}")
            raise HTTPException(
                status_code=403,
                detail="Invalid API key."
            )

        # Rate limit by API key
        if not check_rate_limit(f"key:{mask_api_key(api_key)}"):
            logger.warning(f"Rate limit exceeded for key {mask_api_key(api_key)}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

        return api_key

    return None


def log_request(
    request: Request,
    api_key: Optional[str],
    endpoint: str,
    response_time_ms: float
) -> None:
    """Log API request for audit trail."""
    client_ip = request.client.host if request.client else "unknown"
    key_info = mask_api_key(api_key) if api_key else "no-key"
    logger.info(
        f"API Request | {endpoint} | {client_ip} | {key_info} | {response_time_ms:.2f}ms"
    )


# Request/Response Models
class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query text", min_length=1)
    n_results: int = Field(10, description="Number of results to return", ge=1, le=100)
    filter_podcast: Optional[str] = Field(None, description="Filter by podcast name")
    filter_date_from: Optional[str] = Field(None, description="Filter episodes from this date (YYYY-MM-DD)")
    filter_date_to: Optional[str] = Field(None, description="Filter episodes to this date (YYYY-MM-DD)")


class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int


class StatsResponse(BaseModel):
    total_documents: int
    total_podcasts: int
    collection_name: str
    embedding_dimension: int


# API Endpoints
@app.get("/", tags=["Health"])
async def root() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Podcast Transcript RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/stats", response_model=StatsResponse, tags=["Info"])
async def get_stats(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """Get collection statistics"""
    start_time = time.time()

    if collection is None:
        raise HTTPException(status_code=503, detail="Collection not initialized")

    # Get all metadata to count unique podcasts
    all_data = collection.get(limit=1000000)  # Get all docs
    podcasts = set()
    if all_data and all_data['metadatas']:
        for meta in all_data['metadatas']:
            if 'podcast_name' in meta:
                podcasts.add(meta['podcast_name'])

    response = StatsResponse(
        total_documents=collection.count(),
        total_podcasts=len(podcasts),
        collection_name=collection.name,
        embedding_dimension=embedding_model.get_sentence_embedding_dimension()
    )

    log_request(request, api_key, "GET /stats", (time.time() - start_time) * 1000)
    return response


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    query: SearchQuery,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
):
    """
    Semantic search over podcast transcripts

    Returns the most relevant transcript chunks based on the query.
    Optionally filter by podcast name or date range.
    """
    start_time = time.time()

    if collection is None or embedding_model is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    # Build filter clause
    where_clause = {}
    if query.filter_podcast:
        where_clause['podcast_name'] = query.filter_podcast

    # Note: ChromaDB filtering is limited. Date filtering would require
    # fetching results and filtering in Python for more complex queries.
    # For now, we'll keep it simple with podcast name filtering.

    try:
        # Generate query embedding
        query_embedding = embedding_model.encode([query.query])[0].tolist()

        # Search collection
        search_params = {
            'query_embeddings': [query_embedding],
            'n_results': query.n_results,
        }

        if where_clause:
            search_params['where'] = where_clause

        results = collection.query(**search_params)

        # Format results
        formatted_results = []
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                result = SearchResult(
                    id=results['ids'][0][i],
                    text=results['documents'][0][i],
                    score=1.0 - results['distances'][0][i],  # Convert distance to similarity score
                    metadata=results['metadatas'][0][i]
                )
                formatted_results.append(result)

        response = SearchResponse(
            query=query.query,
            results=formatted_results,
            total_results=len(formatted_results)
        )

        log_request(request, api_key, "POST /search", (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/podcasts", tags=["Info"])
async def list_podcasts(
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
) -> Dict[str, Any]:
    """List all available podcast names in the collection"""
    start_time = time.time()

    if collection is None:
        raise HTTPException(status_code=503, detail="Collection not initialized")

    try:
        # Get all documents (or sample if too large)
        all_data = collection.get(limit=1000000)
        podcasts = set()

        if all_data and all_data['metadatas']:
            for meta in all_data['metadatas']:
                if 'podcast_name' in meta:
                    podcasts.add(meta['podcast_name'])

        response = {
            "podcasts": sorted(list(podcasts)),
            "total": len(podcasts)
        }

        log_request(request, api_key, "GET /podcasts", (time.time() - start_time) * 1000)
        return response

    except Exception as e:
        logger.error(f"Failed to list podcasts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list podcasts: {str(e)}")


@app.get("/podcast/{podcast_name}", tags=["Info"])
async def get_podcast_info(
    podcast_name: str,
    request: Request,
    api_key: Optional[str] = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Get information about a specific podcast"""
    start_time = time.time()

    if collection is None:
        raise HTTPException(status_code=503, detail="Collection not initialized")

    try:
        # Query for this podcast
        results = collection.get(
            where={"podcast_name": podcast_name},
            limit=1000000
        )

        if not results or not results['ids']:
            raise HTTPException(status_code=404, detail=f"Podcast not found: {podcast_name}")

        # Count episodes (unique episode filenames)
        episodes = set()
        for meta in results['metadatas']:
            if 'episode_filename' in meta:
                episodes.add(meta['episode_filename'])

        response = {
            "podcast_name": podcast_name,
            "total_chunks": len(results['ids']),
            "total_episodes": len(episodes),
            "sample_episodes": sorted(list(episodes))[:10]
        }

        log_request(request, api_key, f"GET /podcast/{podcast_name}", (time.time() - start_time) * 1000)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get podcast info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get podcast info: {str(e)}")


# Main entry point
def main() -> None:
    """Run the server"""
    print("\nStarting RAG server...")
    print("This will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        app,
        host="0.0.0.0",  # Listen on all interfaces (localhost and network)
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
