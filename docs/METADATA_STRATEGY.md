# Metadata Strategy

Comprehensive metadata tracking for embeddings and intelligent retrieval.

---

## Table of Contents

- [Overview](#overview)
- [Metadata Schema](#metadata-schema)
- [Storage Strategy](#storage-strategy)
- [Retrieval with Metadata](#retrieval-with-metadata)
- [Source Attribution](#source-attribution)
- [Recency Boosting](#recency-boosting)
- [Quality Scoring](#quality-scoring)
- [Implementation](#implementation)

---

## Overview

Every embedded chunk must carry rich metadata to enable:

1. **Source Attribution**: Show users where information came from
2. **Recency Boosting**: Prioritize newer documentation
3. **Quality Scoring**: Boost chunks from highly-rated sources
4. **Filtering**: Search within specific sources/dates
5. **Debugging**: Track which chunks caused which results
6. **Analytics**: Understand which sources are most useful

---

## Metadata Schema

### Core Metadata (Required)

```python
class ChunkMetadata(BaseModel):
    # Source Information
    source_url: str                    # Original URL
    source_title: str                  # Page/document title
    source_type: str                   # "documentation", "confluence", "github", etc.

    # Document Structure
    chunk_id: str                      # Unique chunk identifier
    chunk_index: int                   # Position in document (0, 1, 2, ...)
    total_chunks: int                  # Total chunks in document

    # Content Context
    section_title: Optional[str]       # H1/H2 section heading
    subsection_title: Optional[str]    # H3/H4 subsection heading
    parent_section: Optional[str]      # Hierarchical breadcrumb

    # Temporal Information
    crawled_at: datetime               # When we scraped it
    last_modified: Optional[datetime]  # From source (if available)
    published_at: Optional[datetime]   # Original publish date

    # Quality Signals
    avg_feedback_score: float          # Average user feedback for this chunk
    num_feedback: int                  # Number of feedback items
    retrieval_count: int               # How often retrieved
    click_count: int                   # How often users clicked source link

    # Configuration
    ingestion_config: dict             # Chunking config used
    embedding_model: str               # Model used for embedding
    embedding_dimension: int           # Embedding dimension
```

### Example Metadata

```json
{
  "source_url": "https://docs.python.org/3/tutorial/interpreter.html#interactive-mode",
  "source_title": "The Python Tutorial - The Python Interpreter",
  "source_type": "documentation",

  "chunk_id": "python-docs-550e8400-chunk-12",
  "chunk_index": 12,
  "total_chunks": 45,

  "section_title": "The Python Interpreter",
  "subsection_title": "Interactive Mode",
  "parent_section": "Tutorial > Interpreter > Interactive Mode",

  "crawled_at": "2025-11-23T10:00:00Z",
  "last_modified": "2025-10-15T08:30:00Z",
  "published_at": "2024-01-01T00:00:00Z",

  "avg_feedback_score": 8.2,
  "num_feedback": 15,
  "retrieval_count": 234,
  "click_count": 89,

  "ingestion_config": {
    "chunk_size": 300,
    "chunk_overlap": 30,
    "profile": "baseline-v1"
  },
  "embedding_model": "all-mpnet-base-v2",
  "embedding_dimension": 768
}
```

### Extended Metadata (Source-Specific)

```python
# Confluence Pages
class ConfluenceMetadata(ChunkMetadata):
    space_key: str                     # Confluence space
    page_id: str                       # Confluence page ID
    author: str                        # Page author
    last_editor: str                   # Who last updated
    version: int                       # Page version number
    labels: List[str]                  # Confluence labels/tags

# GitHub Documentation
class GitHubMetadata(ChunkMetadata):
    repository: str                    # owner/repo
    branch: str                        # main, develop, etc.
    file_path: str                     # path/to/file.md
    commit_sha: str                    # Latest commit
    contributors: List[str]            # File contributors

# Internal Wiki
class WikiMetadata(ChunkMetadata):
    department: str                    # Engineering, Product, etc.
    team: str                          # Team name
    owner: str                         # Page owner
    review_date: Optional[datetime]    # Last review date
    status: str                        # draft, published, archived
```

---

## Storage Strategy

### Elasticsearch Document Structure

```json
{
  "_id": "python-docs-550e8400-chunk-12",
  "_index": "knowledge_base",
  "_source": {
    // Core content
    "content": "The Python REPL (Read-Eval-Print Loop) is an interactive...",
    "content_hash": "a3f8d9c1b2e4f5a6",

    // Vector embedding
    "embedding": [0.123, -0.456, 0.789, ...],  // 768-dim vector

    // All metadata (flattened for easy filtering)
    "metadata": {
      "source_url": "https://docs.python.org/3/tutorial/interpreter.html",
      "source_title": "The Python Tutorial - The Python Interpreter",
      "source_type": "documentation",

      "chunk_id": "python-docs-550e8400-chunk-12",
      "chunk_index": 12,
      "total_chunks": 45,

      "section_title": "The Python Interpreter",
      "subsection_title": "Interactive Mode",
      "parent_section": "Tutorial > Interpreter > Interactive Mode",

      // Dates as timestamps for easy filtering
      "crawled_at": 1700740800000,
      "last_modified": 1697356200000,

      // Quality signals
      "avg_feedback_score": 8.2,
      "num_feedback": 15,
      "retrieval_count": 234,
      "click_count": 89,

      // Configuration
      "ingestion_profile": "baseline-v1",
      "embedding_model": "all-mpnet-base-v2"
    }
  }
}
```

### Index Mapping

```json
PUT /knowledge_base
{
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
      "content_hash": {
        "type": "keyword"
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 768,
        "index": true,
        "similarity": "cosine"
      },
      "metadata": {
        "properties": {
          "source_url": {"type": "keyword"},
          "source_title": {"type": "text"},
          "source_type": {"type": "keyword"},
          "section_title": {"type": "text"},
          "crawled_at": {"type": "date"},
          "last_modified": {"type": "date"},
          "avg_feedback_score": {"type": "float"},
          "num_feedback": {"type": "integer"},
          "retrieval_count": {"type": "integer"},
          "click_count": {"type": "integer"}
        }
      }
    }
  }
}
```

---

## Retrieval with Metadata

### Basic Query with Metadata

```python
POST /query
{
  "query": "describe Python's REPL",
  "top_k": 5,
  "filters": {
    "source_type": ["documentation"],
    "last_modified_after": "2025-01-01"
  }
}

# Response includes full metadata
{
  "query_id": "uuid",
  "answer": "The Python REPL (Read-Eval-Print Loop) is an interactive...",
  "sources": [
    {
      "content": "The Python REPL is...",
      "score": 0.92,
      "url": "https://docs.python.org/3/tutorial/interpreter.html#interactive-mode",
      "title": "The Python Tutorial - The Python Interpreter",
      "section": "Tutorial > Interpreter > Interactive Mode",
      "last_modified": "2025-10-15T08:30:00Z",
      "feedback_score": 8.2
    }
  ]
}
```

### Hybrid Search with Metadata Boosting

```python
# Elasticsearch query with boosting
{
  "query": {
    "script_score": {
      "query": {
        "bool": {
          "should": [
            // Vector similarity
            {
              "knn": {
                "field": "embedding",
                "query_vector": [...],
                "k": 50,
                "num_candidates": 100
              }
            },
            // Keyword matching
            {
              "multi_match": {
                "query": "Python REPL",
                "fields": ["content", "metadata.section_title^2"]
              }
            }
          ]
        }
      },
      // Boost based on metadata
      "script": {
        "source": """
          double base_score = _score;

          // Recency boost (newer = better)
          long now = System.currentTimeMillis();
          long modified = doc['metadata.last_modified'].value.millis;
          long age_days = (now - modified) / (1000 * 60 * 60 * 24);
          double recency_boost = 1.0 + Math.exp(-age_days / 180.0);  // Decay over 6 months

          // Quality boost (higher feedback = better)
          double quality_boost = 1.0 + (doc['metadata.avg_feedback_score'].value / 10.0);

          // Popularity boost (frequently retrieved = useful)
          double popularity_boost = 1.0 + Math.log1p(doc['metadata.retrieval_count'].value) / 10.0;

          return base_score * recency_boost * quality_boost * popularity_boost;
        """
      }
    }
  }
}
```

---

## Source Attribution

### Response Format with Sources

```python
class QueryResponse(BaseModel):
    query_id: str
    query: str
    answer: str
    sources: List[Source]
    metadata: ResponseMetadata

class Source(BaseModel):
    # Core
    url: str
    title: str
    section: Optional[str]

    # Relevance
    score: float
    rank: int

    # Content
    snippet: str  # Relevant excerpt

    # Context
    last_modified: Optional[datetime]
    feedback_score: Optional[float]

    # Attribution
    citation: str  # Formatted citation
```

### Citation Formats

```python
# Inline citations
answer = """
The Python REPL allows interactive code execution[1]. You can start it
by typing `python` in the terminal[2]. It's particularly useful for
testing small code snippets[1].

Sources:
[1] The Python Tutorial - Interactive Mode (https://docs.python.org/3/tutorial/interpreter.html)
[2] Getting Started with Python (https://docs.python.org/3/getting-started.html)
"""

# Footnote citations
answer = """
The Python REPL allows interactive code execution¹. You can start it
by typing `python` in the terminal². It's particularly useful for
testing small code snippets¹.

¹ The Python Tutorial - Interactive Mode
  https://docs.python.org/3/tutorial/interpreter.html
  Last updated: 2025-10-15

² Getting Started with Python
  https://docs.python.org/3/getting-started.html
  Last updated: 2025-09-20
"""

# Structured citations
{
  "answer": "...",
  "citations": [
    {
      "id": 1,
      "title": "The Python Tutorial - Interactive Mode",
      "url": "https://docs.python.org/3/tutorial/interpreter.html",
      "section": "Tutorial > Interpreter > Interactive Mode",
      "last_modified": "2025-10-15T08:30:00Z",
      "relevance_score": 0.92,
      "feedback_score": 8.2
    }
  ]
}
```

---

## Recency Boosting

### Time-Based Scoring

```python
def calculate_recency_boost(last_modified: datetime, now: datetime) -> float:
    """
    Calculate recency boost for a document.

    Recent docs get higher boost, decays over time.
    """
    age_days = (now - last_modified).days

    if age_days < 30:
        return 1.5  # Very recent (< 1 month)
    elif age_days < 90:
        return 1.3  # Recent (< 3 months)
    elif age_days < 180:
        return 1.1  # Somewhat recent (< 6 months)
    elif age_days < 365:
        return 1.0  # Within a year
    else:
        # Exponential decay after 1 year
        return 1.0 * math.exp(-age_days / 730.0)  # Decay over 2 years
```

### Configuration

```python
retrieval_config = {
    "recency_boost": {
        "enabled": true,
        "weight": 0.3,  // 30% weight for recency
        "decay_halflife_days": 180,  // Half boost after 6 months
        "min_boost": 0.5,  // Never go below 50%
        "max_boost": 2.0   // Never exceed 2x
    }
}
```

### Query Example

```python
POST /query
{
  "query": "Python async features",
  "recency_preference": "recent",  // "any", "recent", "latest"
  "date_range": {
    "after": "2024-01-01"  // Optional hard filter
  }
}
```

---

## Quality Scoring

### Feedback-Based Boosting

```python
def calculate_quality_boost(avg_score: float, num_feedback: int) -> float:
    """
    Calculate quality boost based on user feedback.

    Higher scores get higher boost, but require sufficient feedback.
    """
    if num_feedback < 5:
        # Not enough feedback, no boost/penalty
        return 1.0

    # Confidence increases with more feedback
    confidence = min(1.0, num_feedback / 20.0)

    # Normalize score to 0-1 scale (from 0-10)
    normalized_score = avg_score / 10.0

    # Boost ranges from 0.5x (score=0) to 1.5x (score=10)
    boost = 0.5 + normalized_score

    # Apply confidence weighting
    return 1.0 + (boost - 1.0) * confidence
```

### Popularity Boosting

```python
def calculate_popularity_boost(retrieval_count: int, click_count: int) -> float:
    """
    Boost frequently retrieved and clicked chunks.
    """
    # Click-through rate
    ctr = click_count / max(retrieval_count, 1)

    # Logarithmic boost for retrieval count (prevents runaway popularity)
    retrieval_boost = 1.0 + math.log1p(retrieval_count) / 20.0

    # Linear boost for high CTR
    ctr_boost = 1.0 + (ctr * 0.5)

    return retrieval_boost * ctr_boost
```

### Combined Scoring

```python
final_score = (
    base_similarity_score *
    recency_boost(last_modified) *
    quality_boost(avg_feedback_score, num_feedback) *
    popularity_boost(retrieval_count, click_count)
)
```

---

## Implementation

### Ingestion Pipeline with Metadata

```python
# core/ingestion/pipeline.py

class IngestionPipeline:
    async def ingest_url(
        self,
        url: str,
        config: IngestionConfig
    ) -> IngestionResult:
        """Ingest URL with full metadata extraction."""

        # 1. Scrape page
        html = await self.scraper.fetch(url)

        # 2. Extract metadata from HTML
        metadata = self.extract_metadata(html, url)

        # 3. Parse content and structure
        document = self.parser.parse(html)

        # 4. Chunk with context preservation
        chunks = self.chunker.chunk_with_context(
            document,
            preserve_sections=True
        )

        # 5. Enrich each chunk with metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata = ChunkMetadata(
                source_url=url,
                source_title=metadata.title,
                source_type=self.detect_source_type(url),

                chunk_id=f"{metadata.source_id}-chunk-{i}",
                chunk_index=i,
                total_chunks=len(chunks),

                section_title=chunk.section,
                subsection_title=chunk.subsection,
                parent_section=chunk.breadcrumb,

                crawled_at=datetime.now(),
                last_modified=metadata.last_modified,
                published_at=metadata.published_at,

                # Initial quality signals (will update over time)
                avg_feedback_score=5.0,
                num_feedback=0,
                retrieval_count=0,
                click_count=0,

                ingestion_config=config.dict(),
                embedding_model=config.embedding_model,
                embedding_dimension=config.embedding_dimension
            )

        # 6. Generate embeddings
        embeddings = await self.embedder.embed_batch([c.content for c in chunks])

        # 7. Store in vector store with metadata
        await self.vector_store.insert_many([
            {
                "id": chunk.metadata.chunk_id,
                "content": chunk.content,
                "embedding": embedding,
                "metadata": chunk.metadata.dict()
            }
            for chunk, embedding in zip(chunks, embeddings)
        ])

        return IngestionResult(
            url=url,
            chunks_created=len(chunks),
            metadata=metadata
        )

    def extract_metadata(self, html: str, url: str) -> DocumentMetadata:
        """Extract rich metadata from HTML."""
        soup = BeautifulSoup(html, 'html.parser')

        # Title
        title = soup.find('title').text if soup.find('title') else url

        # Last modified from meta tags
        last_modified = None
        meta_modified = soup.find('meta', {'name': 'last-modified'})
        if meta_modified:
            last_modified = parse_datetime(meta_modified['content'])

        # Confluence-specific metadata
        if 'confluence' in url:
            return self.extract_confluence_metadata(soup, url)

        # GitHub-specific metadata
        if 'github.com' in url:
            return self.extract_github_metadata(soup, url)

        return DocumentMetadata(
            title=title,
            last_modified=last_modified,
            source_id=hashlib.md5(url.encode()).hexdigest()[:16]
        )
```

### Query with Metadata Filtering and Boosting

```python
# core/retrieval/rag_service.py

class RAGService:
    async def query(
        self,
        query: str,
        config: QueryConfig
    ) -> QueryResponse:
        """Query with metadata-aware retrieval and attribution."""

        # 1. Embed query
        query_embedding = await self.embedder.embed(query)

        # 2. Hybrid search with metadata boosting
        results = await self.vector_store.hybrid_search(
            query_vector=query_embedding,
            query_text=query,
            top_k=config.top_k,
            filters=config.filters,  # Filter by date, source type, etc.
            boost_config={
                "recency_weight": 0.3,
                "quality_weight": 0.2,
                "popularity_weight": 0.1
            }
        )

        # 3. Build context with source attribution
        sources = []
        context_parts = []

        for i, result in enumerate(results):
            sources.append(Source(
                url=result.metadata.source_url,
                title=result.metadata.source_title,
                section=result.metadata.parent_section,
                score=result.score,
                rank=i + 1,
                snippet=result.content[:200],
                last_modified=result.metadata.last_modified,
                feedback_score=result.metadata.avg_feedback_score,
                citation=f"[{i+1}]"
            ))

            context_parts.append(
                f"[Source {i+1}]: {result.content}\n"
                f"(from: {result.metadata.source_title}, "
                f"section: {result.metadata.parent_section})"
            )

        context = "\n\n".join(context_parts)

        # 4. Generate answer with citations
        prompt = self.build_prompt_with_citations(query, context, sources)
        answer = await self.llm.generate(prompt)

        # 5. Update metadata (retrieval counts)
        await self.update_retrieval_metrics([r.metadata.chunk_id for r in results])

        return QueryResponse(
            query_id=str(uuid.uuid4()),
            query=query,
            answer=answer,
            sources=sources,
            metadata=ResponseMetadata(...)
        )
```

### Metadata Update Service

```python
# metrics/metadata_updater.py

class MetadataUpdater:
    async def update_chunk_quality(
        self,
        chunk_id: str,
        feedback_score: int
    ):
        """Update chunk metadata when feedback is received."""

        # Get current metadata
        chunk = await self.vector_store.get(chunk_id)

        # Update running average
        old_avg = chunk.metadata.avg_feedback_score
        old_count = chunk.metadata.num_feedback

        new_count = old_count + 1
        new_avg = ((old_avg * old_count) + feedback_score) / new_count

        # Update in vector store
        await self.vector_store.update_metadata(
            chunk_id,
            {
                "avg_feedback_score": new_avg,
                "num_feedback": new_count
            }
        )

    async def update_click_metrics(
        self,
        source_url: str
    ):
        """Update click count when user clicks source link."""

        # Update all chunks from this source
        await self.vector_store.update_where(
            filter={"metadata.source_url": source_url},
            update={"$inc": {"metadata.click_count": 1}}
        )
```

---

## Configuration

```python
# config/metadata_config.py

METADATA_CONFIG = {
    "boosting": {
        "recency": {
            "enabled": True,
            "weight": 0.3,
            "decay_halflife_days": 180
        },
        "quality": {
            "enabled": True,
            "weight": 0.2,
            "min_feedback_threshold": 5
        },
        "popularity": {
            "enabled": True,
            "weight": 0.1,
            "log_scale": True
        }
    },

    "attribution": {
        "citation_format": "inline",  # inline, footnote, structured
        "include_last_modified": True,
        "include_feedback_score": False,  # Don't show to end user
        "max_sources": 5
    },

    "filtering": {
        "default_date_range_days": None,  # No default filter
        "allow_source_type_filter": True,
        "allow_url_pattern_filter": True
    }
}
```

---

**Last Updated**: 2025-11-23
