"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Wikidata SPARQL endpoint
    wikidata_endpoint: str = "https://query.wikidata.org/sparql"
    
    # Redis configuration
    redis_url: str = "redis://localhost:6379"
    
    # Cache TTL settings (in seconds)
    cache_ttl_static: int = 604800  # 7 days for historical data
    cache_ttl_search: int = 86400   # 24 hours for search results
    cache_ttl_warm: int = 2592000   # 30 days for warm cache
    
    # Query settings
    default_query_limit: int = 100
    max_query_limit: int = 500
    query_timeout: int = 120  # Increased: Wikidata is slow today
    
    # Retry settings
    max_retries: int = 5
    base_retry_delay: float = 2.0
    
    # Clustering threshold
    geo_cluster_threshold: int = 1000


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
