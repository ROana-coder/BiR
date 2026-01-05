"""Location model for geographic data."""

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Represents a geographic location from Wikidata.
    
    Attributes:
        qid: Wikidata Q-identifier (e.g., Q90 for Paris)
        name: Human-readable location name
        coordinates: Tuple of (latitude, longitude) from P625
        country: Country name or QID
    """
    
    qid: str = Field(..., pattern=r"^Q\d+$", description="Wikidata Q-identifier")
    name: str = Field(..., min_length=1, description="Location name")
    coordinates: tuple[float, float] | None = Field(
        None, 
        description="Geographic coordinates (latitude, longitude) from P625"
    )
    country: str | None = Field(None, description="Country name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "qid": "Q90",
                "name": "Paris",
                "coordinates": (48.8566, 2.3522),
                "country": "France"
            }
        }
