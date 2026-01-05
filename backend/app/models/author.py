"""Author model representing writers and literary figures."""

from datetime import date

from pydantic import BaseModel, Field

from app.models.location import Location


class Author(BaseModel):
    """Represents an author/writer from Wikidata.
    
    Uses verified Wikidata properties:
        - P27: country of citizenship (nationality)
        - P19: place of birth
        - P20: place of death
        - P135: movement (literary/artistic movement)
        - P800: notable work
        - P737: influenced by
    """
    
    qid: str = Field(..., pattern=r"^Q\d+$", description="Wikidata Q-identifier")
    name: str = Field(..., min_length=1, description="Author's name")
    
    # Dates
    birth_date: date | None = Field(None, description="Date of birth")
    death_date: date | None = Field(None, description="Date of death")
    
    # Locations (P19, P20)
    birth_place: Location | None = Field(None, description="Place of birth (P19)")
    death_place: Location | None = Field(None, description="Place of death (P20)")
    
    # Nationality (P27)
    nationality: str | None = Field(None, description="Country of citizenship (P27)")
    nationality_qid: str | None = Field(None, description="Country QID")
    
    # Literary metadata
    movements: list[str] = Field(
        default_factory=list, 
        description="Literary/artistic movements (P135)"
    )
    movement_qids: list[str] = Field(
        default_factory=list,
        description="Movement QIDs for linking"
    )
    
    notable_works: list[str] = Field(
        default_factory=list,
        description="Notable works titles (P800)"
    )
    notable_work_qids: list[str] = Field(
        default_factory=list,
        description="Notable work QIDs for linking"
    )
    
    # Relationships
    influenced_by: list[str] = Field(
        default_factory=list,
        description="Names of influences (P737)"
    )
    influenced_by_qids: list[str] = Field(
        default_factory=list,
        description="Influence QIDs for graph building"
    )
    
    # Occupation (P106)
    occupations: list[str] = Field(
        default_factory=list,
        description="Occupations (P106)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "qid": "Q23434",
                "name": "Ernest Hemingway",
                "birth_date": "1899-07-21",
                "death_date": "1961-07-02",
                "birth_place": {
                    "qid": "Q183287",
                    "name": "Oak Park",
                    "coordinates": (41.885, -87.781),
                    "country": "United States"
                },
                "nationality": "United States",
                "nationality_qid": "Q30",
                "movements": ["Modernism", "Lost Generation"],
                "movement_qids": ["Q37068", "Q213714"],
                "notable_works": ["The Old Man and the Sea", "A Farewell to Arms"],
                "notable_work_qids": ["Q173169", "Q770472"],
                "influenced_by": ["Gertrude Stein", "Ezra Pound"],
                "influenced_by_qids": ["Q188385", "Q161961"],
                "occupations": ["novelist", "journalist"]
            }
        }
