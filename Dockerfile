# Podcast Archive RAG Server
# Multi-stage build for smaller final image

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements-rag.txt .
RUN pip install --no-cache-dir -r requirements-rag.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Create directories for volumes
RUN mkdir -p /app/logs /app/rag_db_v2 /app/data \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser scripts/ /app/scripts/

# Switch to non-root user
USER appuser

# Environment variables with defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RAG_DB_PATH=/app/rag_db_v2 \
    RAG_RATE_LIMIT=100 \
    RAG_REQUIRE_AUTH=false \
    RAG_CORS_ORIGINS=http://localhost:3000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the server
CMD ["python", "-m", "scripts.rag_server"]
