"""Query processing pipeline orchestration."""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from config.models import ConfigurationProfile, GenerationConfig
from core.providers.base import EmbeddingProvider, LLMProvider, VectorStore
from core.retrieval import Retriever


@dataclass
class SourceInfo:
    """Source information for citations."""

    citation: str
    title: str
    url: str
    score: float
    section: Optional[str] = None
    last_modified: Optional[str] = None


@dataclass
class QueryMetrics:
    """Query execution metrics."""

    latency_embedding_ms: float
    latency_retrieval_ms: float
    latency_llm_ms: float
    latency_total_ms: float
    cost_embedding_usd: float
    cost_llm_usd: float
    cost_total_usd: float
    num_chunks_retrieved: int
    num_chunks_used: int
    avg_chunk_score: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class QueryRequest:
    """Query request."""

    query: str
    top_k: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None


@dataclass
class QueryResponse:
    """Query response with answer, sources, and metrics."""

    query_id: UUID
    answer: str
    sources: List[SourceInfo]
    metrics: QueryMetrics
    profile_name: str
    profile_version: str


class QueryPipeline:
    """End-to-end query processing pipeline.

    Orchestrates: Query → Embedding → Retrieval → LLM Generation → Response
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
        profile: ConfigurationProfile,
    ):
        """Initialize query pipeline.

        Args:
            vector_store: Vector store instance
            embedding_provider: Embedding provider instance
            llm_provider: LLM provider instance
            profile: Configuration profile
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider
        self.profile = profile

        # Create retriever
        self.retriever = Retriever(
            vector_store=vector_store,
            embedding_provider=embedding_provider,
            config=profile.retrieval_config,
        )

    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Process query end-to-end.

        Args:
            request: Query request

        Returns:
            Query response with answer, sources, and metrics
        """
        query_id = uuid4()
        start_time = time.time()

        # Step 1: Retrieve relevant chunks
        retrieval_start = time.time()
        retrieval_results = await self.retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
        )
        retrieval_time = (time.time() - retrieval_start) * 1000

        if not retrieval_results:
            # No results found
            return QueryResponse(
                query_id=query_id,
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                metrics=QueryMetrics(
                    latency_embedding_ms=0,
                    latency_retrieval_ms=retrieval_time,
                    latency_llm_ms=0,
                    latency_total_ms=(time.time() - start_time) * 1000,
                    cost_embedding_usd=0,
                    cost_llm_usd=0,
                    cost_total_usd=0,
                    num_chunks_retrieved=0,
                    num_chunks_used=0,
                    avg_chunk_score=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                ),
                profile_name=self.profile.profile_name,
                profile_version=self.profile.version,
            )

        # Step 2: Build context from retrieved chunks
        context = self._build_context(retrieval_results)

        # Step 3: Generate answer using LLM
        llm_start = time.time()
        prompt = self._build_prompt(request.query, context, retrieval_results)
        system_prompt = self._build_system_prompt()

        llm_response = await self.llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=self.profile.provider_config.llm.temperature,
            max_tokens=self.profile.provider_config.llm.max_tokens,
        )
        llm_time = (time.time() - llm_start) * 1000

        # Step 4: Format response with citations
        answer, sources = self._format_response_with_citations(
            llm_response.content, retrieval_results
        )

        # Step 5: Calculate metrics
        total_time = (time.time() - start_time) * 1000

        # Calculate costs
        embedding_tokens = self.llm_provider.count_tokens(request.query)
        embedding_cost = self.embedding_provider.get_cost(embedding_tokens)
        llm_cost = llm_response.cost_usd

        avg_score = (
            sum(r.boosted_score for r in retrieval_results) / len(retrieval_results)
            if retrieval_results
            else 0
        )

        metrics = QueryMetrics(
            latency_embedding_ms=0,  # Embedded in retrieval time
            latency_retrieval_ms=retrieval_time,
            latency_llm_ms=llm_time,
            latency_total_ms=total_time,
            cost_embedding_usd=embedding_cost,
            cost_llm_usd=llm_cost,
            cost_total_usd=embedding_cost + llm_cost,
            num_chunks_retrieved=len(retrieval_results),
            num_chunks_used=len(retrieval_results),
            avg_chunk_score=avg_score,
            prompt_tokens=llm_response.prompt_tokens,
            completion_tokens=llm_response.completion_tokens,
            total_tokens=llm_response.total_tokens,
        )

        return QueryResponse(
            query_id=query_id,
            answer=answer,
            sources=sources,
            metrics=metrics,
            profile_name=self.profile.profile_name,
            profile_version=self.profile.version,
        )

    def _build_context(self, retrieval_results: List) -> str:
        """Build context string from retrieval results.

        Args:
            retrieval_results: List of RetrievalResult

        Returns:
            Context string
        """
        context_parts = []
        for i, result in enumerate(retrieval_results, start=1):
            context_parts.append(f"[{i}] {result.content}")

        return "\n\n".join(context_parts)

    def _build_prompt(
        self, query: str, context: str, retrieval_results: List
    ) -> str:
        """Build prompt for LLM.

        Args:
            query: User query
            context: Context from retrieval
            retrieval_results: Retrieval results for source info

        Returns:
            Formatted prompt
        """
        gen_config = self.profile.generation_config

        if gen_config.include_citations:
            citation_instruction = (
                "When referencing information from the context, "
                "include inline citations using the format [N] where N is the source number. "
                "For example: 'According to the documentation[1], Python uses...'"
            )
        else:
            citation_instruction = ""

        prompt = f"""Answer the following question based on the provided context.

Question: {query}

Context:
{context}

Instructions:
- Provide a clear, accurate answer based on the context
- If the context doesn't contain enough information, say so
{citation_instruction}
- Be concise but thorough
- Use markdown formatting for readability

Answer:"""

        return prompt

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM.

        Returns:
            System prompt
        """
        return (
            "You are a helpful assistant that answers questions based on provided context. "
            "Always ground your answers in the given context and cite your sources."
        )

    def _format_response_with_citations(
        self, answer: str, retrieval_results: List
    ) -> tuple[str, List[SourceInfo]]:
        """Format response with citation sources.

        Args:
            answer: LLM generated answer
            retrieval_results: Retrieval results

        Returns:
            Tuple of (formatted answer, list of SourceInfo)
        """
        sources = []

        for i, result in enumerate(retrieval_results, start=1):
            metadata = result.metadata
            source = SourceInfo(
                citation=f"[{i}]",
                title=metadata.get("title", "Unknown"),
                url=metadata.get("source_url", ""),
                score=result.boosted_score,
                section=metadata.get("section_title"),
                last_modified=metadata.get("last_modified"),
            )
            sources.append(source)

        return answer, sources
