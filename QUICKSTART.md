# Quick Start Guide

## ✅ What's Working

The RAG server is fully functional and tested:

- ✅ Server starts successfully
- ✅ Health endpoint responding
- ✅ Index building working (indexed 19 Python files, 77 chunks)
- ✅ Hybrid search functioning (vector + BM25)
- ✅ API key authentication working
- ✅ Query endpoint returning relevant results

## 🚀 Getting Started

### 1. Set up environment

```bash
# Create .env file (already created)
cat .env

# Should contain:
RAG_API_KEY=test-api-key-123
```

### 2. Install dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Dependencies already installed via pip install -e .
```

### 3. Start the server

```bash
# Start server
uvicorn rag_server.main:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
uvicorn rag_server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Build the index

```bash
# Index your codebase
curl -X POST http://localhost:8000/index/build \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $RAG_API_KEY" \
  -d '{
    "root": "/path/to/your/code",
    "patterns": ["**/*.py", "**/*.js", "**/*.md"],
    "clean": true
  }'
```

### 5. Query the codebase

```bash
# Search for information
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $RAG_API_KEY" \
  -d '{
    "q": "How do I configure settings?",
    "top_k": 5
  }' | python3 -m json.tool
```

## 📊 Test Results

Tested on the RAG server codebase itself:

```
Index Stats:
- Files indexed: 19
- Chunks created: 77
- Last updated: 2025-10-29T03:02:54+00:00

Sample Query: "How do I configure the RAG server settings?"
- Returned 3 relevant matches
- Includes snippets from main.py, server.py, and config.py
- Scores: 0.032, 0.032, 0.031 (hybrid ranking)
```

## 🔧 Common Commands

```bash
# Check server health
curl http://localhost:8000/health

# Get index statistics
curl -H "X-API-Key: $RAG_API_KEY" \
  http://localhost:8000/index/stats

# Get current configuration
curl -H "X-API-Key: $RAG_API_KEY" \
  http://localhost:8000/config

# Incremental index update (only changed files)
curl -X POST http://localhost:8000/index/incremental \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $RAG_API_KEY" \
  -d '{"root": "/path/to/code"}'
```

## 🐳 Using Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

## ⚙️ Configuration Options

Key environment variables in `.env`:

```bash
# Required
RAG_API_KEY=your-secret-key

# Optional - OpenAI integration
OPENAI_API_KEY=sk-...

# Optional - Ollama integration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Optional - Paths and settings
RAG_INDEX_DIR=./data/index
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=128
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 🎯 Next Steps

1. **Production Deployment**: Use Docker or deploy to your cloud provider
2. **Custom Index**: Point to your own codebase
3. **LLM Integration**: Add OpenAI or Ollama API keys for natural language answers
4. **Fine-tuning**: Adjust chunk size, overlap, and search parameters

## 📝 Notes

- Python 3.9+ required (tested on 3.9.6)
- First index build downloads embedding model (~80MB)
- Index is persisted to disk and reused across restarts
- Incremental updates only process changed files
