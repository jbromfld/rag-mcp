"""AWS Bedrock LLM provider implementation."""

import json
import os
import time
from typing import AsyncIterator, Optional

import boto3

from config.models import LLMProviderConfig

from ..base import LLMProvider, LLMResponse


class BedrockProvider(LLMProvider):
    """AWS Bedrock LLM provider.

    Supports Claude, Llama, Titan, and other models via AWS Bedrock.
    """

    def __init__(self, config: LLMProviderConfig):
        """Initialize Bedrock provider.

        Args:
            config: LLM provider configuration
        """
        self.config = config

        # Get AWS credentials from environment
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')

        # Create Bedrock client
        if aws_access_key and aws_secret_key:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=aws_region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
            )
        else:
            # Use default credentials (IAM role, profile, etc.)
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=aws_region,
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
        """Generate response from Bedrock.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Returns:
            LLMResponse with generated text and metadata
        """
        # Build request body based on model family
        if "anthropic.claude" in self.model:
            # Claude models use Messages API format
            messages = [{"role": "user", "content": prompt}]
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            }
            if system_prompt:
                request_body["system"] = system_prompt

        elif "meta.llama" in self.model:
            # Llama models
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            request_body = {
                "prompt": full_prompt,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_gen_len": max_tokens if max_tokens is not None else self.max_tokens,
            }

        elif "amazon.titan" in self.model:
            # Titan models
            request_body = {
                "inputText": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                "textGenerationConfig": {
                    "temperature": temperature if temperature is not None else self.temperature,
                    "maxTokenCount": max_tokens if max_tokens is not None else self.max_tokens,
                }
            }

        elif "amazon.nova" in self.model:
            # Nova models use Messages API format (similar to Claude)
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            request_body = {
                "messages": messages,
                "inferenceConfig": {
                    "temperature": temperature if temperature is not None else self.temperature,
                    "maxTokens": max_tokens if max_tokens is not None else self.max_tokens,
                }
            }
            if system_prompt:
                request_body["system"] = [{"text": system_prompt}]

        else:
            raise ValueError(f"Unsupported Bedrock model: {self.model}")

        # Measure latency
        start_time = time.time()

        # Make API request
        response = self.client.invoke_model(
            modelId=self.model,
            body=json.dumps(request_body),
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Parse response based on model family
        response_body = json.loads(response['body'].read())

        if "anthropic.claude" in self.model:
            content = response_body.get('content', [{}])[0].get('text', '')
            prompt_tokens = response_body.get('usage', {}).get('input_tokens', 0)
            completion_tokens = response_body.get('usage', {}).get('output_tokens', 0)
            finish_reason = response_body.get('stop_reason', 'end_turn')
            # Cost for Claude 3.5 Sonnet on Bedrock
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)

        elif "meta.llama" in self.model:
            content = response_body.get('generation', '')
            prompt_tokens = response_body.get('prompt_token_count', 0)
            completion_tokens = response_body.get('generation_token_count', 0)
            finish_reason = response_body.get('stop_reason', 'stop')
            # Cost for Llama models on Bedrock
            cost_usd = (prompt_tokens * 0.00065 / 1000) + (completion_tokens * 0.00065 / 1000)

        elif "amazon.titan" in self.model:
            content = response_body.get('results', [{}])[0].get('outputText', '')
            prompt_tokens = response_body.get('inputTextTokenCount', 0)
            completion_tokens = response_body.get('results', [{}])[0].get('tokenCount', 0)
            finish_reason = response_body.get('results', [{}])[0].get('completionReason', 'FINISH')
            # Cost for Titan models
            cost_usd = (prompt_tokens * 0.0008 / 1000) + (completion_tokens * 0.0016 / 1000)

        elif "amazon.nova" in self.model:
            # Nova models use Messages API format (similar to Claude)
            content = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            prompt_tokens = response_body.get('usage', {}).get('inputTokens', 0)
            completion_tokens = response_body.get('usage', {}).get('outputTokens', 0)
            finish_reason = response_body.get('stopReason', 'end_turn')
            # Cost for Nova models (Nova Sonic pricing as of January 2025)
            # Input: $0.0002/1K tokens, Output: $0.0008/1K tokens
            if "sonic" in self.model:
                cost_usd = (prompt_tokens * 0.0002 / 1000) + (completion_tokens * 0.0008 / 1000)
            elif "lite" in self.model:
                cost_usd = (prompt_tokens * 0.00006 / 1000) + (completion_tokens * 0.00024 / 1000)
            elif "pro" in self.model:
                cost_usd = (prompt_tokens * 0.0008 / 1000) + (completion_tokens * 0.0032 / 1000)
            else:
                cost_usd = (prompt_tokens * 0.0002 / 1000) + (completion_tokens * 0.0008 / 1000)

        else:
            content = str(response_body)
            prompt_tokens = 0
            completion_tokens = 0
            finish_reason = "unknown"
            cost_usd = 0.0

        total_tokens = prompt_tokens + completion_tokens

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
        """Generate streaming response from Bedrock.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional parameters

        Yields:
            Chunks of generated text
        """
        # Build request body based on model family (similar to generate())
        if "anthropic.claude" in self.model:
            messages = [{"role": "user", "content": prompt}]
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            }
            if system_prompt:
                request_body["system"] = system_prompt
        else:
            # Streaming not fully implemented for all models
            raise NotImplementedError(f"Streaming not yet supported for model: {self.model}")

        # Make streaming API request
        response = self.client.invoke_model_with_response_stream(
            modelId=self.model,
            body=json.dumps(request_body),
        )

        # Parse streaming response
        for event in response['body']:
            chunk = json.loads(event['chunk']['bytes'])
            if chunk.get('type') == 'content_block_delta':
                delta = chunk.get('delta', {})
                if delta.get('type') == 'text_delta':
                    yield delta.get('text', '')

    def get_model_name(self) -> str:
        """Get model name.

        Returns:
            Model name string
        """
        return self.model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses approximate count since Bedrock doesn't provide
        a unified tokenizer across all models.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate number of tokens
        """
        # Use 4 characters per token as approximation
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
        if "anthropic.claude-3-5-sonnet" in self.model:
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "anthropic.claude-3-opus" in self.model:
            cost_usd = (prompt_tokens * 0.015 / 1000) + (completion_tokens * 0.075 / 1000)
        elif "anthropic.claude" in self.model:
            # Default Claude pricing
            cost_usd = (prompt_tokens * 0.003 / 1000) + (completion_tokens * 0.015 / 1000)
        elif "meta.llama" in self.model:
            cost_usd = (prompt_tokens * 0.00065 / 1000) + (completion_tokens * 0.00065 / 1000)
        elif "amazon.titan" in self.model:
            cost_usd = (prompt_tokens * 0.0008 / 1000) + (completion_tokens * 0.0016 / 1000)
        elif "amazon.nova" in self.model:
            # Nova model pricing
            if "sonic" in self.model:
                cost_usd = (prompt_tokens * 0.0002 / 1000) + (completion_tokens * 0.0008 / 1000)
            elif "lite" in self.model:
                cost_usd = (prompt_tokens * 0.00006 / 1000) + (completion_tokens * 0.00024 / 1000)
            elif "pro" in self.model:
                cost_usd = (prompt_tokens * 0.0008 / 1000) + (completion_tokens * 0.0032 / 1000)
            else:
                cost_usd = (prompt_tokens * 0.0002 / 1000) + (completion_tokens * 0.0008 / 1000)
        else:
            cost_usd = 0.0

        return cost_usd

    async def close(self):
        """Close the client connection."""
        # Boto3 clients don't need explicit closing
        pass
