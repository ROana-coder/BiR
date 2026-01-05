"""FastAPI main application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.cache_service import CacheService
from app.routers import (
    search_router,
    graph_router,
    geo_router,
    recommendations_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global cache service for lifespan management
_cache_service: CacheService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _cache_service
    
    # Startup
    logger.info("Starting Republic of Letters API...")
    settings = get_settings()
    
    # Initialize cache
    _cache_service = CacheService()
    await _cache_service.connect()
    
    if await _cache_service.health_check():
        logger.info("Redis cache connected")
    else:
        logger.warning("Redis unavailable - running without cache")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if _cache_service:
        await _cache_service.disconnect()


# Create FastAPI app
app = FastAPI(
    title="Republic of Letters API",
    description="""
    A high-performance API for exploring the Republic of Letters using Wikidata.
    
    ## Features
    
    - **Search**: Query books by country, genre, time period
    - **Graph**: Visualize author relationships and influence networks
    - **Geography**: Map birthplaces, publications, and story settings
    - **Recommendations**: Discover similar authors using Jaccard similarity
    
    ## Wikidata Integration
    
    All data is sourced from Wikidata in real-time with aggressive caching.
    Use Wikidata QIDs (e.g., Q30 for USA, Q23434 for Hemingway) for queries.
    
    ## Use Cases
    
    1. **Parisian Lost Generation**: Explore American writers in Paris 1920s
    2. **Magic Realism Spread**: Trace influence from Latin America globally
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router)
app.include_router(graph_router)
app.include_router(geo_router)
app.include_router(recommendations_router)


@app.get("/", tags=["Health"])
async def root():
    """API root - health check."""
    return {
        "name": "Republic of Letters API",
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    cache_healthy = False
    if _cache_service:
        cache_healthy = await _cache_service.health_check()
    
    return {
        "status": "healthy",
        "cache": "connected" if cache_healthy else "disconnected",
        "wikidata_endpoint": get_settings().wikidata_endpoint,
    }
