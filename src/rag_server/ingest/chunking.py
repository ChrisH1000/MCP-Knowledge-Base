"""Text chunking strategies for embedding."""

from typing import Any, Dict, List, Optional

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class Chunk:
    """A text chunk with metadata."""

    def __init__(
        self,
        content: str,
        start_line: int,
        end_line: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize chunk.

        Args:
            content: Chunk text content
            start_line: Starting line number
            end_line: Ending line number
            metadata: Additional metadata
        """
        self.content = content
        self.start_line = start_line
        self.end_line = end_line
        self.metadata = metadata or {}


class TextChunker:
    """Chunk text content for embedding."""

    def __init__(self, settings: Settings):
        """Initialize the chunker.

        Args:
            settings: Application settings
        """
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.overlap = settings.RAG_CHUNK_OVERLAP

    def chunk(self, content: str, path: str, language: str) -> List[Chunk]:
        """Chunk content into overlapping windows.

        Args:
            content: Text content to chunk
            path: File path for metadata
            language: Language identifier

        Returns:
            List of chunks with metadata
        """
        lines = content.splitlines(keepends=True)
        chunks: List[Chunk] = []

        # Simple line-based chunking with character limit
        current_chunk_lines: List[str] = []
        current_chunk_start = 1
        current_length = 0

        for i, line in enumerate(lines, start=1):
            line_length = len(line)

            # If adding this line exceeds chunk size, save current chunk
            if current_length + line_length > self.chunk_size and current_chunk_lines:
                chunk_text = "".join(current_chunk_lines)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        start_line=current_chunk_start,
                        end_line=i - 1,
                        metadata={
                            "path": path,
                            "language": language,
                        },
                    )
                )

                # Start new chunk with overlap
                overlap_chars = 0
                overlap_lines: List[str] = []
                for prev_line in reversed(current_chunk_lines):
                    if overlap_chars + len(prev_line) <= self.overlap:
                        overlap_lines.insert(0, prev_line)
                        overlap_chars += len(prev_line)
                    else:
                        break

                current_chunk_lines = overlap_lines
                current_chunk_start = i - len(overlap_lines)
                current_length = overlap_chars

            current_chunk_lines.append(line)
            current_length += line_length

        # Add final chunk
        if current_chunk_lines:
            chunk_text = "".join(current_chunk_lines)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    start_line=current_chunk_start,
                    end_line=len(lines),
                    metadata={
                        "path": path,
                        "language": language,
                    },
                )
            )

        logger.debug("chunked_file", path=path, chunks=len(chunks))
        return chunks
