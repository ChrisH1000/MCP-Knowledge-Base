"""Vector store adapter for FAISS."""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """FAISS-based vector store for semantic search."""

    def __init__(self, settings: Settings):
        """Initialize the vector store.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.index_dir = settings.RAG_INDEX_DIR
        self.model: Optional[SentenceTransformer] = None
        self.index: faiss.Optional[Index] = None
        self.documents: List[Dict[str, Any]] = []

    def load_model(self) -> None:
        """Load the embedding model."""
        if self.model is None:
            logger.info("loading_embedding_model", model=self.settings.RAG_EMBEDDING_MODEL)
            self.model = SentenceTransformer(self.settings.RAG_EMBEDDING_MODEL)
            logger.info("model_loaded")

    def build_index(self, chunks: List[Dict[str, Any]]) -> None:
        """Build FAISS index from chunks.

        Args:
            chunks: List of chunks with content and metadata
        """
        self.load_model()
        assert self.model is not None

        logger.info("building_index", chunks=len(chunks))

        # Extract texts for embedding
        texts = [chunk["content"] for chunk in chunks]
        self.documents = chunks

        # Generate embeddings in batches
        logger.info("generating_embeddings")
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True,
        )

        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype("float32"))

        logger.info("index_built", vectors=self.index.ntotal)

    def save(self) -> None:
        """Save index and documents to disk."""
        if self.index is None:
            logger.warning("no_index_to_save")
            return

        index_path = self.index_dir / "faiss.index"
        docs_path = self.index_dir / "documents.pkl"

        faiss.write_index(self.index, str(index_path))
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)

        logger.info("index_saved", path=str(self.index_dir))

    def load(self) -> bool:
        """Load index and documents from disk.

        Returns:
            True if loaded successfully
        """
        index_path = self.index_dir / "faiss.index"
        docs_path = self.index_dir / "documents.pkl"

        if not index_path.exists() or not docs_path.exists():
            logger.warning("index_not_found")
            return False

        try:
            self.load_model()
            self.index = faiss.read_index(str(index_path))
            with open(docs_path, "rb") as f:
                self.documents = pickle.load(f)
            logger.info("index_loaded", vectors=self.index.ntotal)
            return True
        except Exception as e:
            logger.error("index_load_error", error=str(e))
            return False

    def search(self, query: str, top_k: int = 8) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar chunks.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        if self.index is None or not self.documents:
            logger.warning("no_index_loaded")
            return []

        self.load_model()
        assert self.model is not None

        # Encode query
        query_embedding = self.model.encode([query], convert_to_numpy=True)

        # Search
        distances, indices = self.index.search(query_embedding.astype("float32"), top_k)

        # Prepare results
        results: List[Tuple[Dict[str, Any], float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                # Convert distance to similarity score (inverse)
                score = 1.0 / (1.0 + float(dist))
                results.append((self.documents[int(idx)], score))

        return results
