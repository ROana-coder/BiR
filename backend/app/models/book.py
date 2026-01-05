"""Book model representing literary works."""

from datetime import date

from pydantic import BaseModel, Field

from app.models.location import Location


class Book(BaseModel):
    """Represents a book/literary work from Wikidata.
    
    Uses verified Wikidata properties:
        - P31: instance of (Q571=book, Q7725634=literary work)
        - P50: author
        - P577: publication date
        - P136: genre
        - P291: place of publication
    """
    
    qid: str = Field(..., pattern=r"^Q\d+$", description="Wikidata Q-identifier")
    title: str = Field(..., min_length=1, description="Book title")
    
    # Publication metadata (P577)
    publication_date: date | None = Field(
        None, 
        description="Publication date (P577)"
    )
    publication_year: int | None = Field(
        None,
        description="Extracted year for filtering"
    )
    
    # Authors (P50)
    authors: list[str] = Field(
        default_factory=list,
        description="Author names"
    )
    author_qids: list[str] = Field(
        default_factory=list,
        description="Author QIDs for linking"
    )
    
    # Genre (P136)
    genre: str | None = Field(None, description="Primary genre name")
    genre_qid: str | None = Field(None, description="Genre QID")
    genres: list[str] = Field(
        default_factory=list,
        description="All genre names"
    )
    genre_qids: list[str] = Field(
        default_factory=list,
        description="All genre QIDs"
    )
    
    # Publication location (P291)
    publication_place: Location | None = Field(
        None,
        description="Place of publication (P291)"
    )
    
    # Narrative setting (P840)
    narrative_locations: list[Location] = Field(
        default_factory=list,
        description="Narrative locations / story settings (P840)"
    )
    
    # Language (P407)
    language: str | None = Field(None, description="Original language")
    language_qid: str | None = Field(None, description="Language QID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "qid": "Q173169",
                "title": "The Old Man and the Sea",
                "publication_date": "1952-09-01",
                "publication_year": 1952,
                "authors": ["Ernest Hemingway"],
                "author_qids": ["Q23434"],
                "genre": "novella",
                "genre_qid": "Q149537",
                "publication_place": {
                    "qid": "Q60",
                    "name": "New York City",
                    "coordinates": (40.7128, -74.0060),
                    "country": "United States"
                },
                "language": "English",
                "language_qid": "Q1860"
            }
        }
