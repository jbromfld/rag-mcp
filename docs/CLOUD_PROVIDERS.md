# Cloud LLM Providers Configuration

The RAG testing pipeline now supports **7 LLM providers** for comprehensive testing and comparison.

---

## Supported Providers

| Provider | Type | Cost | Speed | Best For |
|----------|------|------|-------|----------|
| **Ollama** | Local | Free | Medium-Fast (M1 GPU) | Development, testing |
| **Vertex AI** | Cloud (GCP) | Low | Fast | Production, Gemini models |
| **Azure OpenAI** | Cloud (Azure) | Medium | Fast | Enterprise, GPT-4 |
| **OpenAI** | Cloud (Direct) | Medium | Fast | Latest GPT models |
| **Bedrock** | Cloud (AWS) | Medium | Fast | AWS ecosystem, Claude |
| **Claude** | Cloud (Anthropic) | Medium | Fast | Direct Anthropic access |
| **Copilot** | Cloud (GitHub) | Medium | Fast | Development workflows |

---

## Configuration

### 1. Ollama (Local - Already Configured ✅)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=2000
```

**Setup**:
```bash
brew install ollama
ollama pull llama3.2
```

**Cost**: $0 (uses your hardware)

---

### 2. GCP Vertex AI (Gemini)

```env
LLM_PROVIDER=vertex
VERTEX_LLM_MODEL=gemini-2.0-flash-exp
VERTEX_TEMPERATURE=0.7
VERTEX_MAX_TOKENS=2000
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
```

**Setup**:
```bash
pip install google-cloud-aiplatform
gcloud auth application-default login
```

**Cost**: ~$0.0005/query (Gemini Flash) - **Best value!**

---

### 3. Azure OpenAI

```env
LLM_PROVIDER=azure
AZURE_LLM_DEPLOYMENT=gpt-4o
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_TEMPERATURE=0.7
AZURE_MAX_TOKENS=2000
```

**Setup**:
```bash
pip install openai
# Create Azure OpenAI resource in Azure Portal
# Deploy a model (gpt-4o, gpt-4, etc.)
```

**Cost**: ~$0.005-0.05/query depending on model

---

### 4. OpenAI (Direct API)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
OPENAI_ORGANIZATION=  # Optional
```

**Setup**:
```bash
pip install openai
# Get API key from https://platform.openai.com/api-keys
```

**Cost**: ~$0.005-0.05/query depending on model

**Note**: For full implementation, add to requirements.txt and create `core/providers/llm/openai.py`:

```python
"""OpenAI LLM provider implementation."""
import os
from typing import Optional
from openai import AsyncOpenAI
from config.models import LLMProviderConfig
from ..base import LLMProvider, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY') or config.api_key,
            organization=os.getenv('OPENAI_ORGANIZATION')
        )

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=kwargs.get('temperature', self.config.temperature),
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            # ... rest of response
        )
```

Then update `core/providers/factory.py` to include:
```python
elif config.provider == "openai":
    from .llm.openai import OpenAIProvider
    return OpenAIProvider(config)
```

---

### 5. AWS Bedrock

```env
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_TEMPERATURE=0.7
BEDROCK_MAX_TOKENS=2000
```

**Setup**:
```bash
pip install boto3
# Configure AWS credentials
aws configure
# Request model access in AWS Bedrock console
```

**Cost**: ~$0.003-0.015/query depending on model

**Note**: Requires `core/providers/llm/bedrock.py` implementation using boto3

---

### 6. Anthropic Claude (Direct API)

```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_TEMPERATURE=0.7
CLAUDE_MAX_TOKENS=2000
```

**Setup**:
```bash
pip install anthropic
# Get API key from https://console.anthropic.com/
```

**Cost**: ~$0.003-0.015/query depending on model

**Note**: Requires `core/providers/llm/claude.py` implementation using anthropic SDK

---

### 7. GitHub Copilot

```env
LLM_PROVIDER=copilot
COPILOT_API_KEY=your-copilot-token
COPILOT_MODEL=gpt-4o
COPILOT_TEMPERATURE=0.7
COPILOT_MAX_TOKENS=2000
```

**Setup**:
```bash
# GitHub Copilot for Business/Enterprise
# Requires GitHub Copilot API access
```

**Cost**: Included with Copilot license

**Note**: Requires custom implementation for GitHub Copilot API

---

## Implementation Status

| Provider | Config ✅ | Implementation | SDK Required |
|----------|-----------|----------------|--------------|
| **Ollama** | ✅ | ✅ Complete | None (HTTP) |
| **Vertex AI** | ✅ | ✅ Complete | google-cloud-aiplatform |
| **Azure** | ✅ | ✅ Complete | openai |
| **OpenAI** | ✅ | ⚠️ Template | openai |
| **Bedrock** | ✅ | ⚠️ Template | boto3 |
| **Claude** | ✅ | ⚠️ Template | anthropic |
| **Copilot** | ✅ | ⚠️ Template | Custom |

**Legend**:
- ✅ Complete: Ready to use
- ⚠️ Template: Configuration ready, needs provider implementation

---

## Testing Different Providers

### Quick Comparison

```bash
# Test with Ollama (local, free)
LLM_PROVIDER=ollama python cli.py query "What is Python?"

# Test with Gemini Flash (fast, cheap)
LLM_PROVIDER=vertex python cli.py query "What is Python?"

# Test with GPT-4 via OpenAI
LLM_PROVIDER=openai python cli.py query "What is Python?"

# Compare all
python cli.py report
```

### Create Testing Profiles

```sql
-- Fast & cheap profile (Gemini Flash)
INSERT INTO configuration_profiles (...) VALUES (
    'gemini-fast',
    ...
    '{"provider": "vertex", "model": "gemini-2.0-flash-exp", ...}'::jsonb
);

-- Premium profile (GPT-4)
INSERT INTO configuration_profiles (...) VALUES (
    'gpt4-premium',
    ...
    '{"provider": "openai", "model": "gpt-4o", ...}'::jsonb
);

-- Budget profile (Gemini Flash)
INSERT INTO configuration_profiles (...) VALUES (
    'budget-cloud',
    ...
    '{"provider": "vertex", "model": "gemini-1.5-flash", ...}'::jsonb
);
```

---

## Cost Comparison (per 1000 queries)

Based on typical RAG queries with ~1500 input tokens, 500 output tokens:

| Provider | Model | Cost/1K | Speed | Quality |
|----------|-------|---------|-------|---------|
| Ollama | llama3.2 | $0 | Medium | Good |
| Vertex | gemini-2.0-flash | **$0.50** | ⚡ Very Fast | Excellent |
| Vertex | gemini-1.5-pro | $5.00 | Fast | Excellent |
| Azure | gpt-4o | $15-20 | Fast | Excellent |
| OpenAI | gpt-4o | $15-20 | Fast | Excellent |
| OpenAI | gpt-4-turbo | $25-30 | Fast | Premium |
| Bedrock | claude-3.5-sonnet | $10-15 | Fast | Excellent |
| Claude | claude-3.5-sonnet | $10-15 | Fast | Excellent |

**Recommendation**: Start with Ollama (free) for development, test Gemini Flash for production ($0.50/1K queries = best value).

---

## Provider-Specific Notes

### Ollama
- Fastest when using M1/M2 Mac with Metal acceleration
- Slower on CPU-only systems (20-40s per query)
- Great for development and testing
- No API keys needed

### Vertex AI (Gemini)
- **Best cost/performance ratio**
- Gemini Flash: Very fast, very cheap
- Requires GCP project and credentials
- Pay only for what you use

### Azure OpenAI
- Enterprise-friendly (compliance, data residency)
- More expensive than direct OpenAI
- Good for existing Azure customers
- Requires resource deployment

### OpenAI Direct
- Access to latest models first
- Simple API
- Good documentation
- Higher cost than Vertex

### AWS Bedrock
- Good for AWS ecosystem
- Access to multiple model families (Claude, Llama, etc.)
- Requires model access request
- Regional availability varies

### Anthropic Claude
- Direct access to Claude models
- Good for specific Claude features
- Comparable pricing to OpenAI
- Requires Anthropic account

### GitHub Copilot
- For GitHub Enterprise/Business
- Uses OpenAI models under the hood
- Integrated with dev workflows
- Requires special API access

---

## Next Steps

1. **Choose a provider** for testing (recommend: Vertex AI Gemini Flash)
2. **Set up credentials** (API keys, service accounts)
3. **Update .env** with your configuration
4. **Test queries** with different providers
5. **Compare results** using `python cli.py report`
6. **Analyze cost vs quality** to pick the best for your use case

---

**Last Updated**: 2025-12-28
