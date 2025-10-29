"""Query and answer API routes."""

import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from rag_server.api.routes_index import get_retriever
from rag_server.core.config import Settings, get_settings
from rag_server.core.logging import get_logger
from rag_server.core.schemas import (
    AnswerRequest,
    AnswerResponse,
    Citation,
    QueryRequest,
    QueryResponse,
)
from rag_server.llm.ollama_client import OllamaClient
from rag_server.llm.openai_client import OpenAIClient
from rag_server.llm.prompt_templates import build_grounding_prompt
from rag_server.search.retriever import HybridRetriever

logger = get_logger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_retriever),
) -> QueryResponse:
    """Search for relevant code/docs."""
    try:
        logger.info("query_received", query=request.q, top_k=request.top_k)

        matches = retriever.retrieve(request.q, request.top_k)

        return QueryResponse(matches=matches)

    except Exception as e:
        logger.error("query_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/answer", response_model=AnswerResponse)
async def answer(
    request: AnswerRequest,
    settings: Settings = Depends(get_settings),
    retriever: HybridRetriever = Depends(get_retriever),
) -> AnswerResponse:
    """Generate an answer using LLM with retrieved context."""
    try:
        logger.info("answer_requested", query=request.q, provider=settings.RAG_LLM_PROVIDER)

        # Retrieve context
        matches = retriever.retrieve(request.q, request.top_k)

        if not matches:
            raise HTTPException(status_code=404, detail="No relevant context found")

        # If no LLM provider, return retrieval-only response
        if settings.RAG_LLM_PROVIDER == "none":
            final_answer = "Retrieval-only mode (no LLM provider configured). See matches for context."
            citations = [
                Citation(path=m.path, start_line=m.start_line, end_line=m.end_line)
                for m in matches
            ]
            return AnswerResponse(final=final_answer, citations=citations, matches=matches)

        # Build prompt
        prompt = build_grounding_prompt(request.q, matches)

        # Generate answer
        final_answer = ""
        if settings.RAG_LLM_PROVIDER == "openai":
            client = OpenAIClient(settings)
            final_answer = client.generate(prompt, request.max_tokens)
        elif settings.RAG_LLM_PROVIDER == "ollama":
            client = OllamaClient(settings)
            final_answer = await client.generate(prompt, request.max_tokens)

        # Extract citations from answer or use all matches
        citations = _extract_citations(final_answer, matches)

        return AnswerResponse(final=final_answer, citations=citations, matches=matches)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("answer_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")


def _extract_citations(answer: str, matches: list) -> List[Citation]:
    """Extract citations from the answer text.

    Args:
        answer: Generated answer text
        matches: Retrieved matches

    Returns:
        List of citations
    """
    citations: List[Citation] = []

    # Try to extract citations from answer
    citation_pattern = r"([a-zA-Z0-9/_.-]+):(\d+)-(\d+)"
    found_citations = re.findall(citation_pattern, answer)

    if found_citations:
        for path, start, end in found_citations:
            citations.append(Citation(path=path, start_line=int(start), end_line=int(end)))
    else:
        # Fallback: use all matches as citations
        for match in matches:
            citations.append(
                Citation(path=match.path, start_line=match.start_line, end_line=match.end_line)
            )

    return citations
