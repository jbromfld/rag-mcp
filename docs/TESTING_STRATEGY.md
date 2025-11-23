# Testing Strategy

Comprehensive testing and evaluation strategy for the KB-Proto testing pipeline.

---

## Table of Contents

- [Overview](#overview)
- [Testing Levels](#testing-levels)
- [Provider Comparison Testing](#provider-comparison-testing)
- [Benchmark Suites](#benchmark-suites)
- [Evaluation Metrics](#evaluation-metrics)
- [Automated Testing](#automated-testing)
- [Performance Testing](#performance-testing)
- [Cost Analysis](#cost-analysis)
- [Drift Detection](#drift-detection)

---

## Overview

The KB-Proto testing strategy focuses on:

1. **Comparative Analysis**: Systematically compare provider combinations
2. **Reproducibility**: Ensure all tests can be reproduced
3. **Automated Evaluation**: Minimize manual intervention
4. **Real-world Scenarios**: Test with realistic queries and data
5. **Cost Awareness**: Track and optimize costs across providers

---

## Testing Levels

### 1. Unit Tests

Test individual components in isolation.

**Coverage Areas**:
- Embedding generation (all providers)
- Vector store operations (CRUD)
- LLM responses
- Document chunking strategies
- URL filtering and scraping
- Cost calculation logic

**Example Test**:
```python
# tests/unit/test_embeddings.py
import pytest
from core.embeddings.local_embeddings import LocalEmbeddings

@pytest.fixture
def local_embedder():
    return LocalEmbeddings(model="all-mpnet-base-v2")

def test_embedding_dimension(local_embedder):
    text = "This is a test sentence."
    embedding = local_embedder.embed(text)
    assert len(embedding) == 768

def test_embedding_consistency(local_embedder):
    text = "Test sentence"
    emb1 = local_embedder.embed(text)
    emb2 = local_embedder.embed(text)
    assert np.allclose(emb1, emb2, rtol=1e-5)

def test_batch_embedding(local_embedder):
    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings = local_embedder.embed_batch(texts)
    assert len(embeddings) == 3
    assert all(len(emb) == 768 for emb in embeddings)
```

**Run Unit Tests**:
```bash
pytest tests/unit/ -v --cov=core --cov-report=html
```

---

### 2. Integration Tests

Test component interactions and end-to-end flows.

**Coverage Areas**:
- Ingestion pipeline (scrape → chunk → embed → store)
- Query flow (embed → retrieve → rank → generate)
- Feedback recording and retrieval
- Metrics collection and aggregation
- Provider switching

**Example Test**:
```python
# tests/integration/test_query_flow.py
import pytest
from api.main import app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_end_to_end_query(client, populated_index):
    # Query the knowledge base
    response = client.post("/query", json={
        "query": "How do I install FastAPI?",
        "top_k": 3,
        "provider_config": {
            "vector_store": "elasticsearch",
            "embedding_provider": "local",
            "llm_provider": "ollama"
        }
    })

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "query_id" in data
    assert "answer" in data
    assert "sources" in data
    assert len(data["sources"]) <= 3

    # Verify metadata
    assert "metadata" in data
    assert data["metadata"]["latency_ms"]["total"] > 0

    # Verify sources have required fields
    for source in data["sources"]:
        assert "title" in source
        assert "url" in source
        assert "score" in source

def test_query_with_feedback_loop(client, populated_index):
    # Submit query
    query_response = client.post("/query", json={
        "query": "Python virtual environments",
        "provider_config": {
            "vector_store": "elasticsearch",
            "embedding_provider": "local",
            "llm_provider": "ollama"
        }
    })
    query_id = query_response.json()["query_id"]

    # Submit feedback
    feedback_response = client.post("/feedback", json={
        "query_id": query_id,
        "rating": "thumbs_up",
        "relevance_score": 5
    })
    assert feedback_response.status_code == 200

    # Verify feedback is recorded
    metrics_response = client.get(f"/metrics?query_id={query_id}")
    assert metrics_response.status_code == 200
    data = metrics_response.json()
    assert data["feedback"]["rating"] == "thumbs_up"
```

**Run Integration Tests**:
```bash
pytest tests/integration/ -v --log-cli-level=INFO
```

---

### 3. Provider Comparison Tests

Systematically test and compare different provider combinations.

**Test Matrix**:

| Test ID | Vector Store | Embedding | Dimension | LLM | Purpose |
|---------|--------------|-----------|-----------|-----|---------|
| LOCAL-768-OL | Elasticsearch | Local | 768 | Ollama | Baseline (zero cost) |
| LOCAL-1536-OL | Elasticsearch | Local | 1536 | Ollama | High-dim baseline |
| LOCAL-768-VX | Elasticsearch | Local | 768 | Vertex | Hybrid: local storage + cloud LLM |
| LOCAL-768-AZ | Elasticsearch | Local | 768 | Azure | Hybrid: local storage + Azure LLM |
| VERTEX-FULL | Vertex Vector | Vertex | 768 | Vertex | Full GCP stack |
| AZURE-FULL | Azure Search | Azure | 1536 | Azure | Full Azure stack |

**Example Test**:
```python
# tests/benchmarks/test_provider_comparison.py
import pytest
from typing import List, Dict
import pandas as pd

CONFIGURATIONS = [
    {
        "name": "local-768-ollama",
        "vector_store": "elasticsearch",
        "embedding_provider": "local",
        "embedding_dimension": 768,
        "llm_provider": "ollama"
    },
    {
        "name": "local-1536-ollama",
        "vector_store": "elasticsearch",
        "embedding_provider": "local",
        "embedding_dimension": 1536,
        "llm_provider": "ollama"
    },
    {
        "name": "local-768-vertex",
        "vector_store": "elasticsearch",
        "embedding_provider": "local",
        "embedding_dimension": 768,
        "llm_provider": "vertex"
    },
    {
        "name": "vertex-full",
        "vector_store": "vertex",
        "embedding_provider": "vertex",
        "llm_provider": "vertex"
    }
]

TEST_QUERIES = [
    "How do I create a virtual environment in Python?",
    "What is FastAPI and how does it work?",
    "How to implement authentication in FastAPI?",
    "How to handle errors in FastAPI?",
    "How to deploy FastAPI to production?"
]

def test_compare_all_configurations(client, populated_index):
    results = []

    for config in CONFIGURATIONS:
        for query in TEST_QUERIES:
            response = client.post("/query", json={
                "query": query,
                "provider_config": config
            })

            data = response.json()
            results.append({
                "configuration": config["name"],
                "query": query,
                "latency_ms": data["metadata"]["latency_ms"]["total"],
                "cost_usd": data["metadata"]["cost_usd"]["total"],
                "top_score": data["sources"][0]["score"] if data["sources"] else 0,
                "num_sources": len(data["sources"])
            })

    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)

    # Generate comparison report
    summary = df.groupby("configuration").agg({
        "latency_ms": ["mean", "std", "min", "max"],
        "cost_usd": "sum",
        "top_score": "mean"
    })

    print("\n=== Provider Comparison Summary ===")
    print(summary)

    # Assert performance criteria
    assert df[df["configuration"] == "local-768-ollama"]["cost_usd"].sum() == 0
    assert df.groupby("configuration")["latency_ms"].mean().max() < 5000
```

**Run Comparison Tests**:
```bash
pytest tests/benchmarks/test_provider_comparison.py -v -s
```

---

## Benchmark Suites

### Benchmark 1: Latency Performance

Measure end-to-end latency and component breakdown.

**Test Scenario**:
- 100 diverse queries
- Measure p50, p95, p99 latency
- Component breakdown (embedding, retrieval, LLM)

**Expected Results**:
- Local providers: < 2s (p95)
- Cloud providers: < 5s (p95)
- Embedding: < 100ms
- Retrieval: < 300ms

**Run**:
```bash
pytest tests/benchmarks/test_latency.py --benchmark-only
```

---

### Benchmark 2: Accuracy & Relevance

Evaluate retrieval accuracy and answer quality.

**Test Scenario**:
- Golden dataset with known correct answers
- Evaluate retrieval precision and recall
- LLM answer quality scoring

**Metrics**:
- Precision@K (K=1,3,5)
- Recall@K
- MRR (Mean Reciprocal Rank)
- NDCG (Normalized Discounted Cumulative Gain)

**Example**:
```python
# tests/benchmarks/test_accuracy.py
import pytest
from evaluation.automated_eval import AutomatedEvaluator

GOLDEN_DATASET = [
    {
        "query": "How to install FastAPI?",
        "relevant_docs": ["doc_123", "doc_456"],
        "expected_answer_keywords": ["pip install", "fastapi", "uvicorn"]
    },
    # ... more test cases
]

def test_retrieval_accuracy(client, populated_index):
    evaluator = AutomatedEvaluator()
    results = []

    for test_case in GOLDEN_DATASET:
        response = client.post("/query", json={
            "query": test_case["query"],
            "provider_config": {...}
        })

        data = response.json()
        retrieved_doc_ids = [s["chunk_id"] for s in data["sources"]]

        # Calculate precision@k
        relevant_retrieved = set(retrieved_doc_ids) & set(test_case["relevant_docs"])
        precision = len(relevant_retrieved) / len(retrieved_doc_ids)

        # Evaluate answer quality
        answer_score = evaluator.score_answer(
            data["answer"],
            test_case["expected_answer_keywords"]
        )

        results.append({
            "query": test_case["query"],
            "precision": precision,
            "answer_score": answer_score
        })

    # Assert minimum accuracy thresholds
    avg_precision = sum(r["precision"] for r in results) / len(results)
    assert avg_precision > 0.7
```

**Run**:
```bash
pytest tests/benchmarks/test_accuracy.py -v
```

---

### Benchmark 3: Cost Analysis

Track and compare costs across providers.

**Test Scenario**:
- 1000 queries per configuration
- Track embedding, retrieval, and LLM costs
- Calculate cost per query

**Expected Costs** (per 1000 queries):
- Local: $0
- Hybrid (local ES + Vertex LLM): ~$5-10
- Full Vertex: ~$15-30
- Full Azure: ~$20-40

**Example**:
```python
# tests/benchmarks/test_cost.py
def test_cost_tracking(client):
    configurations = [...]
    queries = [...]  # 100 test queries

    for config in configurations:
        total_cost = 0
        for query in queries:
            response = client.post("/query", json={
                "query": query,
                "provider_config": config
            })
            total_cost += response.json()["metadata"]["cost_usd"]["total"]

        # Project to 1000 queries
        projected_cost = total_cost * 10

        print(f"{config['name']}: ${projected_cost:.2f} per 1000 queries")

        # Verify local is zero cost
        if "local" in config["name"] and config["llm_provider"] == "ollama":
            assert total_cost == 0
```

**Run**:
```bash
pytest tests/benchmarks/test_cost.py -v -s
```

---

### Benchmark 4: Scalability

Test system behavior under load.

**Test Scenario**:
- Concurrent queries (1, 10, 50, 100)
- Large document collections (10K, 100K, 1M docs)
- Long-running ingestion jobs

**Metrics**:
- Throughput (queries/second)
- Latency degradation under load
- Resource utilization (CPU, memory)

**Example**:
```python
# tests/benchmarks/test_scalability.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_queries(client):
    query = "How to use FastAPI?"

    # Test with increasing concurrency
    for concurrency in [1, 10, 50]:
        tasks = [
            asyncio.create_task(
                client.post("/query", json={"query": query, ...})
            )
            for _ in range(concurrency)
        ]

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        throughput = concurrency / elapsed

        print(f"Concurrency {concurrency}: {throughput:.2f} queries/sec")

        # All queries should succeed
        assert all(r.status_code == 200 for r in responses)
```

**Run**:
```bash
pytest tests/benchmarks/test_scalability.py -v -s
```

---

## Evaluation Metrics

### Retrieval Metrics

**Precision@K**:
```
Precision@K = (Relevant docs in top K) / K
```

**Recall@K**:
```
Recall@K = (Relevant docs in top K) / (Total relevant docs)
```

**Mean Reciprocal Rank (MRR)**:
```
MRR = (1/N) * Σ(1 / rank of first relevant doc)
```

**NDCG (Normalized Discounted Cumulative Gain)**:
```
NDCG@K = DCG@K / IDCG@K
where DCG@K = Σ(relevance_i / log2(i+1))
```

### Answer Quality Metrics

**Semantic Similarity**:
- Compare generated answer to reference answer using embeddings
- Cosine similarity score

**Keyword Coverage**:
- Percentage of expected keywords present in answer

**Factual Accuracy** (manual or LLM-as-judge):
- Does answer contain factually correct information?
- Scale: 1-5

**Completeness**:
- Does answer fully address the query?
- Scale: 1-5

### System Metrics

**Latency Percentiles**:
- p50 (median)
- p95 (95th percentile)
- p99 (99th percentile)

**Availability**:
```
Availability = (Successful requests) / (Total requests)
```

**Error Rate**:
```
Error Rate = (Failed requests) / (Total requests)
```

---

## Automated Testing

### Continuous Testing Pipeline

```bash
# .github/workflows/test.yml (if using GitHub Actions)
name: Test Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      elasticsearch:
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
      postgres:
        image: postgres:15

    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Run benchmarks
        run: pytest tests/benchmarks/ -v --benchmark-only
```

### Scheduled Comparison Tests

Run provider comparisons nightly to detect regressions:

```bash
# Schedule via cron or CI/CD
0 2 * * * cd /path/to/kb-proto && pytest tests/benchmarks/test_provider_comparison.py --html=report.html
```

---

## Performance Testing

### Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class KBProtoUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def query_knowledge_base(self):
        self.client.post("/query", json={
            "query": "How to use FastAPI?",
            "provider_config": {
                "vector_store": "elasticsearch",
                "embedding_provider": "local",
                "llm_provider": "ollama"
            }
        })

    @task(1)
    def get_metrics(self):
        self.client.get("/metrics")
```

**Run Load Test**:
```bash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

## Cost Analysis

### Cost Tracking Framework

```python
# evaluation/cost_analyzer.py
class CostAnalyzer:
    def analyze_provider_costs(self, start_date, end_date):
        """
        Analyze costs across all providers for a date range.
        """
        costs = self.fetch_costs_from_db(start_date, end_date)

        return {
            "total_cost": sum(costs),
            "by_provider": self.group_by_provider(costs),
            "by_component": {
                "embedding": sum(c.embedding_cost for c in costs),
                "retrieval": sum(c.retrieval_cost for c in costs),
                "llm": sum(c.llm_cost for c in costs)
            },
            "cost_per_query": sum(costs) / len(costs),
            "projections": {
                "monthly_1k_queries": self.project_cost(costs, 1000),
                "monthly_10k_queries": self.project_cost(costs, 10000),
                "monthly_100k_queries": self.project_cost(costs, 100000)
            }
        }
```

**Generate Cost Report**:
```bash
python -m evaluation.cost_analyzer --start-date 2025-11-01 --end-date 2025-11-23
```

---

## Drift Detection

### Accuracy Drift Monitoring

Monitor for degradation in retrieval or answer quality over time.

**Detection Method**:
1. Establish baseline accuracy metrics
2. Track metrics over rolling windows (daily, weekly)
3. Alert if metrics drop below threshold

```python
# metrics/drift_detector.py
class DriftDetector:
    def detect_drift(self, baseline_metrics, current_metrics, threshold=0.1):
        """
        Detect if current metrics have drifted from baseline.

        Args:
            baseline_metrics: Dict of baseline metric values
            current_metrics: Dict of current metric values
            threshold: Maximum acceptable drift (default 10%)

        Returns:
            Dict with drift detection results
        """
        drift_detected = False
        drift_details = {}

        for metric, baseline_value in baseline_metrics.items():
            current_value = current_metrics.get(metric, 0)
            drift = abs(current_value - baseline_value) / baseline_value

            if drift > threshold:
                drift_detected = True
                drift_details[metric] = {
                    "baseline": baseline_value,
                    "current": current_value,
                    "drift_pct": drift * 100,
                    "exceeded_threshold": True
                }

        return {
            "drift_detected": drift_detected,
            "details": drift_details
        }
```

**Run Drift Detection**:
```bash
python -m metrics.drift_detector --baseline-period "2025-11-01 to 2025-11-07" --current-period "2025-11-16 to 2025-11-23"
```

---

## Test Data Management

### Golden Test Datasets

Create curated test datasets for reproducible evaluation:

**Dataset Structure**:
```json
{
  "name": "fastapi-golden-dataset-v1",
  "version": "1.0",
  "created": "2025-11-23",
  "test_cases": [
    {
      "query": "How do I install FastAPI?",
      "relevant_docs": ["doc_123", "doc_456"],
      "expected_keywords": ["pip install", "fastapi", "uvicorn"],
      "category": "installation",
      "difficulty": "easy"
    },
    {
      "query": "How to implement OAuth2 authentication?",
      "relevant_docs": ["doc_789", "doc_234", "doc_567"],
      "expected_keywords": ["OAuth2PasswordBearer", "token", "security"],
      "category": "authentication",
      "difficulty": "medium"
    }
  ]
}
```

Store in: `tests/data/golden_datasets/`

---

## Reporting

### Generate Comparison Report

```bash
python -m evaluation.reports generate-comparison \
  --start-date 2025-11-01 \
  --end-date 2025-11-23 \
  --output reports/comparison_2025-11-23.html
```

**Report Includes**:
- Latency comparison (charts)
- Cost comparison (tables and projections)
- Accuracy metrics
- User satisfaction scores
- Recommendations

---

## Best Practices

1. **Isolate Test Data**: Use separate indices/databases for testing
2. **Seed Random State**: For reproducible results
3. **Clean Up**: Reset state between tests
4. **Version Test Datasets**: Track changes to golden datasets
5. **Document Baselines**: Record baseline metrics for drift detection
6. **Automate Everything**: Minimize manual testing
7. **Test in Production-like Environment**: Match production configuration as closely as possible
8. **Monitor Costs**: Set budget alerts for cloud provider tests

---

**Last Updated**: 2025-11-23
