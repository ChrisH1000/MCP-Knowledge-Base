"""OpenAI client for LLM-based answering."""

from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from rag_server.core.config import Settings
from rag_server.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIClient:
    """Client for OpenAI API using LangChain (with LangSmith tracing)."""

    def __init__(self, settings: Settings):
        """Initialize the OpenAI client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client: Optional[ChatOpenAI] = None

    def initialize(self) -> None:
        """Initialize the LangChain OpenAI client."""
        if not self.settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        self.client = ChatOpenAI(
            model=self.settings.LLM_MODEL,
            api_key=self.settings.OPENAI_API_KEY,
            temperature=0.1,
        )
        logger.info("openai_client_initialized", model=self.settings.LLM_MODEL)

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate a response using OpenAI via LangChain.

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
            # LangChain automatically traces this to LangSmith
            response = self.client.invoke(
                [HumanMessage(content=prompt)], config={"max_tokens": max_tokens}
            )

            return response.content if response.content else ""

        except Exception as e:
            logger.error("openai_generation_error", error=str(e))
            return "Error generating response"
