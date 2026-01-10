"""Schema Mapper service for extracting owl:equivalentClass/Property mappings from the ontology."""

import logging
import re
from typing import Any

from rdflib import Graph, Namespace, URIRef, OWL, RDFS, RDF

from app.models.validation import (
    ClassMapping, 
    PropertyMapping, 
    SchemaInfo
)
from app.services.ontology_service import get_ontology_service

logger = logging.getLogger(__name__)

# Define namespaces
LIT = Namespace("http://literature-explorer.org/ontology#")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")


class SchemaMapper:
    """
    Extracts schema mappings between the local ontology and Wikidata.
    
    This service parses owl:equivalentClass and owl:equivalentProperty
    statements to create bidirectional mappings that enable:
    - Generating SPARQL queries using Wikidata properties
    - Validating Wikidata responses against ontology constraints
    
    De ce? (Why?)
    -------------
    Ontologia locală definește schema semantică (TBox), dar datele vin de la Wikidata.
    SchemaMapper creează o "punte" între cele două vocabulare, permițând:
    1. Traducerea conceptelor locale în proprietăți Wikidata pentru interogări
    2. Validarea răspunsurilor Wikidata conform restricțiilor locale
    """
    
    def __init__(self):
        """Initialize the schema mapper."""
        self._ontology_service = get_ontology_service()
        self._schema_info: SchemaInfo | None = None
        self._class_constraints: dict[str, dict] = {}
        self._property_constraints: dict[str, dict] = {}
    
    @property
    def graph(self) -> Graph:
        """Get the ontology graph."""
        return self._ontology_service.graph
    
    def extract_mappings(self, force_refresh: bool = False) -> SchemaInfo:
        """Extract all class and property mappings from the ontology.
        
        Args:
            force_refresh: Force re-extraction even if cached
            
        Returns:
            SchemaInfo containing all mappings and indexes
        """
        if self._schema_info is not None and not force_refresh:
            return self._schema_info
        
        logger.info("Extracting schema mappings from ontology...")
        
        class_mappings = self._extract_class_mappings()
        property_mappings = self._extract_property_mappings()
        
        # Build indexes
        schema_info = SchemaInfo(
            class_mappings=class_mappings,
            property_mappings=property_mappings,
            class_count=len(class_mappings),
            property_count=len(property_mappings)
        )
        
        # Build lookup indexes
        for cm in class_mappings:
            schema_info.wikidata_to_ontology_class[cm.wikidata_id] = cm.ontology_uri
            schema_info.ontology_to_wikidata_class[cm.ontology_uri] = cm.wikidata_id
            schema_info.ontology_to_wikidata_class[cm.ontology_local] = cm.wikidata_id
        
        for pm in property_mappings:
            schema_info.wikidata_to_ontology_property[pm.wikidata_id] = pm.ontology_uri
            schema_info.ontology_to_wikidata_property[pm.ontology_uri] = pm.wikidata_id
            schema_info.ontology_to_wikidata_property[pm.ontology_local] = pm.wikidata_id
        
        self._schema_info = schema_info
        logger.info(f"Extracted {len(class_mappings)} class mappings and {len(property_mappings)} property mappings")
        
        return schema_info
    
    def _extract_class_mappings(self) -> list[ClassMapping]:
        """Extract owl:equivalentClass mappings."""
        query = """
            SELECT ?class ?equivalent ?label ?parent
            WHERE {
                ?class a owl:Class .
                ?class owl:equivalentClass ?equivalent .
                OPTIONAL { ?class rdfs:label ?label . }
                OPTIONAL { ?class rdfs:subClassOf ?parent . }
                FILTER(STRSTARTS(STR(?equivalent), "http://www.wikidata.org/entity/"))
            }
        """
        
        results = self._ontology_service.query(query)
        
        mappings = []
        for row in results:
            ontology_uri = row.get("class", {}).get("value", "")
            wikidata_uri = row.get("equivalent", {}).get("value", "")
            
            if ontology_uri and wikidata_uri:
                mappings.append(ClassMapping(
                    ontology_uri=ontology_uri,
                    ontology_local=self._extract_local_name(ontology_uri),
                    wikidata_uri=wikidata_uri,
                    wikidata_id=self._extract_wikidata_id(wikidata_uri),
                    label=row.get("label", {}).get("value") if row.get("label") else None,
                    parent_class=row.get("parent", {}).get("value") if row.get("parent") else None
                ))
        
        return mappings
    
    def _extract_property_mappings(self) -> list[PropertyMapping]:
        """Extract owl:equivalentProperty mappings."""
        query = """
            SELECT ?property ?equivalent ?label ?domain ?range ?type
            WHERE {
                {
                    ?property a owl:ObjectProperty .
                    BIND("ObjectProperty" AS ?type)
                } UNION {
                    ?property a owl:DatatypeProperty .
                    BIND("DatatypeProperty" AS ?type)
                }
                ?property owl:equivalentProperty ?equivalent .
                OPTIONAL { ?property rdfs:label ?label . }
                OPTIONAL { ?property rdfs:domain ?domain . }
                OPTIONAL { ?property rdfs:range ?range . }
                FILTER(STRSTARTS(STR(?equivalent), "http://www.wikidata.org/prop/direct/"))
            }
        """
        
        results = self._ontology_service.query(query)
        
        mappings = []
        for row in results:
            ontology_uri = row.get("property", {}).get("value", "")
            wikidata_uri = row.get("equivalent", {}).get("value", "")
            
            if ontology_uri and wikidata_uri:
                mappings.append(PropertyMapping(
                    ontology_uri=ontology_uri,
                    ontology_local=self._extract_local_name(ontology_uri),
                    wikidata_uri=wikidata_uri,
                    wikidata_id=self._extract_wikidata_property_id(wikidata_uri),
                    property_type=row.get("type", {}).get("value", ""),
                    domain=row.get("domain", {}).get("value") if row.get("domain") else None,
                    range=row.get("range", {}).get("value") if row.get("range") else None,
                    label=row.get("label", {}).get("value") if row.get("label") else None
                ))
        
        return mappings
    
    def _extract_local_name(self, uri: str) -> str:
        """Extract the local name from a URI."""
        if "#" in uri:
            return uri.split("#")[-1]
        return uri.split("/")[-1]
    
    def _extract_wikidata_id(self, uri: str) -> str:
        """Extract Wikidata QID from entity URI."""
        # http://www.wikidata.org/entity/Q482980 -> Q482980
        match = re.search(r'Q\d+$', uri)
        return match.group(0) if match else ""
    
    def _extract_wikidata_property_id(self, uri: str) -> str:
        """Extract Wikidata property ID from property URI."""
        # http://www.wikidata.org/prop/direct/P50 -> P50
        match = re.search(r'P\d+$', uri)
        return match.group(0) if match else ""
    
    def get_class_mapping(self, identifier: str) -> ClassMapping | None:
        """Get class mapping by ontology local name, URI, or Wikidata ID.
        
        Args:
            identifier: Class identifier (e.g., 'Author', 'Q482980', or full URI)
            
        Returns:
            ClassMapping if found, None otherwise
        """
        schema = self.extract_mappings()
        
        for cm in schema.class_mappings:
            if identifier in (cm.ontology_local, cm.ontology_uri, cm.wikidata_id, cm.wikidata_uri):
                return cm
        
        return None
    
    def get_property_mapping(self, identifier: str) -> PropertyMapping | None:
        """Get property mapping by ontology local name, URI, or Wikidata ID.
        
        Args:
            identifier: Property identifier (e.g., 'writtenBy', 'P50', or full URI)
            
        Returns:
            PropertyMapping if found, None otherwise
        """
        schema = self.extract_mappings()
        
        for pm in schema.property_mappings:
            if identifier in (pm.ontology_local, pm.ontology_uri, pm.wikidata_id, pm.wikidata_uri):
                return pm
        
        return None
    
    def get_properties_for_class(self, class_identifier: str) -> list[PropertyMapping]:
        """Get all properties that have a given class as their domain.
        
        Args:
            class_identifier: Class identifier
            
        Returns:
            List of property mappings with this class as domain
        """
        class_mapping = self.get_class_mapping(class_identifier)
        if not class_mapping:
            return []
        
        schema = self.extract_mappings()
        
        return [
            pm for pm in schema.property_mappings
            if pm.domain and (
                pm.domain == class_mapping.ontology_uri or 
                self._is_subclass_of(pm.domain, class_mapping.ontology_uri)
            )
        ]
    
    def _is_subclass_of(self, subclass_uri: str, superclass_uri: str) -> bool:
        """Check if one class is a subclass of another."""
        if subclass_uri == superclass_uri:
            return True
        
        query = f"""
            ASK WHERE {{
                <{subclass_uri}> rdfs:subClassOf+ <{superclass_uri}> .
            }}
        """
        try:
            results = self.graph.query(query)
            return bool(results)
        except Exception:
            return False
    
    def get_expected_properties_for_class(self, class_identifier: str) -> dict[str, dict]:
        """Get expected properties for a class with their constraints.
        
        Args:
            class_identifier: Class identifier (e.g., 'Author')
            
        Returns:
            Dict mapping property local names to their constraints
        """
        class_mapping = self.get_class_mapping(class_identifier)
        if not class_mapping:
            return {}
        
        properties = self.get_properties_for_class(class_identifier)
        
        result = {}
        for pm in properties:
            result[pm.ontology_local] = {
                "wikidata_property": pm.wikidata_id,
                "property_type": pm.property_type,
                "range": pm.range,
                "label": pm.label,
                "required": False  # Could be extended with cardinality constraints
            }
        
        return result
    
    def translate_to_wikidata(self, ontology_identifier: str) -> str | None:
        """Translate an ontology identifier to its Wikidata equivalent.
        
        Args:
            ontology_identifier: Local name or URI from the ontology
            
        Returns:
            Wikidata ID (Q-number or P-number) if mapping exists
        """
        # Try class mapping first
        class_mapping = self.get_class_mapping(ontology_identifier)
        if class_mapping:
            return class_mapping.wikidata_id
        
        # Try property mapping
        property_mapping = self.get_property_mapping(ontology_identifier)
        if property_mapping:
            return property_mapping.wikidata_id
        
        return None
    
    def translate_from_wikidata(self, wikidata_id: str) -> str | None:
        """Translate a Wikidata ID to its ontology equivalent.
        
        Args:
            wikidata_id: Wikidata Q-number or P-number
            
        Returns:
            Ontology local name if mapping exists
        """
        # Try class mapping first
        class_mapping = self.get_class_mapping(wikidata_id)
        if class_mapping:
            return class_mapping.ontology_local
        
        # Try property mapping
        property_mapping = self.get_property_mapping(wikidata_id)
        if property_mapping:
            return property_mapping.ontology_local
        
        return None
    
    def get_datatype_for_property(self, property_identifier: str) -> str | None:
        """Get the expected datatype for a property.
        
        Args:
            property_identifier: Property identifier
            
        Returns:
            XSD datatype URI or class URI for object properties
        """
        pm = self.get_property_mapping(property_identifier)
        if pm:
            return pm.range
        return None
    
    def get_domain_for_property(self, property_identifier: str) -> str | None:
        """Get the domain class for a property.
        
        Args:
            property_identifier: Property identifier
            
        Returns:
            Domain class URI
        """
        pm = self.get_property_mapping(property_identifier)
        if pm:
            return pm.domain
        return None


# Singleton instance
_schema_mapper: SchemaMapper | None = None


def get_schema_mapper() -> SchemaMapper:
    """Get the singleton schema mapper instance."""
    global _schema_mapper
    if _schema_mapper is None:
        _schema_mapper = SchemaMapper()
    return _schema_mapper
