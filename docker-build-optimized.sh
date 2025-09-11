#!/bin/bash
# Optimized Docker Build Script for Library Management System
# This script addresses common Docker build issues and performance problems

set -e  # Exit on any error

echo "========================================"
echo "  Library Management System - Docker Build"
echo "========================================"
echo

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker is not running or not accessible."
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/6] Checking Docker environment..."
docker --version
docker-compose --version
echo

echo "[2/6] Cleaning up previous builds..."
# Remove dangling images and build cache
docker builder prune -f
docker image prune -f
echo

echo "[3/6] Setting up build environment..."
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
echo "BuildKit enabled for optimized builds"
echo

echo "[4/6] Building web service with optimizations..."
# Build with no-cache to ensure fresh build and parallel processing
if ! docker-compose build --no-cache --parallel web; then
    echo
    echo "========================================"
    echo "  BUILD FAILED - Troubleshooting Tips"
    echo "========================================"
    echo
    echo "Common solutions:"
    echo "1. Check if you have enough disk space (at least 2GB free)"
    echo "2. Restart Docker service: sudo systemctl restart docker"
    echo "3. Clear Docker cache: docker system prune -a"
    echo "4. Check your internet connection for package downloads"
    echo "5. Try building without cache: docker-compose build --no-cache web"
    echo
    echo "If the build is hanging:"
    echo "- Increase Docker memory limit in Docker Desktop settings"
    echo "- Check system resources: htop or top"
    echo "- Close other resource-intensive applications"
    echo "- Try building with: docker build --progress=plain ."
    echo
    exit 1
fi

echo
echo "[5/6] Verifying build..."
docker images | grep library || echo "No library images found"
echo

echo "[6/6] Build completed successfully!"
echo
echo "========================================"
echo "  Next Steps"
echo "========================================"
echo
echo "To start the application:"
echo "  docker-compose --profile development up"
echo
echo "To start in background:"
echo "  docker-compose --profile development up -d"
echo
echo "To view logs:"
echo "  docker-compose logs -f web"
echo
echo "To stop the application:"
echo "  docker-compose down"
echo
echo "========================================"