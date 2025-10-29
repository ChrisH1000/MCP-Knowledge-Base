.PHONY: help install run test lint format clean docker-build docker-run index query

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv venv
	. .venv/bin/activate && uv pip install -e ".[dev]"

run:  ## Run the API server locally
	uv run python -m uvicorn main:app --reload --port 8000 --app-dir src

test:  ## Run tests
	uv run pytest -v

lint:  ## Run linter
	uv run ruff check .

format:  ## Format code
	uv run ruff format .

clean:  ## Clean build artifacts and cache
	rm -rf .venv build dist *.egg-info __pycache__ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:  ## Build Docker image
	docker build -t rag-server:latest .

docker-run:  ## Run with docker-compose
	docker-compose up

index:  ## Build index (example)
	curl -X POST http://localhost:8000/index/build \
		-H "x-api-key: dev-secret" \
		-H "Content-Type: application/json" \
		-d '{"root":"./","clean":true}'

query:  ## Example query
	curl -X POST http://localhost:8000/query \
		-H "x-api-key: dev-secret" \
		-H "Content-Type: application/json" \
		-d '{"q":"How does the RAG server work?","top_k":5}'
