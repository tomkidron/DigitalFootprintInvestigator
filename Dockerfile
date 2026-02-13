# Use Python 3.12 slim image (smaller, faster)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Streamlit Configuration
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_SERVER_HEADLESS=true \
    # Playwright Configuration
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system dependencies (curl for healthcheck + Playwright deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their system dependencies
RUN mkdir -p /ms-playwright && \
    playwright install-deps chromium && \
    playwright install chromium && \
    chmod -R 777 /ms-playwright

# Copy application code
COPY . .

# Create directories for outputs and create a non-root user
RUN mkdir -p reports logs \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

# Use a non-root user for running the app
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Healthcheck to ensure container is ready
# Use --fail to return non-zero exit code if HTTP status is error
# Increase interval to avoid spamming the logs/server
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set default command to run Streamlit
CMD ["streamlit", "run", "app.py"]
