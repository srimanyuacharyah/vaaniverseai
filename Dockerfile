FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (ffmpeg for audio processing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src
COPY data ./data

# Set environment
ENV PYTHONPATH=/app/src
ENV VAANIVERSE_DB=/tmp/vaaniverse.db

EXPOSE 8000

# Use PORT env var from Render (defaults to 8000)
CMD ["sh", "-c", "python -m uvicorn vaaniverse.web:app --host 0.0.0.0 --port ${PORT:-8000}"]
