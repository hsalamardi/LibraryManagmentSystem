@echo off
echo Building Docker image locally...
docker build -t library-management-system:local .

if %ERRORLEVEL% EQU 0 (
    echo Docker build successful!
    
    echo.
    echo Running container for testing...
    echo This will start the application on http://localhost:8000
    echo Press Ctrl+C to stop the container when done testing
    
    REM Run the container with environment variables from .env file
    docker run --rm -p 8000:8000 --env-file .env library-management-system:local
) else (
    echo Docker build failed. Please check the error messages above.
    exit /b 1
)