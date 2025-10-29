"""File parsers for code and documentation."""

from pathlib import Path

from markdown_it import MarkdownIt

from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class FileParser:
    """Parse files and extract content with line numbers."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.md_parser = MarkdownIt()

    def parse(self, path: Path, content: str) -> str:
        """Parse file content based on file type.

        Args:
            path: Path to file
            content: File content

        Returns:
            Parsed content (plain text)
        """
        suffix = path.suffix.lower()

        if suffix in {".md", ".mdx"}:
            return self._parse_markdown(content)
        elif suffix in {".py", ".php", ".js", ".ts"}:
            return self._parse_code(content)
        else:
            return content

    def _parse_markdown(self, content: str) -> str:
        """Parse markdown to plain text while preserving structure.

        Args:
            content: Markdown content

        Returns:
            Plain text with preserved headings
        """
        # Simple approach: keep the markdown as-is for chunking
        # The embeddings model will handle the markdown syntax
        return content

    def _parse_code(self, content: str) -> str:
        """Parse code files.

        Args:
            content: Code content

        Returns:
            Code content (as-is for now)
        """
        # For MVP, we'll keep code as-is
        # Future: use tree-sitter for better parsing
        return content

    def get_language(self, path: Path) -> str:
        """Get language identifier for a file.

        Args:
            path: Path to file

        Returns:
            Language identifier
        """
        suffix = path.suffix.lower()
        lang_map = {
            ".py": "python",
            ".php": "php",
            ".js": "javascript",
            ".ts": "typescript",
            ".md": "markdown",
            ".mdx": "markdown",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
        }
        return lang_map.get(suffix, "text")
