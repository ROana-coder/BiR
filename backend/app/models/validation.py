"""Validation models for ontology-based Wikidata response validation."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity level of a validation issue."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(str, Enum):
    """Type of validation check."""
    MISSING_REQUIRED = "missing_required"
    TYPE_MISMATCH = "type_mismatch"
    INVALID_RANGE = "invalid_range"
    UNKNOWN_PROPERTY = "unknown_property"
    CARDINALITY = "cardinality"
    FORMAT = "format"
    DOMAIN_VIOLATION = "domain_violation"
    RANGE_VIOLATION = "range_violation"


class ValidationIssue(BaseModel):
    """A single validation issue found in the data."""
    
    type: ValidationType = Field(..., description="Type of validation issue")
    severity: ValidationSeverity = Field(..., description="Severity level")
    field: str = Field(..., description="The field/property with the issue")
    message: str = Field(..., description="Human-readable description of the issue")
    expected: str | None = Field(None, description="What was expected")
    actual: str | None = Field(None, description="What was found")
    wikidata_property: str | None = Field(None, description="Related Wikidata property (e.g., P50)")
    ontology_property: str | None = Field(None, description="Related ontology property URI")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "type_mismatch",
                "severity": "error",
                "field": "birthDate",
                "message": "Expected date format, got string",
                "expected": "xsd:date",
                "actual": "plain string: '1899'",
                "wikidata_property": "P569",
                "ontology_property": "http://literature-explorer.org/ontology#birthDate"
            }
        }


class ValidationResult(BaseModel):
    """Result of validating a single entity or response."""
    
    valid: bool = Field(..., description="Whether the data is valid (no errors)")
    entity_type: str = Field(..., description="The type of entity validated (e.g., Author, LiteraryWork)")
    entity_id: str | None = Field(None, description="Identifier of the validated entity (e.g., Q23434)")
    issues: list[ValidationIssue] = Field(default_factory=list, description="List of validation issues found")
    error_count: int = Field(0, description="Number of errors")
    warning_count: int = Field(0, description="Number of warnings")
    info_count: int = Field(0, description="Number of info messages")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """Add an issue and update counts."""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.error_count += 1
            self.valid = False
        elif issue.severity == ValidationSeverity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": False,
                "entity_type": "Author",
                "entity_id": "Q23434",
                "issues": [
                    {
                        "type": "missing_required",
                        "severity": "warning",
                        "field": "deathPlace",
                        "message": "Optional property 'deathPlace' is missing",
                        "wikidata_property": "P20"
                    }
                ],
                "error_count": 0,
                "warning_count": 1,
                "info_count": 0,
                "validated_at": "2025-01-10T12:00:00Z"
            }
        }


class BatchValidationResult(BaseModel):
    """Result of validating multiple entities."""
    
    total_entities: int = Field(..., description="Total number of entities validated")
    valid_entities: int = Field(0, description="Number of valid entities")
    invalid_entities: int = Field(0, description="Number of invalid entities")
    results: list[ValidationResult] = Field(default_factory=list, description="Individual validation results")
    total_errors: int = Field(0, description="Total error count across all entities")
    total_warnings: int = Field(0, description="Total warning count across all entities")
    summary: dict[str, int] = Field(default_factory=dict, description="Issue type summary")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validation was performed")
    
    def add_result(self, result: ValidationResult) -> None:
        """Add a result and update aggregates."""
        self.results.append(result)
        if result.valid:
            self.valid_entities += 1
        else:
            self.invalid_entities += 1
        self.total_errors += result.error_count
        self.total_warnings += result.warning_count
        
        # Update summary
        for issue in result.issues:
            key = issue.type.value
            self.summary[key] = self.summary.get(key, 0) + 1


class PropertyMapping(BaseModel):
    """Mapping between ontology property and Wikidata property."""
    
    ontology_uri: str = Field(..., description="Full URI of the ontology property")
    ontology_local: str = Field(..., description="Local name of the ontology property")
    wikidata_uri: str = Field(..., description="Full URI of the Wikidata property")
    wikidata_id: str = Field(..., description="Wikidata property ID (e.g., P50)")
    property_type: str = Field(..., description="ObjectProperty or DatatypeProperty")
    domain: str | None = Field(None, description="Domain class URI")
    range: str | None = Field(None, description="Range class or datatype URI")
    label: str | None = Field(None, description="Human-readable label")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ontology_uri": "http://literature-explorer.org/ontology#writtenBy",
                "ontology_local": "writtenBy",
                "wikidata_uri": "http://www.wikidata.org/prop/direct/P50",
                "wikidata_id": "P50",
                "property_type": "ObjectProperty",
                "domain": "http://literature-explorer.org/ontology#LiteraryWork",
                "range": "http://literature-explorer.org/ontology#Author",
                "label": "written by"
            }
        }


class ClassMapping(BaseModel):
    """Mapping between ontology class and Wikidata class."""
    
    ontology_uri: str = Field(..., description="Full URI of the ontology class")
    ontology_local: str = Field(..., description="Local name of the ontology class")
    wikidata_uri: str = Field(..., description="Full URI of the Wikidata entity")
    wikidata_id: str = Field(..., description="Wikidata QID (e.g., Q482980)")
    label: str | None = Field(None, description="Human-readable label")
    parent_class: str | None = Field(None, description="Parent class URI if any")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ontology_uri": "http://literature-explorer.org/ontology#Author",
                "ontology_local": "Author",
                "wikidata_uri": "http://www.wikidata.org/entity/Q482980",
                "wikidata_id": "Q482980",
                "label": "Author",
                "parent_class": "http://xmlns.com/foaf/0.1/Person"
            }
        }


class SchemaInfo(BaseModel):
    """Complete schema information extracted from the ontology."""
    
    class_mappings: list[ClassMapping] = Field(default_factory=list, description="Class mappings")
    property_mappings: list[PropertyMapping] = Field(default_factory=list, description="Property mappings")
    class_count: int = Field(0, description="Number of mapped classes")
    property_count: int = Field(0, description="Number of mapped properties")
    
    # Index for quick lookup
    wikidata_to_ontology_class: dict[str, str] = Field(default_factory=dict)
    ontology_to_wikidata_class: dict[str, str] = Field(default_factory=dict)
    wikidata_to_ontology_property: dict[str, str] = Field(default_factory=dict)
    ontology_to_wikidata_property: dict[str, str] = Field(default_factory=dict)


class ValidationRequest(BaseModel):
    """Request to validate Wikidata data against the ontology schema."""
    
    entity_type: str = Field(..., description="Type of entity (Author, LiteraryWork, etc.)")
    data: dict[str, Any] = Field(..., description="The data to validate")
    strict: bool = Field(False, description="Whether to treat warnings as errors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "Author",
                "data": {
                    "qid": "Q23434",
                    "name": "Ernest Hemingway",
                    "birthDate": "1899-07-21",
                    "birthPlace": "Q183287"
                },
                "strict": False
            }
        }


class BatchValidationRequest(BaseModel):
    """Request to validate multiple entities."""
    
    entity_type: str = Field(..., description="Type of entities (Author, LiteraryWork, etc.)")
    data: list[dict[str, Any]] = Field(..., description="List of entities to validate")
    strict: bool = Field(False, description="Whether to treat warnings as errors")
