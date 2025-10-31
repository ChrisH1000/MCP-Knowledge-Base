"""Ollama client for local LLM inference."""

from langchain_community.llms import Ollama

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Client for Ollama local LLM using LangChain (with LangSmith tracing)."""

    def __init__(self, settings: Settings):
        """Initialize the Ollama client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = Ollama(
            base_url=settings.OLLAMA_ENDPOINT,
            model=settings.LLM_MODEL,
            temperature=0.1,
        )
        logger.info("ollama_client_initialized", endpoint=settings.OLLAMA_ENDPOINT, model=settings.LLM_MODEL)

    async def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate a response using Ollama via LangChain.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            # LangChain automatically traces this to LangSmith
            response = await self.client.ainvoke(
                prompt,
                config={"max_tokens": max_tokens}
            )

            return response if isinstance(response, str) else str(response)

        except Exception as e:
            logger.error("ollama_generation_error", error=str(e))
            return "Error generating response"
