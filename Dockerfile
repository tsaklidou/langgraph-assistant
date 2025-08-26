# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding models to avoid download during runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the entire src directory
COPY src/ ./src/

# Copy data directory
COPY data/ ./data/

# Create necessary directories
RUN mkdir -p ./src/chromadb ./src/app/static

# Copy startup script
COPY startup.sh .
RUN chmod +x startup.sh

# Expose Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run startup script
CMD ["./startup.sh"]