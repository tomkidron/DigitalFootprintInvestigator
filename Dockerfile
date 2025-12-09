# Use Python 3.12 slim image (smaller, faster)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (if needed for web scraping)
# Copy requirements first (for better caching)
COPY requirements.txt .

# Install build dependencies, install Python deps, then remove build deps
# This reduces final image size and keeps useful pip caching behavior.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc libssl-dev libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create directories for outputs and create a non-root user
RUN mkdir -p reports logs \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

# Use a non-root user for running the app
USER appuser

# Set default command
ENTRYPOINT ["python", "main.py"]

# Default argument (can be overridden)
CMD ["--help"]
