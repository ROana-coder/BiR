"""Router for local ontology queries using RDFLib."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.services.ontology_service import get_ontology_service

router = APIRouter(prefix="/ontology", tags=["Ontology"])


# ----- Request/Response Models -----

class SPARQLQueryRequest(BaseModel):
    """Request model for SPARQL queries."""
    query: str = Field(
        ...,
        description="SPARQL SELECT query to execute against the ontology",
        examples=[
            "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
            "SELECT ?author ?name WHERE { ?author a lit:Author . ?author lit:name ?name . }"
        ]
    )


class SPARQLQueryResponse(BaseModel):
    """Response model for SPARQL queries."""
    results: list[dict[str, Any]] = Field(..., description="Query results")
    count: int = Field(..., description="Number of results")


class OntologyClassResponse(BaseModel):
    """Response model for ontology classes."""
    uri: str
    label: str
    comment: str
    equivalent_class: str


class OntologyPropertyResponse(BaseModel):
    """Response model for ontology properties."""
    uri: str
    label: str
    domain: str
    range: str
    type: str
    equivalent_property: str


class AuthorResponse(BaseModel):
    """Response model for authors."""
    uri: str
    name: str
    birth_date: str | None
    death_date: str | None
    wikidata_id: str
    movements: str


class LiteraryWorkResponse(BaseModel):
    """Response model for literary works."""
    uri: str
    title: str
    author: str
    publication_year: str | None
    genre: str
    wikidata_id: str


class GraphNodeResponse(BaseModel):
    """Response model for graph nodes."""
    id: str
    label: str
    wikidata_id: str


class GraphEdgeResponse(BaseModel):
    """Response model for graph edges."""
    source: str
    target: str
    source_label: str
    target_label: str
    relationship: str


class InfluenceGraphResponse(BaseModel):
    """Response model for influence graph."""
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class OntologyStatsResponse(BaseModel):
    """Response model for ontology statistics."""
    triple_count: int
    class_count: int
    property_count: int
    author_count: int
    work_count: int


# ----- Endpoints -----

@router.post("/query", response_model=SPARQLQueryResponse)
async def execute_sparql_query(request: SPARQLQueryRequest):
    """Execute a SPARQL query against the local ontology.
    
    The ontology uses the following namespace prefixes:
    - `lit:` - http://literature-explorer.org/ontology#
    - `owl:` - http://www.w3.org/2002/07/owl#
    - `rdfs:` - http://www.w3.org/2000/01/rdf-schema#
    - `rdf:` - http://www.w3.org/1999/02/22-rdf-syntax-ns#
    - `wd:` - http://www.wikidata.org/entity/
    - `wdt:` - http://www.wikidata.org/prop/direct/
    - `schema:` - http://schema.org/
    - `foaf:` - http://xmlns.com/foaf/0.1/
    - `dc:` - http://purl.org/dc/elements/1.1/
    
    Example queries:
    ```sparql
    # Get all authors
    SELECT ?author ?name WHERE { 
        ?author a lit:Author . 
        ?author lit:name ?name . 
    }
    
    # Get works by genre
    SELECT ?work ?title ?genre WHERE {
        ?work lit:hasGenre ?g .
        ?g rdfs:label ?genre .
        ?work lit:title ?title .
    }
    ```
    """
    try:
        service = get_ontology_service()
        results = service.query(request.query)
        return SPARQLQueryResponse(results=results, count=len(results))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")


@router.get("/classes", response_model=list[OntologyClassResponse])
async def get_ontology_classes():
    """Get all classes defined in the Literature ontology.
    
    Returns OWL classes with their labels, comments, and Wikidata equivalents.
    """
    try:
        service = get_ontology_service()
        classes = service.get_classes()
        return [OntologyClassResponse(**c) for c in classes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve classes: {e}")


@router.get("/properties", response_model=list[OntologyPropertyResponse])
async def get_ontology_properties():
    """Get all properties defined in the Literature ontology.
    
    Returns both ObjectProperties and DatatypeProperties with their
    domains, ranges, and Wikidata equivalents.
    """
    try:
        service = get_ontology_service()
        properties = service.get_properties()
        return [OntologyPropertyResponse(**p) for p in properties]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve properties: {e}")


@router.get("/authors", response_model=list[AuthorResponse])
async def get_authors():
    """Get all authors defined in the ontology.
    
    Returns authors with their names, dates, Wikidata IDs, and literary movements.
    """
    try:
        service = get_ontology_service()
        authors = service.get_authors()
        return [AuthorResponse(**a) for a in authors]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve authors: {e}")


@router.get("/works", response_model=list[LiteraryWorkResponse])
async def get_literary_works():
    """Get all literary works defined in the ontology.
    
    Returns works with their titles, authors, publication years, and genres.
    """
    try:
        service = get_ontology_service()
        works = service.get_literary_works()
        return [LiteraryWorkResponse(**w) for w in works]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve works: {e}")


@router.get("/influence-graph", response_model=InfluenceGraphResponse)
async def get_influence_graph():
    """Get author influence relationships for graph visualization.
    
    Returns nodes (authors) and edges (influence relationships) suitable
    for rendering with D3.js or similar visualization libraries.
    """
    try:
        service = get_ontology_service()
        graph = service.get_influence_graph()
        return InfluenceGraphResponse(
            nodes=[GraphNodeResponse(**n) for n in graph["nodes"]],
            edges=[GraphEdgeResponse(**e) for e in graph["edges"]]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve influence graph: {e}")


@router.get("/stats", response_model=OntologyStatsResponse)
async def get_ontology_stats():
    """Get statistics about the ontology.
    
    Returns counts of triples, classes, properties, authors, and works.
    """
    try:
        service = get_ontology_service()
        classes = service.get_classes()
        properties = service.get_properties()
        authors = service.get_authors()
        works = service.get_literary_works()
        
        return OntologyStatsResponse(
            triple_count=service.triple_count,
            class_count=len(classes),
            property_count=len(properties),
            author_count=len(authors),
            work_count=len(works)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {e}")


@router.get("/ttl", response_class=PlainTextResponse)
async def get_ontology_ttl():
    """Download the raw ontology as a Turtle (TTL) file.
    
    Returns the complete ontology in Turtle format for inspection or reuse.
    """
    try:
        service = get_ontology_service()
        ttl_content = service.get_raw_ttl()
        return PlainTextResponse(
            content=ttl_content,
            media_type="text/turtle",
            headers={"Content-Disposition": "attachment; filename=literature-ontology.ttl"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve TTL: {e}")


@router.get("/namespaces")
async def get_namespaces():
    """Get the namespace prefixes used in the ontology.
    
    Useful for constructing SPARQL queries.
    """
    return {
        "prefixes": {
            "lit": "http://literature-explorer.org/ontology#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "schema": "http://schema.org/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "wd": "http://www.wikidata.org/entity/",
            "wdt": "http://www.wikidata.org/prop/direct/"
        },
        "base_uri": "http://literature-explorer.org/ontology#"
    }
