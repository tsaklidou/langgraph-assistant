#!/bin/bash

echo "Docker Build & Run Script"
echo "========================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo " .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - SERPAPI_API_KEY"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if required directories exist
if [ ! -d "src" ]; then
    echo "src/ directory not found!"
    echo "Make sure you're running this from the project root."
    exit 1
fi

if [ ! -d "data" ]; then
    echo "data/ directory not found!"
    echo "Creating data directory. Please add your data.md file there."
    mkdir -p data
fi

echo "Building Docker image..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo ""
    echo "Starting app..."
    echo "App will be available at: http://localhost:8501"
    echo ""
    echo "Press Ctrl+C to stop the application"
    echo ""
    
    docker-compose up
else
    echo "Build failed!"
    exit 1
fi