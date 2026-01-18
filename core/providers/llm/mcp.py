"""MCP (Model Context Protocol) Provider - passthrough for external generation."""

from typing import Optional

from config.models import LLMProviderConfig
from ..base import LLMProvider, LLMResponse


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
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """MCP provider doesn't generate - raises error if called.
        
        The query endpoint should use retrieve_only mode for MCP profiles.

        Args:
            prompt: User query
            system_prompt: Optional system prompt (ignored)
            temperature: Temperature (ignored)
            max_tokens: Max tokens (ignored)
            **kwargs: Additional parameters (ignored)

        Returns:
            Empty LLMResponse (should not be called)

        Raises:
            NotImplementedError: MCP provider doesn't generate responses
        """
        raise NotImplementedError(
            "MCP provider does not generate responses. "
            "Use retrieve_only=True in query endpoint for MCP profiles."
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """MCP provider doesn't support streaming.

        Args:
            prompt: User query
            system_prompt: Optional system prompt (ignored)
            temperature: Temperature (ignored)
            max_tokens: Max tokens (ignored)
            **kwargs: Additional parameters (ignored)

        Raises:
            NotImplementedError: MCP provider doesn't generate responses
        """
        raise NotImplementedError(
            "MCP provider does not generate responses. "
            "Use retrieve_only=True in query endpoint for MCP profiles."
        )
        yield  # Make this a generator

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name (passthrough)
        """
        return self.model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (estimate).

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count (4 chars per token)
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    def get_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for generation.

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
