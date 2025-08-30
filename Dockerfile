FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies required for mysqlclient and other packages
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/logs
RUN mkdir -p /app/media/book_covers
RUN mkdir -p /app/media/profile_pics
RUN mkdir -p /app/static

# Collect static files
RUN python manage.py collectstatic --noinput

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "nta_library.wsgi:application"]