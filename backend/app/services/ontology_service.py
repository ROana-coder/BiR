"""Ontology service for querying local RDF/TTL files using RDFLib."""

import logging
from pathlib import Path
from typing import Any

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from rdflib.query import ResultRow
from rdflib.namespace import XSD, DC, DCTERMS, FOAF

logger = logging.getLogger(__name__)

# Define namespaces
LIT = Namespace("http://literature-explorer.org/ontology#")
SCHEMA = Namespace("http://schema.org/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")


class OntologyService:
    """Service for loading and querying local RDF ontologies with RDFLib."""
    
    def __init__(self, ontology_path: str | Path | None = None):
        """Initialize the ontology service.
        
        Args:
            ontology_path: Path to the TTL ontology file. 
                          Defaults to literature.ttl in the ontology directory.
        """
        self._graph = Graph()
        self._bind_namespaces()
        
        if ontology_path is None:
            # Default to the literature.ttl in the ontology directory
            ontology_path = Path(__file__).parent.parent / "ontology" / "literature.ttl"
        
        self._ontology_path = Path(ontology_path)
        self._loaded = False
    
    def _bind_namespaces(self) -> None:
        """Bind common namespace prefixes to the graph."""
        self._graph.bind("lit", LIT)
        self._graph.bind("schema", SCHEMA)
        self._graph.bind("dc", DC)
        self._graph.bind("dcterms", DCTERMS)
        self._graph.bind("foaf", FOAF)
        self._graph.bind("wd", WD)
        self._graph.bind("wdt", WDT)
        self._graph.bind("owl", OWL)
        self._graph.bind("rdf", RDF)
        self._graph.bind("rdfs", RDFS)
        self._graph.bind("xsd", XSD)
    
    def load(self) -> None:
        """Load the ontology from the TTL file."""
        if not self._ontology_path.exists():
            raise FileNotFoundError(f"Ontology file not found: {self._ontology_path}")
        
        self._graph.parse(str(self._ontology_path), format="turtle")
        self._loaded = True
        logger.info(f"Loaded ontology from {self._ontology_path} ({len(self._graph)} triples)")
    
    def ensure_loaded(self) -> None:
        """Ensure the ontology is loaded."""
        if not self._loaded:
            self.load()
    
    @property
    def graph(self) -> Graph:
        """Get the RDF graph."""
        self.ensure_loaded()
        return self._graph
    
    @property
    def triple_count(self) -> int:
        """Get the number of triples in the graph."""
        self.ensure_loaded()
        return len(self._graph)
    
    def _get_sparql_prefixes(self) -> str:
        """Get SPARQL prefix declarations for queries."""
        return """
            PREFIX lit: <http://literature-explorer.org/ontology#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX schema: <http://schema.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX foaf: <http://xmlns.com/foaf/0.1/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        """
    
    def query(self, sparql_query: str, add_prefixes: bool = True) -> list[dict[str, Any]]:
        """Execute a SPARQL query against the ontology.
        
        Args:
            sparql_query: A SPARQL SELECT query string.
            add_prefixes: Whether to automatically add namespace prefixes.
            
        Returns:
            List of dictionaries with variable bindings.
        """
        self.ensure_loaded()
        
        # Add prefixes if not already present and requested
        if add_prefixes and "PREFIX" not in sparql_query.upper():
            sparql_query = self._get_sparql_prefixes() + sparql_query
        
        try:
            results = self._graph.query(sparql_query)
            
            output = []
            for row in results:
                row_dict = {}
                for var in results.vars:
                    value = row[var]
                    if value is not None:
                        if isinstance(value, URIRef):
                            row_dict[str(var)] = {"type": "uri", "value": str(value)}
                        elif isinstance(value, Literal):
                            row_dict[str(var)] = {
                                "type": "literal",
                                "value": str(value),
                                "datatype": str(value.datatype) if value.datatype else None,
                                "language": value.language
                            }
                        else:
                            row_dict[str(var)] = {"type": "unknown", "value": str(value)}
                    else:
                        row_dict[str(var)] = None
                output.append(row_dict)
            
            return output
            
        except Exception as e:
            logger.error(f"SPARQL query error: {e}")
            raise ValueError(f"Invalid SPARQL query: {e}")
    
    def get_classes(self) -> list[dict[str, str]]:
        """Get all classes defined in the ontology.
        
        Returns:
            List of classes with URI, label, and comment.
        """
        query = """
            SELECT ?class ?label ?comment ?equivalent
            WHERE {
                ?class a owl:Class .
                OPTIONAL { ?class rdfs:label ?label . }
                OPTIONAL { ?class rdfs:comment ?comment . }
                OPTIONAL { ?class owl:equivalentClass ?equivalent . }
            }
            ORDER BY ?label
        """
        results = self.query(query)
        
        classes = []
        for row in results:
            classes.append({
                "uri": row.get("class", {}).get("value", ""),
                "label": row.get("label", {}).get("value", "") if row.get("label") else "",
                "comment": row.get("comment", {}).get("value", "") if row.get("comment") else "",
                "equivalent_class": row.get("equivalent", {}).get("value", "") if row.get("equivalent") else ""
            })
        
        return classes
    
    def get_properties(self) -> list[dict[str, str]]:
        """Get all properties (object and datatype) defined in the ontology.
        
        Returns:
            List of properties with URI, label, domain, range, and type.
        """
        query = """
            SELECT ?property ?label ?domain ?range ?type ?equivalent
            WHERE {
                {
                    ?property a owl:ObjectProperty .
                    BIND("ObjectProperty" AS ?type)
                } UNION {
                    ?property a owl:DatatypeProperty .
                    BIND("DatatypeProperty" AS ?type)
                }
                OPTIONAL { ?property rdfs:label ?label . }
                OPTIONAL { ?property rdfs:domain ?domain . }
                OPTIONAL { ?property rdfs:range ?range . }
                OPTIONAL { ?property owl:equivalentProperty ?equivalent . }
            }
            ORDER BY ?type ?label
        """
        results = self.query(query)
        
        properties = []
        for row in results:
            properties.append({
                "uri": row.get("property", {}).get("value", ""),
                "label": row.get("label", {}).get("value", "") if row.get("label") else "",
                "domain": row.get("domain", {}).get("value", "") if row.get("domain") else "",
                "range": row.get("range", {}).get("value", "") if row.get("range") else "",
                "type": row.get("type", {}).get("value", "") if row.get("type") else "",
                "equivalent_property": row.get("equivalent", {}).get("value", "") if row.get("equivalent") else ""
            })
        
        return properties
    
    def get_instances(self, class_uri: str | None = None) -> list[dict[str, str]]:
        """Get instances, optionally filtered by class.
        
        Args:
            class_uri: Optional URI of class to filter by.
            
        Returns:
            List of instances with URI, label, and class.
        """
        if class_uri:
            query = f"""
                SELECT ?instance ?label ?class
                WHERE {{
                    ?instance a <{class_uri}> .
                    BIND(<{class_uri}> AS ?class)
                    OPTIONAL {{ ?instance rdfs:label ?label . }}
                }}
                ORDER BY ?label
            """
        else:
            query = """
                SELECT ?instance ?label ?class
                WHERE {
                    ?instance a ?class .
                    ?class a owl:Class .
                    OPTIONAL { ?instance rdfs:label ?label . }
                }
                ORDER BY ?class ?label
            """
        
        results = self.query(query)
        
        instances = []
        for row in results:
            instances.append({
                "uri": row.get("instance", {}).get("value", ""),
                "label": row.get("label", {}).get("value", "") if row.get("label") else "",
                "class": row.get("class", {}).get("value", "") if row.get("class") else ""
            })
        
        return instances
    
    def get_authors(self) -> list[dict[str, Any]]:
        """Get all authors with their details.
        
        Returns:
            List of authors with name, dates, movements, etc.
        """
        query = """
            SELECT ?author ?name ?birthDate ?deathDate ?wikidataId 
                   (GROUP_CONCAT(DISTINCT ?movementLabel; separator=", ") AS ?movements)
            WHERE {
                ?author a lit:Author .
                OPTIONAL { ?author lit:name ?name . }
                OPTIONAL { ?author lit:birthDate ?birthDate . }
                OPTIONAL { ?author lit:deathDate ?deathDate . }
                OPTIONAL { ?author lit:wikidataId ?wikidataId . }
                OPTIONAL { 
                    ?author lit:partOfMovement ?movement . 
                    ?movement rdfs:label ?movementLabel .
                }
            }
            GROUP BY ?author ?name ?birthDate ?deathDate ?wikidataId
            ORDER BY ?name
        """
        results = self.query(query)
        
        authors = []
        for row in results:
            authors.append({
                "uri": row.get("author", {}).get("value", ""),
                "name": row.get("name", {}).get("value", "") if row.get("name") else "",
                "birth_date": row.get("birthDate", {}).get("value", "") if row.get("birthDate") else None,
                "death_date": row.get("deathDate", {}).get("value", "") if row.get("deathDate") else None,
                "wikidata_id": row.get("wikidataId", {}).get("value", "") if row.get("wikidataId") else "",
                "movements": row.get("movements", {}).get("value", "") if row.get("movements") else ""
            })
        
        return authors
    
    def get_literary_works(self) -> list[dict[str, Any]]:
        """Get all literary works with their details.
        
        Returns:
            List of works with title, author, year, genre, etc.
        """
        query = """
            SELECT ?work ?title ?authorName ?year ?genreLabel ?wikidataId
            WHERE {
                ?work a ?workType .
                ?workType rdfs:subClassOf* lit:LiteraryWork .
                OPTIONAL { ?work lit:title ?title . }
                OPTIONAL { 
                    ?work lit:writtenBy ?author . 
                    ?author lit:name ?authorName .
                }
                OPTIONAL { ?work lit:publicationYear ?year . }
                OPTIONAL { 
                    ?work lit:hasGenre ?genre . 
                    ?genre rdfs:label ?genreLabel .
                }
                OPTIONAL { ?work lit:wikidataId ?wikidataId . }
            }
            ORDER BY ?year ?title
        """
        results = self.query(query)
        
        works = []
        for row in results:
            works.append({
                "uri": row.get("work", {}).get("value", ""),
                "title": row.get("title", {}).get("value", "") if row.get("title") else "",
                "author": row.get("authorName", {}).get("value", "") if row.get("authorName") else "",
                "publication_year": row.get("year", {}).get("value", "") if row.get("year") else None,
                "genre": row.get("genreLabel", {}).get("value", "") if row.get("genreLabel") else "",
                "wikidata_id": row.get("wikidataId", {}).get("value", "") if row.get("wikidataId") else ""
            })
        
        return works
    
    def get_influence_graph(self) -> dict[str, Any]:
        """Get author influence relationships for graph visualization.
        
        Returns:
            Dict with nodes (authors) and edges (influence relationships).
        """
        # Get authors as nodes
        authors_query = """
            SELECT ?author ?name ?wikidataId
            WHERE {
                ?author a lit:Author .
                OPTIONAL { ?author lit:name ?name . }
                OPTIONAL { ?author lit:wikidataId ?wikidataId . }
            }
        """
        author_results = self.query(authors_query)
        
        nodes = []
        for row in author_results:
            nodes.append({
                "id": row.get("author", {}).get("value", ""),
                "label": row.get("name", {}).get("value", "") if row.get("name") else "",
                "wikidata_id": row.get("wikidataId", {}).get("value", "") if row.get("wikidataId") else ""
            })
        
        # Get influence relationships as edges
        influence_query = """
            SELECT ?source ?target ?sourceLabel ?targetLabel
            WHERE {
                ?source lit:influencedBy ?target .
                OPTIONAL { ?source lit:name ?sourceLabel . }
                OPTIONAL { ?target lit:name ?targetLabel . }
            }
        """
        influence_results = self.query(influence_query)
        
        edges = []
        for row in influence_results:
            edges.append({
                "source": row.get("source", {}).get("value", ""),
                "target": row.get("target", {}).get("value", ""),
                "source_label": row.get("sourceLabel", {}).get("value", "") if row.get("sourceLabel") else "",
                "target_label": row.get("targetLabel", {}).get("value", "") if row.get("targetLabel") else "",
                "relationship": "influencedBy"
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def get_raw_ttl(self) -> str:
        """Get the raw TTL content of the ontology file.
        
        Returns:
            The ontology serialized as Turtle.
        """
        self.ensure_loaded()
        return self._graph.serialize(format="turtle")
    
    def add_triple(self, subject: str, predicate: str, obj: str, is_literal: bool = False) -> None:
        """Add a triple to the graph.
        
        Args:
            subject: Subject URI
            predicate: Predicate URI
            obj: Object (URI or literal value)
            is_literal: Whether the object is a literal (vs URI)
        """
        self.ensure_loaded()
        
        subj_ref = URIRef(subject)
        pred_ref = URIRef(predicate)
        
        if is_literal:
            obj_ref = Literal(obj)
        else:
            obj_ref = URIRef(obj)
        
        self._graph.add((subj_ref, pred_ref, obj_ref))
        logger.info(f"Added triple: {subject} {predicate} {obj}")
    
    def save(self, path: str | Path | None = None) -> None:
        """Save the graph to a TTL file.
        
        Args:
            path: Output path. Defaults to the original ontology path.
        """
        if path is None:
            path = self._ontology_path
        
        self._graph.serialize(str(path), format="turtle")
        logger.info(f"Saved ontology to {path}")


# Singleton instance for the application
_ontology_service: OntologyService | None = None


def get_ontology_service() -> OntologyService:
    """Get the singleton ontology service instance."""
    global _ontology_service
    if _ontology_service is None:
        _ontology_service = OntologyService()
    return _ontology_service
