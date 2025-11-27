"""Retrieval system with metadata boosting."""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.models import RetrievalConfig
from core.providers.base import EmbeddingProvider, SearchResult, VectorStore


@dataclass
class RetrievalResult:
    """Enhanced retrieval result with boosted score."""

    chunk_id: str
    content: str
    score: float  # Base score
    boosted_score: float  # Score after metadata boosting
    rank: int
    metadata: Dict[str, Any]

    # Boost breakdown for debugging
    recency_boost: float = 1.0
    quality_boost: float = 1.0
    popularity_boost: float = 1.0


class Retriever:
    """Retrieval system with metadata boosting.

    Implements recency, quality, and popularity boosting as defined
    in METADATA_STRATEGY.md.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        config: RetrievalConfig,
    ):
        """Initialize retriever.

        Args:
            vector_store: Vector store instance
            embedding_provider: Embedding provider instance
            config: Retrieval configuration
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.config = config

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks for query with metadata boosting.

        Args:
            query: Query text
            top_k: Number of results (defaults to config.top_k)
            filters: Optional metadata filters

        Returns:
            List of RetrievalResult objects, sorted by boosted score
        """
        top_k = top_k or self.config.top_k

        # Generate query embedding
        query_vector = await self.embedding_provider.embed_text(query)

        # Perform search
        if self.config.hybrid_search:
            # Hybrid search (vector + keyword)
            search_results = await self.vector_store.hybrid_search(
                query_text=query,
                query_vector=query_vector,
                top_k=top_k * 2,  # Get more results for boosting
                vector_weight=self.config.vector_weight,
                keyword_weight=self.config.bm25_weight,
                filter_dict=filters,
            )
        else:
            # Pure vector search
            search_results = await self.vector_store.vector_search(
                query_vector=query_vector,
                top_k=top_k * 2,
                filter_dict=filters,
            )

        # Apply metadata boosting
        boosted_results = self._apply_metadata_boosting(search_results)

        # Filter by relevance threshold
        if self.config.relevance_threshold:
            boosted_results = [
                r for r in boosted_results
                if r.boosted_score >= self.config.relevance_threshold
            ]

        # Re-rank by boosted score
        boosted_results.sort(key=lambda x: x.boosted_score, reverse=True)

        # Take top K
        boosted_results = boosted_results[:top_k]

        # Update ranks
        for rank, result in enumerate(boosted_results, start=1):
            result.rank = rank

        return boosted_results

    def _apply_metadata_boosting(
        self, search_results: List[SearchResult]
    ) -> List[RetrievalResult]:
        """Apply metadata boosting to search results.

        Implements boosting based on:
        - Recency (last_modified date)
        - Quality (avg_feedback_score)
        - Popularity (retrieval_count)

        Args:
            search_results: Raw search results

        Returns:
            List of RetrievalResult with boosted scores
        """
        now = datetime.utcnow()
        results = []

        for search_result in search_results:
            chunk = search_result.chunk
            base_score = search_result.score
            metadata = chunk.metadata or {}

            # Calculate individual boosts
            recency_boost = self._calculate_recency_boost(metadata, now)
            quality_boost = self._calculate_quality_boost(metadata)
            popularity_boost = self._calculate_popularity_boost(metadata)

            # Calculate final boosted score
            boosted_score = base_score * recency_boost * quality_boost * popularity_boost

            result = RetrievalResult(
                chunk_id=str(chunk.id),
                content=chunk.content,
                score=base_score,
                boosted_score=boosted_score,
                rank=search_result.rank,
                metadata=metadata,
                recency_boost=recency_boost,
                quality_boost=quality_boost,
                popularity_boost=popularity_boost,
            )
            results.append(result)

        return results

    def _calculate_recency_boost(
        self, metadata: Dict[str, Any], now: datetime
    ) -> float:
        """Calculate recency boost based on last_modified date.

        Boost formula (from METADATA_STRATEGY.md):
        - < 30 days: 1.5x
        - 30-90 days: 1.3x
        - 90-180 days: 1.1x
        - > 180 days: exp(-age_days / 730.0)

        Args:
            metadata: Chunk metadata
            now: Current datetime

        Returns:
            Recency boost multiplier (>= 1.0)
        """
        if not self.config.recency_boost_enabled:
            return 1.0

        last_modified_str = metadata.get("last_modified")
        if not last_modified_str:
            return 1.0  # No boost if no date

        try:
            # Parse last_modified date
            if isinstance(last_modified_str, str):
                # Try ISO format
                last_modified = datetime.fromisoformat(
                    last_modified_str.replace("Z", "+00:00")
                )
            else:
                last_modified = last_modified_str

            # Calculate age in days
            age_days = (now - last_modified).days

            # Apply boost based on age
            if age_days < 0:
                # Future date, use 1.0
                return 1.0
            elif age_days < 30:
                return 1.5
            elif age_days < 90:
                return 1.3
            elif age_days < 180:
                return 1.1
            else:
                # Exponential decay for older content
                # Half-life of 730 days (2 years)
                return max(1.0, math.exp(-age_days / 730.0) * 1.5)

        except Exception:
            # If date parsing fails, no boost
            return 1.0

    def _calculate_quality_boost(self, metadata: Dict[str, Any]) -> float:
        """Calculate quality boost based on user feedback.

        Boost formula:
        - If avg_feedback_score >= 7 and num_feedback >= min_feedback: 1.2x
        - If avg_feedback_score >= 5: 1.1x
        - If avg_feedback_score < 5: 0.9x (penalty)
        - If no feedback: 1.0x (neutral)

        Args:
            metadata: Chunk metadata

        Returns:
            Quality boost multiplier
        """
        if not self.config.quality_boost_enabled:
            return 1.0

        avg_score = metadata.get("avg_feedback_score")
        num_feedback = metadata.get("num_feedback", 0)

        if avg_score is None or num_feedback < 3:
            # No boost if insufficient feedback
            return 1.0

        # Apply boost based on score
        if avg_score >= 7:
            return 1.2
        elif avg_score >= 5:
            return 1.1
        else:
            return 0.9  # Penalty for low-rated content

    def _calculate_popularity_boost(self, metadata: Dict[str, Any]) -> float:
        """Calculate popularity boost based on retrieval count.

        Boost formula:
        - retrieval_count > 100: 1.15x
        - retrieval_count > 50: 1.1x
        - retrieval_count > 20: 1.05x
        - Otherwise: 1.0x

        Args:
            metadata: Chunk metadata

        Returns:
            Popularity boost multiplier
        """
        if not self.config.popularity_boost_enabled:
            return 1.0

        retrieval_count = metadata.get("retrieval_count", 0)

        if retrieval_count > 100:
            return 1.15
        elif retrieval_count > 50:
            return 1.1
        elif retrieval_count > 20:
            return 1.05
        else:
            return 1.0
