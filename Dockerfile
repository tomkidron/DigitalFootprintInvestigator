# Use Python 3.12 slim image (smaller, faster)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for outputs and create a non-root user
RUN mkdir -p reports logs \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

# Use a non-root user for running the app
USER appuser

# Set default command
CMD ["python", "main.py"]
