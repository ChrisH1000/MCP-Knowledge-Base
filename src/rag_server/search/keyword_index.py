"""Keyword-based search using BM25."""

import pickle
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class KeywordIndex:
    """BM25-based keyword search index."""

    def __init__(self, settings: Settings):
        """Initialize the keyword index.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.index_dir = settings.RAG_INDEX_DIR
        self.bm25: BM25Okapi | None = None
        self.documents: list[dict[str, Any]] = []

    def build_index(self, chunks: list[dict[str, Any]]) -> None:
        """Build BM25 index from chunks.

        Args:
            chunks: List of chunks with content and metadata
        """
        logger.info("building_keyword_index", chunks=len(chunks))

        self.documents = chunks
        tokenized_corpus = [chunk["content"].lower().split() for chunk in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        logger.info("keyword_index_built")

    def save(self) -> None:
        """Save BM25 index to disk."""
        if self.bm25 is None:
            logger.warning("no_keyword_index_to_save")
            return

        bm25_path = self.index_dir / "bm25.pkl"
        docs_path = self.index_dir / "bm25_docs.pkl"

        with open(bm25_path, "wb") as f:
            pickle.dump(self.bm25, f)
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)

        logger.info("keyword_index_saved")

    def load(self) -> bool:
        """Load BM25 index from disk.

        Returns:
            True if loaded successfully
        """
        bm25_path = self.index_dir / "bm25.pkl"
        docs_path = self.index_dir / "bm25_docs.pkl"

        if not bm25_path.exists() or not docs_path.exists():
            logger.warning("keyword_index_not_found")
            return False

        try:
            with open(bm25_path, "rb") as f:
                self.bm25 = pickle.load(f)
            with open(docs_path, "rb") as f:
                self.documents = pickle.load(f)
            logger.info("keyword_index_loaded")
            return True
        except Exception as e:
            logger.error("keyword_index_load_error", error=str(e))
            return False

    def search(self, query: str, top_k: int = 8) -> list[tuple[dict[str, Any], float]]:
        """Search using BM25.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        if self.bm25 is None or not self.documents:
            logger.warning("no_keyword_index_loaded")
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Get top K indices
        top_indices = scores.argsort()[-top_k:][::-1]

        results: list[tuple[dict[str, Any], float]] = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.documents[int(idx)], float(scores[idx])))

        return results
