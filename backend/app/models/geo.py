"""Geo models for map visualization."""

from enum import Enum

from pydantic import BaseModel, Field


class GeoLayerType(str, Enum):
    """Types of geographic layers for the map."""
    BIRTHPLACES = "birthplaces"
    DEATHPLACES = "deathplaces"
    PUBLICATIONS = "publications"
    STORY_SETTINGS = "settings"


class GeoPoint(BaseModel):
    """A geographic point for map visualization.
    
    Represents data from P625 (coordinate location) combined
    with context from P19 (birthplace), P20 (deathplace), 
    P291 (publication place), or P840 (narrative location).
    """
    
    qid: str = Field(..., pattern=r"^Q\d+$", description="Location QID")
    name: str = Field(..., description="Location name")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    
    layer: GeoLayerType = Field(..., description="Which map layer this belongs to")
    
    # Reference to the entity this point is associated with
    entity_qid: str | None = Field(
        None,
        description="QID of the associated author/book"
    )
    entity_name: str | None = Field(
        None,
        description="Name of the associated author/book"
    )
    entity_type: str | None = Field(
        None,
        description="Type: 'author' or 'book'"
    )
    
    # Additional context
    year: int | None = Field(None, description="Associated year (birth/death/publication)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "qid": "Q90",
                "name": "Paris",
                "latitude": 48.8566,
                "longitude": 2.3522,
                "layer": "birthplaces",
                "entity_qid": "Q188385",
                "entity_name": "Gertrude Stein",
                "entity_type": "author",
                "year": None
            }
        }


class GeoCluster(BaseModel):
    """A cluster of geographic points for performance optimization.
    
    Used when point count exceeds threshold (default 1000) to prevent
    frontend DOM thrashing.
    """
    
    center_latitude: float = Field(..., ge=-90, le=90)
    center_longitude: float = Field(..., ge=-180, le=180)
    
    point_count: int = Field(..., ge=1, description="Number of points in cluster")
    
    layer: GeoLayerType = Field(..., description="Layer type")
    
    # Representative points (up to 5 for popup display)
    sample_points: list[GeoPoint] = Field(
        default_factory=list,
        max_length=5,
        description="Sample points for popup display"
    )
    
    # Bounding box for zoom
    bounds: tuple[float, float, float, float] | None = Field(
        None,
        description="Bounding box (min_lat, min_lon, max_lat, max_lon)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "center_latitude": 48.8566,
                "center_longitude": 2.3522,
                "point_count": 42,
                "layer": "birthplaces",
                "sample_points": [],
                "bounds": (48.8, 2.2, 48.9, 2.4)
            }
        }


class GeoResponse(BaseModel):
    """Response model for geo endpoints."""
    
    points: list[GeoPoint] = Field(default_factory=list)
    clusters: list[GeoCluster] = Field(default_factory=list)
    
    total_count: int = Field(0, ge=0)
    is_clustered: bool = Field(False, description="Whether clustering was applied")
    
    layer: GeoLayerType = Field(..., description="The requested layer type")
