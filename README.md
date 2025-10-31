# RAG Server - Code-Knowledge Retrieval-Augmented Generation

A production-ready RAG (Retrieval-Augmented Generation) microservice for indexing and querying local codebases with natural language. Built with FastAPI, FAISS, and sentence-transformers.

## Features

- 🔍 **Hybrid Search**: Combines semantic (vector) and keyword (BM25) search
- 📁 **Multi-Format Support**: Python, PHP, JavaScript, TypeScript, Markdown, and more
- 🤖 **LLM Integration**: Works with OpenAI, Ollama, or retrieval-only mode
- 📊 **Incremental Indexing**: Only re-index changed files
- 🐳 **Docker Ready**: Easy deployment with Docker and docker-compose
- 🔐 **API Key Authentication**: Secure your endpoints
- 📝 **Source Citations**: All answers include file:line references
- 🔬 **LangSmith Tracing**: Built-in observability for LLM operations

## Quick Start

### Local Development

```bash
# Install dependencies
make install

# Run the server
make run

# In another terminal, build the index
make index SRC=/path/to/your/code

# Query the codebase (retrieval only)
make query Q="How does authentication work?"

# Generate LLM-powered answer (with LangSmith tracing)
make answer Q="How does authentication work?"
```

### With Docker

```bash
# Build and run
docker-compose up

# Build index
curl -X POST http://localhost:8000/index/build \
  -H "x-api-key: dev-secret" \
  -H "Content-Type: application/json" \
  -d '{"root":"./","clean":true}'
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Data directories
RAG_DATA_DIR=./data
RAG_INDEX_DIR=./data/index

# File types to index
RAG_ALLOWED_FILETYPES=.py,.php,.js,.ts,.md,.mdx,.json,.yml,.yaml

# Embedding model
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# API Security
RAG_API_KEY=dev-secret

# LLM Provider (openai, ollama, or none)
RAG_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OLLAMA_ENDPOINT=http://localhost:11434
LLM_MODEL=gpt-4o-mini

# LangSmith Tracing (optional but recommended)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_your-key-here
LANGCHAIN_PROJECT=my-rag-project
```

## API Endpoints

### Health & Config

```bash
# Health check
curl http://localhost:8000/health

# Get configuration
curl http://localhost:8000/config
```

### Index Management

```bash
# Build index
curl -X POST http://localhost:8000/index/build \
  -H "x-api-key: dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "root": "./",
    "clean": true,
    "patterns": ["**/*.py", "**/*.md"],
    "exclude": ["node_modules/**", ".git/**"]
  }'

# Get index stats
curl http://localhost:8000/index/stats \
  -H "x-api-key: dev-secret"

# Incremental update
curl -X POST http://localhost:8000/index/incremental \
  -H "x-api-key: dev-secret" \
  -H "Content-Type: application/json" \
  -d '{"root": "./"}'
```

### Query & Answer

```bash
# Search for relevant code (retrieval only, no LLM)
curl -X POST http://localhost:8000/query \
  -H "x-api-key: dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "Where is the file reader implemented?",
    "top_k": 8
  }'

# Or use the Make command
make query Q="Where is the file reader implemented?"

# Generate answer with LLM (creates LangSmith traces)
curl -X POST http://localhost:8000/answer \
  -H "x-api-key: dev-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "How does the ingestion pipeline work?",
    "top_k": 8,
    "max_tokens": 500
  }'

# Or use the Make command
make answer Q="How does the ingestion pipeline work?"
```

## Architecture

```
┌─────────────┐
│ Filesystem  │
│ (code+docs) │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Ingestion        │
│ Pipeline         │
│ - File discovery │
│ - Parsing        │
│ - Chunking       │
└──────┬───────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐   ┌──────────────┐
│ Vector      │   │ Keyword      │
│ Store       │   │ Index        │
│ (FAISS)     │   │ (BM25)       │
└──────┬──────┘   └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
        ┌───────────────┐
        │ Hybrid        │
        │ Retriever     │
        │ (RRF Fusion)  │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ LLM           │
        │ (LangChain)   │
        └───────┬───────┘
                │
                ├──────────────────┐
                │                  │
                ▼                  ▼
        ┌───────────────┐  ┌──────────────┐
        │ FastAPI       │  │ LangSmith    │
        │ Response      │  │ Tracing      │
        └───────────────┘  └──────────────┘
```

## LangSmith Observability

This RAG server includes built-in LangSmith tracing for LLM operations:

### Setup

1. **Get a LangSmith API key** at [smith.langchain.com](https://smith.langchain.com/)

2. **Configure your `.env`:**
   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_pt_your-key-here
   LANGCHAIN_PROJECT=my-rag-project

   # Must also configure an LLM provider
   RAG_LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-openai-key
   ```

3. **Restart the server** - you'll see: `langsmith_enabled project=my-rag-project`

### What Gets Traced

When you use the `/answer` endpoint (or `make answer`), LangSmith automatically captures:
- 📝 Full prompts sent to the LLM (including retrieved context)
- 🤖 LLM responses
- ⏱️ Token usage and latency
- ❌ Errors and exceptions
- 🔗 Request metadata

**Note:** The `/query` endpoint doesn't use LLMs, so it won't create traces.

### View Traces

1. Go to [smith.langchain.com](https://smith.langchain.com/)
2. Navigate to your project (e.g., "my-rag-project")
3. See detailed traces for every LLM call!

For more details, see [`LANGSMITH_TRACING_GUIDE.md`](./LANGSMITH_TRACING_GUIDE.md)

## Architecture

```
┌─────────────┐
│ Filesystem  │
│ (code+docs) │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Ingestion        │
│ Pipeline         │
│ - File discovery │
│ - Parsing        │
│ - Chunking       │
└──────┬───────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐   ┌──────────────┐
│ Vector      │   │ Keyword      │
│ Store       │   │ Index        │
│ (FAISS)     │   │ (BM25)       │
└──────┬──────┘   └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
                ▼
        ┌───────────────┐
        │ Hybrid        │
        │ Retriever     │
        │ (RRF Fusion)  │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ LLM           │
        │ (Optional)    │
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ FastAPI       │
        │ Response      │
        └───────────────┘
```

## Project Structure

```
rag-server/
├── src/
│   ├── rag_server/
│   │   ├── api/
│   │   │   ├── routes_admin.py    # Health & config endpoints
│   │   │   ├── routes_index.py    # Index management
│   │   │   └── routes_query.py    # Query & answer
│   │   ├── core/
│   │   │   ├── config.py          # Settings management
│   │   │   ├── schemas.py         # Pydantic models
│   │   │   └── logging.py         # Structured logging
│   │   ├── ingest/
│   │   │   ├── readers.py         # File discovery
│   │   │   ├── parsers.py         # Code/doc parsing
│   │   │   ├── chunking.py        # Text chunking
│   │   │   └── pipeline.py        # Ingestion orchestration
│   │   ├── search/
│   │   │   ├── vector_store.py    # FAISS vector search
│   │   │   ├── keyword_index.py   # BM25 keyword search
│   │   │   └── retriever.py       # Hybrid retrieval
│   │   ├── llm/
│   │   │   ├── openai_client.py   # OpenAI integration
│   │   │   ├── ollama_client.py   # Ollama integration
│   │   │   └── prompt_templates.py# Grounding prompts
│   │   └── server.py              # FastAPI app
│   └── main.py                    # Entry point
├── tests/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest -v

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy src
```

## Make Commands

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run the server
make run

# Build index for a directory
make index SRC=/path/to/code PATTERNS='["**/*.py","**/*.js"]'

# Quick index for PHP servers (example)
make index-php

# Query without LLM (fast retrieval only)
make query Q="your question here"

# Answer with LLM (creates LangSmith traces)
make answer Q="your question here"

# Run tests
make test

# Lint and format
make lint
make format

# Clean build artifacts
make clean
```

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest -v

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy src
```

## Example Queries

Try these example queries on your codebase:

- "Where is the database connection configured?"
- "Show me all functions that handle user authentication"
- "How does the caching layer work?"
- "What are the side effects of the `process_data` function?"
- "Explain the API rate limiting implementation"

## Performance

- **Indexing**: > 5 MB/s on SSD
- **Query latency**: < 800ms P95 (warm index)
- **Memory**: < 2 GB for typical codebases
- **Index size**: ~1.5 KB per chunk

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [sentence-transformers](https://www.sbert.net/) - Semantic embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) - Keyword search
- [structlog](https://www.structlog.org/) - Structured logging
