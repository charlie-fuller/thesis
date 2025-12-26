# Backend-only Dockerfile for Thesis
# Frontend is deployed separately to Vercel
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy help docs
COPY docs/help ./docs_help

# Expose port (Railway uses dynamic PORT)
EXPOSE 8000

# Start command - uses PORT env var from Railway, defaults to 8000
CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
