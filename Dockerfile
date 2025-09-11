FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies in a single layer with optimizations
RUN echo "deb http://deb.debian.org/debian trixie main" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential libmariadb-dev libmariadb-dev-compat python3-dev curl apt-transport-https ca-certificates pkg-config \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first (as root)
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create non-root user for security
RUN groupadd -r django && useradd -r -g django django

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/media/book_covers /app/media/profile_pics /app/static /app/staticfiles \
    && chown -R django:django /app

# Copy project files
COPY --chown=django:django . /app/

# Switch to non-root user
USER django

# Collect static files (only if DJANGO_SETTINGS_MODULE is properly set)
RUN python manage.py collectstatic --noinput --settings=nta_library.settings || echo "Static files collection skipped"

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health/ || exit 1

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["web"]