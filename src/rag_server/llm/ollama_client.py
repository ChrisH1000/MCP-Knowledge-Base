"""Ollama client for local LLM inference."""

import httpx

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Client for Ollama local LLM."""

    def __init__(self, settings: Settings):
        """Initialize the Ollama client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.endpoint = settings.OLLAMA_ENDPOINT

    async def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate a response using Ollama.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.endpoint}/api/generate",
                    json={
                        "model": self.settings.LLM_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.1,
                        },
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "")
                else:
                    logger.error("ollama_error", status=response.status_code)
                    return "Error generating response"

        except Exception as e:
            logger.error("ollama_generation_error", error=str(e))
            return "Error generating response"
