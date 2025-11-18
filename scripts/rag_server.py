#!/usr/bin/env python3
"""
RAG Server for Podcast Transcripts
Provides semantic search and retrieval endpoints via FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Podcast Transcript RAG API",
    description="Semantic search and retrieval for podcast transcripts",
    version="1.0.0"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local use - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
db_client = None
collection = None
embedding_model = None


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


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize ChromaDB and embedding model on startup"""
    global db_client, collection, embedding_model

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

    print("\n" + "="*80)
    print("RAG SERVER READY")
    print("="*80)
    print(f"Collection: {collection.count()} documents indexed")
    print(f"API Docs: http://localhost:8000/docs")
    print("="*80 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down RAG server...")


# API Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Podcast Transcript RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/stats", response_model=StatsResponse, tags=["Info"])
async def get_stats():
    """Get collection statistics"""
    if collection is None:
        raise HTTPException(status_code=503, detail="Collection not initialized")

    # Get all metadata to count unique podcasts
    all_data = collection.get(limit=1000000)  # Get all docs
    podcasts = set()
    if all_data and all_data['metadatas']:
        for meta in all_data['metadatas']:
            if 'podcast_name' in meta:
                podcasts.add(meta['podcast_name'])

    return StatsResponse(
        total_documents=collection.count(),
        total_podcasts=len(podcasts),
        collection_name=collection.name,
        embedding_dimension=embedding_model.get_sentence_embedding_dimension()
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(query: SearchQuery):
    """
    Semantic search over podcast transcripts

    Returns the most relevant transcript chunks based on the query.
    Optionally filter by podcast name or date range.
    """
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

        return SearchResponse(
            query=query.query,
            results=formatted_results,
            total_results=len(formatted_results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/podcasts", tags=["Info"])
async def list_podcasts():
    """List all available podcast names in the collection"""
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

        return {
            "podcasts": sorted(list(podcasts)),
            "total": len(podcasts)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list podcasts: {str(e)}")


@app.get("/podcast/{podcast_name}", tags=["Info"])
async def get_podcast_info(podcast_name: str):
    """Get information about a specific podcast"""
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

        return {
            "podcast_name": podcast_name,
            "total_chunks": len(results['ids']),
            "total_episodes": len(episodes),
            "sample_episodes": sorted(list(episodes))[:10]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get podcast info: {str(e)}")


# Main entry point
def main():
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
