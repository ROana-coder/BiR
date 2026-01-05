"""Search API endpoints for books and literary works."""

from fastapi import APIRouter, Query, Path, HTTPException, Depends
from typing import Annotated

from app.models import Book
from app.services.search_service import SearchService
from app.services.wikidata_client import WikidataClient, WikidataTimeoutError
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/search", tags=["Search"])


# Dependency injection
async def get_search_service() -> SearchService:
    """Dependency to get SearchService instance."""
    client = WikidataClient()
    cache = CacheService()
    await cache.connect()
    return SearchService(client, cache)


@router.get(
    "/books",
    response_model=list[Book],
    summary="Search for books",
    description="""
    Search for books/literary works with optional filters.
    
    **Filters:**
    - `country`: Author's nationality (Wikidata QID, e.g., Q30 for USA)
    - `genre`: Book genre (Wikidata QID, e.g., Q1422746 for Magic Realism)
    - `location`: Author's location (birthplace/residence QID)
    - `year_start` / `year_end`: Publication year range
    
    **Common Country QIDs:**
    - Q30 = United States
    - Q142 = France
    - Q183 = Germany
    - Q145 = United Kingdom
    - Q96 = Mexico
    - Q414 = Argentina
    
    **Common Genre QIDs:**
    - Q1422746 = Magic Realism
    - Q8261 = Novel
    - Q49084 = Short Story
    - Q482 = Poetry
    """,
)
async def search_books(
    country: Annotated[str | None, Query(
        description="Author nationality QID (e.g., Q30 for USA)",
        pattern=r"^Q\d+$",
    )] = None,
    genre: Annotated[str | None, Query(
        description="Genre QID (e.g., Q8261 for novel)",
        pattern=r"^Q\d+$",
    )] = None,
    location: Annotated[str | None, Query(
        description="Location QID for author birthplace/residence",
        pattern=r"^Q\d+$",
    )] = None,
    year_start: Annotated[int | None, Query(
        description="Start of publication year range",
        ge=1,
        le=2030,
    )] = None,
    year_end: Annotated[int | None, Query(
        description="End of publication year range",
        ge=1,
        le=2030,
    )] = None,
    limit: Annotated[int, Query(
        description="Maximum results to return",
        ge=1,
        le=200,
    )] = 50,
    offset: Annotated[int, Query(
        description="Pagination offset",
        ge=0,
    )] = 0,
    service: SearchService = Depends(get_search_service),
) -> list[Book]:
    """Search for books with filters."""
    try:
        return await service.search_books(
            country_qid=country,
            genre_qid=genre,
            location_qid=location,
            year_start=year_start,
            year_end=year_end,
            limit=limit,
            offset=offset,
        )
    except WikidataTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query timeout. Try narrowing your search with more filters or smaller year range.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@router.get(
    "/books/{qid}",
    response_model=Book,
    summary="Get a specific book by QID",
)
async def get_book(
    qid: Annotated[str, Path(pattern=r"^Q\d+$", description="Wikidata QID")],
    service: SearchService = Depends(get_search_service),
) -> Book:
    """Get a specific book by its Wikidata QID."""
    book = await service.get_book_by_qid(qid)
    if not book:
        raise HTTPException(
            status_code=404,
            detail=f"Book {qid} not found",
        )
    return book
