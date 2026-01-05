"""Recommendations API endpoints."""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Annotated
from pydantic import BaseModel

from app.services.recommendation_service import RecommendationService
from app.services.wikidata_client import WikidataClient, WikidataTimeoutError
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


class SimilarAuthor(BaseModel):
    """Similar author recommendation."""
    qid: str
    name: str
    similarity: float
    shared_movements: list[str]
    shared_genres: list[str]


async def get_recommendation_service() -> RecommendationService:
    """Dependency to get RecommendationService instance."""
    client = WikidataClient()
    cache = CacheService()
    await cache.connect()
    return RecommendationService(client, cache)


@router.get(
    "/similar-authors/{qid}",
    response_model=list[SimilarAuthor],
    summary="Find similar authors",
    description="""
    Find authors similar to the given author using Jaccard similarity.
    
    **Similarity Factors:**
    - Literary movements (P135)
    - Genres of works (P136)
    - Awards received (P166)
    - Birth decade (era proximity)
    
    **Example (Magic Realism spread):**
    ```
    /api/recommendations/similar-authors/Q5765
    ```
    (Gabriel García Márquez → similar Magic Realism authors)
    
    **Use Case:**
    Discover overlooked authors in other languages who share
    similar literary properties with well-known authors.
    """,
)
async def find_similar_authors(
    qid: str,
    limit: Annotated[int, Query(
        description="Maximum recommendations to return",
        ge=1,
        le=50,
    )] = 10,
    service: RecommendationService = Depends(get_recommendation_service),
) -> list[SimilarAuthor]:
    """Find authors similar to the given author."""
    if not qid.startswith("Q") or not qid[1:].isdigit():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid QID format: {qid}. Expected format: Q12345",
        )
    
    try:
        results = await service.find_similar_authors(qid, limit=limit)
        return [SimilarAuthor(**r) for r in results]
    except WikidataTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query timeout.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {str(e)}",
        )
