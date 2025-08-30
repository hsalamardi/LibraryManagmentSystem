#!/bin/bash

# Script to test Docker build locally before deploying to GCP

echo "Building Docker image locally..."
docker build -t library-management-system:local .

if [ $? -eq 0 ]; then
    echo "Docker build successful!"
    
    echo "\nRunning container for testing..."
    echo "This will start the application on http://localhost:8000"
    echo "Press Ctrl+C to stop the container when done testing"
    
    # Run the container with environment variables from .env file
    docker run --rm -p 8000:8000 --env-file .env library-management-system:local
else
    echo "Docker build failed. Please check the error messages above."
    exit 1
fi