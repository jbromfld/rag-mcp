"""Ollama LLM provider implementation."""

import time
from typing import Optional

import aiohttp

from config.models import LLMProviderConfig

from ..base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local LLM inference.

    Communicates with Ollama API via HTTP.
    Zero cost, but requires local compute resources.
    """

    def __init__(self, config: LLMProviderConfig):
        """Initialize Ollama provider.

        Args:
            config: LLM provider configuration
        """
        import os

        self.config = config

        # Prefer environment variable over config (allows switching local/container)
        # Priority: ENV > config > default
        self.base_url = os.getenv(
            'OLLAMA_BASE_URL') or config.base_url or "http://localhost:11434"

        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.top_p = config.top_p

        # Remove trailing slash from base URL
        self.base_url = self.base_url.rstrip("/")

        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.

        Returns:
            aiohttp ClientSession
        """
        if self.session is None or self.session.closed:
            # Create session with generous timeout for LLM generation
            timeout = aiohttp.ClientTimeout(
                total=300,  # 5 minutes total
                connect=30,  # 30s to establish connection
                sock_read=180  # 3 minutes to read response
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
            )
        return self.session

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate response from Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated text and metadata
        """
        session = await self._get_session()

        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
                "top_p": self.top_p,
            },
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Measure latency
        start_time = time.time()

        # Make API request
        async with session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(
                    f"Ollama API error ({response.status}): {error_text}"
                )

            data = await response.json()

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract response
        content = data.get("response", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.model,
            finish_reason=data.get("done_reason", "stop"),
            latency_ms=latency_ms,
            cost_usd=0.0,  # Local inference is free
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ):
        """Generate streaming response from Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text
        """
        session = await self._get_session()

        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_predict": max_tokens if max_tokens is not None else self.max_tokens,
                "top_p": self.top_p,
            },
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Make streaming API request
        async with session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=120),
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise RuntimeError(
                    f"Ollama API error ({response.status}): {error_text}"
                )

            # Stream response chunks
            async for line in response.content:
                if line:
                    import json

                    data = json.loads(line.decode("utf-8"))
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk

                    # Check if done
                    if data.get("done", False):
                        break

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name string
        """
        return self.model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses simple word-based estimation (Ollama doesn't expose tokenizer).
        Roughly 1.3 tokens per word for English.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated number of tokens
        """
        # Simple estimation: ~1.3 tokens per word
        words = len(text.split())
        return int(words * 1.3)

    def get_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost for LLM generation.

        Local Ollama inference is free.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            0.0 (local inference has no cost)
        """
        return 0.0

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
