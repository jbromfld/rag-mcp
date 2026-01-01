"""OpenAI LLM provider implementation."""

import os
import time
from typing import AsyncIterator, Optional

import tiktoken
from openai import AsyncOpenAI

from config.models import LLMProviderConfig

from ..base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider using official OpenAI API.

    Supports GPT-4, GPT-4 Turbo, GPT-3.5, and other OpenAI models.
    """

    def __init__(self, config: LLMProviderConfig):
        """Initialize OpenAI provider.

        Args:
            config: LLM provider configuration
        """
        self.config = config

        # Prefer environment variable over config
        api_key = os.getenv('OPENAI_API_KEY') or config.api_key
        organization = os.getenv('OPENAI_ORGANIZATION')

        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=organization,
        )

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
        """Generate response from OpenAI.

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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Measure latency
        start_time = time.time()

        # Make API request
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            top_p=self.config.top_p if hasattr(self.config, 'top_p') else 1.0,
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract response
        content = response.choices[0].message.content or ""
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        finish_reason = response.choices[0].finish_reason or "stop"

        # Calculate cost (approximate, based on GPT-4o pricing)
        # Input: $0.005/1K tokens, Output: $0.015/1K tokens
        if "gpt-4o" in self.model:
            cost_usd = (prompt_tokens * 0.005 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "gpt-4-turbo" in self.model:
            cost_usd = (prompt_tokens * 0.01 / 1000) + (completion_tokens * 0.03 / 1000)
        elif "gpt-4" in self.model:
            cost_usd = (prompt_tokens * 0.03 / 1000) + (completion_tokens * 0.06 / 1000)
        elif "gpt-3.5-turbo" in self.model:
            cost_usd = (prompt_tokens * 0.0005 / 1000) + (completion_tokens * 0.0015 / 1000)
        else:
            cost_usd = 0.0

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=response.model,
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
        """Generate streaming response from OpenAI.

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
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Make streaming API request
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name string
        """
        return self.model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Default to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))

    def get_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for LLM generation.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD
        """
        # Pricing as of January 2025
        if "gpt-4o" in self.model:
            cost_usd = (prompt_tokens * 0.005 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "gpt-4-turbo" in self.model:
            cost_usd = (prompt_tokens * 0.01 / 1000) + (completion_tokens * 0.03 / 1000)
        elif "gpt-4" in self.model:
            cost_usd = (prompt_tokens * 0.03 / 1000) + (completion_tokens * 0.06 / 1000)
        elif "gpt-3.5-turbo" in self.model:
            cost_usd = (prompt_tokens * 0.0005 / 1000) + (completion_tokens * 0.0015 / 1000)
        else:
            cost_usd = 0.0

        return cost_usd

    async def close(self):
        """Close the client connection."""
        await self.client.close()
