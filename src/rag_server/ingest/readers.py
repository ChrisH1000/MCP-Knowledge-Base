"""File discovery and reading utilities."""

import hashlib
from pathlib import Path
from typing import Iterator

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class FileReader:
    """Handles file discovery and reading."""

    def __init__(self, settings: Settings):
        """Initialize the file reader.

        Args:
            settings: Application settings
        """
        self.settings = settings

    def discover_files(
        self,
        root: Path,
        patterns: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> Iterator[Path]:
        """Discover files matching patterns and exclusions.

        Args:
            root: Root directory to search
            patterns: Glob patterns to include (default: all files)
            exclude: Glob patterns to exclude

        Yields:
            Paths to discovered files
        """
        if patterns is None:
            patterns = ["**/*"]
        if exclude is None:
            exclude = []

        # Add default exclusions from settings
        exclude.extend(self.settings.exclude_globs)
        allowed_extensions = set(self.settings.allowed_filetypes)

        logger.info(
            "discovering_files",
            root=str(root),
            patterns=patterns,
            exclude_count=len(exclude),
        )

        discovered = 0
        for pattern in patterns:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue

                # Check exclusions
                relative = path.relative_to(root)
                if any(relative.match(ex) for ex in exclude):
                    continue

                # Check file extension
                if path.suffix not in allowed_extensions:
                    continue

                discovered += 1
                yield path

        logger.info("discovery_complete", files_found=discovered)

    def read_file(self, path: Path) -> tuple[str, str]:
        """Read file content and compute hash.

        Args:
            path: Path to file

        Returns:
            Tuple of (content, sha256_hash)
        """
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return content, sha256
        except Exception as e:
            logger.warning("file_read_error", path=str(path), error=str(e))
            return "", ""

    def should_reindex(self, path: Path, stored_hash: str | None) -> bool:
        """Check if file should be reindexed based on content hash.

        Args:
            path: Path to file
            stored_hash: Previously stored hash

        Returns:
            True if file should be reindexed
        """
        if stored_hash is None:
            return True

        _, current_hash = self.read_file(path)
        return current_hash != stored_hash
