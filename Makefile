.PHONY: help install run test lint format clean docker-build docker-run index query

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv venv
	. .venv/bin/activate && uv pip install -e ".[dev]"

run:  ## Run the API server locally
	. .venv/bin/activate && python -m uvicorn rag_server.main:app --reload --port 8000

test:  ## Run tests
	. .venv/bin/activate && pytest -v

lint:  ## Run linter
	. .venv/bin/activate && ruff check .

format:  ## Format code
	. .venv/bin/activate && ruff format .

clean:  ## Clean build artifacts and cache
	rm -rf .venv build dist *.egg-info __pycache__ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:  ## Build Docker image
	docker build -t rag-server:latest .

docker-run:  ## Run with docker-compose
	docker-compose up

index:  ## Build index - Usage: make index SRC=/path/to/code PATTERNS='["**/*.py","**/*.js"]'
	@if [ -z "$(SRC)" ]; then \
		echo "Error: SRC not specified. Usage: make index SRC=/path/to/code"; \
		echo "Optional: PATTERNS='[\"**/*.py\",\"**/*.js\"]' CLEAN=true"; \
		exit 1; \
	fi
	curl -X POST http://localhost:8000/index/build \
		-H "x-api-key: test-api-key-123" \
		-H "Content-Type: application/json" \
		-d '{"root":"$(SRC)","patterns":$(if $(PATTERNS),$(PATTERNS),["**/*"]),"clean":$(if $(CLEAN),$(CLEAN),true)}'

index-php:  ## Index PHP servers repo (shortcut)
	$(MAKE) index SRC="/Users/christopher.hill/Desktop/PD/Work repos/php-servers" PATTERNS='["**/*.php","**/*.js","**/*.md","**/*.json"]'

query:  ## Example query
	curl -X POST http://localhost:8000/query \
		-H "x-api-key: dev-secret" \
		-H "Content-Type: application/json" \
		-d '{"q":"How does the RAG server work?","top_k":5}'
