# Combined Dockerfile for Frontend + Backend
FROM python:3.12-slim AS base

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# ============================================
# Backend Setup
# ============================================
COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

COPY backend/app ./backend/app

# Create preview directories (will be owned by appuser later)
RUN mkdir -p /app/backend/previews/builds /app/backend/previews/shared_template

# ============================================
# Frontend Setup
# ============================================
# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json* ./frontend/

# Install frontend dependencies (with devDependencies for build tools)
WORKDIR /app/frontend
RUN NODE_ENV=development npm ci

# Copy frontend source code
COPY frontend/ ./

# Accept build arguments for frontend
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

# Set environment variables for build
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

# Suppress ESLint/Prettier warnings during build
ENV ESLINT_NO_DEV_ERRORS=true
ENV NEXT_IGNORE_ESLINT=true

# Build frontend (warnings will be suppressed)
RUN npm run build

# Copy public folder and static files to standalone directory
# The standalone server.js looks for .next/static relative to its location
WORKDIR /app/frontend
RUN mkdir -p .next/standalone/.next && \
    cp -r .next/static .next/standalone/.next/static && \
    if [ -d public ]; then cp -r public .next/standalone/public; fi

# ============================================
# Production Setup
# ============================================
WORKDIR /app

# Create non-root user and configure npm
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/.npm-cache && \
    chown -R appuser:appuser /app && \
    mkdir -p /home/appuser/.npm && \
    chown -R appuser:appuser /home/appuser && \
    # Ensure preview directories are writable
    chown -R appuser:appuser /app/backend/previews

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d && \
    echo '[supervisord]' > /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo '' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo '[program:backend]' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'command=uvicorn app.main:app --host 0.0.0.0 --port 8000' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'directory=/app/backend' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'user=appuser' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'stderr_logfile=/var/log/backend.err.log' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'stdout_logfile=/var/log/backend.out.log' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'environment=PYTHONUNBUFFERED=1,HOME="/home/appuser",NPM_CONFIG_CACHE="/app/.npm-cache"' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo '' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo '[program:frontend]' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'command=node server.js' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'directory=/app/frontend/.next/standalone' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'user=appuser' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'stderr_logfile=/var/log/frontend.err.log' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'stdout_logfile=/var/log/frontend.out.log' >> /etc/supervisor/conf.d/sitesmith.conf && \
    echo 'environment=NODE_ENV=production,PORT=3000,HOSTNAME="0.0.0.0"' >> /etc/supervisor/conf.d/sitesmith.conf

# Create log directory
RUN mkdir -p /var/log && chown -R appuser:appuser /var/log

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health && curl -f http://localhost:3000 || exit 1

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/sitesmith.conf"]

