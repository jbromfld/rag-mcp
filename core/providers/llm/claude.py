"""Anthropic Claude LLM provider implementation."""

import os
import time
from typing import AsyncIterator, Optional

from anthropic import AsyncAnthropic

from config.models import LLMProviderConfig

from ..base import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """Anthropic Claude LLM provider using official Anthropic API.

    Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models.
    """

    def __init__(self, config: LLMProviderConfig):
        """Initialize Claude provider.

        Args:
            config: LLM provider configuration
        """
        self.config = config

        # Prefer environment variable over config
        api_key = os.getenv('ANTHROPIC_API_KEY') or config.api_key

        if not api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")

        self.client = AsyncAnthropic(api_key=api_key)

        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate response from Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated text and metadata
        """
        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Measure latency
        start_time = time.time()

        # Make API request
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = system_prompt

        response = await self.client.messages.create(**request_params)

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract response
        content = response.content[0].text if response.content else ""
        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens
        total_tokens = prompt_tokens + completion_tokens
        finish_reason = response.stop_reason or "end_turn"

        # Calculate cost (based on Claude 3.5 Sonnet pricing)
        # Input: $0.003/1K tokens, Output: $0.015/1K tokens
        if "claude-3-5-sonnet" in self.model or "claude-3.5-sonnet" in self.model or "claude-sonnet-4" in self.model:
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "claude-3-opus" in self.model:
            cost_usd = (prompt_tokens * 0.015 / 1000) + (completion_tokens * 0.075 / 1000)
        elif "claude-3-sonnet" in self.model:
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "claude-3-haiku" in self.model:
            cost_usd = (prompt_tokens * 0.00025 / 1000) + (completion_tokens * 0.00125 / 1000)
        else:
            cost_usd = 0.0

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.model,
            finish_reason=finish_reason,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Generate streaming response from Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text
        """
        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Build request params
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": True,
        }

        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = system_prompt

        # Make streaming API request
        async with self.client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield text

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name string
        """
        return self.model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses approximate count (4 chars per token) since Anthropic
        doesn't provide a public tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate number of tokens
        """
        # Anthropic uses approximately 4 characters per token
        return len(text) // 4

    def get_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for LLM generation.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD
        """
        # Pricing as of January 2025
        if "claude-3-5-sonnet" in self.model or "claude-3.5-sonnet" in self.model:
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "claude-3-opus" in self.model:
            cost_usd = (prompt_tokens * 0.015 / 1000) + (completion_tokens * 0.075 / 1000)
        elif "claude-3-sonnet" in self.model:
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "claude-3-haiku" in self.model:
            cost_usd = (prompt_tokens * 0.00025 / 1000) + (completion_tokens * 0.00125 / 1000)
        else:
            cost_usd = 0.0

        return cost_usd

    async def close(self):
        """Close the client connection."""
        await self.client.close()
