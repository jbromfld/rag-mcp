# Configuration Tracking & Versioning

Comprehensive system for tracking all configuration parameters to enable holistic comparison and drift analysis.

---

## Table of Contents

- [Overview](#overview)
- [Trackable Parameters](#trackable-parameters)
- [Configuration Versioning](#configuration-versioning)
- [Database Schema](#database-schema)
- [Configuration Snapshots](#configuration-snapshots)
- [Drift Detection](#drift-detection)
- [Comparison Analysis](#comparison-analysis)
- [Best Practices](#best-practices)

---

## Overview

To enable comprehensive analysis and comparison, the system tracks **every configuration parameter** that could affect query results. This includes:

- Provider selections (embedding, vector store, LLM)
- Model parameters (temperature, chunk size, overlap)
- Search parameters (top_k, hybrid weights, thresholds)
- System parameters (timeouts, retry policies)

### Why Track Everything?

1. **Reproducibility**: Recreate exact results from any query
2. **Comparison**: Compare apples-to-apples across tests
3. **Drift Detection**: Identify when results degrade over time
4. **Parameter Impact**: Understand which parameters affect quality/cost
5. **Rollback**: Revert to previous configurations if needed
6. **Audit Trail**: Full history of all configuration changes

---

## Trackable Parameters

### 1. Provider Configuration

```python
provider_config = {
    # Vector Store
    "vector_store": {
        "provider": "elasticsearch",  # elasticsearch, vertex, azure
        "url": "http://localhost:9200",
        "index_name": "knowledge_base",
        "version": "8.11.0"
    },

    # Embedding Provider
    "embedding": {
        "provider": "local",  # local, vertex, azure
        "model": "all-mpnet-base-v2",
        "dimension": 768,
        "batch_size": 32,
        "normalize": true
    },

    # LLM Provider
    "llm": {
        "provider": "ollama",  # ollama, vertex, azure
        "model": "llama3.2",
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
}
```

### 2. Chunking Configuration

```python
chunking_config = {
    "strategy": "recursive",  # fixed, recursive, semantic
    "chunk_size": 300,  # words
    "chunk_overlap": 30,  # words
    "min_chunk_size": 50,
    "max_chunk_size": 500,
    "separators": ["\n\n", "\n", ". ", " ", ""],
    "keep_separator": true,

    # Semantic-specific
    "semantic_threshold": 0.7,  # if strategy=semantic

    # Metadata
    "preserve_metadata": true,
    "metadata_fields": ["url", "title", "section", "timestamp"]
}
```

### 3. Retrieval Configuration

```python
retrieval_config = {
    # Search Parameters
    "top_k": 5,
    "hybrid_search": true,
    "vector_weight": 0.7,
    "bm25_weight": 0.3,
    "fusion_method": "rrf",  # rrf, weighted, cascade

    # Filtering
    "relevance_threshold": 0.7,
    "min_score": 0.5,
    "date_filter": null,  # optional date range
    "source_filter": null,  # optional source URLs

    # Reranking
    "enable_reranking": false,
    "rerank_model": null,  # e.g., "cross-encoder/ms-marco-MiniLM-L-6-v2"
    "rerank_top_k": 10,

    # Query Expansion
    "enable_query_expansion": false,
    "expansion_method": null,  # synonym, llm, embedding
    "max_expansions": 3
}
```

### 4. Generation Configuration

```python
generation_config = {
    # Prompt Configuration
    "prompt_template": "default",  # or custom template name
    "prompt_version": "1.0",
    "include_sources": true,
    "max_context_tokens": 8000,

    # Response Configuration
    "response_format": "markdown",  # text, markdown, json
    "include_citations": true,
    "citation_format": "inline",  # inline, footnote, list

    # Safety
    "content_filter": true,
    "pii_detection": false,
    "toxic_filter": false
}
```

### 5. System Configuration

```python
system_config = {
    # Performance
    "timeout_seconds": 30,
    "max_retries": 3,
    "retry_backoff": "exponential",
    "enable_caching": true,
    "cache_ttl_seconds": 3600,

    # Logging
    "log_level": "INFO",
    "log_queries": true,
    "log_responses": true,

    # Rate Limiting
    "rate_limit_per_minute": 60,
    "burst_limit": 10
}
```

---

## Configuration Versioning

### Configuration Profiles

Create named configuration profiles for easy switching:

```python
# config/profiles.py

PROFILES = {
    "local-baseline-v1": {
        "version": "1.0.0",
        "description": "Local providers, 768-dim, temp 0.7",
        "created_at": "2025-11-23T10:00:00Z",
        "provider": {
            "vector_store": "elasticsearch",
            "embedding": "local",
            "llm": "ollama"
        },
        "embedding": {
            "model": "all-mpnet-base-v2",
            "dimension": 768
        },
        "llm": {
            "model": "llama3.2",
            "temperature": 0.7
        },
        "chunking": {
            "chunk_size": 300,
            "chunk_overlap": 30
        },
        "retrieval": {
            "top_k": 5,
            "hybrid_search": true,
            "vector_weight": 0.7
        }
    },

    "local-high-dim-v1": {
        "version": "1.0.0",
        "description": "Local providers, 1536-dim, temp 0.7",
        # ... similar structure with dimension=1536
    },

    "vertex-optimal-v1": {
        "version": "1.0.0",
        "description": "GCP Vertex, optimized for cost",
        # ... vertex configuration
    }
}
```

### Version Tracking

Track configuration versions over time:

```python
configuration_version = {
    "profile_name": "local-baseline-v1",
    "version": "1.0.0",
    "parent_version": null,  # or previous version
    "changes": [
        {
            "parameter": "llm.temperature",
            "old_value": 0.7,
            "new_value": 0.5,
            "reason": "Reduce variability in responses",
            "changed_by": "user@example.com",
            "changed_at": "2025-11-24T10:00:00Z"
        }
    ],
    "performance_impact": {
        "avg_latency_delta_ms": -50,
        "avg_cost_delta_usd": 0.002,
        "avg_relevance_delta": -0.05
    }
}
```

---

## Database Schema

### Enhanced Schema with Configuration Tracking

```sql
-- Configuration profiles table
CREATE TABLE configuration_profiles (
    profile_id UUID PRIMARY KEY,
    profile_name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    parent_profile_id UUID REFERENCES configuration_profiles(profile_id),
    description TEXT,

    -- Complete configuration as JSONB
    provider_config JSONB NOT NULL,
    chunking_config JSONB NOT NULL,
    retrieval_config JSONB NOT NULL,
    generation_config JSONB NOT NULL,
    system_config JSONB NOT NULL,

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_profile_name (profile_name),
    INDEX idx_profile_active (is_active),
    INDEX idx_profile_created (created_at)
);

-- Configuration change log
CREATE TABLE configuration_changes (
    change_id UUID PRIMARY KEY,
    profile_id UUID REFERENCES configuration_profiles(profile_id),
    version_from VARCHAR(20),
    version_to VARCHAR(20),

    -- What changed
    parameter_path VARCHAR(200) NOT NULL,  -- e.g., "llm.temperature"
    old_value JSONB,
    new_value JSONB,

    -- Why and when
    reason TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Impact (populated after analysis)
    performance_impact JSONB,

    -- Indexes
    INDEX idx_changes_profile (profile_id),
    INDEX idx_changes_parameter (parameter_path),
    INDEX idx_changes_date (changed_at)
);

-- Update queries table to reference configuration
ALTER TABLE queries ADD COLUMN profile_id UUID REFERENCES configuration_profiles(profile_id);
ALTER TABLE queries ADD COLUMN config_snapshot JSONB NOT NULL;

-- Index for configuration-based queries
CREATE INDEX idx_queries_profile ON queries(profile_id);
CREATE INDEX idx_queries_config_hash ON queries((config_snapshot->>'hash'));

-- Metrics by configuration view
CREATE MATERIALIZED VIEW metrics_by_config AS
SELECT
    cp.profile_name,
    cp.version,
    DATE(q.created_at) as date,

    -- Provider info
    (cp.provider_config->'embedding'->>'model') as embedding_model,
    (cp.provider_config->'embedding'->>'dimension')::int as embedding_dimension,
    (cp.provider_config->'llm'->>'model') as llm_model,
    (cp.provider_config->'llm'->>'temperature')::float as llm_temperature,

    -- Chunking info
    (cp.chunking_config->>'chunk_size')::int as chunk_size,
    (cp.chunking_config->>'chunk_overlap')::int as chunk_overlap,

    -- Retrieval info
    (cp.retrieval_config->>'top_k')::int as top_k,
    (cp.retrieval_config->>'vector_weight')::float as vector_weight,

    -- Aggregated metrics
    COUNT(*) as total_queries,
    AVG(m.latency_total_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.latency_total_ms) as p95_latency_ms,
    AVG(m.cost_total_usd) as avg_cost_usd,
    AVG(m.top_relevance_score) as avg_relevance_score,

    -- User satisfaction
    COUNT(CASE WHEN f.rating = 'thumbs_up' THEN 1 END)::float / NULLIF(COUNT(f.rating), 0) as satisfaction_rate

FROM queries q
JOIN configuration_profiles cp ON q.profile_id = cp.profile_id
JOIN metrics m ON q.query_id = m.query_id
LEFT JOIN feedback f ON q.query_id = f.query_id
GROUP BY
    cp.profile_name, cp.version, date,
    embedding_model, embedding_dimension, llm_model, llm_temperature,
    chunk_size, chunk_overlap, top_k, vector_weight;

-- Refresh daily
-- Add to cron: 0 1 * * * psql -c "REFRESH MATERIALIZED VIEW metrics_by_config;"
```

---

## Configuration Snapshots

Every query stores a complete configuration snapshot for reproducibility.

### Snapshot Format

```python
config_snapshot = {
    # Unique hash of configuration
    "hash": "a3f8d9c1b2e4f5a6",

    # Profile reference
    "profile_name": "local-baseline-v1",
    "profile_version": "1.0.0",

    # Complete configuration at query time
    "provider": {...},
    "chunking": {...},
    "retrieval": {...},
    "generation": {...},
    "system": {...},

    # Timestamp
    "snapshot_at": "2025-11-23T10:30:00Z"
}
```

### Benefits

1. **Exact Reproducibility**: Rerun query with exact same config
2. **Regression Testing**: Compare old vs new configurations
3. **Audit Trail**: Know exactly what config produced each result
4. **A/B Testing**: Compare results from different configs

---

## Drift Detection

### Parameter-Based Drift Detection

Monitor how parameter changes affect results:

```python
class ParameterDriftDetector:
    def detect_drift(
        self,
        parameter: str,  # e.g., "llm.temperature"
        baseline_period: DateRange,
        current_period: DateRange,
        threshold: float = 0.1
    ) -> DriftReport:
        """
        Detect if a parameter change caused performance drift.

        Returns:
            DriftReport with:
            - parameter_changes: List of changes to this parameter
            - metric_impacts: How metrics changed after each change
            - drift_detected: Boolean if significant drift occurred
            - recommendations: Suggested actions
        """
        # 1. Find all changes to parameter in date range
        changes = self.get_parameter_changes(parameter, baseline_period, current_period)

        # 2. For each change, compare metrics before/after
        impacts = []
        for change in changes:
            before_metrics = self.get_metrics(
                profile_id=change.profile_id,
                end_date=change.changed_at,
                days=7
            )
            after_metrics = self.get_metrics(
                profile_id=change.profile_id,
                start_date=change.changed_at,
                days=7
            )

            impact = self.calculate_impact(before_metrics, after_metrics)
            impacts.append({
                "change": change,
                "impact": impact,
                "significant": abs(impact.relevance_delta) > threshold
            })

        # 3. Generate report
        return DriftReport(
            parameter=parameter,
            changes=changes,
            impacts=impacts,
            drift_detected=any(i["significant"] for i in impacts),
            recommendations=self.generate_recommendations(impacts)
        )
```

### Configuration Drift Monitoring

Automatically monitor for drift on a schedule:

```python
# Monitored parameters with thresholds
DRIFT_MONITORS = {
    "llm.temperature": {
        "metric": "avg_relevance_score",
        "threshold": 0.1,  # 10% change triggers alert
        "check_frequency": "daily"
    },
    "chunking.chunk_size": {
        "metric": "avg_relevance_score",
        "threshold": 0.15,
        "check_frequency": "weekly"
    },
    "retrieval.top_k": {
        "metric": "avg_relevance_score",
        "threshold": 0.1,
        "check_frequency": "daily"
    },
    "retrieval.vector_weight": {
        "metric": "avg_relevance_score",
        "threshold": 0.1,
        "check_frequency": "weekly"
    }
}
```

---

## Comparison Analysis

### Multi-Parameter Comparison

Compare results across multiple parameter variations:

```python
# Compare temperature variations
POST /compare/parameters

{
    "base_profile": "local-baseline-v1",
    "parameter": "llm.temperature",
    "values": [0.3, 0.5, 0.7, 0.9, 1.0],
    "test_queries": [
        "How do I create a virtual environment?",
        "What is FastAPI?",
        "How to implement authentication?"
    ],
    "metrics_to_track": [
        "avg_relevance_score",
        "avg_latency_ms",
        "avg_cost_usd",
        "response_variability"
    ]
}
```

Response:
```json
{
    "comparison_id": "comp_123",
    "parameter": "llm.temperature",
    "results": [
        {
            "value": 0.3,
            "avg_relevance_score": 4.2,
            "avg_latency_ms": 1050,
            "avg_cost_usd": 0.0,
            "response_variability": 0.15
        },
        {
            "value": 0.5,
            "avg_relevance_score": 4.3,
            "avg_latency_ms": 1100,
            "avg_cost_usd": 0.0,
            "response_variability": 0.22
        },
        {
            "value": 0.7,
            "avg_relevance_score": 4.1,
            "avg_latency_ms": 1200,
            "avg_cost_usd": 0.0,
            "response_variability": 0.35
        },
        {
            "value": 0.9,
            "avg_relevance_score": 3.8,
            "avg_latency_ms": 1300,
            "avg_cost_usd": 0.0,
            "response_variability": 0.48
        },
        {
            "value": 1.0,
            "avg_relevance_score": 3.5,
            "avg_latency_ms": 1350,
            "avg_cost_usd": 0.0,
            "response_variability": 0.61
        }
    ],
    "optimal_value": 0.5,
    "recommendations": [
        "Temperature 0.5 provides best balance of quality and consistency",
        "Higher temperatures (0.9+) show too much variability",
        "Lower temperatures (0.3) too deterministic, may miss nuance"
    ]
}
```

### Holistic Configuration Comparison

Compare complete configuration profiles:

```python
POST /compare/profiles

{
    "profiles": [
        "local-baseline-v1",
        "local-high-dim-v1",
        "vertex-optimal-v1",
        "custom-tuned-v2"
    ],
    "test_dataset": "golden-dataset-v1",
    "metrics": "all"
}
```

Response includes:
- Performance comparison (latency, throughput)
- Cost comparison (total, per-query, projected monthly)
- Quality comparison (relevance, accuracy, satisfaction)
- Configuration differences highlighted
- Recommendations for optimization

---

## Best Practices

### 1. Version Everything

```python
# Bad: Unnamed configuration
config = {"temperature": 0.7, "chunk_size": 300}

# Good: Named, versioned profile
profile = {
    "name": "local-baseline-v1",
    "version": "1.0.0",
    "description": "Initial baseline configuration",
    "temperature": 0.7,
    "chunk_size": 300
}
```

### 2. Document Configuration Changes

```python
# Always include reason for changes
change_config(
    profile="local-baseline-v1",
    parameter="llm.temperature",
    new_value=0.5,
    reason="Reduce variability after observing inconsistent responses in production",
    changed_by="john@example.com"
)
```

### 3. Test Before Deploying

```python
# Test configuration changes on golden dataset first
test_results = test_configuration_change(
    current_profile="local-baseline-v1",
    proposed_changes={"llm.temperature": 0.5},
    test_dataset="golden-dataset-v1"
)

if test_results.quality_delta < -0.1:
    print("WARNING: Quality decreased by more than 10%")
    # Don't deploy
```

### 4. Monitor After Deployment

```python
# Set up monitoring for new configuration
monitor_config_deployment(
    profile="local-baseline-v2",
    alert_on={
        "relevance_drop": 0.1,
        "latency_increase": 0.2,
        "cost_increase": 0.5
    },
    duration_days=7
)
```

### 5. Create Configuration Templates

```python
# Template for new profiles
PROFILE_TEMPLATE = {
    "name": "REQUIRED",
    "version": "REQUIRED",
    "description": "REQUIRED",
    "based_on": "optional-parent-profile",
    "provider": {
        "vector_store": "elasticsearch",
        "embedding": "local",
        "llm": "ollama"
    },
    # ... rest of config with sensible defaults
}
```

### 6. Regular Configuration Audits

```bash
# Weekly configuration audit script
python scripts/audit_configurations.py --report weekly

# Checks:
# - Which configurations are actively used?
# - Which have best performance?
# - Which have drifted from baseline?
# - Recommendations for consolidation
```

---

## API Endpoints

### Configuration Management

```bash
# List all configuration profiles
GET /config/profiles

# Get specific profile
GET /config/profiles/{profile_name}

# Create new profile
POST /config/profiles

# Update profile (creates new version)
PUT /config/profiles/{profile_name}

# Delete profile
DELETE /config/profiles/{profile_name}

# Get configuration change history
GET /config/profiles/{profile_name}/history

# Compare profiles
POST /config/compare

# Test profile changes
POST /config/test
```

---

## Example: Parameter Optimization Workflow

```python
# 1. Start with baseline
baseline = load_profile("local-baseline-v1")

# 2. Test temperature variations
temps = [0.3, 0.5, 0.7, 0.9]
results = []

for temp in temps:
    test_profile = baseline.copy()
    test_profile["llm"]["temperature"] = temp

    result = run_test_suite(test_profile, "golden-dataset-v1")
    results.append({
        "temperature": temp,
        "metrics": result
    })

# 3. Analyze results
best_temp = max(results, key=lambda x: x["metrics"]["avg_relevance_score"])

# 4. Create optimized profile
optimized = create_profile(
    name="local-optimized-temp-v1",
    based_on="local-baseline-v1",
    changes={"llm.temperature": best_temp["temperature"]},
    description=f"Optimized temperature to {best_temp['temperature']} based on testing"
)

# 5. A/B test in production
run_ab_test(
    control="local-baseline-v1",
    treatment="local-optimized-temp-v1",
    traffic_split=0.5,
    duration_days=7
)

# 6. Monitor and decide
results = get_ab_test_results("ab_test_123")
if results.treatment_better and results.statistically_significant:
    promote_profile("local-optimized-temp-v1")
```

---

## Configuration Export/Import

```python
# Export configuration for sharing
POST /config/profiles/{profile_name}/export

# Returns:
{
    "profile": {...},
    "metrics": {...},
    "test_results": {...}
}

# Import configuration
POST /config/profiles/import

{
    "profile": {...},
    "validate": true,
    "test_first": true
}
```

---

**Last Updated**: 2025-11-23
