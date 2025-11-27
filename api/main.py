"""FastAPI application main entry point."""

import asyncpg
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import ConfigLoader, Settings, get_settings, set_config_loader
from config.models import ConfigurationProfile
from core.metrics import MetricsTracker
from core.pipeline import IngestionPipeline, IngestionRequest, QueryPipeline, QueryRequest
from core.providers import ProviderFactory


# ============================================
# Global State
# ============================================


class AppState:
    """Application state container."""

    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.settings: Optional[Settings] = None
        self.config_loader: Optional[ConfigLoader] = None
        self.provider_factory: Optional[ProviderFactory] = None
        self.metrics_tracker: Optional[MetricsTracker] = None


app_state = AppState()


# ============================================
# Lifecycle Management
# ============================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting RAG Testing Pipeline API...")

    # Load settings
    app_state.settings = get_settings()
    print(f"Environment: {app_state.settings.environment}")

    # Create database pool
    print("Connecting to database...")
    app_state.db_pool = await asyncpg.create_pool(
        host=app_state.settings.postgres_host,
        port=app_state.settings.postgres_port,
        database=app_state.settings.postgres_db,
        user=app_state.settings.postgres_user,
        password=app_state.settings.postgres_password,
        min_size=5,
        max_size=app_state.settings.db_pool_size,
    )
    print("Database connected!")

    # Initialize config loader
    app_state.config_loader = ConfigLoader(app_state.settings, app_state.db_pool)
    set_config_loader(app_state.config_loader)

    # Initialize provider factory
    app_state.provider_factory = ProviderFactory(app_state.db_pool)

    # Initialize metrics tracker
    app_state.metrics_tracker = MetricsTracker(app_state.db_pool)

    print("API ready! 🚀")

    yield

    # Shutdown
    print("Shutting down...")
    if app_state.db_pool:
        await app_state.db_pool.close()
    print("Shutdown complete.")


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="RAG Testing Pipeline API",
    description="Testing framework for RAG system with multiple providers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Request/Response Models
# ============================================


class IngestRequest(BaseModel):
    """Ingest endpoint request."""

    url: Optional[str] = Field(None, description="URL to scrape")
    content: Optional[str] = Field(None, description="Direct content")
    title: Optional[str] = Field(None, description="Document title")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    profile: str = Field("default", description="Configuration profile name")


class QueryRequestAPI(BaseModel):
    """Query endpoint request."""

    query: str = Field(..., description="Question to answer")
    top_k: Optional[int] = Field(None, description="Number of results to retrieve")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")
    profile: str = Field("default", description="Configuration profile name")


class FeedbackRequest(BaseModel):
    """Feedback endpoint request."""

    query_id: UUID = Field(..., description="Query UUID")
    score: int = Field(..., ge=0, le=10, description="Feedback score (0-10)")
    comment: Optional[str] = Field(None, description="Optional comment")


# ============================================
# Helper Functions
# ============================================


def get_profile(profile_name: str) -> ConfigurationProfile:
    """Get configuration profile.

    Args:
        profile_name: Profile name

    Returns:
        ConfigurationProfile

    Raises:
        HTTPException: If profile not found
    """
    if profile_name == "default":
        # Create default profile from environment
        return app_state.config_loader.create_default_profile()

    try:
        # Load from database (async call needs to be wrapped)
        import asyncio

        return asyncio.run(app_state.config_loader.get_profile_by_name(profile_name))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================
# Endpoints
# ============================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "RAG Testing Pipeline API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}


@app.post("/ingest")
async def ingest(request: IngestRequest):
    """Ingest document (URL or direct content).

    This endpoint:
    1. Scrapes content from URL (if provided) or uses direct content
    2. Chunks the document
    3. Generates embeddings
    4. Stores in vector database

    Returns job statistics.
    """
    if not request.url and not request.content:
        raise HTTPException(
            status_code=400, detail="Must provide either url or content"
        )

    # Get configuration profile
    profile = get_profile(request.profile)

    # Create providers
    vector_store = app_state.provider_factory.create_vector_store(
        profile.provider_config.vector_store
    )
    embedding_provider = app_state.provider_factory.create_embedding_provider(
        profile.provider_config.embedding
    )

    # Create ingestion pipeline
    pipeline = IngestionPipeline(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        profile=profile,
    )

    # Process ingestion
    try:
        ingestion_request = IngestionRequest(
            url=request.url,
            content=request.content,
            title=request.title,
            metadata=request.metadata,
        )

        result = await pipeline.ingest(ingestion_request)

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message)

        return {
            "job_id": str(result.job_id),
            "success": result.success,
            "chunks_created": result.chunks_created,
            "embeddings_generated": result.embeddings_generated,
            "processing_time_ms": result.processing_time_ms,
            "profile": request.profile,
        }

    finally:
        await pipeline.close()


@app.post("/query")
async def query(request: QueryRequestAPI):
    """Query the knowledge base.

    This endpoint:
    1. Generates embedding for the query
    2. Performs hybrid search (vector + keyword)
    3. Applies metadata boosting (recency, quality, popularity)
    4. Generates answer using LLM
    5. Returns answer with sources and citations

    Tracks all metrics to database.
    """
    # Get configuration profile
    profile = get_profile(request.profile)

    # Create providers
    vector_store = app_state.provider_factory.create_vector_store(
        profile.provider_config.vector_store
    )
    embedding_provider = app_state.provider_factory.create_embedding_provider(
        profile.provider_config.embedding
    )
    llm_provider = app_state.provider_factory.create_llm_provider(
        profile.provider_config.llm
    )

    # Create query pipeline
    pipeline = QueryPipeline(
        vector_store=vector_store,
        embedding_provider=embedding_provider,
        llm_provider=llm_provider,
        profile=profile,
    )

    # Process query
    query_request = QueryRequest(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters,
    )

    response = await pipeline.process_query(query_request)

    # Save metrics to database
    retrieved_chunk_ids = [source.citation.strip("[]") for source in response.sources]
    await app_state.metrics_tracker.save_query(
        query_response=response,
        query_text=request.query,
        profile_id=profile.profile_id,
        config_snapshot=profile.to_dict(),
        retrieved_chunk_ids=[s.url for s in response.sources],  # Using URL as temp ID
    )

    # Format response
    return {
        "query_id": str(response.query_id),
        "answer": response.answer,
        "sources": [
            {
                "citation": s.citation,
                "title": s.title,
                "url": s.url,
                "score": s.score,
                "section": s.section,
                "last_modified": s.last_modified,
            }
            for s in response.sources
        ],
        "metrics": {
            "latency_ms": response.metrics.latency_total_ms,
            "latency_retrieval_ms": response.metrics.latency_retrieval_ms,
            "latency_llm_ms": response.metrics.latency_llm_ms,
            "cost_usd": response.metrics.cost_total_usd,
            "chunks_retrieved": response.metrics.num_chunks_retrieved,
            "tokens_used": response.metrics.total_tokens,
        },
        "profile": {
            "name": response.profile_name,
            "version": response.profile_version,
        },
    }


@app.post("/feedback")
async def feedback(request: FeedbackRequest):
    """Submit user feedback for a query.

    Feedback score: 0-10
    - 0-2: Completely wrong
    - 3-4: Partially correct
    - 5-6: Acceptable
    - 7-8: Good
    - 9-10: Excellent

    Score >= 7 is considered "satisfied"
    """
    await app_state.metrics_tracker.save_feedback(
        query_id=request.query_id,
        score=request.score,
        comment=request.comment,
    )

    return {
        "success": True,
        "message": "Feedback saved",
        "query_id": str(request.query_id),
        "score": request.score,
    }


@app.get("/metrics")
async def get_metrics(profile: Optional[str] = None):
    """Get aggregated metrics.

    Returns statistics like:
    - Total queries
    - Average latency
    - Average cost
    - Satisfaction rate
    """
    profile_id = None
    if profile and profile != "default":
        prof = get_profile(profile)
        profile_id = prof.profile_id

    summary = await app_state.metrics_tracker.get_metrics_summary(profile_id)

    return {
        "profile": profile or "all",
        "metrics": summary,
    }


@app.get("/profiles")
async def list_profiles():
    """List available configuration profiles."""
    async with app_state.db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT profile_name, version, description, created_at, is_active
            FROM configuration_profiles
            ORDER BY created_at DESC
            """
        )

    profiles = [
        {
            "name": row["profile_name"],
            "version": row["version"],
            "description": row["description"],
            "created_at": row["created_at"].isoformat(),
            "is_active": row["is_active"],
        }
        for row in rows
    ]

    # Add default profile
    profiles.insert(
        0,
        {
            "name": "default",
            "version": "1.0.0",
            "description": "Default configuration from environment variables",
            "created_at": None,
            "is_active": True,
        },
    )

    return {"profiles": profiles}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    print(f"Error processing request: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
    )
