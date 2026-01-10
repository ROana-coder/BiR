"""Pydantic models for the Literature Explorer platform."""

from app.models.location import Location
from app.models.author import Author
from app.models.book import Book
from app.models.graph import GraphNode, GraphEdge, GraphData
from app.models.geo import GeoPoint, GeoCluster
from app.models.validation import (
    ValidationSeverity,
    ValidationType,
    ValidationIssue,
    ValidationResult,
    BatchValidationResult,
    PropertyMapping,
    ClassMapping,
    SchemaInfo,
    ValidationRequest,
    BatchValidationRequest,
)

__all__ = [
    "Location",
    "Author", 
    "Book",
    "GraphNode",
    "GraphEdge",
    "GraphData",
    "GeoPoint",
    "GeoCluster",
    # Validation models
    "ValidationSeverity",
    "ValidationType",
    "ValidationIssue",
    "ValidationResult",
    "BatchValidationResult",
    "PropertyMapping",
    "ClassMapping",
    "SchemaInfo",
    "ValidationRequest",
    "BatchValidationRequest",
]
