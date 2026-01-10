"""SPARQL Generator service for creating Wikidata queries from ontology schema."""

import logging
from typing import Any

from app.services.schema_mapper import get_schema_mapper, SchemaMapper

logger = logging.getLogger(__name__)


class SPARQLGenerator:
    """
    Generates Wikidata SPARQL queries based on ontology schema mappings.
    
    This service uses owl:equivalentProperty and owl:equivalentClass mappings
    to automatically generate valid Wikidata SPARQL queries that retrieve
    the properties defined in our ontology.
    
    De ce? (Why?)
    -------------
    În loc să scriem manual interogări SPARQL pentru Wikidata, folosim ontologia
    ca sursă unică de adevăr pentru structura datelor. Generator-ul traduce
    automat conceptele locale (lit:Author, lit:birthDate) în proprietăți Wikidata
    (wd:Q482980, wdt:P569), asigurând consistență și ușurința în întreținere.
    """
    
    # Wikidata SPARQL prefixes
    WIKIDATA_PREFIXES = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
"""
    
    def __init__(self, schema_mapper: SchemaMapper | None = None):
        """Initialize the SPARQL generator.
        
        Args:
            schema_mapper: Optional schema mapper instance (uses singleton if not provided)
        """
        self._mapper = schema_mapper or get_schema_mapper()
    
    def generate_entity_query(
        self,
        entity_type: str,
        qid: str | None = None,
        include_labels: bool = True,
        limit: int = 100
    ) -> str:
        """Generate a query to fetch an entity with all mapped properties.
        
        Args:
            entity_type: Ontology class name (e.g., 'Author', 'LiteraryWork')
            qid: Optional specific entity QID to fetch
            include_labels: Whether to include label service
            limit: Maximum results
            
        Returns:
            SPARQL query string for Wikidata
        """
        class_mapping = self._mapper.get_class_mapping(entity_type)
        if not class_mapping:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Get all properties for this class
        properties = self._mapper.get_properties_for_class(entity_type)
        
        # Build SELECT variables and patterns
        select_vars = ["?item", "?itemLabel"]
        patterns = []
        optionals = []
        
        # Main type constraint
        if qid:
            patterns.append(f"BIND(wd:{qid} AS ?item)")
        else:
            patterns.append(f"?item wdt:P31/wdt:P279* wd:{class_mapping.wikidata_id} .")
        
        # Add property patterns
        for prop in properties:
            var_name = f"?{prop.ontology_local}"
            select_vars.append(var_name)
            
            if prop.property_type == "ObjectProperty":
                # For object properties, also get the label
                label_var = f"?{prop.ontology_local}Label"
                select_vars.append(label_var)
                optionals.append(
                    f"OPTIONAL {{ ?item wdt:{prop.wikidata_id} {var_name} . }}"
                )
            else:
                optionals.append(
                    f"OPTIONAL {{ ?item wdt:{prop.wikidata_id} {var_name} . }}"
                )
        
        # Build query
        query_parts = [
            self.WIKIDATA_PREFIXES,
            f"SELECT DISTINCT {' '.join(select_vars)}",
            "WHERE {",
            "  " + "\n  ".join(patterns),
            "  " + "\n  ".join(optionals),
        ]
        
        if include_labels:
            query_parts.append('  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }')
        
        query_parts.append("}")
        query_parts.append(f"LIMIT {limit}")
        
        return "\n".join(query_parts)
    
    def generate_author_query(
        self,
        author_qid: str | None = None,
        country_qid: str | None = None,
        movement_qid: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> str:
        """Generate a query for authors with common filters.
        
        Args:
            author_qid: Specific author QID
            country_qid: Filter by country of citizenship (P27)
            movement_qid: Filter by literary movement (P135)
            year_start: Birth year start
            year_end: Birth year end
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            SPARQL query for Wikidata
        """
        # Get Author properties from schema
        author_props = self._mapper.get_expected_properties_for_class("Author")
        
        select_vars = [
            "?author", "?authorLabel", "?authorDescription",
            "?birthDate", "?deathDate",
            "?birthPlace", "?birthPlaceLabel",
            "?deathPlace", "?deathPlaceLabel",
            "?nationality", "?nationalityLabel",
            "?movement", "?movementLabel",
            "?image"
        ]
        
        patterns = []
        filters = []
        
        if author_qid:
            patterns.append(f"BIND(wd:{author_qid} AS ?author)")
        else:
            # Authors are instances of Q482980 (author) or Q36180 (writer)
            patterns.append("{ ?author wdt:P31 wd:Q482980 } UNION { ?author wdt:P106 wd:Q36180 }")
        
        # Standard optional properties based on schema mappings
        optionals = [
            "OPTIONAL { ?author wdt:P569 ?birthDate . }",  # P569 = birth date
            "OPTIONAL { ?author wdt:P570 ?deathDate . }",  # P570 = death date
            "OPTIONAL { ?author wdt:P19 ?birthPlace . }",  # P19 = birth place
            "OPTIONAL { ?author wdt:P20 ?deathPlace . }",  # P20 = death place
            "OPTIONAL { ?author wdt:P27 ?nationality . }",  # P27 = country of citizenship
            "OPTIONAL { ?author wdt:P135 ?movement . }",  # P135 = movement
            "OPTIONAL { ?author wdt:P18 ?image . }",  # P18 = image
        ]
        
        # Add filters
        if country_qid:
            patterns.append(f"?author wdt:P27 wd:{country_qid} .")
        
        if movement_qid:
            patterns.append(f"?author wdt:P135 wd:{movement_qid} .")
        
        if year_start:
            filters.append(f"YEAR(?birthDate) >= {year_start}")
        
        if year_end:
            filters.append(f"YEAR(?birthDate) <= {year_end}")
        
        # Build query
        query_parts = [
            self.WIKIDATA_PREFIXES,
            f"SELECT DISTINCT {' '.join(select_vars)}",
            "WHERE {",
            "  " + "\n  ".join(patterns),
            "  " + "\n  ".join(optionals),
        ]
        
        if filters:
            query_parts.append(f"  FILTER({' && '.join(filters)})")
        
        query_parts.append('  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }')
        query_parts.append("}")
        query_parts.append(f"LIMIT {limit}")
        
        if offset > 0:
            query_parts.append(f"OFFSET {offset}")
        
        return "\n".join(query_parts)
    
    def generate_work_query(
        self,
        work_qid: str | None = None,
        author_qid: str | None = None,
        genre_qid: str | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> str:
        """Generate a query for literary works with common filters.
        
        Args:
            work_qid: Specific work QID
            author_qid: Filter by author
            genre_qid: Filter by genre (P136)
            year_start: Publication year start
            year_end: Publication year end
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            SPARQL query for Wikidata
        """
        select_vars = [
            "?work", "?workLabel", "?workDescription",
            "?author", "?authorLabel",
            "?publicationDate",
            "?genre", "?genreLabel",
            "?narrativeLocation", "?narrativeLocationLabel",
            "?language", "?languageLabel"
        ]
        
        patterns = []
        filters = []
        
        if work_qid:
            patterns.append(f"BIND(wd:{work_qid} AS ?work)")
        else:
            # Literary works: Q7725634 or subclasses (novel Q8261, etc.)
            patterns.append("?work wdt:P31/wdt:P279* wd:Q7725634 .")
        
        optionals = [
            "OPTIONAL { ?work wdt:P50 ?author . }",  # P50 = author
            "OPTIONAL { ?work wdt:P577 ?publicationDate . }",  # P577 = publication date
            "OPTIONAL { ?work wdt:P136 ?genre . }",  # P136 = genre
            "OPTIONAL { ?work wdt:P840 ?narrativeLocation . }",  # P840 = narrative location
            "OPTIONAL { ?work wdt:P407 ?language . }",  # P407 = language of work
        ]
        
        # Add filters
        if author_qid:
            patterns.append(f"?work wdt:P50 wd:{author_qid} .")
        
        if genre_qid:
            patterns.append(f"?work wdt:P136 wd:{genre_qid} .")
        
        if year_start:
            filters.append(f"YEAR(?publicationDate) >= {year_start}")
        
        if year_end:
            filters.append(f"YEAR(?publicationDate) <= {year_end}")
        
        # Build query
        query_parts = [
            self.WIKIDATA_PREFIXES,
            f"SELECT DISTINCT {' '.join(select_vars)}",
            "WHERE {",
            "  " + "\n  ".join(patterns),
            "  " + "\n  ".join(optionals),
        ]
        
        if filters:
            query_parts.append(f"  FILTER({' && '.join(filters)})")
        
        query_parts.append('  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }')
        query_parts.append("}")
        query_parts.append(f"LIMIT {limit}")
        
        if offset > 0:
            query_parts.append(f"OFFSET {offset}")
        
        return "\n".join(query_parts)
    
    def generate_influence_graph_query(
        self,
        center_qid: str | None = None,
        depth: int = 2,
        limit: int = 200
    ) -> str:
        """Generate a query for author influence relationships.
        
        Args:
            center_qid: Optional center author QID
            depth: How many levels of influence to traverse
            limit: Maximum results
            
        Returns:
            SPARQL query for influence graph
        """
        if center_qid:
            # Get influences for a specific author
            return f"""{self.WIKIDATA_PREFIXES}
SELECT DISTINCT ?source ?sourceLabel ?target ?targetLabel ?relationship
WHERE {{
  BIND(wd:{center_qid} AS ?center)
  {{
    ?center wdt:P737 ?target .
    BIND(?center AS ?source)
    BIND("influencedBy" AS ?relationship)
  }} UNION {{
    ?source wdt:P737 ?center .
    BIND(?center AS ?target)
    BIND("influencedBy" AS ?relationship)
  }}
  ?source wdt:P31/wdt:P279* wd:Q5 .  # human
  ?target wdt:P31/wdt:P279* wd:Q5 .  # human
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}
LIMIT {limit}"""
        else:
            # Get general influence network among authors
            return f"""{self.WIKIDATA_PREFIXES}
SELECT DISTINCT ?source ?sourceLabel ?target ?targetLabel
WHERE {{
  ?source wdt:P737 ?target .
  ?source wdt:P106 wd:Q36180 .  # writer
  ?target wdt:P106 wd:Q36180 .  # writer
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}
LIMIT {limit}"""
    
    def generate_property_values_query(
        self,
        entity_qid: str,
        properties: list[str]
    ) -> str:
        """Generate a query to fetch specific properties for an entity.
        
        Args:
            entity_qid: Entity QID
            properties: List of ontology property names or Wikidata property IDs
            
        Returns:
            SPARQL query string
        """
        select_vars = ["?item"]
        optionals = []
        
        for prop in properties:
            # Translate to Wikidata if needed
            wd_prop = self._mapper.translate_to_wikidata(prop)
            if not wd_prop:
                wd_prop = prop  # Assume it's already a Wikidata ID
            
            var_name = f"?{prop.replace('P', 'prop_')}"
            select_vars.append(var_name)
            select_vars.append(f"{var_name}Label")
            optionals.append(f"OPTIONAL {{ ?item wdt:{wd_prop} {var_name} . }}")
        
        return f"""{self.WIKIDATA_PREFIXES}
SELECT {' '.join(select_vars)}
WHERE {{
  BIND(wd:{entity_qid} AS ?item)
  {chr(10).join(optionals)}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}"""
    
    def generate_validation_query(
        self,
        entity_type: str,
        entity_qid: str
    ) -> str:
        """Generate a query that fetches all expected properties for validation.
        
        This query returns all properties that the ontology expects for a given
        entity type, allowing the validator to check completeness and correctness.
        
        Args:
            entity_type: Ontology class name
            entity_qid: Wikidata QID of the entity
            
        Returns:
            SPARQL query for validation data
        """
        expected_props = self._mapper.get_expected_properties_for_class(entity_type)
        
        select_vars = ["?item", "?itemLabel"]
        optionals = []
        
        for prop_name, prop_info in expected_props.items():
            wd_prop = prop_info.get("wikidata_property")
            if wd_prop:
                var_name = f"?{prop_name}"
                select_vars.append(var_name)
                if prop_info.get("property_type") == "ObjectProperty":
                    select_vars.append(f"{var_name}Label")
                optionals.append(f"OPTIONAL {{ ?item wdt:{wd_prop} {var_name} . }}")
        
        return f"""{self.WIKIDATA_PREFIXES}
SELECT {' '.join(select_vars)}
WHERE {{
  BIND(wd:{entity_qid} AS ?item)
  {chr(10).join('  ' + opt for opt in optionals)}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
}}"""


# Singleton instance
_sparql_generator: SPARQLGenerator | None = None


def get_sparql_generator() -> SPARQLGenerator:
    """Get the singleton SPARQL generator instance."""
    global _sparql_generator
    if _sparql_generator is None:
        _sparql_generator = SPARQLGenerator()
    return _sparql_generator
