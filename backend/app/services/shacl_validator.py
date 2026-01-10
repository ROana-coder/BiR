"""
SHACL Validation Service for Literature Explorer.

This service provides W3C-standard SHACL (Shapes Constraint Language) validation
for RDF data. It validates data against the literature ontology shapes defined
in literature_shapes.ttl.

SHACL provides:
- Declarative constraints for RDF data
- Multiple severity levels (Violation, Warning, Info)
- Rich constraint types (cardinality, datatypes, patterns, etc.)
- Standardized validation reports

Usage:
    validator = get_shacl_validator()
    
    # Validate RDF data in Turtle format
    result = validator.validate_rdf(turtle_data)
    
    # Validate JSON data (converted to RDF)
    result = validator.validate_json("Author", {"name": "Hemingway", ...})
    
    # Get information about available shapes
    shapes_info = validator.get_shapes_info()
"""

import logging
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD, BNode
from pyshacl import validate

from app.models.validation import (
    SHACLSeverity,
    SHACLConstraintComponent,
    SHACLValidationViolation,
    SHACLValidationResult,
    SHACLShapeInfo,
    SHACLShapesInfo,
)

logger = logging.getLogger(__name__)

# Namespaces
LIT = Namespace("http://literature-explorer.org/ontology#")
DATA = Namespace("http://literature-explorer.org/data/")
SH = Namespace("http://www.w3.org/ns/shacl#")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")


class SHACLValidator:
    """
    SHACL Validation Service.
    
    Validates RDF data against SHACL shapes defined for the literature domain.
    Supports both direct RDF validation and JSON-to-RDF conversion.
    """
    
    def __init__(self, shapes_path: str | None = None, ontology_path: str | None = None):
        """
        Initialize the SHACL validator.
        
        Args:
            shapes_path: Path to the SHACL shapes file (Turtle format)
            ontology_path: Path to the ontology file for RDFS inference
        """
        # Default paths
        if shapes_path is None:
            shapes_path = str(Path(__file__).parent.parent / "ontology" / "literature_shapes.ttl")
        if ontology_path is None:
            ontology_path = str(Path(__file__).parent.parent / "ontology" / "literature.ttl")
        
        self.shapes_path = shapes_path
        self.ontology_path = ontology_path
        
        # Load shapes graph
        self.shapes_graph = Graph()
        self._load_shapes()
        
        # Load ontology for inference (optional)
        self.ontology_graph = Graph()
        self._load_ontology()
        
        # Cache shape info
        self._shapes_info: SHACLShapesInfo | None = None
        
        logger.info(f"SHACL Validator initialized with {len(self.shapes_graph)} shape triples")
    
    def _load_shapes(self) -> None:
        """Load the SHACL shapes graph."""
        try:
            self.shapes_graph.parse(self.shapes_path, format="turtle")
            logger.info(f"Loaded SHACL shapes from {self.shapes_path}")
        except Exception as e:
            logger.error(f"Failed to load SHACL shapes: {e}")
            raise RuntimeError(f"Cannot load SHACL shapes from {self.shapes_path}: {e}")
    
    def _load_ontology(self) -> None:
        """Load the ontology graph for inference."""
        try:
            self.ontology_graph.parse(self.ontology_path, format="turtle")
            logger.info(f"Loaded ontology from {self.ontology_path}")
        except Exception as e:
            logger.warning(f"Could not load ontology for inference: {e}")
    
    def _parse_severity(self, severity_uri: str | None) -> SHACLSeverity:
        """Convert SHACL severity URI to enum."""
        if severity_uri is None:
            return SHACLSeverity.VIOLATION
        
        severity_str = str(severity_uri)
        if "Warning" in severity_str:
            return SHACLSeverity.WARNING
        elif "Info" in severity_str:
            return SHACLSeverity.INFO
        return SHACLSeverity.VIOLATION
    
    def _parse_constraint_component(self, component_uri: str | None) -> SHACLConstraintComponent:
        """Convert SHACL constraint component URI to enum."""
        if component_uri is None:
            return SHACLConstraintComponent.OTHER
        
        component_str = str(component_uri)
        
        # Map URI to enum
        component_map = {
            "MinCountConstraintComponent": SHACLConstraintComponent.MIN_COUNT,
            "MaxCountConstraintComponent": SHACLConstraintComponent.MAX_COUNT,
            "DatatypeConstraintComponent": SHACLConstraintComponent.DATATYPE,
            "ClassConstraintComponent": SHACLConstraintComponent.CLASS,
            "NodeKindConstraintComponent": SHACLConstraintComponent.NODE_KIND,
            "MinLengthConstraintComponent": SHACLConstraintComponent.MIN_LENGTH,
            "MaxLengthConstraintComponent": SHACLConstraintComponent.MAX_LENGTH,
            "PatternConstraintComponent": SHACLConstraintComponent.PATTERN,
            "MinInclusiveConstraintComponent": SHACLConstraintComponent.MIN_INCLUSIVE,
            "MaxInclusiveConstraintComponent": SHACLConstraintComponent.MAX_INCLUSIVE,
            "InConstraintComponent": SHACLConstraintComponent.IN,
            "HasValueConstraintComponent": SHACLConstraintComponent.HAS_VALUE,
            "ClosedConstraintComponent": SHACLConstraintComponent.CLOSED,
        }
        
        for name, enum_val in component_map.items():
            if name in component_str:
                return enum_val
        
        return SHACLConstraintComponent.OTHER
    
    def _extract_violations_from_report(self, results_graph: Graph) -> list[SHACLValidationViolation]:
        """Extract structured violations from pyshacl results graph."""
        violations = []
        
        # Query for validation results
        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            # Extract violation details
            focus_node = results_graph.value(result, SH.focusNode)
            result_path = results_graph.value(result, SH.resultPath)
            value = results_graph.value(result, SH.value)
            source_shape = results_graph.value(result, SH.sourceShape)
            source_constraint = results_graph.value(result, SH.sourceConstraintComponent)
            severity = results_graph.value(result, SH.resultSeverity)
            message = results_graph.value(result, SH.resultMessage)
            
            violation = SHACLValidationViolation(
                focus_node=str(focus_node) if focus_node else "unknown",
                result_path=str(result_path) if result_path else None,
                value=str(value) if value else None,
                source_shape=str(source_shape) if source_shape else "unknown",
                source_constraint=str(source_constraint) if source_constraint else None,
                constraint_component=self._parse_constraint_component(
                    str(source_constraint) if source_constraint else None
                ),
                severity=self._parse_severity(str(severity) if severity else None),
                message=str(message) if message else "Validation constraint violated"
            )
            violations.append(violation)
        
        return violations
    
    def validate_rdf(
        self,
        data: str,
        data_format: str = "turtle",
        target_shapes: list[str] | None = None,
        inference: bool = False,
        abort_on_first: bool = False
    ) -> SHACLValidationResult:
        """
        Validate RDF data against SHACL shapes.
        
        Args:
            data: RDF data as string
            data_format: Format of RDF data (turtle, json-ld, n-triples, xml)
            target_shapes: Specific shapes to validate against (optional)
            inference: Whether to perform RDFS inference
            abort_on_first: Stop validation after first violation
            
        Returns:
            SHACLValidationResult with conformance status and violations
        """
        start_time = time.time()
        
        # Parse the data graph
        data_graph = Graph()
        try:
            format_map = {
                "turtle": "turtle",
                "json-ld": "json-ld",
                "n-triples": "nt",
                "xml": "xml",
                "n3": "n3"
            }
            rdf_format = format_map.get(data_format, data_format)
            data_graph.parse(data=data, format=rdf_format)
        except Exception as e:
            logger.error(f"Failed to parse RDF data: {e}")
            result = SHACLValidationResult(
                conforms=False,
                shapes_used=[],
                validation_time_ms=(time.time() - start_time) * 1000
            )
            result.add_violation(SHACLValidationViolation(
                focus_node="data_graph",
                source_shape="parsing",
                severity=SHACLSeverity.VIOLATION,
                message=f"Failed to parse RDF data: {e}"
            ))
            return result
        
        # Prepare shapes graph (filter if target_shapes specified)
        shapes_to_use = self.shapes_graph
        if target_shapes:
            # Create filtered shapes graph
            shapes_to_use = self._filter_shapes(target_shapes)
        
        # Prepare ontology graph for inference
        ont_graph = self.ontology_graph if inference and len(self.ontology_graph) > 0 else None
        
        # Run SHACL validation
        try:
            conforms, results_graph, results_text = validate(
                data_graph,
                shacl_graph=shapes_to_use,
                ont_graph=ont_graph,
                inference="rdfs" if inference else None,
                abort_on_first=abort_on_first,
                meta_shacl=False,
                advanced=False,  # Disabled to avoid issues with property shapes
                debug=False
            )
        except Exception as e:
            logger.error(f"SHACL validation error: {e}")
            result = SHACLValidationResult(
                conforms=False,
                shapes_used=target_shapes or [],
                validation_time_ms=(time.time() - start_time) * 1000
            )
            result.add_violation(SHACLValidationViolation(
                focus_node="validation",
                source_shape="shacl_engine",
                severity=SHACLSeverity.VIOLATION,
                message=f"SHACL validation error: {e}"
            ))
            return result
        
        # Extract violations from results graph
        violations = self._extract_violations_from_report(results_graph)
        
        # Build result
        validation_time = (time.time() - start_time) * 1000
        result = SHACLValidationResult(
            conforms=conforms,
            violations=[],
            shapes_used=target_shapes or self._get_all_shape_names(),
            validation_time_ms=validation_time
        )
        
        for violation in violations:
            result.add_violation(violation)
        
        logger.info(
            f"SHACL validation completed: conforms={conforms}, "
            f"violations={result.violation_count}, warnings={result.warning_count}, "
            f"time={validation_time:.2f}ms"
        )
        
        return result
    
    def _filter_shapes(self, shape_names: list[str]) -> Graph:
        """Create a filtered shapes graph with only specified shapes.
        
        Note: This method creates a deep copy of the relevant shapes including
        all nested blank nodes (property shapes). Due to how RDFLib handles blank
        nodes, we serialize and deserialize to ensure proper copying.
        """
        from rdflib import BNode
        
        filtered = Graph()
        
        # Bind namespaces
        for prefix, ns in self.shapes_graph.namespaces():
            filtered.bind(prefix, ns)
        
        # Collect all triples that need to be copied
        triples_to_copy = set()
        blank_nodes_to_process = set()
        
        for shape_name in shape_names:
            # Handle both full URIs and local names
            if shape_name.startswith("http://"):
                shape_uri = URIRef(shape_name)
            else:
                shape_uri = LIT[shape_name]
            
            # Copy all triples where shape is subject
            for p, o in self.shapes_graph.predicate_objects(shape_uri):
                triples_to_copy.add((shape_uri, p, o))
                
                # Track blank nodes for further processing
                if isinstance(o, BNode):
                    blank_nodes_to_process.add(o)
        
        # Recursively process blank nodes
        processed_bnodes = set()
        while blank_nodes_to_process:
            bnode = blank_nodes_to_process.pop()
            if bnode in processed_bnodes:
                continue
            processed_bnodes.add(bnode)
            
            for p, o in self.shapes_graph.predicate_objects(bnode):
                triples_to_copy.add((bnode, p, o))
                if isinstance(o, BNode):
                    blank_nodes_to_process.add(o)
        
        # Add all collected triples to filtered graph
        for triple in triples_to_copy:
            filtered.add(triple)
        
        return filtered
    
    def _get_all_shape_names(self) -> list[str]:
        """Get names of all shapes in the shapes graph."""
        shapes = []
        for shape in self.shapes_graph.subjects(RDF.type, SH.NodeShape):
            local_name = str(shape).split("#")[-1] if "#" in str(shape) else str(shape).split("/")[-1]
            shapes.append(local_name)
        return shapes
    
    def validate_json(
        self,
        entity_type: str,
        data: dict[str, Any],
        include_related: bool = False
    ) -> SHACLValidationResult:
        """
        Validate JSON data by converting it to RDF and running SHACL validation.
        
        Args:
            entity_type: Type of entity (Author, LiteraryWork, Novel, etc.)
            data: JSON data to validate
            include_related: Whether to validate related entities
            
        Returns:
            SHACLValidationResult with conformance status and violations
        """
        # Convert JSON to RDF Turtle
        turtle_data = self._json_to_rdf(entity_type, data, include_related)
        
        # Determine target shape
        target_shape = f"{entity_type}Shape"
        
        # Validate
        return self.validate_rdf(
            data=turtle_data,
            data_format="turtle",
            target_shapes=[target_shape]
        )
    
    def _json_to_rdf(
        self,
        entity_type: str,
        data: dict[str, Any],
        include_related: bool = False
    ) -> str:
        """
        Convert JSON data to RDF Turtle format.
        
        Maps JSON keys to ontology properties and creates proper RDF triples.
        """
        # Create data graph
        g = Graph()
        g.bind("lit", LIT)
        g.bind("xsd", XSD)
        g.bind("data", DATA)
        
        # Determine entity URI
        qid = data.get("qid", data.get("id", "unknown"))
        entity_uri = DATA[f"{entity_type.lower()}/{qid}"]
        
        # Add type triple
        entity_class = LIT[entity_type]
        g.add((entity_uri, RDF.type, entity_class))
        
        # Property mappings (JSON key -> ontology property, datatype)
        property_map = self._get_property_map(entity_type)
        
        # Add property triples
        for key, value in data.items():
            if key in ("qid", "id", "type"):
                continue
            
            if key in property_map:
                prop_uri, datatype, is_object = property_map[key]
                
                if value is None:
                    continue
                
                if is_object:
                    # Object property - reference another entity
                    if isinstance(value, dict):
                        # Nested entity
                        ref_qid = value.get("qid", value.get("id", "unknown"))
                        ref_type = value.get("type", self._infer_type_from_property(key))
                        ref_uri = DATA[f"{ref_type.lower()}/{ref_qid}"]
                        g.add((entity_uri, prop_uri, ref_uri))
                        
                        # Optionally include related entity
                        if include_related and ref_type:
                            ref_turtle = self._json_to_rdf(ref_type, value, False)
                            ref_graph = Graph()
                            ref_graph.parse(data=ref_turtle, format="turtle")
                            for t in ref_graph:
                                g.add(t)
                    elif isinstance(value, str):
                        # QID reference
                        ref_uri = DATA[f"entity/{value}"]
                        g.add((entity_uri, prop_uri, ref_uri))
                    elif isinstance(value, list):
                        # List of references
                        for item in value:
                            if isinstance(item, dict):
                                ref_qid = item.get("qid", item.get("id", "unknown"))
                                ref_uri = DATA[f"entity/{ref_qid}"]
                                g.add((entity_uri, prop_uri, ref_uri))
                            elif isinstance(item, str):
                                ref_uri = DATA[f"entity/{item}"]
                                g.add((entity_uri, prop_uri, ref_uri))
                else:
                    # Datatype property
                    if isinstance(value, list):
                        for item in value:
                            literal = Literal(str(item), datatype=datatype)
                            g.add((entity_uri, prop_uri, literal))
                    else:
                        literal = Literal(str(value), datatype=datatype)
                        g.add((entity_uri, prop_uri, literal))
        
        return g.serialize(format="turtle")
    
    def _get_property_map(self, entity_type: str) -> dict[str, tuple[URIRef, URIRef | None, bool]]:
        """
        Get property mapping for an entity type.
        
        Returns dict: {json_key: (property_uri, datatype_uri, is_object_property)}
        """
        # Common properties across all types
        common_map = {
            "name": (LIT.name, XSD.string, False),
            "label": (RDFS.label, XSD.string, False),
            "description": (LIT.description, XSD.string, False),
        }
        
        # Type-specific properties
        type_maps = {
            "Author": {
                **common_map,
                "birthDate": (LIT.birthDate, XSD.date, False),
                "deathDate": (LIT.deathDate, XSD.date, False),
                "birthPlace": (LIT.birthPlace, None, True),
                "deathPlace": (LIT.deathPlace, None, True),
                "citizenship": (LIT.citizenship, None, True),
                "influencedBy": (LIT.influencedBy, None, True),
                "studentOf": (LIT.studentOf, None, True),
                "partOfMovement": (LIT.partOfMovement, None, True),
                "awards": (LIT.receivedAward, None, True),
                "notableWorks": (LIT.wroteWork, None, True),
            },
            "LiteraryWork": {
                **common_map,
                "author": (LIT.writtenBy, None, True),
                "writtenBy": (LIT.writtenBy, None, True),
                "publicationDate": (LIT.publicationDate, XSD.date, False),
                "publishedIn": (LIT.publishedIn, XSD.gYear, False),
                "genre": (LIT.hasGenre, None, True),
                "language": (LIT.writtenInLanguage, None, True),
                "publisher": (LIT.hasPublisher, None, True),
                "setting": (LIT.hasSetting, None, True),
                "characters": (LIT.hasCharacter, None, True),
            },
            "Novel": {
                **common_map,
                "author": (LIT.writtenBy, None, True),
                "writtenBy": (LIT.writtenBy, None, True),
                "publicationDate": (LIT.publicationDate, XSD.date, False),
                "publishedIn": (LIT.publishedIn, XSD.gYear, False),
                "genre": (LIT.hasGenre, None, True),
                "language": (LIT.writtenInLanguage, None, True),
                "publisher": (LIT.hasPublisher, None, True),
                "setting": (LIT.hasSetting, None, True),
                "pageCount": (LIT.pageCount, XSD.integer, False),
            },
            "Genre": {
                **common_map,
            },
            "Location": {
                **common_map,
                "country": (LIT.locatedIn, None, True),
                "coordinates": (LIT.coordinates, XSD.string, False),
            },
            "LiteraryMovement": {
                **common_map,
                "startDate": (LIT.startDate, XSD.date, False),
                "endDate": (LIT.endDate, XSD.date, False),
                "country": (LIT.originCountry, None, True),
            },
            "Publisher": {
                **common_map,
                "foundedDate": (LIT.foundedDate, XSD.date, False),
                "headquarters": (LIT.headquartersLocation, None, True),
            },
            "Award": {
                **common_map,
                "forWork": (LIT.awardedFor, None, True),
            },
        }
        
        return type_maps.get(entity_type, common_map)
    
    def _infer_type_from_property(self, property_name: str) -> str:
        """Infer entity type from property name."""
        type_inference = {
            "birthPlace": "Location",
            "deathPlace": "Location",
            "citizenship": "Location",
            "author": "Author",
            "writtenBy": "Author",
            "influencedBy": "Author",
            "studentOf": "Author",
            "genre": "Genre",
            "hasGenre": "Genre",
            "publisher": "Publisher",
            "hasPublisher": "Publisher",
            "partOfMovement": "LiteraryMovement",
            "setting": "Location",
            "hasSetting": "Location",
            "awards": "Award",
            "receivedAward": "Award",
        }
        return type_inference.get(property_name, "Entity")
    
    def get_shapes_info(self) -> SHACLShapesInfo:
        """
        Get information about all SHACL shapes.
        
        Returns detailed information about each shape including:
        - Shape URI and name
        - Target class
        - Property constraints
        """
        if self._shapes_info is not None:
            return self._shapes_info
        
        shapes = []
        
        # Find all NodeShapes
        for shape_uri in self.shapes_graph.subjects(RDF.type, SH.NodeShape):
            shape_info = self._extract_shape_info(shape_uri)
            shapes.append(shape_info)
        
        self._shapes_info = SHACLShapesInfo(
            shapes=shapes,
            total_shapes=len(shapes),
            shapes_file=self.shapes_path
        )
        
        return self._shapes_info
    
    def _extract_shape_info(self, shape_uri: URIRef) -> SHACLShapeInfo:
        """Extract information about a single shape."""
        # Get basic info
        local_name = str(shape_uri).split("#")[-1] if "#" in str(shape_uri) else str(shape_uri).split("/")[-1]
        
        target_class = self.shapes_graph.value(shape_uri, SH.targetClass)
        label = self.shapes_graph.value(shape_uri, RDFS.label)
        description = self.shapes_graph.value(shape_uri, RDFS.comment)
        
        # Extract property constraints
        constraints = []
        property_count = 0
        
        for prop_shape in self.shapes_graph.objects(shape_uri, SH.property):
            property_count += 1
            constraint = self._extract_property_constraint(prop_shape)
            constraints.append(constraint)
        
        return SHACLShapeInfo(
            shape_uri=str(shape_uri),
            shape_name=local_name,
            target_class=str(target_class) if target_class else None,
            label=str(label) if label else None,
            description=str(description) if description else None,
            property_count=property_count,
            constraints=constraints
        )
    
    def _extract_property_constraint(self, prop_shape) -> dict[str, Any]:
        """Extract constraint details from a property shape."""
        constraint = {}
        
        # Path
        path = self.shapes_graph.value(prop_shape, SH.path)
        if path:
            path_str = str(path)
            constraint["path"] = path_str.split("#")[-1] if "#" in path_str else path_str
        
        # Cardinality
        min_count = self.shapes_graph.value(prop_shape, SH.minCount)
        max_count = self.shapes_graph.value(prop_shape, SH.maxCount)
        if min_count:
            constraint["minCount"] = int(min_count)
        if max_count:
            constraint["maxCount"] = int(max_count)
        
        # Datatype
        datatype = self.shapes_graph.value(prop_shape, SH.datatype)
        if datatype:
            dt_str = str(datatype)
            constraint["datatype"] = dt_str.split("#")[-1] if "#" in dt_str else dt_str
        
        # Class constraint
        class_constraint = self.shapes_graph.value(prop_shape, SH["class"])
        if class_constraint:
            cc_str = str(class_constraint)
            constraint["class"] = cc_str.split("#")[-1] if "#" in cc_str else cc_str
        
        # String constraints
        min_length = self.shapes_graph.value(prop_shape, SH.minLength)
        max_length = self.shapes_graph.value(prop_shape, SH.maxLength)
        pattern = self.shapes_graph.value(prop_shape, SH.pattern)
        if min_length:
            constraint["minLength"] = int(min_length)
        if max_length:
            constraint["maxLength"] = int(max_length)
        if pattern:
            constraint["pattern"] = str(pattern)
        
        # Numeric constraints
        min_inclusive = self.shapes_graph.value(prop_shape, SH.minInclusive)
        max_inclusive = self.shapes_graph.value(prop_shape, SH.maxInclusive)
        if min_inclusive:
            constraint["minInclusive"] = str(min_inclusive)
        if max_inclusive:
            constraint["maxInclusive"] = str(max_inclusive)
        
        # Severity and message
        severity = self.shapes_graph.value(prop_shape, SH.severity)
        message = self.shapes_graph.value(prop_shape, SH.message)
        if severity:
            sev_str = str(severity)
            constraint["severity"] = sev_str.split("#")[-1] if "#" in sev_str else sev_str
        if message:
            constraint["message"] = str(message)
        
        return constraint
    
    def get_shape_for_type(self, entity_type: str) -> SHACLShapeInfo | None:
        """Get shape information for a specific entity type."""
        shapes_info = self.get_shapes_info()
        shape_name = f"{entity_type}Shape"
        
        for shape in shapes_info.shapes:
            if shape.shape_name == shape_name:
                return shape
        
        return None
    
    def reload_shapes(self) -> None:
        """Reload shapes from file (useful after updates)."""
        self.shapes_graph = Graph()
        self._load_shapes()
        self._shapes_info = None
        logger.info("SHACL shapes reloaded")


# Singleton instance
_shacl_validator: SHACLValidator | None = None


def get_shacl_validator() -> SHACLValidator:
    """Get or create the singleton SHACL validator instance."""
    global _shacl_validator
    if _shacl_validator is None:
        _shacl_validator = SHACLValidator()
    return _shacl_validator
