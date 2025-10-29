Code-Knowledge RAG Server — MVP (Python)

1) Summary

Build a Retrieval-Augmented Generation (RAG) microservice that indexes a local codebase + docs and answers natural-language questions with grounded citations back to files/lines. The service exposes a clean FastAPI HTTP interface and a minimal CLI. Optimized for local/offline workflows and easy containerization.

Primary use: assist developers by answering “Where is X implemented?”, “How does Y work?”, “What are side-effects of Z?”, with linked sources across PHP/JS/Python/Markdown/Docs.

⸻

2) Goals & Non-Goals

Goals (MVP)
	•	Index code + docs from a directory; support incremental re-index.
	•	Embed content into a vector store; support semantic + keyword retrieval.
	•	Answer questions with:
	•	Top-K passages + file:line citations.
	•	Concise final answer grounded in retrieved text.
	•	Provide HTTP API + curlable examples + minimal UI (optional).
	•	Config via .env and sane defaults; run locally or in Docker.
	•	Testable and observable (basic logs + health endpoints).

Non-Goals (MVP)
	•	Full IDE plugin.
	•	AuthN/OAuth SSO; use static API key in MVP.
	•	Multi-tenant isolation.
	•	Advanced agents/tools (editors, refactors).

⸻

3) Users & Primary Scenarios
	•	Developers: ask codebase questions, navigate cross-file context, surface definitions/usages.
	•	Tech writers: verify docs accuracy vs. code.
	•	Reviewers: summarize diffs and related modules (stretch).

⸻

4) High-Level Architecture

flowchart LR
    A[Filesystem\n(code + docs)] --> B[Ingestion Pipeline\nparsing, chunking, metadata]
    B --> C[Embedding Model\n(e.g., sentence-transformers)]
    C --> D[Vector Store\nFAISS or Chroma]
    A --> E[BM25/Keyword Index\nWhoosh or tantivy-py]
    F[FastAPI Service] --> D
    F --> E
    F --> G[LLM (local/cloud)\n(OpenAI/Ollama configurable)]
    F --> H[Response Composer\ncitations + re-ranking]

5) Tech Stack (Python)
	•	Runtime: Python 3.11+
	•	Web: FastAPI + Uvicorn
	•	Embedding: sentence-transformers (default: all-MiniLM-L6-v2); pluggable
	•	Vector store: FAISS (default) or Chroma (config)
	•	Keyword search: whoosh (simple BM25) or rank-bm25 fallback
	•	Parsing: tree_sitter (optional) + markdown-it-py + plain text fallback
	•	LLM: configurable (OpenAI via openai SDK or local ollama HTTP)
	•	Config: pydantic-settings + .env
	•	Packaging: uv or poetry (choose one; default: uv)
	•	Quality: ruff (lint/format), pytest, mypy (strict), pre-commit
	•	Logging: structlog
	•	Container: Docker + slim Python base

⸻

6) Directory Structure

rag-server/
  ├─ src/
  │   ├─ rag_server/
  │   │   ├─ api/
  │   │   │   ├─ __init__.py
  │   │   │   ├─ routes_index.py        # /index/* endpoints
  │   │   │   ├─ routes_query.py        # /query, /answer
  │   │   │   └─ routes_admin.py        # /health, /config
  │   │   ├─ core/
  │   │   │   ├─ config.py              # pydantic settings
  │   │   │   ├─ logging.py
  │   │   │   └─ schemas.py             # Pydantic models
  │   │   ├─ ingest/
  │   │   │   ├─ readers.py             # file globbing, ignore rules
  │   │   │   ├─ parsers.py             # code/doc parsers
  │   │   │   ├─ chunking.py            # splitter strategies
  │   │   │   └─ pipeline.py            # orchestrates ingestion -> vectors
  │   │   ├─ search/
  │   │   │   ├─ vector_store.py        # FAISS/Chroma adapters
  │   │   │   ├─ keyword_index.py       # Whoosh/BM25
  │   │   │   └─ retriever.py           # hybrid retrieval + re-ranking
  │   │   ├─ llm/
  │   │   │   ├─ openai_client.py
  │   │   │   ├─ ollama_client.py
  │   │   │   └─ prompt_templates.py
  │   │   └─ server.py                  # FastAPI app factory
  │   └─ main.py                        # uvicorn entrypoint
  ├─ tests/
  │   ├─ test_ingest.py
  │   ├─ test_retrieval.py
  │   ├─ test_api.py
  │   └─ fixtures/
  ├─ .env.example
  ├─ pyproject.toml
  ├─ uv.lock (if using uv)
  ├─ Dockerfile
  ├─ docker-compose.yml
  ├─ Makefile
  ├─ README.md
  └─ LICENSE

7) Configuration

.env.example

RAG_DATA_DIR=./data
RAG_INDEX_DIR=./data/index
RAG_ALLOWED_FILETYPES=.py,.php,.js,.ts,.md,.mdx,.json,.yml,.yaml,.ini,.txt
RAG_EXCLUDE_GLOBS=node_modules,dist,build,.git,venv,.venv,__pycache__
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_VECTOR_STORE=faiss           # faiss|chroma
RAG_TOP_K=8
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
RAG_API_KEY=dev-secret
RAG_LLM_PROVIDER=openai          # openai|ollama|none
OPENAI_API_KEY=your-key
OLLAMA_ENDPOINT=http://localhost:11434
LLM_MODEL=gpt-4o-mini             # or e.g. "llama3.1"

8) APIs

Auth
	•	Header: x-api-key: <RAG_API_KEY>

8.1 Health & Config
	•	GET /health → { "status": "ok", "version": "0.1.0" }
	•	GET /config → returns effective config (redact secrets)

8.2 Indexing
	•	POST /index/build
	•	Body:

	{
		"root": "./",
		"clean": false,
		"patterns": ["**/*.py", "**/*.md"],
		"exclude": ["node_modules/**", ".git/**"]
	}

•	200: { "ok": true, "files_indexed": 152, "chunks": 1043, "duration_s": 12.3 }

	•	POST /index/incremental
	•	Same body as /index/build, only updates changed files.
	•	GET /index/stats
	•	200: { "files": 152, "chunks": 1043, "updated_at": "2025-10-29T02:10:01Z" }

8.3 Query & Answer
	•	POST /query
	•	Body:

	{ "q": "Where is doCurlGet implemented and what are its side effects?", "top_k": 8 }
	•	200:

	{
		"matches": [
			{
				"score": 0.78,
				"path": "src/helpers/curl.php",
				"start_line": 12,
				"end_line": 68,
				"snippet": "function doCurlGet($url) { ... }",
				"metadata": {
					"lang": "php",
					"symbol": "doCurlGet",
					"sha256": "…"
				}
			}
		]
	}

	•	POST /answer
	•	Body:

	{
		"q": "How do sessions work in our Docker PHP image?",
		"top_k": 8,
		"max_tokens": 500
	}

	•	200:

	{
		"final": "Sessions are initialized in … Key settings include `session.save_handler=memcached`...",
		"citations": [
			{ "path": "config/php/session.php", "start_line": 10, "end_line": 42 },
			{ "path": "Dockerfile", "start_line": 55, "end_line": 88 }
		],
		"matches": [ /* same structure as /query */ ]
	}

8.4 Example cURL

curl -s http://localhost:8000/health

curl -s -X POST http://localhost:8000/index/build \
  -H "x-api-key: dev-secret" \
  -H "content-type: application/json" \
  -d '{"root":"./","clean":true}'

curl -s -X POST http://localhost:8000/answer \
  -H "x-api-key: dev-secret" \
  -H "content-type: application/json" \
  -d '{"q":"Where are Google Sheets calls made?","top_k":6}'

9) Data Model (Pydantic)

# src/rag_server/core/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

class Match(BaseModel):
    score: float
    path: str
    start_line: int
    end_line: int
    snippet: str
    metadata: dict = Field(default_factory=dict)

class QueryRequest(BaseModel):
    q: str
    top_k: int = 8

class AnswerRequest(QueryRequest):
    max_tokens: int = 512

class QueryResponse(BaseModel):
    matches: List[Match]

class AnswerResponse(BaseModel):
    final: str
    citations: List[dict]
    matches: List[Match]

10) Ingestion Pipeline
	1.	Discovery: walk directory; apply include/exclude globs.
	2.	Reading: load file content; compute sha256; skip unchanged.
	3.	Parsing:
	•	Code: try tree_sitter for symbol boundaries (optional).
	•	Docs: markdown to plain text preserving headings.
	4.	Chunking:
	•	Default semantic-ish splitter: by heading/functions; fallback to fixed window:
	•	chunk_size=800 chars, overlap=120.
	•	Store metadata: path, start_line, end_line, lang, symbol (if known).
	5.	Embedding:
	•	Batched inference with sentence-transformers.
	6.	Indexing:
	•	Write to FAISS index + docstore (SQLite or JSONL).
	•	Build/update Whoosh keyword index (title/path/snippet).

Acceptance: full run over a medium repo (<5k files) completes within ≤10 min on laptop; memory stays <2 GB.

⸻

11) Retrieval Pipeline
	1.	Hybrid search: vector Top-K + BM25 Top-K → merge by RRf or score normalization.
	2.	De-dup & diversity: limit per-file results to avoid same-file clustering.
	3.	Re-ranking: optional cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2).
	4.	Context builder: pack passages to token budget (LLM-agnostic).
	5.	Answering (if /answer): call configured LLM with grounding prompt.
	6.	Citations: always include file paths and line ranges.

⸻

12) Prompt Template (Grounded Answer)

System: You are a precise code assistant. Use ONLY the provided context to answer.
If unsure, say you don’t know. Always include file:line citations.

User question:
{question}

Context (top-ranked snippets with file and line numbers):
{context}

Answer with a concise explanation and bullet points when helpful. End with "Sources:" and list each citation.

13) Security & Privacy (MVP)
	•	Static API key via x-api-key.
	•	Never send file contents to remote LLM unless user enables OPENAI_API_KEY.
Default RAG_LLM_PROVIDER=none returns retrieval-only answers (no generation).
	•	Respect .gitignore + RAG_EXCLUDE_GLOBS.
	•	Log paths, not raw content, at INFO level.

⸻

14) Performance Targets
	•	P95 /query under 800ms for warm index on typical questions.
	•	Index build throughput > 5 MB/s on SSD.
	•	Vector index size: ~1.5 KB/embedding * chunks.

⸻

15) Testing Strategy
	•	Unit: chunking boundaries, metadata mapping, vector adapter, keyword search.
	•	Integration: full ingestion → query pipeline.
	•	API: FastAPI test client, auth, error codes.
	•	Golden tests: queries mapped to expected files in a small fixture repo.

⸻

16) Observability
	•	/health
	•	Structured logs (structlog) with request IDs.
	•	Basic counters: files indexed, chunks, avg embed latency.

⸻

17) Developer Workflow

With uv (recommended):

uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run uvicorn src.rag_server.main:app --reload --port 8000

Docker:

docker build -t rag-server:dev .
docker run --rm -p 8000:8000 -v "$PWD:/work" rag-server:dev

Makefile (snippets):

run:        ## run api locally
\tuv run uvicorn src.rag_server.main:app --reload --port 8000
index:      ## rebuild index
\tcurl -s -X POST localhost:8000/index/build -H "x-api-key: $$RAG_API_KEY" -d '{"root":"./","clean":true}'
test:
\tuv run pytest -q
lint:
\tuv run ruff check .
format:
\tuv run ruff format .

18) Minimal FastAPI Skeleton

# src/rag_server/main.py
from fastapi import FastAPI
from rag_server.server import create_app

app = create_app()

# src/rag_server/server.py
from fastapi import FastAPI, Depends, Header, HTTPException
from rag_server.core.config import Settings
from rag_server.api import routes_index, routes_query, routes_admin

def api_key_guard(x_api_key: str | None = Header(default=None), settings: Settings = Depends(Settings)):
    if settings.RAG_API_KEY and x_api_key != settings.RAG_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def create_app() -> FastAPI:
    app = FastAPI(title="RAG Server", version="0.1.0")
    app.include_router(routes_admin.router, prefix="/", tags=["admin"])
    app.include_router(routes_index.router, prefix="/index", tags=["index"], dependencies=[Depends(api_key_guard)])
    app.include_router(routes_query.router, prefix="/", tags=["query"], dependencies=[Depends(api_key_guard)])
    return app

19) Acceptance Criteria (MVP)
	•	✅ POST /index/build indexes a demo repo, reporting files & chunks.
	•	✅ POST /query returns ≥1 relevant match for seeded questions in fixtures.
	•	✅ POST /answer produces grounded text with ≥2 citations when available.
	•	✅ Works offline (retrieval-only) when RAG_LLM_PROVIDER=none.
	•	✅ Docker image runs with volume-mounted repo and persists index to RAG_INDEX_DIR.

⸻

20) Stretch Enhancements (Post-MVP)
	•	Cross-encoder re-ranking toggle; reciprocal rank fusion tuning.
	•	Symbol graph (callers/callees) from tree_sitter for code intelligence.
	•	Diff-aware incremental indexing (Git hook).
	•	RST/Asciidoc parsers; PDF via pypdf + OCR via tesseract (opt-in).
	•	Simple web UI (React or static HTMX) for search + previews.
	•	LangSmith/OpenTelemetry traces.
	•	Multi-repo / workspace tags.

⸻

21) Copilot TODO Roadmap
	•	Create pyproject.toml with deps: fastapi, uvicorn, sentence-transformers, faiss-cpu, whoosh, pydantic-settings, structlog, ruff, pytest.
	•	Implement Settings with .env support.
	•	Implement file discovery + ignore rules.
	•	Implement markdown + code parsers (line numbers).
	•	Implement chunker and metadata (file, start_line, end_line).
	•	Implement embedding client and FAISS adapter.
	•	Implement BM25 index (Whoosh) and hybrid retriever.
	•	Implement /index/build, /index/stats, /query, /answer.
	•	Add tests and fixtures; wire CI (optional GitHub Actions).
	•	Build Dockerfile and compose; document examples.

⸻

22) Example Dockerfile (slim)

FROM python:3.11-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install uv && uv pip install --system .

COPY src ./src
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.rag_server.main:app", "--host", "0.0.0.0", "--port", "8000"]

23) Licensing & Compliance
	•	Default to MIT for internal PD, or organization’s standard license.
	•	Document third-party models and licenses (sentence-transformers, FAISS).

⸻

24) Risks & Mitigations
	•	Large repos → memory spikes: stream embeddings, batch writes.
	•	Noisy retrieval → add BM25 hybrid, re-ranker toggle, better chunking.
	•	Privacy → default to local LLM off; mask secrets; obey exclude globs.

⸻

25) Example Queries to Validate
	•	“Where is the memcached session handler configured?”
	•	“Show how the Google Sheets API client is initialized.”
	•	“What sanitization does doVars() apply to $_FILES?”
	•	“Outline the cURL helper functions and their logging.”