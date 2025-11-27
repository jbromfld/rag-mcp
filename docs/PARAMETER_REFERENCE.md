# Parameter Reference

Quick reference for all trackable configuration parameters.

---

## Configuration Parameter Hierarchy

```
Configuration Profile
├── Provider Config
│   ├── Vector Store
│   ├── Embedding Provider
│   └── LLM Provider
├── Chunking Config
├── Retrieval Config
├── Generation Config
└── System Config
```

---

## All Trackable Parameters

### Provider Configuration

#### Vector Store Parameters

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `provider` | string | `elasticsearch` | `elasticsearch`, `vertex`, `azure` | Cost, Latency, Features |
| `url` | string | `http://localhost:9200` | Any valid URL | - |
| `index_name` | string | `knowledge_base` | Any string | - |
| `version` | string | - | Provider version | Features |

#### Embedding Parameters

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `provider` | string | `local` | `local`, `vertex`, `azure` | Cost, Latency |
| `model` | string | `all-mpnet-base-v2` | See [Models](#embedding-models) | Quality, Cost |
| `dimension` | integer | 768 | 384, 768, 1024, 1536, 3072 | Quality, Storage, Latency |
| `batch_size` | integer | 32 | 1-256 | Latency, Cost |
| `normalize` | boolean | true | true, false | Quality |

#### LLM Parameters

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `provider` | string | `ollama` | `ollama`, `vertex`, `azure` | Cost, Latency, Quality |
| `model` | string | `llama3.2` | See [Models](#llm-models) | Quality, Cost, Features |
| `temperature` | float | 0.7 | 0.0-2.0 | **Quality, Variability** |
| `max_tokens` | integer | 2000 | 1-32000 | Cost, Response Length |
| `top_p` | float | 0.9 | 0.0-1.0 | Quality, Variability |
| `frequency_penalty` | float | 0.0 | -2.0 to 2.0 | Repetition |
| `presence_penalty` | float | 0.0 | -2.0 to 2.0 | Topic Diversity |

---

### Chunking Configuration

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `strategy` | string | `recursive` | `fixed`, `recursive`, `semantic` | **Quality, Latency** |
| `chunk_size` | integer | 300 | 50-1000 words | **Quality, Cost, Latency** |
| `chunk_overlap` | integer | 30 | 0-200 words | **Quality** |
| `min_chunk_size` | integer | 50 | 10-500 words | Quality |
| `max_chunk_size` | integer | 500 | 100-2000 words | Quality, Cost |
| `separators` | array[string] | `["\n\n", "\n", ". "]` | Any separators | Quality |
| `keep_separator` | boolean | true | true, false | Quality |
| `semantic_threshold` | float | 0.7 | 0.0-1.0 | Quality (if semantic) |
| `preserve_metadata` | boolean | true | true, false | Features |

**High Impact**: `chunk_size`, `chunk_overlap`, `strategy`

---

### Retrieval Configuration

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `top_k` | integer | 5 | 1-50 | **Quality, Cost, Latency** |
| `hybrid_search` | boolean | true | true, false | **Quality** |
| `vector_weight` | float | 0.7 | 0.0-1.0 | **Quality** |
| `bm25_weight` | float | 0.3 | 0.0-1.0 | **Quality** |
| `fusion_method` | string | `rrf` | `rrf`, `weighted`, `cascade` | Quality |
| `relevance_threshold` | float | 0.7 | 0.0-1.0 | **Quality, Recall** |
| `min_score` | float | 0.5 | 0.0-1.0 | Quality, Recall |
| `date_filter` | object | null | Date range | Filtering |
| `source_filter` | array[string] | null | URL patterns | Filtering |
| `enable_reranking` | boolean | false | true, false | Quality, Latency |
| `rerank_model` | string | null | Model name | Quality, Latency |
| `rerank_top_k` | integer | 10 | 1-100 | Quality, Latency |
| `enable_query_expansion` | boolean | false | true, false | Quality, Latency |
| `expansion_method` | string | null | `synonym`, `llm`, `embedding` | Quality, Latency |
| `max_expansions` | integer | 3 | 1-10 | Quality, Latency |

**High Impact**: `top_k`, `hybrid_search`, `vector_weight`, `relevance_threshold`

---

### Generation Configuration

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `prompt_template` | string | `default` | Template name | **Quality** |
| `prompt_version` | string | `1.0` | Version string | Quality |
| `include_sources` | boolean | true | true, false | Features |
| `max_context_tokens` | integer | 8000 | 1000-32000 | Quality, Cost |
| `response_format` | string | `markdown` | `text`, `markdown`, `json` | Features |
| `include_citations` | boolean | true | true, false | Features |
| `citation_format` | string | `inline` | `inline`, `footnote`, `list` | Features |
| `content_filter` | boolean | true | true, false | Safety |
| `pii_detection` | boolean | false | true, false | Safety, Latency |
| `toxic_filter` | boolean | false | true, false | Safety, Latency |

**High Impact**: `prompt_template`, `max_context_tokens`

---

### System Configuration

| Parameter | Type | Default | Options | Impact On |
|-----------|------|---------|---------|-----------|
| `timeout_seconds` | integer | 30 | 5-300 | Reliability |
| `max_retries` | integer | 3 | 0-10 | Reliability, Latency |
| `retry_backoff` | string | `exponential` | `linear`, `exponential`, `constant` | Latency |
| `enable_caching` | boolean | true | true, false | Latency, Cost |
| `cache_ttl_seconds` | integer | 3600 | 60-86400 | Freshness, Cost |
| `log_level` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Debugging |
| `log_queries` | boolean | true | true, false | Privacy, Storage |
| `log_responses` | boolean | true | true, false | Privacy, Storage |
| `rate_limit_per_minute` | integer | 60 | 1-1000 | Throughput |
| `burst_limit` | integer | 10 | 1-100 | Throughput |

---

## Embedding Models

### Local (sentence-transformers)

| Model | Dimension | Best For | Speed | Quality |
|-------|-----------|----------|-------|---------|
| `all-MiniLM-L6-v2` | 384 | Fast, lightweight | ⚡⚡⚡⚡ | ⭐⭐⭐ |
| `all-mpnet-base-v2` | 768 | **General purpose (recommended)** | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| `bge-large-en` | 1024 | High quality | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| `jina-embeddings-v2-base-en` | 768 | General purpose | ⚡⚡⚡ | ⭐⭐⭐⭐ |

### GCP Vertex AI

| Model | Dimension | Cost (per 1K requests) |
|-------|-----------|------------------------|
| `text-embedding-004` | 768 | $0.025 |
| `textembedding-gecko@003` | 768 | $0.025 |

### Azure OpenAI

| Model | Dimension | Cost (per 1M tokens) |
|-------|-----------|----------------------|
| `text-embedding-3-small` | 1536 | $0.02 |
| `text-embedding-3-large` | 3072 | $0.13 |
| `text-embedding-ada-002` | 1536 | $0.10 |

---

## LLM Models

### Local (Ollama)

| Model | Parameters | Best For | Speed | Quality |
|-------|------------|----------|-------|---------|
| `llama3.2` | 3B | **General purpose** | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| `mistral` | 7B | High quality | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| `phi3` | 3.8B | Fast, efficient | ⚡⚡⚡ | ⭐⭐⭐ |
| `codellama` | 7B | Code generation | ⚡⚡ | ⭐⭐⭐⭐ |

### GCP Vertex AI

| Model | Cost (per 1M tokens) | Input | Output |
|-------|----------------------|-------|--------|
| `gemini-2.0-flash-exp` | $0.10 | $0.30 | **Recommended** |
| `gemini-pro` | $3.50 | $10.50 | High quality |

### Azure OpenAI

| Model | Cost (per 1M tokens) | Input | Output |
|-------|----------------------|-------|--------|
| `gpt-3.5-turbo` | $0.50 | $1.50 | Fast, cheap |
| `gpt-4o` | $5.00 | $15.00 | **High quality** |
| `gpt-4-turbo` | $10.00 | $30.00 | Best quality |

---

## Parameter Impact Matrix

### Quality Impact (High to Low)

1. **LLM Model** - Choice of LLM has largest quality impact
2. **Prompt Template** - How you prompt the LLM
3. **Chunk Size** - Affects context quality
4. **Top K** - More sources = better context
5. **Temperature** - Affects response consistency
6. **Embedding Model** - Affects retrieval quality
7. **Hybrid Search Weights** - Balance semantic vs keyword
8. **Chunk Overlap** - Context preservation
9. **Relevance Threshold** - Filters poor results

### Cost Impact (High to Low)

1. **LLM Provider** - Azure > GCP > Local ($0)
2. **Max Tokens** - Longer responses cost more
3. **Top K** - More sources = more processing
4. **Embedding Provider** - Cloud > Local ($0)
5. **Chunk Size** - Smaller = more embeddings
6. **Reranking** - Additional model calls

### Latency Impact (High to Low)

1. **LLM Provider** - Cloud providers add network latency
2. **LLM Model** - Larger models slower
3. **Top K** - More retrieval time
4. **Embedding Provider** - Cloud adds latency
5. **Reranking** - Additional processing
6. **Query Expansion** - More searches
7. **Chunk Size** - Affects processing time

---

## Recommended Starting Configurations

### Baseline (Local, Zero Cost)

```yaml
provider:
  vector_store: elasticsearch
  embedding: local (all-mpnet-base-v2, 768)
  llm: ollama (llama3.2)
chunking:
  strategy: recursive
  chunk_size: 300
  chunk_overlap: 30
retrieval:
  top_k: 5
  hybrid_search: true
  vector_weight: 0.7
llm:
  temperature: 0.7
  max_tokens: 2000
```

### Quality-Optimized (Higher Cost)

```yaml
provider:
  vector_store: elasticsearch
  embedding: azure (text-embedding-3-large, 3072)
  llm: azure (gpt-4o)
chunking:
  strategy: semantic
  chunk_size: 250
  chunk_overlap: 50
retrieval:
  top_k: 10
  hybrid_search: true
  vector_weight: 0.75
  enable_reranking: true
llm:
  temperature: 0.5
  max_tokens: 2000
```

### Speed-Optimized (Low Latency)

```yaml
provider:
  vector_store: elasticsearch
  embedding: local (all-MiniLM-L6-v2, 384)
  llm: ollama (phi3)
chunking:
  strategy: fixed
  chunk_size: 200
  chunk_overlap: 20
retrieval:
  top_k: 3
  hybrid_search: false
llm:
  temperature: 0.3
  max_tokens: 1000
```

### Cost-Optimized (Cloud)

```yaml
provider:
  vector_store: elasticsearch
  embedding: local (all-mpnet-base-v2, 768)
  llm: vertex (gemini-2.0-flash-exp)
chunking:
  strategy: recursive
  chunk_size: 350
  chunk_overlap: 30
retrieval:
  top_k: 5
  hybrid_search: true
llm:
  temperature: 0.5
  max_tokens: 1500
```

---

## Parameter Tuning Guidelines

### Temperature

- **0.0-0.3**: Deterministic, factual responses (good for documentation)
- **0.4-0.6**: Balanced (recommended for most use cases)
- **0.7-0.9**: Creative, varied responses
- **1.0+**: Very creative, potentially inconsistent

### Chunk Size

- **100-200**: Short, focused chunks (good for specific facts)
- **200-400**: Balanced (recommended for most documents)
- **400-600**: Longer context (good for complex topics)
- **600+**: Very long (may lose focus)

### Top K

- **1-3**: Fast, focused on most relevant
- **4-6**: Balanced (recommended)
- **7-10**: Comprehensive, may include less relevant
- **10+**: Risk of noise

### Vector Weight (in hybrid search)

- **0.0-0.3**: Prefer keyword matching (good for exact terms)
- **0.4-0.6**: Balanced
- **0.7-0.9**: Prefer semantic similarity (recommended)
- **1.0**: Pure vector search (no keyword)

---

## Configuration Change Checklist

When changing any configuration parameter:

- [ ] Document reason for change
- [ ] Test on golden dataset first
- [ ] Run A/B test if in production
- [ ] Monitor metrics for 7 days
- [ ] Check for drift
- [ ] Update documentation

---

**Last Updated**: 2025-11-23
