"""Redis caching service implementing Cache-Aside pattern."""

import json
import logging
from typing import Any, Callable, TypeVar

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheService:
    """Redis-based caching service with Cache-Aside pattern.
    
    Features:
        - Cache-Aside: Check cache first, fetch on miss, update cache
        - Configurable TTLs for different data types
        - Graceful degradation if Redis unavailable
        - JSON serialization for complex objects
    
    TTL Strategy:
        - Static data (historical authors): 7 days (604800s)
        - Search results: 24 hours (86400s)
        - Warm cache (popular queries): 30 days (2592000s)
    """
    
    def __init__(self, redis_url: str | None = None):
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self._pool: redis.ConnectionPool | None = None
        self._client: redis.Redis | None = None
        
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        if self._pool is None:
            try:
                self._pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    decode_responses=True,
                )
                self._client = redis.Redis(connection_pool=self._pool)
                await self._client.ping()
                logger.info("Connected to Redis cache")
            except RedisError as e:
                logger.warning(f"Redis unavailable, caching disabled: {e}")
                self._client = None
    
    async def disconnect(self) -> None:
        """Close Redis connection pool."""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.disconnect()
    
    async def get(self, key: str) -> Any | None:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/unavailable
        """
        if not self._client:
            return None
            
        try:
            value = await self._client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key[:16]}...")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key[:16]}...")
            return None
        except RedisError as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            return False
            
        try:
            serialized = json.dumps(value, default=str)
            if ttl_seconds:
                await self._client.setex(key, ttl_seconds, serialized)
            else:
                await self._client.set(key, serialized)
            logger.debug(f"Cache SET: {key[:16]}... (TTL: {ttl_seconds}s)")
            return True
        except RedisError as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._client:
            return False
            
        try:
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def get_or_fetch(
        self,
        cache_key: str,
        fetch_fn: Callable[[], Any],
        ttl_seconds: int = 86400,
    ) -> Any:
        """Cache-Aside pattern: get from cache or fetch and cache.
        
        Args:
            cache_key: Cache key (use WikidataClient.generate_cache_key)
            fetch_fn: Async function to fetch data on cache miss
            ttl_seconds: TTL for cached data
            
        Returns:
            Cached or freshly fetched data
        """
        # Try cache first
        cached = await self.get(cache_key)
        if cached is not None:
            return cached
        
        # Fetch on miss
        data = await fetch_fn()
        
        # Cache the result
        await self.set(cache_key, data, ttl_seconds)
        
        return data
    
    async def warm_cache(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Pre-populate cache with data (warm cache).
        
        Used for popular queries like "French Novels 19th Century".
        
        Args:
            key: Cache key
            value: Data to cache
            ttl_seconds: TTL (defaults to warm cache TTL: 30 days)
        """
        settings = get_settings()
        ttl = ttl_seconds or settings.cache_ttl_warm
        return await self.set(key, value, ttl)
    
    async def health_check(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except RedisError:
            return False
