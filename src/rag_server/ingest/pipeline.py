"""Ingestion pipeline orchestration."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger
from rag_server.ingest.chunking import TextChunker
from rag_server.ingest.parsers import FileParser
from rag_server.ingest.readers import FileReader

logger = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates the ingestion pipeline."""
    def __init__(self, settings: Settings):
        """Initialize the pipeline.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.reader = FileReader(settings)
        self.parser = FileParser()
        self.chunker = TextChunker(settings)

    def ingest(
        self,
        root: Path,
        patterns: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        clean: bool = False,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Run the ingestion pipeline.

        Args:
            root: Root directory to index
            patterns: Glob patterns to include
            exclude: Glob patterns to exclude
            clean: Whether to clean existing index

        Returns:
            Tuple of (chunks_with_metadata, stats)
        """
        start_time = time.time()
        logger.info("starting_ingestion", root=str(root), clean=clean)

        # Load existing hashes for incremental indexing
        hashes_file = self.settings.RAG_INDEX_DIR / "file_hashes.json"
        file_hashes: Dict[str, str] = {}
        if not clean and hashes_file.exists():
            try:
                file_hashes = json.loads(hashes_file.read_text())
                logger.info("loaded_hashes", count=len(file_hashes))
            except Exception as e:
                logger.warning("hash_load_error", error=str(e))

        all_chunks: List[Dict[str, Any]] = []
        files_indexed = 0
        new_hashes: Dict[str, str] = {}

        # Discover and process files
        for file_path in self.reader.discover_files(root, patterns, exclude):
            try:
                # Read file
                content, sha256 = self.reader.read_file(file_path)
                if not content:
                    continue

                relative_path = str(file_path.relative_to(root))

                # Check if reindexing needed
                if not clean and not self.reader.should_reindex(file_path, file_hashes.get(relative_path)):
                    logger.debug("skipping_unchanged", path=relative_path)
                    new_hashes[relative_path] = file_hashes[relative_path]
                    continue

                # Parse file
                parsed_content = self.parser.parse(file_path, content)
                language = self.parser.get_language(file_path)

                # Chunk content
                chunks = self.chunker.chunk(parsed_content, relative_path, language)

                # Convert to dicts for storage
                for chunk in chunks:
                    all_chunks.append({
                        "content": chunk.content,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "metadata": {
                            "path": relative_path,
                            "language": language,
                            "sha256": sha256,
                        },
                    })

                new_hashes[relative_path] = sha256
                files_indexed += 1
                logger.debug("indexed_file", path=relative_path, chunks=len(chunks))

            except Exception as e:
                logger.error("file_processing_error", path=str(file_path), error=str(e))

        # Save new hashes
        try:
            hashes_file.write_text(json.dumps(new_hashes, indent=2))
        except Exception as e:
            logger.warning("hash_save_error", error=str(e))

        duration = time.time() - start_time
        stats = {
            "files_indexed": files_indexed,
            "chunks": len(all_chunks),
            "duration_s": duration,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("ingestion_complete", **stats)
        return all_chunks, stats
