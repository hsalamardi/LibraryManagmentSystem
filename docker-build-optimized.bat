@echo off
REM Optimized Docker Build Script for Library Management System
REM This script addresses common Docker build issues and performance problems

echo ========================================
echo  Library Management System - Docker Build
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running or not accessible.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/6] Checking Docker environment...
docker --version
echo.

echo [2/6] Cleaning up previous builds...
REM Remove dangling images and build cache
docker builder prune -f
docker image prune -f
echo.

echo [3/6] Setting up build environment...
REM Enable BuildKit for faster builds
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1
echo BuildKit enabled for optimized builds
echo.

echo [4/6] Building web service with optimizations...
REM Build with no-cache to ensure fresh build and parallel processing
docker-compose build --no-cache --parallel web

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo  BUILD FAILED - Troubleshooting Tips
    echo ========================================
    echo.
    echo Common solutions:
    echo 1. Check if you have enough disk space (at least 2GB free)
    echo 2. Restart Docker Desktop
    echo 3. Clear Docker cache: docker system prune -a
    echo 4. Check your internet connection for package downloads
    echo 5. Try building without cache: docker-compose build --no-cache web
    echo.
    echo If the build is hanging:
    echo - Increase Docker memory limit to 4GB+ in Docker Desktop settings
    echo - Disable antivirus real-time scanning for the project folder
    echo - Close other resource-intensive applications
    echo.
    pause
    exit /b 1
)

echo.
echo [5/6] Verifying build...
docker images | findstr library
echo.

echo [6/6] Build completed successfully!
echo.
echo ========================================
echo  Next Steps
echo ========================================
echo.
echo To start the application:
echo   docker-compose --profile development up
echo.
echo To start in background:
echo   docker-compose --profile development up -d
echo.
echo To view logs:
echo   docker-compose logs -f web
echo.
echo To stop the application:
echo   docker-compose down
echo.
echo ========================================

pause