"""Graph models for network visualization."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the literary network graph."""
    AUTHOR = "author"
    BOOK = "book"
    MOVEMENT = "movement"
    LOCATION = "location"


class EdgeType(str, Enum):
    """Types of relationships in the literary network.
    
    Based on Wikidata properties:
        - P50: author (book -> author)
        - P737: influenced by (author -> author)
        - P1066: student of (author -> author)
        - P135: movement (author -> movement)
    """
    AUTHORED = "authored"           # P50 inverse
    INFLUENCED_BY = "influenced_by" # P737
    STUDENT_OF = "student_of"       # P1066
    MEMBER_OF = "member_of"         # P135 (movement membership)


class GraphNode(BaseModel):
    """A node in the literary network graph."""
    
    id: str = Field(..., description="Unique node ID (usually QID)")
    label: str = Field(..., description="Display label")
    type: NodeType = Field(..., description="Node type for styling")
    
    # Optional metadata for tooltips/details
    metadata: dict = Field(
        default_factory=dict,
        description="Additional node metadata"
    )
    
    # Graph metrics (computed server-side)
    centrality: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Betweenness centrality score"
    )
    degree: int | None = Field(None, ge=0, description="Node degree")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "Q23434",
                "label": "Ernest Hemingway",
                "type": "author",
                "metadata": {
                    "birth_year": 1899,
                    "death_year": 1961,
                    "nationality": "American"
                },
                "centrality": 0.42,
                "degree": 8
            }
        }


class GraphEdge(BaseModel):
    """An edge/relationship in the literary network graph."""
    
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Relationship type")
    
    # Optional edge metadata
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="Edge weight for force layout"
    )
    label: str | None = Field(None, description="Optional edge label")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "Q23434",
                "target": "Q188385",
                "type": "influenced_by",
                "weight": 1.0,
                "label": "influenced by"
            }
        }


class GraphData(BaseModel):
    """Complete graph data for D3.js visualization."""
    
    nodes: list[GraphNode] = Field(
        default_factory=list,
        description="List of graph nodes"
    )
    edges: list[GraphEdge] = Field(
        default_factory=list,
        description="List of graph edges"
    )
    
    # Graph-level metadata
    node_count: int = Field(0, ge=0, description="Total node count")
    edge_count: int = Field(0, ge=0, description="Total edge count")
    
    # Central nodes (for highlighting)
    central_nodes: list[str] = Field(
        default_factory=list,
        description="QIDs of nodes with highest centrality"
    )
    
    def model_post_init(self, __context) -> None:
        """Update counts after initialization."""
        object.__setattr__(self, 'node_count', len(self.nodes))
        object.__setattr__(self, 'edge_count', len(self.edges))
