"""Index management API routes."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from rag_server.core.config import Settings, get_settings
from rag_server.core.logging import get_logger
from rag_server.core.schemas import IndexBuildRequest, IndexBuildResponse, IndexStatsResponse
from rag_server.ingest.pipeline import IngestionPipeline
from rag_server.search.retriever import HybridRetriever

logger = get_logger(__name__)
router = APIRouter()

# Global retriever instance
_retriever: Optional[HybridRetriever] = None


def get_retriever(settings: Settings = Depends(get_settings)) -> HybridRetriever:
    """Get or create the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(settings)
        _retriever.load()  # Try to load existing index
    return _retriever


@router.post("/build", response_model=IndexBuildResponse)
async def build_index(
    request: IndexBuildRequest,
    settings: Settings = Depends(get_settings),
    retriever: HybridRetriever = Depends(get_retriever),
) -> IndexBuildResponse:
    """Build or rebuild the search index."""
    try:
        logger.info("index_build_requested", root=request.root, clean=request.clean)

        # Run ingestion pipeline
        pipeline = IngestionPipeline(settings)
        root_path = Path(request.root).resolve()

        if not root_path.exists():
            raise HTTPException(status_code=400, detail=f"Root path does not exist: {request.root}")

        chunks, stats = pipeline.ingest(
            root=root_path,
            patterns=request.patterns,
            exclude=request.exclude,
            clean=request.clean,
        )

        if not chunks:
            raise HTTPException(status_code=400, detail="No files were indexed")

        # Build indices
        retriever.build_indices(chunks)
        retriever.save()

        # Save stats
        stats_file = settings.RAG_INDEX_DIR / "stats.json"
        stats_file.write_text(json.dumps(stats, indent=2))

        return IndexBuildResponse(
            ok=True,
            files_indexed=stats["files_indexed"],
            chunks=stats["chunks"],
            duration_s=stats["duration_s"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("index_build_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Index build failed: {str(e)}")


@router.post("/incremental", response_model=IndexBuildResponse)
async def incremental_index(
    request: IndexBuildRequest,
    settings: Settings = Depends(get_settings),
    retriever: HybridRetriever = Depends(get_retriever),
) -> IndexBuildResponse:
    """Incrementally update the index (only changed files)."""
    # For MVP, this is the same as build but with clean=False
    request.clean = False
    return await build_index(request, settings, retriever)


@router.get("/stats", response_model=IndexStatsResponse)
async def get_index_stats(settings: Settings = Depends(get_settings)) -> IndexStatsResponse:
    """Get index statistics."""
    stats_file = settings.RAG_INDEX_DIR / "stats.json"

    if not stats_file.exists():
        raise HTTPException(status_code=404, detail="No index found")

    try:
        stats = json.loads(stats_file.read_text())
        return IndexStatsResponse(
            files=stats.get("files_indexed", 0),
            chunks=stats.get("chunks", 0),
            updated_at=stats.get("updated_at", "unknown"),
        )
    except Exception as e:
        logger.error("stats_read_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to read stats")
