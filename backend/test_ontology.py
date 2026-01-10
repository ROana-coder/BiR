#!/usr/bin/env python3
"""Test script for the ontology."""

from rdflib import Graph

def main():
    g = Graph()
    g.parse("app/ontology/literature.ttl", format="turtle")
    print(f"Loaded {len(g)} triples")
    
    # Query authors
    results = list(g.query("""
        PREFIX lit: <http://literature-explorer.org/ontology#>
        SELECT ?name WHERE {
            ?author a lit:Author .
            ?author lit:name ?name .
        }
    """))
    
    print(f"\nFound {len(results)} authors:")
    for row in results:
        print(f"  - {row[0]}")

if __name__ == "__main__":
    main()
