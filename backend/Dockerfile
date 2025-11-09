# Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including Node.js and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY ./app ./app

# Copy preview template files (needed for vite_preview_service)
COPY ./previews/shared_template ./previews/shared_template

# Create directories for preview builds
RUN mkdir -p /app/previews/builds

# Create non-root user and configure npm
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/.npm-cache && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.npm && \
    chown -R appuser:appuser /home/appuser

# Set npm cache directory and HOME for appuser
ENV NPM_CONFIG_CACHE=/app/.npm-cache \
    HOME=/home/appuser

USER appuser

# Expose port
EXPOSE 8000

# Health check using curl (already installed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
