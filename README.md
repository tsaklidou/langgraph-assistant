# AI Insight - AI Chat Assistant

AI-powered chat application with RAG (Retrieval-Augmented Generation) capabilities, featuring knowledge base search and web search fallback.

## Features

- **Intelligent Response Generation**: Knowledge base search and web search
- **Real-time Streaming**: Live thought process and response streaming
- **Conversation Management**: Persistent chat history with smart titles
- **Source Attribution**: Shows sources for all responses (RAG chunks or web results)
- **User Feedback**: Like/dislike system for response quality improvement
- **Feedback Integration**: Incorporates user feedback into conversation context/history
- **Responsive UI**: Clean Streamlit interface with modern design

## Tech Stack

- **Frontend**: Streamlit
- **LLM**: OpenAI GPT-4o
- **Vector Database**: ChromaDB
- **Web Search**: SerpAPI
- **Text Processing**: LangChain, Sentence Transformers
- **Database**: SQLite

## Prerequisites

- Python 3.10+
- OpenAI API Key
- SerpAPI Key

## Installation & Usage

### Option 1: Docker (Recommended - Cross-Platform Compatible)

Easiest way to run, especially for ARM-based systems (M1/M2 Macs) where kernel compatibility might be an issue:

```bash
# 1. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 2. Make the scripts executable
chmod +x build-and-run.sh startup.sh

# 3. Run with Docker
./build-and-run.sh
```

App will be available at http://localhost:8501

### Option 2: Local Setup (Using Invoke)

One-command setup using invoke:
```bash
invoke all    # Setup everything
invoke run    # Start the app
```

Or step by step:
```bash
invoke setup     # Install dependencies and create .env
invoke process   # Process data and create vector database
invoke run       # Start the application
```

### Option 3: Manual Installation

1. Clone the repository
```bash
git clone https://github.com/tsaklidou/langgraph-assistant.git
cd ai-insight
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
```
Edit .env with your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
SERP_API_KEY=your_serpapi_key_here
```

## Manual Usage

### 1. Data Processing (Run Once)
```bash
cd src
python preprocessing/main.py
```
This will load the `data/data.md` file, chunk the content, create ChromaDB embeddings, and store in `./chroma_db` directory.

### 2. Run the Application
```bash
cd src
streamlit run app/ui_app.py
```
The app will be available at http://localhost:8501

## Project Structure

```
├── src/
│   ├── agent/              # AI agent components
│   ├── app/               # Streamlit app and database
│   ├── preprocessing/     # Data processing pipeline
│   └── tools/            # RAG, web search, classification tools
├── tests/                # Unit tests
├── data/                 # Data files
├── tasks.py              # Invoke automation tasks
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker orchestration
├── startup.sh           # Wrapper for running dockerized app 
├── build-and-run.sh     # Build and run Docker container
└── README.md
```

## Available Commands

```bash
invoke --list           # Show all available tasks
invoke setup           # Install dependencies and setup environment
invoke process         # Process data and create vector database
invoke run             # Start the application
invoke test            # Run tests
invoke clean           # Clean up generated files
invoke all             # Complete setup (setup + process)
```

## Testing

```bash
invoke test
# or
pytest tests/ -v
```

## Development

The application follows a modular architecture:

- **Agent**: Core AI logic using LangGraph
- **Tools**: Classifier, RAG search, and web search components
- **App**: Streamlit UI and SQLite database management
- **Preprocessing**: Data chunking and vector database creation

## Configuration

All configuration is handled through environment variables in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key for GPT-4o
- `SERP_API_KEY`: SerpAPI key for web search functionality

## Docker Configuration

The application includes Docker support for easy deployment:

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SERPAPI_API_KEY=${SERPAPI_API_KEY}
    volumes:
      - ./data:/app/data:ro
      - app-data:/app/src/chromadb
      - app-db:/app/src/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Future Enhancements

- **Enhanced Title Generation**: Implement AI-powered summarization for better conversation titles
- **Interactive Chat Features**: Add interruption button to stop response generation mid-stream
- **UI/UX Improvements**: Disable chat input while generating responses to prevent conflicts
- **Response Quality**: Implement better handling for generic/low-quality AI responses
- **Performance Optimization**: Add caching layer for embeddings and database queries
- **Smart Token Management**: Develop more sophisticated text truncation strategies for LLM context limits
- **Configuration System**: Add user-configurable settings (LLM temperature, model selection, etc.)

