"""MCP (Model Context Protocol) Provider - passthrough for external generation."""

from typing import List

from config.models import LLMProviderConfig
from ..base import LLMProvider


class MCPProvider(LLMProvider):
    """MCP provider that returns chunks without generation.
    
    This provider is used when the MCP host (e.g., Copilot) will handle
    the actual text generation. The RAG system only does retrieval.
    """

    def __init__(self, config: LLMProviderConfig):
        """Initialize MCP provider.

        Args:
            config: LLM provider configuration
        """
        self.config = config
        self.model = config.model

    async def generate(
        self,
        prompt: str,
        context: List[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """MCP provider doesn't generate - raises error if called.
        
        The query endpoint should use retrieve_only mode for MCP profiles.

        Args:
            prompt: User query
            context: Retrieved context chunks
            temperature: Temperature (ignored)
            max_tokens: Max tokens (ignored)

        Returns:
            Empty string (should not be called)

        Raises:
            NotImplementedError: MCP provider doesn't generate responses
        """
        raise NotImplementedError(
            "MCP provider does not generate responses. "
            "Use retrieve_only=True in query endpoint for MCP profiles."
        )

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for generation.

        Args:
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion

        Returns:
            Cost in USD (always 0 for MCP)
        """
        return 0.0

    async def close(self) -> None:
        """Close provider (no-op for MCP)."""
        pass
