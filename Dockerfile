# ==============================================================================
# Multi-stage Dockerfile for SunnetChat - Production Ready
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and compile packages
# ------------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages to user directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------------------------
FROM python:3.11-slim

# Metadata labels
LABEL maintainer="SunnetChat Team"
LABEL version="1.0.0"
LABEL description="SunnetChat - Intelligent AI Slack Bot with RAG capabilities"
LABEL org.opencontainers.image.source="https://github.com/trionnemesis/sunnetchat"

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OCR support (Chinese Traditional)
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    # File type detection for unstructured package
    libmagic1 \
    # PDF processing
    poppler-utils \
    # DOCX/PPTX processing
    pandoc \
    # Health check utility
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Add Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Environment variables with defaults
ENV PORT=8000 \
    WORKERS=4 \
    LOG_LEVEL=info \
    PYTHONUNBUFFERED=1

# Declare volume for documents
VOLUME ["/app/local_documents"]

# Expose application port
EXPOSE ${PORT}

# Health check - verifies the application is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run the application with multiple workers for production
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WORKERS} --log-level ${LOG_LEVEL}"]
