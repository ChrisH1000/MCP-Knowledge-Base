"""OpenAI client for LLM-based answering."""

from openai import OpenAI

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    """Client for OpenAI API."""

from typing import Optional
    def __init__(self, settings: Settings):
        """Initialize the OpenAI client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client: Optional[OpenAI] = None

    def initialize(self) -> None:
        """Initialize the OpenAI client."""
        if not self.settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
        logger.info("openai_client_initialized")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate a response using OpenAI.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        if self.client is None:
            self.initialize()

        assert self.client is not None

        try:
            response = self.client.chat.completions.create(
                model=self.settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.1,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error("openai_generation_error", error=str(e))
            return "Error generating response"
