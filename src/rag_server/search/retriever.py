"""Hybrid retrieval combining vector and keyword search."""

from typing import Any, Dict, List

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger
from rag_server.core.schemas import Match
from rag_server.search.keyword_index import KeywordIndex
from rag_server.search.vector_store import VectorStore

logger = get_logger(__name__)


class HybridRetriever:
    """Combines vector and keyword search with re-ranking."""

    def __init__(self, settings: Settings):
        """Initialize the retriever.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.vector_store = VectorStore(settings)
        self.keyword_index = KeywordIndex(settings)

    def build_indices(self, chunks: List[Dict[str, Any]]) -> None:
        """Build both vector and keyword indices.

        Args:
            chunks: List of chunks to index
        """
        logger.info("building_indices")
        self.vector_store.build_index(chunks)
        self.keyword_index.build_index(chunks)

    def save(self) -> None:
        """Save indices to disk."""
        self.vector_store.save()
        self.keyword_index.save()

    def load(self) -> bool:
        """Load indices from disk.

        Returns:
            True if loaded successfully
        """
        vector_ok = self.vector_store.load()
        keyword_ok = self.keyword_index.load()
        return vector_ok and keyword_ok

    def retrieve(self, query: str, top_k: int = 8) -> List[Match]:
        """Hybrid retrieval with RRF fusion.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of Match objects
        """
        logger.info("retrieving", query=query, top_k=top_k)

        # Get results from both indices
        vector_results = self.vector_store.search(query, top_k * 2)
        keyword_results = self.keyword_index.search(query, top_k * 2)

        # Reciprocal Rank Fusion (RRF)
        k = 60  # RRF constant
        scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Add vector scores
        for rank, (doc, score) in enumerate(vector_results, start=1):
            doc_id = f"{doc['metadata']['path']}:{doc['start_line']}"
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
            doc_map[doc_id] = doc

        # Add keyword scores
        for rank, (doc, score) in enumerate(keyword_results, start=1):
            doc_id = f"{doc['metadata']['path']}:{doc['start_line']}"
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
            doc_map[doc_id] = doc

        # Sort by fused score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Convert to Match objects
        matches: List[Match] = []
        for doc_id, score in sorted_docs:
            doc = doc_map[doc_id]
            matches.append(
                Match(
                    score=score,
                    path=doc["metadata"]["path"],
                    start_line=doc["start_line"],
                    end_line=doc["end_line"],
                    snippet=doc["content"][:500],  # Limit snippet length
                    metadata=doc["metadata"],
                )
            )

        logger.info("retrieval_complete", matches=len(matches))
        return matches
