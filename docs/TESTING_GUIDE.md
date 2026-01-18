# RAG Testing Pipeline - Complete Testing Guide

A comprehensive guide to testing different RAG configurations using profiles, feedback loops, and comparative analysis.

---

## Table of Contents

- [Overview](#overview)
- [Configuration Profiles](#configuration-profiles)
- [Running Experiments](#running-experiments)
- [Feedback Loops](#feedback-loops)
- [Comparing Configurations](#comparing-configurations)
- [Local vs Remote Testing](#local-vs-remote-testing)
- [Cost Tracking](#cost-tracking)
- [Common Testing Scenarios](#common-testing-scenarios)

---

## Overview

This pipeline is designed to answer questions like:
- **Which embedding model works best for my domain?**
- **Is a larger embedding dimension worth the cost?**
- **How does chunk size affect retrieval quality?**
- **Should I use local models or cloud providers?**
- **What's the cost/quality tradeoff for different LLMs?**

### Testing Philosophy

1. **Test systematically**: Use configuration profiles to isolate variables
2. **Track everything**: Latency, cost, quality metrics, user feedback
3. **Compare objectively**: Side-by-side comparisons with statistical significance
4. **Iterate based on data**: Let feedback loops guide optimization

---

## Configuration Profiles

Profiles let you test different RAG configurations without changing code.

### What Gets Configured

Each profile specifies:
- **Vector Store**: PostgreSQL (pgvector), Elasticsearch, GCP Vertex, Azure
- **Embedding Provider**: Local (sentence-transformers), Vertex AI, Azure OpenAI
- **Embedding Model**: all-mpnet-base-v2, bge-large-en, text-embedding-004, etc.
- **Embedding Dimension**: 768, 1536, 3072
- **LLM Provider**: Ollama (local), Vertex AI (Gemini), Azure OpenAI (GPT-4)
- **Chunking Strategy**: Fixed size, recursive, semantic
- **Chunk Size**: 300-1000 words
- **Chunk Overlap**: 0-200 words
- **Retrieval Config**: hybrid search weights, top_k, relevance threshold
- **Generation Config**: temperature, max_tokens, citation format

### Creating Profiles

Profiles are stored in the database and can be created via:

**1. Default Profile (Auto-created)**
```bash
# Uses environment variables from .env
# Created automatically on first query
curl http://localhost:8000/profiles
```

**2. Custom Profile via Database**
```sql
INSERT INTO configuration_profiles (
    profile_name,
    version,
    description,
    provider_config,
    chunking_config,
    retrieval_config,
    generation_config,
    system_config
) VALUES (
    'high-quality',
    '1.0.0',
    'Larger chunks, more results, stricter relevance',
    '{"vector_store": {"provider": "postgresql", ...}, ...}'::jsonb,
    '{"strategy": "recursive", "chunk_size": 500, "chunk_overlap": 50}'::jsonb,
    '{"top_k": 10, "hybrid_search": true, "relevance_threshold": 0.0}'::jsonb,
    '{"temperature": 0.3, "max_tokens": 3000}'::jsonb,
    '{"timeout_seconds": 60}'::jsonb
);
```

### Using Profiles

```bash
# Ingest with specific profile
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org/3/",
    "profile": "high-quality"
  }'

# Query with specific profile
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?",
    "profile": "high-quality"
  }'
```

### Example Testing Profiles

| Profile Name | Purpose | Vector Store | Embedding | Chunk Size | LLM | Cost/Query |
|--------------|---------|--------------|-----------|------------|-----|------------|
| `baseline-local` | Zero-cost baseline | pgvector | Local (768) | 300 | Ollama | $0 |
| `high-dim-local` | Test larger embeddings | pgvector | Local (1536) | 300 | Ollama | $0 |
| `large-chunks` | Test chunking impact | pgvector | Local (768) | 800 | Ollama | $0 |
| `semantic-chunks` | Semantic chunking | pgvector | Local (768) | variable | Ollama | $0 |
| `cloud-llm` | Hybrid (local storage + cloud LLM) | pgvector | Local (768) | 300 | Gemini Flash | ~$0.001 |
| `full-vertex` | Full GCP stack | Vertex | Vertex (768) | 300 | Gemini Pro | ~$0.01 |
| `azure-premium` | Premium Azure setup | Azure | Azure (3072) | 500 | GPT-4 | ~$0.05 |

---

## Running Experiments

### Experiment 1: Embedding Dimension Comparison

**Question**: Is 1536-dim better than 768-dim for my use case?

```bash
# Step 1: Ingest with both profiles
python cli.py ringest https://docs.python.org/3/library/ 2 100 --profile baseline-local
python cli.py ringest https://docs.python.org/3/library/ 2 100 --profile high-dim-local

# Step 2: Test with same queries
for query in "What is asyncio?" "How do I use collections?" "Explain itertools"; do
  echo "Testing: $query"
  python cli.py query "$query" --profile baseline-local
  python cli.py query "$query" --profile high-dim-local
done

# Step 3: Compare metrics
python cli.py metrics --profile baseline-local
python cli.py metrics --profile high-dim-local
```

**What to compare**:
- Average chunk scores (higher = more relevant retrieval)
- User feedback scores (after manual review)
- Latency differences
- Storage requirements (check database size)

---

### Experiment 2: Chunk Size Optimization

**Question**: What chunk size gives the best retrieval quality?

```bash
# Create profiles with different chunk sizes: 200, 400, 600, 800
# Test each with identical query sets
# Analyze: retrieval precision, answer completeness, context relevance
```

**Key Metrics**:
- **Too small (200)**: Fragmented context, incomplete answers
- **Optimal (300-500)**: Balanced context, good retrieval
- **Too large (800+)**: Diluted relevance, longer answers

---

### Experiment 3: Local vs Cloud LLMs

**Question**: Is GPT-4 worth 50x the cost vs Llama 3.2?

```bash
# Same vector store and embeddings, different LLMs
python cli.py query "Explain Python decorators" --profile baseline-local
python cli.py query "Explain Python decorators" --profile cloud-llm

# Compare answer quality, citations, latency, cost
```

**Evaluation criteria**:
- Factual accuracy
- Citation quality
- Answer completeness
- Response time
- Cost per query

---

## Feedback Loops

Feedback improves retrieval over time through **quality boosting**.

### How Feedback Works

1. **User submits feedback** (0-10 score) for a query
2. **System updates chunk metrics** in `embeddings` table:
   - `avg_feedback_score`: Average score across all feedback
   - `num_feedback`: Number of feedback submissions
   - `retrieval_count`: How often chunk was retrieved
3. **Future queries benefit** from quality boosting:
   - High-rated chunks (≥7) get 1.2x boost
   - Medium-rated chunks (5-6) get 1.1x boost
   - Low-rated chunks (<5) get 0.9x penalty

### Submitting Feedback

```bash
# Query returns query_id
QUERY_ID=$(python cli.py query "What is Python?" | jq -r '.query_id')

# Submit feedback (0-10 scale)
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d "{
    \"query_id\": \"$QUERY_ID\",
    \"score\": 8,
    \"comment\": \"Great answer with relevant sources\"
  }"
```

### Feedback Loop Testing

**Test feedback effectiveness**:

```bash
# 1. Baseline: query before feedback
python cli.py query "Python async programming" --profile default > before.json

# 2. Submit feedback for multiple queries
# Rate good sources highly, bad sources poorly
for i in {1..10}; do
  # Query and provide feedback
  python cli.py query "async/await in Python" --profile default
  # Manually rate the results
done

# 3. Query again after feedback
python cli.py query "Python async programming" --profile default > after.json

# 4. Compare source rankings
# Good chunks should rank higher after positive feedback
```

### Feedback Analytics

```sql
-- View chunk quality metrics
SELECT
    substring(content, 1, 100) as content_preview,
    avg_feedback_score,
    num_feedback,
    retrieval_count,
    metadata->>'source_url' as source
FROM embeddings
WHERE num_feedback > 0
ORDER BY avg_feedback_score DESC
LIMIT 20;

-- Feedback distribution
SELECT
    score,
    COUNT(*) as count
FROM feedback
GROUP BY score
ORDER BY score DESC;

-- Profile performance by user satisfaction
SELECT
    cp.profile_name,
    COUNT(q.query_id) as total_queries,
    AVG(f.score) as avg_satisfaction,
    COUNT(f.feedback_id) FILTER (WHERE f.score >= 7) as satisfied,
    ROUND(
        COUNT(f.feedback_id) FILTER (WHERE f.score >= 7)::numeric /
        COUNT(f.feedback_id)::numeric,
        2
    ) as satisfaction_rate
FROM configuration_profiles cp
JOIN queries q ON cp.profile_id = q.profile_id
LEFT JOIN feedback f ON q.query_id = f.query_id
GROUP BY cp.profile_name
ORDER BY avg_satisfaction DESC;
```

---

## Comparing Configurations

### Side-by-Side Comparison

```bash
# Query multiple profiles at once
QUERY="How do I use virtual environments?"

for profile in baseline-local high-dim-local cloud-llm; do
  echo "=== Testing: $profile ==="
  python cli.py query "$QUERY" --profile $profile | \
    jq '{profile: .profile, latency: .metrics.latency_ms, cost: .metrics.cost_usd, chunks: .metrics.chunks_retrieved}'
done
```

### Metrics Comparison

```sql
-- Compare profiles across key metrics
SELECT
    cp.profile_name,
    COUNT(DISTINCT q.query_id) as queries,
    AVG(m.latency_total_ms) as avg_latency_ms,
    AVG(m.cost_total_usd) as avg_cost_usd,
    AVG(m.num_chunks_retrieved) as avg_chunks,
    AVG(m.avg_chunk_score) as avg_relevance_score,
    AVG(f.score) as avg_user_satisfaction
FROM configuration_profiles cp
LEFT JOIN queries q ON cp.profile_id = q.profile_id
LEFT JOIN metrics m ON q.query_id = m.query_id
LEFT JOIN feedback f ON q.query_id = f.query_id
WHERE q.created_at > NOW() - INTERVAL '7 days'
GROUP BY cp.profile_name
ORDER BY avg_user_satisfaction DESC;
```

### Statistical Significance

For proper A/B testing, collect enough samples:

```python
# tests/benchmarks/test_comparison.py
import scipy.stats as stats

def test_profile_comparison():
    """Test if profile differences are statistically significant."""

    # Get metrics for each profile (n=30+ queries each)
    baseline_latencies = get_latencies("baseline-local", n=30)
    test_latencies = get_latencies("high-dim-local", n=30)

    # T-test for statistical significance
    t_stat, p_value = stats.ttest_ind(baseline_latencies, test_latencies)

    # p < 0.05 = statistically significant difference
    assert p_value < 0.05, f"No significant difference (p={p_value:.3f})"
```

---

## Local vs Remote Testing

### Local-Only Setup (Zero Cost)

**Use Case**: Development, experimentation, cost-sensitive testing

```env
# .env
VECTOR_STORE=postgresql
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

**Pros**:
- ✅ Zero API costs
- ✅ Full control
- ✅ Fast iteration
- ✅ Works offline

**Cons**:
- ⚠️ Requires local GPU for best performance
- ⚠️ Limited to available models
- ⚠️ Slower inference than cloud

---

### Hybrid Setup (Best of Both)

**Use Case**: Local embeddings + cloud LLM for quality answers

```env
# Local embeddings (free)
VECTOR_STORE=postgresql
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-mpnet-base-v2

# Cloud LLM (pay only for generation)
LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-2.0-flash-exp
GCP_PROJECT=your-project
```

**Cost**: ~$0.50-1.00 per 1000 queries
**Sweet spot**: 90% cost savings vs full cloud, similar quality

---

### Full Cloud Setup

**Use Case**: Production deployment, maximum performance

```env
# GCP Example
VECTOR_STORE=vertex
EMBEDDING_PROVIDER=vertex
EMBEDDING_MODEL=text-embedding-004
LLM_PROVIDER=vertex
VERTEX_MODEL=gemini-1.5-pro
GCP_PROJECT=your-project
GCP_REGION=us-central1
```

**Cost**: ~$10-20 per 1000 queries
**Use when**: Need maximum performance, managed infrastructure

---

### Remote Ollama Setup

**Use Case**: Self-hosted LLM on GPU server

```env
# Run embeddings locally
EMBEDDING_PROVIDER=local

# Point to remote Ollama server
LLM_PROVIDER=ollama
OLLAMA_URL=http://your-gpu-server:11434
OLLAMA_MODEL=llama3.2
```

**Setup on GPU server**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.2

# Expose port (edit /etc/systemd/system/ollama.service)
Environment="OLLAMA_HOST=0.0.0.0:11434"

# Restart
sudo systemctl restart ollama
```

---

## Cost Tracking

All queries automatically track costs broken down by component.

### Viewing Costs

```bash
# Overall metrics
python cli.py metrics

# Profile-specific costs
curl http://localhost:8000/metrics?profile=cloud-llm | jq '.metrics.cost_total_usd'
```

### Cost Analysis Queries

```sql
-- Total costs by profile
SELECT
    cp.profile_name,
    COUNT(m.metric_id) as queries,
    SUM(m.cost_embedding_usd) as embedding_cost,
    SUM(m.cost_llm_usd) as llm_cost,
    SUM(m.cost_total_usd) as total_cost,
    AVG(m.cost_total_usd) as avg_cost_per_query,
    -- Project to 1000 queries
    AVG(m.cost_total_usd) * 1000 as cost_per_1k_queries
FROM configuration_profiles cp
JOIN queries q ON cp.profile_id = q.profile_id
JOIN metrics m ON q.query_id = m.query_id
GROUP BY cp.profile_name
ORDER BY total_cost DESC;

-- Cost over time (daily breakdown)
SELECT
    DATE(q.created_at) as date,
    cp.profile_name,
    COUNT(*) as queries,
    SUM(m.cost_total_usd) as daily_cost
FROM queries q
JOIN metrics m ON q.query_id = m.query_id
JOIN configuration_profiles cp ON q.profile_id = cp.profile_id
GROUP BY DATE(q.created_at), cp.profile_name
ORDER BY date DESC, daily_cost DESC;

-- Cost efficiency (cost per satisfied user)
SELECT
    cp.profile_name,
    AVG(m.cost_total_usd) as avg_cost,
    COUNT(f.feedback_id) FILTER (WHERE f.score >= 7) as satisfied_users,
    CASE
        WHEN COUNT(f.feedback_id) FILTER (WHERE f.score >= 7) > 0
        THEN SUM(m.cost_total_usd) / COUNT(f.feedback_id) FILTER (WHERE f.score >= 7)
        ELSE NULL
    END as cost_per_satisfied_user
FROM configuration_profiles cp
JOIN queries q ON cp.profile_id = q.profile_id
JOIN metrics m ON q.query_id = m.query_id
LEFT JOIN feedback f ON q.query_id = f.query_id
GROUP BY cp.profile_name
ORDER BY cost_per_satisfied_user;
```

### Cost Models

Cost calculation per provider:

**Local (Ollama)**:
- Embeddings: $0
- LLM: $0
- Total: $0

**GCP Vertex AI**:
- Embeddings: $0.00002/1000 characters
- Gemini Flash: $0.000125/1000 input tokens, $0.000375/1000 output tokens
- Gemini Pro: $0.001875/1000 input tokens, $0.003750/1000 output tokens

**Azure OpenAI**:
- text-embedding-3-large: $0.00013/1000 tokens
- GPT-4o: $0.005/1000 input tokens, $0.015/1000 output tokens

---

## Common Testing Scenarios

### Scenario 1: Optimize for Accuracy

**Goal**: Best possible answer quality, cost not a concern

```sql
-- Create high-quality profile
INSERT INTO configuration_profiles (profile_name, version, ...)
VALUES (
    'high-accuracy',
    '1.0.0',
    ...
    -- Large embeddings, semantic chunking, more context
    '{"provider": "azure", "model": "text-embedding-3-large", "dimension": 3072}'::jsonb,
    '{"strategy": "semantic", "chunk_size": 600}'::jsonb,
    '{"top_k": 15, "hybrid_search": true}'::jsonb,
    '{"temperature": 0.3, "max_tokens": 4000}'::jsonb,
    ...
);
```

---

### Scenario 2: Optimize for Cost

**Goal**: Acceptable quality at minimal cost

```sql
-- Budget-conscious profile
INSERT INTO configuration_profiles (profile_name, version, ...)
VALUES (
    'budget-local',
    '1.0.0',
    ...
    -- Local everything, smaller chunks, fewer results
    '{"provider": "local", "model": "all-mpnet-base-v2", "dimension": 768}'::jsonb,
    '{"strategy": "fixed", "chunk_size": 250}'::jsonb,
    '{"top_k": 3, "hybrid_search": true}'::jsonb,
    '{"temperature": 0.7, "max_tokens": 1500}'::jsonb,
    ...
);
```

---

### Scenario 3: Optimize for Speed

**Goal**: Fastest response time

```sql
-- Low-latency profile
INSERT INTO configuration_profiles (profile_name, version, ...)
VALUES (
    'fast-response',
    '1.0.0',
    ...
    -- Local embeddings, small context, Flash LLM
    '{"provider": "local", "model": "all-mpnet-base-v2", "dimension": 768}'::jsonb,
    '{"strategy": "fixed", "chunk_size": 200}'::jsonb,
    '{"top_k": 3, "hybrid_search": false}'::jsonb,  -- Pure vector search
    '{"temperature": 0.9, "max_tokens": 1000}'::jsonb,
    ...
);
```

---

### Scenario 4: Test Chunking Strategies

**Goal**: Find optimal chunking for your content type

```bash
# Create 3 profiles with different chunking
# - fixed-200: Small fixed chunks
# - recursive-400: Medium recursive chunks
# - semantic-var: Semantic boundary detection

# Ingest same content with each
for profile in fixed-200 recursive-400 semantic-var; do
  python cli.py ingest https://docs.python.org/3/library/ --profile $profile
done

# Test with diverse queries
QUERIES=(
  "What is asyncio?"  # Requires technical detail
  "Explain Python collections"  # Needs overview
  "How to use threading vs multiprocessing?"  # Requires comparison
)

for query in "${QUERIES[@]}"; do
  for profile in fixed-200 recursive-400 semantic-var; do
    python cli.py query "$query" --profile $profile
  done
done

# Compare: chunk coherence, answer completeness, citation quality
```

---

## Best Practices

### Testing Methodology

1. **Isolate variables**: Change one thing at a time
2. **Use consistent test sets**: Same queries across profiles
3. **Collect sufficient samples**: 30+ queries for statistical significance
4. **Blind evaluation**: Rate answers without knowing the profile
5. **Track everything**: All queries → database for analysis
6. **Document findings**: Note what works and what doesn't

### Profile Management

- Use semantic versioning (1.0.0, 1.1.0, 2.0.0)
- Document profile purpose in description
- Keep default profile stable
- Create new profiles for experiments
- Compare against baseline consistently

### Cost Management

- Start with local-only for development
- Test cloud providers with limited query sets
- Set budget alerts in cloud console
- Track projected monthly costs
- Use hybrid setups when possible

### Feedback Collection

- Establish feedback guidelines (what's a 7 vs 9?)
- Collect feedback from multiple users
- Balance positive/negative examples
- Review feedback for patterns
- Iterate based on data, not intuition

---

## Quick Reference

### Essential Commands

```bash
# Health check
curl http://localhost:8000/health

# Ingest
python cli.py ringest <url> <depth> <max_pages> --profile <name>

# Query
python cli.py query "<question>" --profile <name>

# Feedback
python cli.py feedback <query_id> <score>

# Metrics
python cli.py metrics --profile <name>

# List profiles
python cli.py profiles
```

### Database Queries

```sql
-- View all profiles
SELECT profile_name, version, description FROM configuration_profiles;

-- Recent queries
SELECT query_text, created_at FROM queries ORDER BY created_at DESC LIMIT 10;

-- Profile performance
SELECT cp.profile_name, COUNT(q.query_id), AVG(m.latency_total_ms), AVG(m.cost_total_usd)
FROM configuration_profiles cp
JOIN queries q ON cp.profile_id = q.profile_id
JOIN metrics m ON q.query_id = m.query_id
GROUP BY cp.profile_name;
```

---

**Last Updated**: 2025-12-28
