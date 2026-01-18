"""Metrics tracking and database persistence."""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from asyncpg import Pool

from core.pipeline.query_pipeline import QueryMetrics, QueryResponse


class MetricsTracker:
    """Track and persist metrics to database."""

    def __init__(self, db_pool: Pool):
        """Initialize metrics tracker.

        Args:
            db_pool: Database connection pool
        """
        self.db_pool = db_pool

    async def save_query(
        self,
        query_response: QueryResponse,
        query_text: str,
        profile_id: UUID,
        config_snapshot: Dict[str, Any],
        retrieved_chunk_ids: List[str],
    ) -> None:
        """Save query and metrics to database.

        Args:
            query_response: Query response with metrics
            query_text: Original query text
            profile_id: Configuration profile ID
            config_snapshot: Full configuration snapshot
            retrieved_chunk_ids: List of chunk IDs used
        """
        async with self.db_pool.acquire() as conn:
            # Insert query
            query_insert = """
                INSERT INTO queries (
                    query_id, query_text, profile_id, config_snapshot,
                    response, retrieved_chunks, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
            """

            # Build response JSON
            response_json = {
                "answer": query_response.answer,
                "sources": [
                    {
                        "citation": s.citation,
                        "title": s.title,
                        "url": s.url,
                        "score": s.score,
                        "section": s.section,
                        "last_modified": s.last_modified,
                    }
                    for s in query_response.sources
                ],
            }

            await conn.execute(
                query_insert,
                query_response.query_id,
                query_text,
                profile_id,
                json.dumps(config_snapshot),
                json.dumps(response_json),
                [UUID(chunk_id) for chunk_id in retrieved_chunk_ids],
            )

            # Insert metrics
            metrics = query_response.metrics
            metrics_insert = """
                INSERT INTO metrics (
                    metric_id, query_id,
                    latency_embedding_ms, latency_retrieval_ms,
                    latency_llm_ms, latency_total_ms,
                    cost_embedding_usd, cost_llm_usd, cost_total_usd,
                    num_chunks_retrieved, num_chunks_used, avg_chunk_score,
                    prompt_tokens, completion_tokens, total_tokens,
                    created_at
                ) VALUES (
                    gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8,
                    $9, $10, $11, $12, $13, $14, CURRENT_TIMESTAMP
                )
            """

            await conn.execute(
                metrics_insert,
                query_response.query_id,
                metrics.latency_embedding_ms,
                metrics.latency_retrieval_ms,
                metrics.latency_llm_ms,
                metrics.latency_total_ms,
                metrics.cost_embedding_usd,
                metrics.cost_llm_usd,
                metrics.cost_total_usd,
                metrics.num_chunks_retrieved,
                metrics.num_chunks_used,
                metrics.avg_chunk_score,
                metrics.prompt_tokens,
                metrics.completion_tokens,
                metrics.total_tokens,
            )

            # Update retrieval counts for chunks
            if retrieved_chunk_ids:
                update_retrieval_count = """
                    UPDATE embeddings
                    SET retrieval_count = retrieval_count + 1
                    WHERE id = ANY($1::uuid[])
                """
                await conn.execute(
                    update_retrieval_count, [UUID(cid) for cid in retrieved_chunk_ids]
                )

    async def save_feedback(
        self, query_id: UUID, score: int, comment: Optional[str] = None
    ) -> None:
        """Save user feedback.

        Args:
            query_id: Query UUID
            score: Feedback score (0-10)
            comment: Optional comment
        """
        if not (0 <= score <= 10):
            raise ValueError("Score must be between 0 and 10")

        async with self.db_pool.acquire() as conn:
            query = """
                INSERT INTO feedback (
                    feedback_id, query_id, score, comment, created_at
                ) VALUES (
                    gen_random_uuid(), $1, $2, $3, CURRENT_TIMESTAMP
                )
            """
            await conn.execute(query, query_id, score, comment)

    async def get_metrics_summary(
        self, profile_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get metrics summary.

        Args:
            profile_id: Optional profile filter

        Returns:
            Dictionary with aggregated metrics
        """
        async with self.db_pool.acquire() as conn:
            if profile_id:
                query = """
                    SELECT
                        COUNT(DISTINCT q.query_id) as total_queries,
                        AVG(m.latency_total_ms) as avg_latency_ms,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.latency_total_ms) as median_latency_ms,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.latency_total_ms) as p95_latency_ms,
                        AVG(m.cost_total_usd) as avg_cost_usd,
                        SUM(m.cost_total_usd) as total_cost_usd,
                        AVG(f.score) as avg_feedback_score,
                        COUNT(f.feedback_id) FILTER (WHERE f.score >= 7) as satisfied_count,
                        COUNT(f.feedback_id) as total_feedback
                    FROM queries q
                    JOIN metrics m ON q.query_id = m.query_id
                    LEFT JOIN feedback f ON q.query_id = f.query_id
                    WHERE q.profile_id = $1
                """
                row = await conn.fetchrow(query, profile_id)
            else:
                query = """
                    SELECT
                        COUNT(DISTINCT q.query_id) as total_queries,
                        AVG(m.latency_total_ms) as avg_latency_ms,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.latency_total_ms) as median_latency_ms,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY m.latency_total_ms) as p95_latency_ms,
                        AVG(m.cost_total_usd) as avg_cost_usd,
                        SUM(m.cost_total_usd) as total_cost_usd,
                        AVG(f.score) as avg_feedback_score,
                        COUNT(f.feedback_id) FILTER (WHERE f.score >= 7) as satisfied_count,
                        COUNT(f.feedback_id) as total_feedback
                    FROM queries q
                    JOIN metrics m ON q.query_id = m.query_id
                    LEFT JOIN feedback f ON q.query_id = f.query_id
                """
                row = await conn.fetchrow(query)

            if not row or row["total_queries"] == 0:
                return {
                    "total_queries": 0,
                    "avg_latency_ms": 0,
                    "median_latency_ms": 0,
                    "p95_latency_ms": 0,
                    "avg_cost_usd": 0,
                    "total_cost_usd": 0,
                    "avg_feedback_score": None,
                    "satisfaction_rate": None,
                }

            satisfaction_rate = None
            if row["total_feedback"] and row["total_feedback"] > 0:
                satisfaction_rate = row["satisfied_count"] / row["total_feedback"]

            return {
                "total_queries": int(row["total_queries"]),
                "avg_latency_ms": float(row["avg_latency_ms"] or 0),
                "median_latency_ms": float(row["median_latency_ms"] or 0),
                "p95_latency_ms": float(row["p95_latency_ms"] or 0),
                "avg_cost_usd": float(row["avg_cost_usd"] or 0),
                "total_cost_usd": float(row["total_cost_usd"] or 0),
                "avg_feedback_score": float(row["avg_feedback_score"])
                if row["avg_feedback_score"]
                else None,
                "satisfaction_rate": satisfaction_rate,
                "total_feedback": int(row["total_feedback"] or 0),
            }
