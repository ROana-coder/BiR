"""Validation API endpoints for ontology-based data validation."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.models.validation import (
    ValidationRequest,
    BatchValidationRequest,
    ValidationResult,
    BatchValidationResult,
    SchemaInfo,
    ClassMapping,
    PropertyMapping,
)
from app.services.schema_mapper import get_schema_mapper
from app.services.sparql_generator import get_sparql_generator
from app.services.response_validator import get_response_validator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["Validation"])


# =============================================================================
# SCHEMA MAPPING ENDPOINTS
# =============================================================================

@router.get("/schema", response_model=SchemaInfo)
async def get_schema_mappings() -> SchemaInfo:
    """
    Get complete schema mappings between ontology and Wikidata.
    
    Returns all owl:equivalentClass and owl:equivalentProperty mappings
    extracted from the local ontology. These mappings enable translation
    between local concepts and Wikidata identifiers.
    
    Example response:
    ```json
    {
        "class_mappings": [
            {
                "ontology_uri": "http://literature-explorer.org/ontology#Author",
                "ontology_local": "Author",
                "wikidata_uri": "http://www.wikidata.org/entity/Q482980",
                "wikidata_id": "Q482980"
            }
        ],
        "property_mappings": [...],
        "class_count": 10,
        "property_count": 15
    }
    ```
    """
    try:
        mapper = get_schema_mapper()
        return mapper.extract_mappings()
    except Exception as e:
        logger.error(f"Error extracting schema mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/classes", response_model=list[ClassMapping])
async def get_class_mappings() -> list[ClassMapping]:
    """
    Get all class mappings (ontology ↔ Wikidata).
    
    Returns owl:equivalentClass mappings for all classes in the ontology.
    Use these to translate between local class names (Author, LiteraryWork)
    and Wikidata QIDs (Q482980, Q7725634).
    """
    try:
        mapper = get_schema_mapper()
        schema = mapper.extract_mappings()
        return schema.class_mappings
    except Exception as e:
        logger.error(f"Error getting class mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/properties", response_model=list[PropertyMapping])
async def get_property_mappings() -> list[PropertyMapping]:
    """
    Get all property mappings (ontology ↔ Wikidata).
    
    Returns owl:equivalentProperty mappings for all properties.
    Includes domain, range, and property type (Object vs Datatype).
    
    Use these to:
    - Generate SPARQL queries with correct Wikidata properties
    - Validate that data matches expected types
    """
    try:
        mapper = get_schema_mapper()
        schema = mapper.extract_mappings()
        return schema.property_mappings
    except Exception as e:
        logger.error(f"Error getting property mappings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/class/{identifier}")
async def get_class_mapping(identifier: str) -> ClassMapping:
    """
    Get mapping for a specific class.
    
    Args:
        identifier: Class identifier - can be:
            - Local name: "Author"
            - Full URI: "http://literature-explorer.org/ontology#Author"
            - Wikidata QID: "Q482980"
    
    Returns:
        ClassMapping with ontology and Wikidata URIs
    """
    try:
        mapper = get_schema_mapper()
        mapping = mapper.get_class_mapping(identifier)
        
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"No mapping found for class: {identifier}"
            )
        
        return mapping
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting class mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/property/{identifier}")
async def get_property_mapping(identifier: str) -> PropertyMapping:
    """
    Get mapping for a specific property.
    
    Args:
        identifier: Property identifier - can be:
            - Local name: "writtenBy"
            - Full URI: "http://literature-explorer.org/ontology#writtenBy"
            - Wikidata PID: "P50"
    
    Returns:
        PropertyMapping with ontology URI, Wikidata URI, domain, range, etc.
    """
    try:
        mapper = get_schema_mapper()
        mapping = mapper.get_property_mapping(identifier)
        
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"No mapping found for property: {identifier}"
            )
        
        return mapping
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/translate")
async def translate_identifier(
    identifier: str = Query(..., description="Identifier to translate"),
    direction: str = Query("to_wikidata", description="Direction: 'to_wikidata' or 'from_wikidata'")
) -> dict[str, str | None]:
    """
    Translate between ontology and Wikidata identifiers.
    
    Args:
        identifier: The identifier to translate
        direction: "to_wikidata" (lit:Author → Q482980) or "from_wikidata" (Q482980 → Author)
    
    Returns:
        Translation result with original and translated identifiers
    """
    try:
        mapper = get_schema_mapper()
        
        if direction == "to_wikidata":
            result = mapper.translate_to_wikidata(identifier)
        elif direction == "from_wikidata":
            result = mapper.translate_from_wikidata(identifier)
        else:
            raise HTTPException(
                status_code=400,
                detail="Direction must be 'to_wikidata' or 'from_wikidata'"
            )
        
        return {
            "original": identifier,
            "direction": direction,
            "translated": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error translating identifier: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SPARQL GENERATION ENDPOINTS
# =============================================================================

@router.get("/sparql/entity/{entity_type}")
async def generate_entity_query(
    entity_type: str,
    qid: str | None = Query(None, description="Specific entity QID"),
    limit: int = Query(100, ge=1, le=1000)
) -> dict[str, str]:
    """
    Generate a Wikidata SPARQL query for an entity type.
    
    This endpoint uses the ontology schema to automatically generate
    a SPARQL query that retrieves all mapped properties for the given
    entity type.
    
    Args:
        entity_type: Ontology class name (Author, LiteraryWork, etc.)
        qid: Optional specific entity QID to fetch
        limit: Maximum results
    
    Returns:
        Generated SPARQL query ready for Wikidata
    
    Example:
        GET /validation/sparql/entity/Author?limit=50
    """
    try:
        generator = get_sparql_generator()
        query = generator.generate_entity_query(entity_type, qid, limit=limit)
        
        return {
            "entity_type": entity_type,
            "qid": qid,
            "sparql": query
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating entity query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sparql/author")
async def generate_author_query(
    author_qid: str | None = Query(None),
    country_qid: str | None = Query(None, description="Filter by country (e.g., Q30 for USA)"),
    movement_qid: str | None = Query(None, description="Filter by literary movement"),
    year_start: int | None = Query(None, description="Birth year start"),
    year_end: int | None = Query(None, description="Birth year end"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> dict[str, Any]:
    """
    Generate a Wikidata SPARQL query for authors.
    
    This specialized endpoint generates queries optimized for author
    searches with common filters like country, movement, and date range.
    
    Example:
        GET /validation/sparql/author?country_qid=Q30&year_start=1800&year_end=1900
    """
    try:
        generator = get_sparql_generator()
        query = generator.generate_author_query(
            author_qid=author_qid,
            country_qid=country_qid,
            movement_qid=movement_qid,
            year_start=year_start,
            year_end=year_end,
            limit=limit,
            offset=offset
        )
        
        return {
            "filters": {
                "author_qid": author_qid,
                "country_qid": country_qid,
                "movement_qid": movement_qid,
                "year_range": [year_start, year_end]
            },
            "sparql": query
        }
    except Exception as e:
        logger.error(f"Error generating author query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sparql/work")
async def generate_work_query(
    work_qid: str | None = Query(None),
    author_qid: str | None = Query(None, description="Filter by author QID"),
    genre_qid: str | None = Query(None, description="Filter by genre (e.g., Q8261 for novel)"),
    year_start: int | None = Query(None, description="Publication year start"),
    year_end: int | None = Query(None, description="Publication year end"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> dict[str, Any]:
    """
    Generate a Wikidata SPARQL query for literary works.
    
    Example:
        GET /validation/sparql/work?author_qid=Q23434&genre_qid=Q8261
    """
    try:
        generator = get_sparql_generator()
        query = generator.generate_work_query(
            work_qid=work_qid,
            author_qid=author_qid,
            genre_qid=genre_qid,
            year_start=year_start,
            year_end=year_end,
            limit=limit,
            offset=offset
        )
        
        return {
            "filters": {
                "work_qid": work_qid,
                "author_qid": author_qid,
                "genre_qid": genre_qid,
                "year_range": [year_start, year_end]
            },
            "sparql": query
        }
    except Exception as e:
        logger.error(f"Error generating work query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sparql/influence")
async def generate_influence_query(
    center_qid: str | None = Query(None, description="Center author QID for influence network"),
    limit: int = Query(200, ge=1, le=1000)
) -> dict[str, Any]:
    """
    Generate a Wikidata SPARQL query for author influence relationships.
    
    Use this to build influence graphs showing who influenced whom.
    
    Example:
        GET /validation/sparql/influence?center_qid=Q23434&limit=100
    """
    try:
        generator = get_sparql_generator()
        query = generator.generate_influence_graph_query(center_qid, limit=limit)
        
        return {
            "center_qid": center_qid,
            "sparql": query
        }
    except Exception as e:
        logger.error(f"Error generating influence query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sparql/validation/{entity_type}/{qid}")
async def generate_validation_query(
    entity_type: str,
    qid: str
) -> dict[str, str]:
    """
    Generate a SPARQL query for validating a specific entity.
    
    This query retrieves all properties that the ontology expects
    for the given entity type, enabling comprehensive validation.
    
    Args:
        entity_type: Ontology class name
        qid: Wikidata QID of the entity to validate
    
    Example:
        GET /validation/sparql/validation/Author/Q23434
    """
    try:
        generator = get_sparql_generator()
        query = generator.generate_validation_query(entity_type, qid)
        
        return {
            "entity_type": entity_type,
            "qid": qid,
            "sparql": query
        }
    except Exception as e:
        logger.error(f"Error generating validation query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VALIDATION ENDPOINTS
# =============================================================================

@router.post("/validate", response_model=ValidationResult)
async def validate_entity(request: ValidationRequest) -> ValidationResult:
    """
    Validate a single entity against the ontology schema.
    
    This endpoint checks that the provided data conforms to the
    constraints defined in the local ontology, including:
    - Property types (object vs datatype)
    - Datatypes (date, string, integer)
    - Required vs optional properties
    - Entity reference formats
    
    Request body:
    ```json
    {
        "entity_type": "Author",
        "data": {
            "qid": "Q23434",
            "name": "Ernest Hemingway",
            "birthDate": "1899-07-21",
            "birthPlace": "Q183287"
        },
        "strict": false
    }
    ```
    
    Returns validation result with any issues found.
    """
    try:
        validator = get_response_validator()
        result = validator.validate_entity(
            entity_type=request.entity_type,
            data=request.data,
            strict=request.strict
        )
        return result
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/batch", response_model=BatchValidationResult)
async def validate_batch(request: BatchValidationRequest) -> BatchValidationResult:
    """
    Validate multiple entities against the ontology schema.
    
    Use this endpoint to validate bulk data, such as search results
    from Wikidata. Returns aggregated statistics and individual
    validation results.
    
    Request body:
    ```json
    {
        "entity_type": "Author",
        "data": [
            {"qid": "Q23434", "name": "Ernest Hemingway", ...},
            {"qid": "Q150905", "name": "Gabriel García Márquez", ...}
        ],
        "strict": false
    }
    ```
    """
    try:
        validator = get_response_validator()
        result = validator.validate_batch(
            entity_type=request.entity_type,
            data_list=request.data,
            strict=request.strict
        )
        return result
    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expected-properties/{entity_type}")
async def get_expected_properties(entity_type: str) -> dict[str, Any]:
    """
    Get expected properties for an entity type.
    
    Returns all properties that the ontology defines as applicable
    to the given entity type, including their Wikidata equivalents,
    types, and ranges.
    
    Use this to understand what data is expected for each entity type.
    
    Example:
        GET /validation/expected-properties/Author
    """
    try:
        mapper = get_schema_mapper()
        properties = mapper.get_expected_properties_for_class(entity_type)
        
        if not properties:
            raise HTTPException(
                status_code=404,
                detail=f"No properties found for entity type: {entity_type}"
            )
        
        return {
            "entity_type": entity_type,
            "property_count": len(properties),
            "properties": properties
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting expected properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{entity_type}")
async def get_entity_type_summary(entity_type: str) -> dict[str, Any]:
    """
    Get a complete summary of an entity type.
    
    Combines class mapping, expected properties, and sample SPARQL
    query for the given entity type.
    
    Example:
        GET /validation/summary/Author
    """
    try:
        mapper = get_schema_mapper()
        generator = get_sparql_generator()
        
        class_mapping = mapper.get_class_mapping(entity_type)
        if not class_mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown entity type: {entity_type}"
            )
        
        properties = mapper.get_expected_properties_for_class(entity_type)
        sample_query = generator.generate_entity_query(entity_type, limit=10)
        
        return {
            "entity_type": entity_type,
            "class_mapping": class_mapping,
            "properties": {
                "count": len(properties),
                "list": properties
            },
            "sample_sparql_query": sample_query
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
