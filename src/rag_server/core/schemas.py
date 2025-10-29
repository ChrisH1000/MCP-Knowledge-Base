"""Pydantic schemas for API requests and responses."""

from typing import Any

from pydantic import BaseModel, Field


class Match(BaseModel):
    """A single search result match."""

    score: float = Field(description="Relevance score")
    path: str = Field(description="File path relative to root")
    start_line: int = Field(description="Starting line number", ge=1)
    end_line: int = Field(description="Ending line number", ge=1)
    snippet: str = Field(description="Code/text snippet")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Citation(BaseModel):
    """A citation to a source file."""

    path: str = Field(description="File path")
    start_line: int = Field(description="Starting line number", ge=1)
    end_line: int = Field(description="Ending line number", ge=1)


class QueryRequest(BaseModel):
    """Request to search for relevant code/docs."""

    q: str = Field(description="Natural language query")
    top_k: int = Field(default=8, ge=1, le=50, description="Number of results to return")


class AnswerRequest(QueryRequest):
    """Request to generate an answer with LLM."""

    max_tokens: int = Field(default=512, ge=50, le=4000, description="Max tokens for answer")


class QueryResponse(BaseModel):
    """Response with search matches."""

    matches: list[Match] = Field(description="Ranked search results")


class AnswerResponse(BaseModel):
    """Response with generated answer and citations."""

    final: str = Field(description="Generated answer")
    citations: list[Citation] = Field(description="Source citations")
    matches: list[Match] = Field(description="Retrieved context matches")


class IndexBuildRequest(BaseModel):
    """Request to build or rebuild the index."""

    root: str = Field(default="./", description="Root directory to index")
    clean: bool = Field(default=False, description="Clean index before building")
    patterns: list[str] = Field(
        default_factory=lambda: ["**/*"], description="Glob patterns to include"
    )
    exclude: list[str] = Field(
        default_factory=lambda: [], description="Glob patterns to exclude"
    )


class IndexBuildResponse(BaseModel):
    """Response from index build operation."""

    ok: bool = Field(description="Success status")
    files_indexed: int = Field(description="Number of files indexed")
    chunks: int = Field(description="Number of chunks created")
    duration_s: float = Field(description="Duration in seconds")


class IndexStatsResponse(BaseModel):
    """Response with index statistics."""

    files: int = Field(description="Number of indexed files")
    chunks: int = Field(description="Number of indexed chunks")
    updated_at: str = Field(description="Last update timestamp (ISO format)")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok")
    version: str = Field(default="0.1.0")
