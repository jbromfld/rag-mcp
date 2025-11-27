"""Document ingestion pipeline orchestration."""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from config.models import ConfigurationProfile
from core.ingestion.chunker import DocumentChunker
from core.ingestion.scraper import DocumentScraper
from core.providers.base import Chunk, EmbeddingProvider, VectorStore


@dataclass
class IngestionRequest:
    """Ingestion request."""

    url: Optional[str] = None  # URL to scrape
    content: Optional[str] = None  # Or direct content
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class IngestionResult:
    """Ingestion result with statistics."""

    job_id: UUID
    success: bool
    chunks_created: int
    embeddings_generated: int
    processing_time_ms: float
    error_message: Optional[str] = None


class IngestionPipeline:
    """End-to-end ingestion pipeline.

    Orchestrates: Scrape → Chunk → Embed → Store
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        profile: ConfigurationProfile,
    ):
        """Initialize ingestion pipeline.

        Args:
            vector_store: Vector store instance
            embedding_provider: Embedding provider instance
            profile: Configuration profile
        """
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.profile = profile

        # Create chunker
        self.chunker = DocumentChunker(profile.chunking_config)

        # Create scraper
        self.scraper = DocumentScraper()

    async def ingest(self, request: IngestionRequest) -> IngestionResult:
        """Ingest document end-to-end.

        Args:
            request: Ingestion request

        Returns:
            Ingestion result with statistics
        """
        job_id = uuid4()
        start_time = time.time()

        try:
            # Step 1: Get content (scrape or use provided)
            if request.url:
                scraped_doc = await self.scraper.scrape_url(request.url)
                content = scraped_doc.content
                metadata = scraped_doc.metadata
            elif request.content:
                content = request.content
                metadata = request.metadata or {}
                if request.title:
                    metadata["title"] = request.title
            else:
                raise ValueError("Must provide either url or content")

            # Add profile to metadata
            metadata["profile_id"] = str(self.profile.profile_id)

            # Step 2: Chunk document
            chunk_results = self.chunker.chunk_document(content, metadata)

            if not chunk_results:
                return IngestionResult(
                    job_id=job_id,
                    success=False,
                    chunks_created=0,
                    embeddings_generated=0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    error_message="No chunks created (content may be too short)",
                )

            # Step 3: Generate embeddings
            texts = [chunk.content for chunk in chunk_results]
            embeddings = await self.embedding_provider.embed_batch(texts)

            # Step 4: Create Chunk objects for vector store
            chunks = []
            for chunk_result, embedding in zip(chunk_results, embeddings):
                chunk = Chunk(
                    id=chunk_result.id,
                    content=chunk_result.content,
                    content_hash=chunk_result.content_hash,
                    vector=embedding,
                    metadata=chunk_result.metadata,
                )
                chunks.append(chunk)

            # Step 5: Insert into vector store
            inserted_count = await self.vector_store.insert_chunks(chunks)

            processing_time = (time.time() - start_time) * 1000

            return IngestionResult(
                job_id=job_id,
                success=True,
                chunks_created=len(chunk_results),
                embeddings_generated=len(embeddings),
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return IngestionResult(
                job_id=job_id,
                success=False,
                chunks_created=0,
                embeddings_generated=0,
                processing_time_ms=processing_time,
                error_message=str(e),
            )

    async def close(self):
        """Close resources."""
        await self.scraper.close()
