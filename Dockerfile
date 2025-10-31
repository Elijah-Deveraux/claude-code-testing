# ============================================================================
# Multi-stage Dockerfile for PDF Summarization System
# ============================================================================
# This Dockerfile builds a production-ready image for the PDF summarization app
# with both FastAPI backend and Streamlit frontend.
#
# Build: docker build -t pdf-summarizer:latest .
# Run:   docker run -p 8000:8000 -p 8501:8501 --env-file .env pdf-summarizer:latest
# ============================================================================

# ============================================================================
# Stage 1: Base Python Image with Dependencies
# ============================================================================
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials for Python packages
    gcc \
    g++ \
    make \
    # PDF processing libraries
    libpoppler-cpp-dev \
    poppler-utils \
    # SSL and networking
    libssl-dev \
    ca-certificates \
    curl \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# ============================================================================
# Stage 2: Dependencies Installation
# ============================================================================
FROM base AS dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    # Remove build dependencies to reduce image size
    apt-get remove -y gcc g++ make && \
    apt-get autoremove -y

# ============================================================================
# Stage 3: Application Build
# ============================================================================
FROM python:3.12-slim AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:${PYTHONPATH}"

# Install only runtime dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-cpp0v5 \
    poppler-utils \
    ca-certificates \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./frontend ./frontend
COPY --chown=appuser:appuser ./tests ./tests
COPY --chown=appuser:appuser ./requirements.txt ./requirements.txt

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/uploads && \
    chown -R appuser:appuser /app/logs /app/data /app/uploads

# Copy startup script
COPY --chown=appuser:appuser <<'EOF' /app/docker-entrypoint.sh
#!/bin/bash
set -e

echo "=========================================="
echo "PDF Summarization System - Starting"
echo "=========================================="

# Function to check if backend is ready
wait_for_backend() {
    echo "Waiting for backend API to be ready..."
    for i in {1..30}; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "Backend API is ready!"
            return 0
        fi
        echo "Attempt $i/30: Backend not ready yet..."
        sleep 2
    done
    echo "ERROR: Backend did not start in time"
    return 1
}

# Start backend in background
echo "Starting FastAPI backend on port 8000..."
uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-level info &

BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
if ! wait_for_backend; then
    echo "Failed to start backend. Exiting..."
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start Streamlit frontend
echo "Starting Streamlit frontend on port 8501..."
streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none \
    --browser.gatherUsageStats false &

FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo "=========================================="
echo "Application started successfully!"
echo "Backend API:  http://localhost:8000"
echo "Frontend UI:  http://localhost:8501"
echo "API Docs:     http://localhost:8000/docs"
echo "=========================================="

# Function to handle shutdown
shutdown() {
    echo "Shutting down gracefully..."
    kill $FRONTEND_PID 2>/dev/null || true
    kill $BACKEND_PID 2>/dev/null || true
    wait $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
    echo "Shutdown complete"
    exit 0
}

# Trap signals
trap shutdown SIGTERM SIGINT

# Wait for processes
wait
EOF

# Make startup script executable
RUN chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# ============================================================================
# Build Information (metadata labels)
# ============================================================================
LABEL maintainer="PDF Summarization System"
LABEL version="1.0.0"
LABEL description="FastAPI + Streamlit PDF Summarization with AI"
LABEL org.opencontainers.image.source="https://github.com/your-repo/pdf-summarizer"
