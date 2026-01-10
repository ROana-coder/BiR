"""Search service for querying books and literary works."""

import logging
from datetime import date

from app.config import get_settings
from app.models import Book, Location, Author
from app.services.wikidata_client import WikidataClient
from app.services.cache_service import CacheService
from app.sparql.template_loader import render_sparql

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching books and literary works in Wikidata.
    
    Features:
        - Dynamic SPARQL query building via Jinja2 templates
        - Caching with configurable TTL
        - Pagination support
    """
    
    def __init__(
        self,
        wikidata_client: WikidataClient,
        cache_service: CacheService,
    ):
        self.client = wikidata_client
        self.cache = cache_service
        self.settings = get_settings()
    
    async def search_books(
        self,
        country_qid: str | None = None,
        genre_qid: str | None = None,
        location_qid: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Book]:
        """Search for books with optional filters.
        
        Args:
            country_qid: Filter by author's nationality (e.g., Q30 for USA)
            genre_qid: Filter by genre (e.g., Q1422746 for Magic Realism)
            location_qid: Filter by author's location (birthplace/residence)
            year_start: Start of publication year range
            year_end: End of publication year range
            limit: Maximum results (default 50, max 200)
            offset: Pagination offset
            
        Returns:
            List of Book models
        """
        # Clamp limit
        limit = min(limit, self.settings.max_query_limit)
        
        # Generate cache key
        cache_key = WikidataClient.generate_cache_key(
            "search_books",
            country=country_qid or "",
            genre=genre_qid or "",
            location=location_qid or "",
            year_start=year_start or "",
            year_end=year_end or "",
            limit=limit,
            offset=offset,
        )
        cache_key += "_v2" # Force cache invalidation
        
        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            return [Book(**b) for b in cached]
        
        # Render SPARQL query
        query = render_sparql(
            "search_books.sparql",
            country_qid=country_qid,
            genre_qid=genre_qid,
            location_qid=location_qid,
            year_start=year_start,
            year_end=year_end,
            limit=limit,
            offset=offset,
        )
        
        logger.debug(f"Executing search query with filters: country={country_qid}, genre={genre_qid}")
        
        # Execute query
        results = await self.client.execute_query(query)
        
        # Transform to Book models
        books = self._parse_book_results(results)
        
        # Cache results
        await self.cache.set(
            cache_key,
            [b.model_dump() for b in books],
            ttl_seconds=self.settings.cache_ttl_search,
        )
        
        return books
    
    def _parse_book_results(self, results: list[dict]) -> list[Book]:
        """Parse SPARQL results into Book models."""
        books_map: dict[str, Book] = {}
        
        for row in results:
            qid = row.get("book", "")
            if not qid:
                continue
            
            if qid not in books_map:
                # Parse publication date
                pub_date = None
                pub_year = None
                if "pubDate" in row:
                    try:
                        pub_date = date.fromisoformat(row["pubDate"][:10])
                        pub_year = pub_date.year
                    except (ValueError, TypeError):
                        pass
                
                book = Book(
                    qid=qid,
                    title=row.get("bookLabel", "Unknown"),
                    publication_date=pub_date,
                    publication_year=pub_year,
                    authors=[],
                    author_qids=[],
                    genres=[],
                    genre_qids=[],
                    awards=[],
                    award_qids=[],
                )
                
                # Parse comma-separated genres and awards
                genre_str = row.get("genres", "")
                if genre_str:
                    book.genres = [g.strip() for g in genre_str.split(", ") if g.strip()]
                    if book.genres:
                        book.genre = book.genres[0] # Default to first genre
                
                award_str = row.get("awards", "")
                if award_str:
                    book.awards = [a.strip() for a in award_str.split(", ") if a.strip()]
                
                books_map[qid] = book
            
            book = books_map[qid]
            
            # Add author if present (still need to handle potential duplicate rows if author join caused them, but new query should GROUP BY book/author pair if 1 author)
            # Actually new query groups by ?author too. If book has multiple authors, we get multiple rows.
            # So duplicate check is still valid.
            author_qid = row.get("author")
            author_label = row.get("authorLabel")
            if author_qid and author_qid not in book.author_qids:
                # Check if we have a real label (not just the QID as fallback)
                # Wikidata returns QID as label when no label exists
                if author_label and not author_label.startswith("Q"):
                    book.author_qids.append(author_qid)
                    book.authors.append(author_label)
                elif author_label:
                    # We have a QID as label - still add but mark as unknown
                    # This ensures arrays stay aligned
                    book.author_qids.append(author_qid)
                    book.authors.append(f"Unknown Author ({author_qid})")
        
        return list(books_map.values())
    
    async def get_book_by_qid(self, qid: str) -> Book | None:
        """Get a specific book by its Wikidata QID."""
        query = f"""
        SELECT ?book ?bookLabel ?author ?authorLabel ?pubDate ?genre ?genreLabel ?award ?awardLabel
        WHERE {{
            BIND(wd:{qid} AS ?book)
            ?book wdt:P31/wdt:P279* wd:Q7725634.
            OPTIONAL {{ ?book wdt:P50 ?author. }}
            OPTIONAL {{ ?book wdt:P577 ?pubDate. }}
            OPTIONAL {{ ?book wdt:P136 ?genre. }}
            OPTIONAL {{ ?book wdt:P166 ?award. }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,auto,it,fr,de,es". }}
        }}
        LIMIT 50
        """
        
        results = await self.client.execute_query(query)
        books = self._parse_book_results(results)
        return books[0] if books else None

    async def get_author(self, qid: str) -> Author | None:
        """Get author details by QID."""
        # Try cache
        cache_key = f"author:{qid}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Author(**cached)

        try:
            # Query
            query = render_sparql("get_author.sparql", qid=qid)
            results = await self.client.execute_query(query)
            
            if not results:
                return None
                
            row = results[0]
            
            # Parse dates
            birth_date = None
            if "birthDate" in row:
                try:
                    date_str = row["birthDate"].replace("+", "").split("T")[0]
                    birth_date = date.fromisoformat(date_str)
                except Exception:
                    pass
                    
            death_date = None
            if "deathDate" in row:
                try:
                    date_str = row["deathDate"].replace("+", "").split("T")[0]
                    death_date = date.fromisoformat(date_str)
                except Exception:
                    pass

            author = Author(
                qid=qid,
                name=row.get("name", "Unknown"),
                description=row.get("description"),
                image_url=row.get("image"),
                nationality=row.get("nationalityLabel"),
                nationality_qid=row.get("nationality"),
                birth_date=birth_date,
                death_date=death_date,
            )
            
            await self.cache.set(cache_key, author.model_dump(), ttl_seconds=86400)
            return author
            
        except Exception as e:
            # Fallback for ANY error to prevent 500
            return Author(
                qid=qid,
                name=f"Author {qid}",
                description=f"Could not load details: {str(e)}",
            )
