# ML Service Dockerfile for SALF
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_NAME=all-MiniLM-L6-v2 \
    DEVICE=cpu

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu \
    sentence-transformers==2.2.2 \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    numpy==1.26.3 \
    scikit-learn==1.4.0

# Download model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${MODEL_NAME}')"

# Copy application code
COPY ml_service.py .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["uvicorn", "ml_service:app", "--host", "0.0.0.0", "--port", "8001"]
