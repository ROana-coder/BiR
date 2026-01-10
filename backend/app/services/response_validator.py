"""Response Validator service for validating Wikidata responses against ontology schema."""

import logging
import re
from datetime import datetime
from typing import Any

from app.models.validation import (
    ValidationSeverity,
    ValidationType,
    ValidationIssue,
    ValidationResult,
    BatchValidationResult,
    PropertyMapping,
)
from app.services.schema_mapper import get_schema_mapper, SchemaMapper

logger = logging.getLogger(__name__)


class ResponseValidator:
    """
    Validates Wikidata query responses against the local ontology schema.
    
    This service checks that data retrieved from Wikidata conforms to:
    - Expected property types (object vs datatype properties)
    - Expected datatypes (xsd:date, xsd:string, etc.)
    - Domain and range constraints
    - Required vs optional properties
    
    De ce? (Why?)
    -------------
    Wikidata este o sursă externă, necontrolată. Datele pot fi incomplete,
    inconsistente sau în formate neașteptate. Validatorul asigură că datele
    care ajung în aplicație respectă structura definită în ontologia noastră,
    permițând detectarea erorilor înainte ca acestea să afecteze experiența
    utilizatorului sau vizualizările.
    """
    
    # XSD datatype patterns for validation
    DATATYPE_PATTERNS = {
        "http://www.w3.org/2001/XMLSchema#date": r"^\d{4}-\d{2}-\d{2}$",
        "http://www.w3.org/2001/XMLSchema#dateTime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        "http://www.w3.org/2001/XMLSchema#gYear": r"^-?\d{4}$",
        "http://www.w3.org/2001/XMLSchema#integer": r"^-?\d+$",
        "http://www.w3.org/2001/XMLSchema#decimal": r"^-?\d+\.?\d*$",
        "http://www.w3.org/2001/XMLSchema#boolean": r"^(true|false|0|1)$",
        "http://www.w3.org/2001/XMLSchema#string": r".*",  # Any string
    }
    
    # Wikidata entity patterns
    QID_PATTERN = re.compile(r"^Q\d+$")
    PID_PATTERN = re.compile(r"^P\d+$")
    WIKIDATA_URI_PATTERN = re.compile(r"^http://www\.wikidata\.org/entity/(Q\d+)$")
    
    def __init__(self, schema_mapper: SchemaMapper | None = None):
        """Initialize the response validator.
        
        Args:
            schema_mapper: Optional schema mapper instance (uses singleton if not provided)
        """
        self._mapper = schema_mapper or get_schema_mapper()
    
    def validate_entity(
        self,
        entity_type: str,
        data: dict[str, Any],
        strict: bool = False
    ) -> ValidationResult:
        """Validate a single entity against the ontology schema.
        
        Args:
            entity_type: Ontology class name (e.g., 'Author', 'LiteraryWork')
            data: The entity data to validate
            strict: Whether to treat warnings as errors
            
        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(
            valid=True,
            entity_type=entity_type,
            entity_id=self._extract_entity_id(data)
        )
        
        # Check if entity type is known
        class_mapping = self._mapper.get_class_mapping(entity_type)
        if not class_mapping:
            result.add_issue(ValidationIssue(
                type=ValidationType.UNKNOWN_PROPERTY,
                severity=ValidationSeverity.ERROR,
                field="entity_type",
                message=f"Unknown entity type: {entity_type}",
                expected="One of: Author, LiteraryWork, Genre, etc.",
                actual=entity_type
            ))
            return result
        
        # Get expected properties for this entity type
        expected_props = self._mapper.get_expected_properties_for_class(entity_type)
        
        # Validate each field in the data
        for field_name, field_value in data.items():
            if field_name in ("qid", "id", "uri", "type"):
                continue  # Skip meta fields
            
            # Check if this field maps to an ontology property
            prop_info = expected_props.get(field_name)
            
            if prop_info:
                # Validate the value against property constraints
                issues = self._validate_property_value(
                    field_name=field_name,
                    value=field_value,
                    prop_info=prop_info,
                    strict=strict
                )
                for issue in issues:
                    result.add_issue(issue)
            else:
                # Unknown property - check if it might be a Wikidata property
                wd_prop = self._mapper.translate_from_wikidata(field_name)
                if not wd_prop:
                    # Truly unknown property
                    severity = ValidationSeverity.WARNING if not strict else ValidationSeverity.ERROR
                    result.add_issue(ValidationIssue(
                        type=ValidationType.UNKNOWN_PROPERTY,
                        severity=severity,
                        field=field_name,
                        message=f"Property '{field_name}' is not defined in the ontology schema",
                        actual=field_name
                    ))
        
        # Check for missing expected properties
        for prop_name, prop_info in expected_props.items():
            if prop_name not in data:
                # Property is missing
                is_required = prop_info.get("required", False)
                severity = ValidationSeverity.ERROR if is_required else ValidationSeverity.INFO
                
                if strict and not is_required:
                    severity = ValidationSeverity.WARNING
                
                result.add_issue(ValidationIssue(
                    type=ValidationType.MISSING_REQUIRED if is_required else ValidationType.MISSING_REQUIRED,
                    severity=severity,
                    field=prop_name,
                    message=f"{'Required' if is_required else 'Optional'} property '{prop_name}' is missing",
                    expected=prop_info.get("wikidata_property"),
                    wikidata_property=prop_info.get("wikidata_property"),
                    ontology_property=prop_name
                ))
        
        return result
    
    def _validate_property_value(
        self,
        field_name: str,
        value: Any,
        prop_info: dict,
        strict: bool = False
    ) -> list[ValidationIssue]:
        """Validate a single property value.
        
        Args:
            field_name: The property name
            value: The value to validate
            prop_info: Property constraints from schema
            strict: Whether to be strict about validation
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        if value is None:
            return issues  # Null values are handled in missing property check
        
        property_type = prop_info.get("property_type")
        expected_range = prop_info.get("range")
        wikidata_prop = prop_info.get("wikidata_property")
        
        if property_type == "ObjectProperty":
            # Value should be an entity reference
            issues.extend(self._validate_object_property(
                field_name, value, expected_range, wikidata_prop
            ))
        elif property_type == "DatatypeProperty":
            # Value should match expected datatype
            issues.extend(self._validate_datatype_property(
                field_name, value, expected_range, wikidata_prop
            ))
        
        return issues
    
    def _validate_object_property(
        self,
        field_name: str,
        value: Any,
        expected_range: str | None,
        wikidata_prop: str | None
    ) -> list[ValidationIssue]:
        """Validate an object property value."""
        issues = []
        
        # Handle different value formats
        if isinstance(value, dict):
            # Might be a structured entity reference
            entity_id = value.get("qid") or value.get("value") or value.get("id")
        elif isinstance(value, str):
            entity_id = value
        elif isinstance(value, list):
            # Validate each item in the list
            for item in value:
                issues.extend(self._validate_object_property(
                    field_name, item, expected_range, wikidata_prop
                ))
            return issues
        else:
            issues.append(ValidationIssue(
                type=ValidationType.TYPE_MISMATCH,
                severity=ValidationSeverity.ERROR,
                field=field_name,
                message=f"Object property '{field_name}' should be an entity reference",
                expected="Entity reference (QID or URI)",
                actual=f"{type(value).__name__}: {value}",
                wikidata_property=wikidata_prop
            ))
            return issues
        
        # Validate entity reference format
        if entity_id:
            # Check if it's a valid QID or Wikidata URI
            if not self.QID_PATTERN.match(str(entity_id)):
                match = self.WIKIDATA_URI_PATTERN.match(str(entity_id))
                if not match:
                    issues.append(ValidationIssue(
                        type=ValidationType.FORMAT,
                        severity=ValidationSeverity.WARNING,
                        field=field_name,
                        message=f"Value '{entity_id}' doesn't look like a valid Wikidata entity",
                        expected="QID (e.g., Q23434) or Wikidata URI",
                        actual=str(entity_id),
                        wikidata_property=wikidata_prop
                    ))
        
        return issues
    
    def _validate_datatype_property(
        self,
        field_name: str,
        value: Any,
        expected_range: str | None,
        wikidata_prop: str | None
    ) -> list[ValidationIssue]:
        """Validate a datatype property value."""
        issues = []
        
        if isinstance(value, list):
            # Validate each item in the list
            for item in value:
                issues.extend(self._validate_datatype_property(
                    field_name, item, expected_range, wikidata_prop
                ))
            return issues
        
        # Handle structured values (from Wikidata)
        if isinstance(value, dict):
            actual_value = value.get("value", value)
            actual_type = value.get("datatype")
        else:
            actual_value = value
            actual_type = None
        
        # Validate against expected range (datatype)
        if expected_range and expected_range in self.DATATYPE_PATTERNS:
            pattern = self.DATATYPE_PATTERNS[expected_range]
            str_value = str(actual_value)
            
            if not re.match(pattern, str_value):
                issues.append(ValidationIssue(
                    type=ValidationType.TYPE_MISMATCH,
                    severity=ValidationSeverity.WARNING,
                    field=field_name,
                    message=f"Value doesn't match expected datatype format",
                    expected=self._get_datatype_name(expected_range),
                    actual=f"{type(actual_value).__name__}: {str_value[:50]}...",
                    wikidata_property=wikidata_prop
                ))
        
        # Additional type-specific validation
        if expected_range:
            if "date" in expected_range.lower():
                issues.extend(self._validate_date_value(field_name, actual_value, wikidata_prop))
            elif "integer" in expected_range.lower():
                issues.extend(self._validate_integer_value(field_name, actual_value, wikidata_prop))
        
        return issues
    
    def _validate_date_value(
        self,
        field_name: str,
        value: Any,
        wikidata_prop: str | None
    ) -> list[ValidationIssue]:
        """Validate a date value."""
        issues = []
        
        str_value = str(value)
        
        # Try to parse as date
        date_patterns = [
            (r"^\d{4}-\d{2}-\d{2}$", "%Y-%m-%d"),  # Full date
            (r"^\d{4}-\d{2}$", "%Y-%m"),  # Year-month
            (r"^-?\d{4}$", "%Y"),  # Year only
        ]
        
        parsed = False
        for pattern, date_format in date_patterns:
            if re.match(pattern, str_value):
                try:
                    if str_value.startswith("-"):
                        # BCE date
                        parsed = True
                    else:
                        datetime.strptime(str_value, date_format)
                        parsed = True
                    break
                except ValueError:
                    pass
        
        if not parsed and str_value:
            issues.append(ValidationIssue(
                type=ValidationType.FORMAT,
                severity=ValidationSeverity.WARNING,
                field=field_name,
                message=f"Date value '{str_value}' may not be in standard format",
                expected="ISO 8601 date (YYYY-MM-DD, YYYY-MM, or YYYY)",
                actual=str_value,
                wikidata_property=wikidata_prop
            ))
        
        return issues
    
    def _validate_integer_value(
        self,
        field_name: str,
        value: Any,
        wikidata_prop: str | None
    ) -> list[ValidationIssue]:
        """Validate an integer value."""
        issues = []
        
        if not isinstance(value, (int, float)):
            try:
                int(str(value))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    type=ValidationType.TYPE_MISMATCH,
                    severity=ValidationSeverity.ERROR,
                    field=field_name,
                    message=f"Expected integer value for '{field_name}'",
                    expected="Integer",
                    actual=f"{type(value).__name__}: {value}",
                    wikidata_property=wikidata_prop
                ))
        
        return issues
    
    def _extract_entity_id(self, data: dict[str, Any]) -> str | None:
        """Extract entity ID from data."""
        for key in ("qid", "id", "uri", "item"):
            if key in data:
                value = data[key]
                if isinstance(value, dict):
                    return value.get("value")
                return str(value)
        return None
    
    def _get_datatype_name(self, datatype_uri: str) -> str:
        """Get human-readable datatype name."""
        return datatype_uri.split("#")[-1] if "#" in datatype_uri else datatype_uri.split("/")[-1]
    
    def validate_batch(
        self,
        entity_type: str,
        data_list: list[dict[str, Any]],
        strict: bool = False
    ) -> BatchValidationResult:
        """Validate multiple entities.
        
        Args:
            entity_type: Ontology class name
            data_list: List of entities to validate
            strict: Whether to be strict about validation
            
        Returns:
            BatchValidationResult with aggregated results
        """
        batch_result = BatchValidationResult(
            total_entities=len(data_list)
        )
        
        for data in data_list:
            result = self.validate_entity(entity_type, data, strict)
            batch_result.add_result(result)
        
        return batch_result
    
    def validate_wikidata_response(
        self,
        entity_type: str,
        bindings: list[dict[str, Any]],
        strict: bool = False
    ) -> BatchValidationResult:
        """Validate raw Wikidata SPARQL results.
        
        This method handles the raw binding format from Wikidata queries.
        
        Args:
            entity_type: Ontology class name
            bindings: Raw SPARQL result bindings
            strict: Whether to be strict
            
        Returns:
            BatchValidationResult
        """
        # Transform bindings to simplified format
        simplified = []
        for binding in bindings:
            entity = {}
            for key, value in binding.items():
                if isinstance(value, dict):
                    entity[key] = value.get("value", value)
                else:
                    entity[key] = value
            simplified.append(entity)
        
        return self.validate_batch(entity_type, simplified, strict)
    
    def get_validation_summary(
        self,
        result: ValidationResult | BatchValidationResult
    ) -> dict[str, Any]:
        """Get a summary of validation results.
        
        Args:
            result: Validation result to summarize
            
        Returns:
            Summary dictionary
        """
        if isinstance(result, BatchValidationResult):
            return {
                "total_entities": result.total_entities,
                "valid_entities": result.valid_entities,
                "invalid_entities": result.invalid_entities,
                "validity_rate": (
                    result.valid_entities / result.total_entities * 100
                    if result.total_entities > 0 else 0
                ),
                "total_errors": result.total_errors,
                "total_warnings": result.total_warnings,
                "issue_breakdown": result.summary
            }
        else:
            return {
                "valid": result.valid,
                "entity_type": result.entity_type,
                "entity_id": result.entity_id,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "info_count": result.info_count,
                "issue_types": [issue.type.value for issue in result.issues]
            }


# Singleton instance
_response_validator: ResponseValidator | None = None


def get_response_validator() -> ResponseValidator:
    """Get the singleton response validator instance."""
    global _response_validator
    if _response_validator is None:
        _response_validator = ResponseValidator()
    return _response_validator
