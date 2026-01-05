"""Graph API endpoints for network visualization."""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Annotated

from app.models import GraphData
from app.services.graph_service import GraphService
from app.services.wikidata_client import WikidataClient, WikidataTimeoutError
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/graph", tags=["Graph"])


async def get_graph_service() -> GraphService:
    """Dependency to get GraphService instance."""
    client = WikidataClient()
    cache = CacheService()
    await cache.connect()
    return GraphService(client, cache)


@router.get(
    "/network",
    response_model=GraphData,
    summary="Get author relationship network",
    description="""
    Build a network graph of author relationships for D3.js visualization.
    
    **Relationship Types:**
    - `influenced_by`: P737 - Intellectual influence relationships
    - `student_of`: P1066 - Mentor/student relationships  
    - `coauthor`: Shared authorship on works
    - `same_movement`: Shared literary movement (P135)
    
    **Graph Metrics:**
    - Nodes include betweenness centrality scores
    - `central_nodes` lists the most influential authors in the subgraph
    
    **Example Use Case (Parisian Lost Generation):**
    ```
    /api/graph/network?authors=Q23434&authors=Q188385&authors=Q229466&depth=2
    ```
    (Hemingway, Gertrude Stein, F. Scott Fitzgerald)
    """,
)
async def get_author_network(
    authors: Annotated[list[str], Query(
        description="Author QIDs to build network from",
        min_length=1,
    )],
    depth: Annotated[int, Query(
        description="Relationship depth (hops)",
        ge=1,
        le=3,
    )] = 2,
    include_coauthorship: Annotated[bool, Query(
        description="Include co-authorship edges",
    )] = False,
    include_movements: Annotated[bool, Query(
        description="Include same-movement connections",
    )] = True,
    service: GraphService = Depends(get_graph_service),
) -> GraphData:
    """Build author relationship network graph."""
    # Validate QID format
    for qid in authors:
        if not qid.startswith("Q") or not qid[1:].isdigit():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid QID format: {qid}. Expected format: Q12345",
            )
    
    try:
        return await service.get_author_network(
            author_qids=authors,
            depth=depth,
            include_coauthorship=include_coauthorship,
            include_movements=include_movements,
        )
    except WikidataTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Query timeout. Try reducing depth or number of authors.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Graph query failed: {str(e)}",
        )


@router.get(
    "/author/{qid}/books",
    summary="Get books by an author",
    description="Get all books authored by a specific author for graph expansion.",
)
async def get_author_books(
    qid: str,
    service: GraphService = Depends(get_graph_service),
) -> list[dict]:
    """Get books by a specific author."""
    if not qid.startswith("Q") or not qid[1:].isdigit():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid QID format: {qid}",
        )
    
    return await service.get_author_books(qid)
