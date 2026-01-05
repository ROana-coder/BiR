"""Geo API endpoints for map visualization."""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Annotated, Literal

from app.models.geo import GeoResponse, GeoLayerType
from app.services.geo_service import GeoService
from app.services.wikidata_client import WikidataClient, WikidataTimeoutError
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/geo", tags=["Geography"])


async def get_geo_service() -> GeoService:
    """Dependency to get GeoService instance."""
    client = WikidataClient()
    cache = CacheService()
    await cache.connect()
    return GeoService(client, cache)


@router.get(
    "/locations",
    response_model=GeoResponse,
    summary="Get geographic locations for map",
    description="""
    Get geographic coordinates for map visualization.
    
    **Layer Types:**
    - `birthplaces`: Author birth locations (P19 + P625)
    - `deathplaces`: Author death locations (P20 + P625)
    - `publications`: Book publication places (P291 + P625)
    - `settings`: Narrative/story locations (P840 + P625)
    
    **Clustering:**
    When point count exceeds 1000, server-side clustering is applied
    to prevent frontend DOM performance issues.
    
    **Example:**
    ```
    /api/geo/locations?layer=birthplaces&authors=Q23434&authors=Q188385
    ```
    """,
)
async def get_locations(
    layer: Annotated[GeoLayerType, Query(
        description="Type of geographic layer",
    )],
    authors: Annotated[list[str] | None, Query(
        description="Filter by author QIDs",
    )] = None,
    books: Annotated[list[str] | None, Query(
        description="Filter by book QIDs",
    )] = None,
    cluster: Annotated[bool, Query(
        description="Enable server-side clustering",
    )] = True,
    service: GeoService = Depends(get_geo_service),
) -> GeoResponse:
    """Get geographic locations for a map layer."""
    # Validate QIDs
    for qid_list in [authors, books]:
        if qid_list:
            for qid in qid_list:
                if not qid.startswith("Q") or not qid[1:].isdigit():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid QID format: {qid}",
                    )
    
    # Validate layer + entity combination
    if layer in [GeoLayerType.BIRTHPLACES, GeoLayerType.DEATHPLACES]:
        if not authors and books:
            raise HTTPException(
                status_code=400,
                detail=f"Layer '{layer.value}' requires author QIDs, not book QIDs",
            )
    elif layer in [GeoLayerType.PUBLICATIONS, GeoLayerType.STORY_SETTINGS]:
        if not books and not authors:
            raise HTTPException(
                status_code=400,
                detail=f"Layer '{layer.value}' requires book or author QIDs",
            )
    
    try:
        return await service.get_locations(
            layer=layer,
            author_qids=authors,
            book_qids=books,
            cluster=cluster,
        )
    except WikidataTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query timeout. Try with fewer entities.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Geo query failed: {str(e)}",
        )


@router.get(
    "/author/{qid}/locations",
    summary="Get all locations for an author",
    description="Get birthplace, death place, and residence locations for an author.",
)
async def get_author_all_locations(
    qid: str,
    service: GeoService = Depends(get_geo_service),
) -> dict[str, GeoResponse]:
    """Get all location types for a specific author."""
    if not qid.startswith("Q") or not qid[1:].isdigit():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid QID format: {qid}",
        )
    
    return await service.get_all_author_locations([qid])
