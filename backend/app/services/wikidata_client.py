"""Robust Wikidata SPARQL client with retry logic and pagination."""

import hashlib
import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import get_settings

logger = logging.getLogger(__name__)


class WikidataError(Exception):
    """Base exception for Wikidata client errors."""
    pass


class WikidataTimeoutError(WikidataError):
    """Query timeout error (60s limit on WDQS)."""
    pass


class WikidataRateLimitError(WikidataError):
    """Rate limit error (429 Too Many Requests)."""
    pass


class WikidataServiceError(WikidataError):
    """Service unavailable error (503)."""
    pass


class WikidataClient:
    """Robust SPARQL client for Wikidata Query Service.
    
    Features:
        - Automatic retry with exponential backoff for 503/429 errors
        - Pagination support with LIMIT/OFFSET
        - Query hash generation for caching
        - Proper User-Agent header per Wikidata guidelines
    
    Example:
        client = WikidataClient()
        results = await client.execute_query(
            "SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q571. } LIMIT 10"
        )
    """
    
    USER_AGENT = "RepublicOfLetters/1.0 (https://github.com/republic-of-letters; contact@example.com) httpx/0.26"
    
    def __init__(self):
        self.settings = get_settings()
        self.endpoint = self.settings.wikidata_endpoint
        
    def _get_client(self) -> httpx.AsyncClient:
        """Create a configured async HTTP client."""
        return httpx.AsyncClient(
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "application/sparql-results+json",
            },
            timeout=httpx.Timeout(self.settings.query_timeout),
        )
    
    @staticmethod
    def generate_cache_key(query: str, **params) -> str:
        """Generate a cache key from query and parameters.
        
        Args:
            query: SPARQL query string
            **params: Additional parameters (limit, offset, etc.)
            
        Returns:
            SHA256 hash suitable for cache key
        """
        key_parts = [query] + [f"{k}={v}" for k, v in sorted(params.items())]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @retry(
        retry=retry_if_exception_type((WikidataServiceError, WikidataRateLimitError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        reraise=True,
    )
    async def execute_query(
        self,
        query: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a SPARQL query against Wikidata.
        
        Args:
            query: SPARQL query (may include LIMIT/OFFSET or not)
            limit: Override LIMIT in query
            offset: Override OFFSET in query
            
        Returns:
            List of result bindings as dictionaries
            
        Raises:
            WikidataTimeoutError: Query exceeded 60s timeout
            WikidataRateLimitError: 429 response (retried)
            WikidataServiceError: 503 response (retried)
            WikidataError: Other errors
        """
        # Apply pagination if provided
        if limit is not None or offset is not None:
            query = self._apply_pagination(query, limit, offset)
        
        logger.debug(f"Executing SPARQL query (hash: {self.generate_cache_key(query)[:8]}...)")
        
        async with self._get_client() as client:
            try:
                response = await client.post(
                    self.endpoint,
                    data={"query": query},
                )
                
                # Handle specific error codes
                if response.status_code == 429:
                    logger.warning("Rate limited by Wikidata, will retry...")
                    raise WikidataRateLimitError("Rate limit exceeded (429)")
                
                if response.status_code == 502:
                    logger.warning("Wikidata bad gateway (502), will retry...")
                    raise WikidataServiceError("Bad gateway (502)")
                
                if response.status_code == 503:
                    logger.warning("Wikidata service unavailable, will retry...")
                    raise WikidataServiceError("Service unavailable (503)")
                
                if response.status_code == 500:
                    # Often indicates query timeout
                    error_text = response.text
                    if "timeout" in error_text.lower():
                        raise WikidataTimeoutError(
                            "Query timeout - consider adding LIMIT or optimizing query"
                        )
                    raise WikidataError(f"Server error: {error_text[:200]}")
                
                response.raise_for_status()
                
                data = response.json()
                return self._parse_results(data)
                
            except httpx.TimeoutException:
                raise WikidataTimeoutError(
                    f"Request timeout after {self.settings.query_timeout}s"
                )
            except httpx.HTTPStatusError as e:
                raise WikidataError(f"HTTP error: {e}")
    
    def _apply_pagination(
        self,
        query: str,
        limit: int | None,
        offset: int | None,
    ) -> str:
        """Apply or override LIMIT/OFFSET in query.
        
        Intelligently handles queries that may already have these clauses.
        """
        import re
        
        # Remove existing LIMIT/OFFSET
        query = re.sub(r'\bLIMIT\s+\d+', '', query, flags=re.IGNORECASE)
        query = re.sub(r'\bOFFSET\s+\d+', '', query, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        query = query.strip()
        
        # Add new clauses
        if limit is not None:
            query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"
            
        return query
    
    @staticmethod
    def _parse_results(data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse SPARQL JSON results into simple dictionaries.
        
        Converts the verbose SPARQL JSON format into cleaner dicts:
        {
            "head": {"vars": ["item", "itemLabel"]},
            "results": {"bindings": [{"item": {"type": "uri", "value": "..."}}]}
        }
        ->
        [{"item": "Q123", "itemLabel": "Example"}]
        """
        results = []
        bindings = data.get("results", {}).get("bindings", [])
        
        for binding in bindings:
            row = {}
            for var, val in binding.items():
                value = val.get("value", "")
                
                # Extract QID from URIs
                if val.get("type") == "uri" and "entity/" in value:
                    value = value.split("/")[-1]
                    
                row[var] = value
            results.append(row)
            
        return results
    
    async def execute_paginated(
        self,
        query: str,
        page_size: int = 100,
        max_pages: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute a query with automatic pagination.
        
        Fetches multiple pages of results up to max_pages.
        
        Args:
            query: SPARQL query (without LIMIT/OFFSET)
            page_size: Results per page
            max_pages: Maximum pages to fetch
            
        Returns:
            Combined results from all pages
        """
        all_results = []
        
        for page in range(max_pages):
            offset = page * page_size
            results = await self.execute_query(
                query,
                limit=page_size,
                offset=offset,
            )
            
            if not results:
                break  # No more results
                
            all_results.extend(results)
            
            if len(results) < page_size:
                break  # Last page
        
        return all_results
