# Design Decisions

Key architectural and implementation decisions for the RAG testing pipeline.

---

## Table of Contents

- [Feedback Scoring System](#feedback-scoring-system)
- [Chunking Strategy](#chunking-strategy)
- [Configuration Management](#configuration-management)
- [Provider Abstraction](#provider-abstraction)

---

## Feedback Scoring System

### Decision: 0-10 Integer Scale

**Chosen**: Single integer score from 0-10
**Rejected**: Thumbs up/down, separate relevance/accuracy scores

### Rationale

**Advantages of 0-10 Scale**:
1. **Granular Feedback**: Captures nuance (poor=2, okay=5, good=8, excellent=10)
2. **Statistical Analysis**: Easy to calculate averages, medians, trends
3. **Drift Detection**: Small degradations visible (7.5 → 7.0 alerts on 7% drop)
4. **Simple UI**: Single rating input, not multiple fields
5. **Universal**: Everyone understands 0-10 (like NPS, movie ratings)

**Score Interpretation**:
```
0-2:  Completely wrong or unhelpful
3-4:  Partially correct but missing key information
5-6:  Acceptable but could be better
7-8:  Good, helpful response
9-10: Excellent, exactly what was needed
```

**Satisfaction Rate**: Score ≥7 is considered "satisfied"
```sql
satisfaction_rate = COUNT(score >= 7) / COUNT(*)
```

### Implementation

```python
# API Endpoint
POST /feedback
{
  "query_id": "uuid",
  "score": 8,  # 0-10
  "comment": "optional text"
}

# Database
CREATE TABLE feedback (
    feedback_id UUID PRIMARY KEY,
    query_id UUID REFERENCES queries(query_id),
    score INT NOT NULL CHECK (score BETWEEN 0 AND 10),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Metrics Tracked

```python
{
  "avg_score": 7.2,
  "median_score": 8,
  "score_distribution": {
    "0-2": 5,    # 3.3%
    "3-4": 10,   # 6.7%
    "5-6": 25,   # 16.7%
    "7-8": 60,   # 40%
    "9-10": 50   # 33.3%
  },
  "satisfaction_rate": 0.73,  # 73% scored 7+
  "trend": "+0.2 from last week"
}
```

---

## Chunking Strategy

### Decision: Fixed Configuration, No Randomization

**Chosen**: Explicit, deterministic chunk sizes per configuration profile
**Rejected**: Randomized chunk sizes for each document

### Rationale

**Why No Randomization**:

1. **Simplicity** ✅
   - Fixed chunk size = predictable behavior
   - Easy to understand and debug
   - No complex tracking of which chunks used which size

2. **Reproducibility** ✅
   - Same document = same chunks every time
   - Can reproduce exact query results
   - Easier to debug issues

3. **Clear Comparison** ✅
   - Direct A/B test: 200 vs 300 vs 400 word chunks
   - Statistical significance easier to determine
   - No confounding variables

4. **Debugging** ✅
   - "Why did this query fail?" → Check the fixed chunk size
   - Not: "Which random chunk size was used for this specific document?"

5. **Performance** ✅
   - No overhead from random number generation
   - Caching more effective (same input = same output)

**Why Randomization Would Be Problematic**:
- ❌ Inconsistent results for same query
- ❌ Harder to attribute performance to specific configuration
- ❌ Confounds A/B tests (is difference due to model or chunk size?)
- ❌ More complex code with no real benefit

### Better Approach: Explicit Testing

Instead of randomization, create multiple configuration profiles:

```python
# Configuration profiles for chunk size testing
PROFILES = {
    "chunks-200": {
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 200,
            "chunk_overlap": 20
        }
    },
    "chunks-300": {
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 300,
            "chunk_overlap": 30
        }
    },
    "chunks-400": {
        "chunking": {
            "strategy": "recursive",
            "chunk_size": 400,
            "chunk_overlap": 40
        }
    }
}

# Test each explicitly
for profile in PROFILES:
    results = run_test_suite(profile, golden_dataset)
    analyze_results(results)

# Compare results
compare_profiles(["chunks-200", "chunks-300", "chunks-400"])
```

### Chunk Size Testing Strategy

**1. Baseline Testing**
```python
# Test range of chunk sizes with fixed other parameters
chunk_sizes = [100, 200, 300, 400, 500, 600]
for size in chunk_sizes:
    profile = create_profile(f"chunks-{size}", chunk_size=size)
    run_tests(profile)

# Analyze which size performs best
optimal_size = find_optimal_chunk_size(results)
```

**2. Chunk Overlap Testing**
```python
# After finding optimal size, test overlap ratios
chunk_size = 300
overlaps = [0, 30, 60, 90]  # 0%, 10%, 20%, 30%
for overlap in overlaps:
    profile = create_profile(f"chunks-{size}-overlap-{overlap}")
    run_tests(profile)
```

**3. Strategy Testing**
```python
# Test different chunking strategies
strategies = ["fixed", "recursive", "semantic"]
for strategy in strategies:
    profile = create_profile(f"chunks-{strategy}")
    run_tests(profile)
```

### Implementation

```python
# core/ingestion/chunker.py

class DocumentChunker:
    def __init__(self, config: ChunkingConfig):
        self.chunk_size = config.chunk_size  # Fixed, not random
        self.chunk_overlap = config.chunk_overlap
        self.strategy = config.strategy

    def chunk(self, document: str) -> List[Chunk]:
        """
        Chunk document using fixed configuration.
        Same document always produces same chunks.
        """
        if self.strategy == "fixed":
            return self._chunk_fixed(document)
        elif self.strategy == "recursive":
            return self._chunk_recursive(document)
        elif self.strategy == "semantic":
            return self._chunk_semantic(document)

    def _chunk_fixed(self, document: str) -> List[Chunk]:
        # Always use self.chunk_size (deterministic)
        words = document.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunks.append(Chunk(text=" ".join(chunk_words)))
        return chunks
```

### Configuration Tracking

Every chunk's size is tracked via configuration profile:

```sql
-- Query references configuration profile
SELECT
    q.query_text,
    cp.profile_name,
    (cp.chunking_config->>'chunk_size')::int as chunk_size,
    m.avg_relevance_score
FROM queries q
JOIN configuration_profiles cp ON q.profile_id = cp.profile_id
JOIN metrics m ON q.query_id = m.query_id;
```

### Result: Simple, Testable, Reproducible

```python
# Ingest with chunks-300 profile
POST /ingest
{
  "url": "https://docs.python.org",
  "profile": "chunks-300"
}

# Query always uses same chunk size as ingestion
POST /query
{
  "query": "How to create virtual env?",
  "profile": "chunks-300"
}

# Results are deterministic
# Same query + same profile = same results
```

---

## Configuration Management

### Decision: Named Profiles with Versioning

**Chosen**: Configuration profiles with semantic versioning
**Rejected**: Inline configuration for each request

### Rationale

**Advantages**:
1. **Reusability**: Define once, use many times
2. **Versioning**: Track changes over time
3. **Comparison**: Easy to compare named profiles
4. **Reproducibility**: Reference by name/version
5. **Auditability**: Full change history

### Example

```python
# Create profile
POST /config/profiles
{
  "name": "production-v1",
  "version": "1.0.0",
  "provider": {...},
  "chunking": {"chunk_size": 300},
  "retrieval": {...}
}

# Use profile (simple)
POST /query
{
  "query": "...",
  "profile": "production-v1"
}

# vs Inline config (complex, not tracked)
POST /query
{
  "query": "...",
  "provider": {...},
  "chunking": {...},
  "retrieval": {...}
}
```

---

## Provider Abstraction

### Decision: Abstract Base Classes

**Chosen**: ABC (Abstract Base Class) pattern for all providers
**Rejected**: Duck typing, no abstraction

### Rationale

**Advantages**:
1. **Type Safety**: Ensures all providers implement required methods
2. **Consistency**: Uniform interface across providers
3. **Testability**: Easy to mock for testing
4. **Extensibility**: New providers follow same pattern
5. **Documentation**: Interface is self-documenting

### Example

```python
class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        pass

    @abstractmethod
    def get_cost(self, num_tokens: int) -> float:
        pass

# All implementations must provide these methods
class LocalEmbeddings(EmbeddingProvider):
    def embed(self, text: str) -> List[float]:
        return self.model.encode(text)

    def get_dimension(self) -> int:
        return 768

    def get_cost(self, num_tokens: int) -> float:
        return 0.0  # Local = free
```

---

## Future Decisions

### To Be Determined

1. **Reranking**: Cross-encoder vs LLM-based reranking?
2. **Query Expansion**: Synonym-based vs embedding-based?
3. **Caching Strategy**: Redis vs in-memory vs none?
4. **Multi-modal**: How to handle images, PDFs, code?

---

## Decision Making Process

When adding new features or making architectural decisions:

1. **Document the decision** in this file
2. **List alternatives** considered
3. **Explain rationale** with pros/cons
4. **Show examples** of implementation
5. **Note trade-offs** clearly

---

**Last Updated**: 2025-11-23
