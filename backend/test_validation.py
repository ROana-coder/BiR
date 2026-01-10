"""Test script for the ontology validation system."""

import sys
sys.path.insert(0, '.')

from app.services.schema_mapper import get_schema_mapper
from app.services.sparql_generator import get_sparql_generator
from app.services.response_validator import get_response_validator


def test_schema_mapper():
    """Test SchemaMapper functionality."""
    print("\n" + "="*60)
    print("Testing SchemaMapper")
    print("="*60)
    
    mapper = get_schema_mapper()
    schema = mapper.extract_mappings()
    
    print(f"\n✓ Extracted {schema.class_count} class mappings")
    print(f"✓ Extracted {schema.property_count} property mappings")
    
    # Test class mappings
    print("\nClass Mappings:")
    for cm in schema.class_mappings[:5]:
        print(f"  {cm.ontology_local:20} ↔ {cm.wikidata_id}")
    
    # Test property mappings
    print("\nProperty Mappings:")
    for pm in schema.property_mappings[:5]:
        print(f"  {pm.ontology_local:20} ({pm.property_type:16}) ↔ {pm.wikidata_id}")
    
    # Test translation
    print("\nTranslation Tests:")
    tests = [
        ("Author", "to_wikidata"),
        ("LiteraryWork", "to_wikidata"),
        ("writtenBy", "to_wikidata"),
        ("Q482980", "from_wikidata"),
        ("P50", "from_wikidata"),
    ]
    
    for identifier, direction in tests:
        if direction == "to_wikidata":
            result = mapper.translate_to_wikidata(identifier)
        else:
            result = mapper.translate_from_wikidata(identifier)
        print(f"  {identifier:15} → {result}")
    
    # Test expected properties
    print("\nExpected Properties for Author:")
    props = mapper.get_expected_properties_for_class("Author")
    for name, info in props.items():
        print(f"  {name:20} → {info['wikidata_property']} ({info['property_type']})")


def test_sparql_generator():
    """Test SPARQLGenerator functionality."""
    print("\n" + "="*60)
    print("Testing SPARQLGenerator")
    print("="*60)
    
    generator = get_sparql_generator()
    
    # Test author query
    print("\nAuthor Query (American authors):")
    query = generator.generate_author_query(country_qid="Q30", limit=5)
    print(query[:500] + "...")
    
    # Test work query
    print("\nWork Query (by Hemingway):")
    query = generator.generate_work_query(author_qid="Q23434", limit=5)
    print(query[:500] + "...")
    
    # Test influence query
    print("\nInfluence Graph Query:")
    query = generator.generate_influence_graph_query(center_qid="Q23434", limit=10)
    print(query[:500] + "...")
    
    # Test validation query
    print("\nValidation Query for Author Q23434:")
    query = generator.generate_validation_query("Author", "Q23434")
    print(query[:500] + "...")


def test_response_validator():
    """Test ResponseValidator functionality."""
    print("\n" + "="*60)
    print("Testing ResponseValidator")
    print("="*60)
    
    validator = get_response_validator()
    
    # Test valid author data
    print("\n1. Testing valid author data:")
    valid_author = {
        "qid": "Q23434",
        "birthDate": "1899-07-21",
        "birthPlace": "Q183287",
        "deathDate": "1961-07-02",
        "deathPlace": "Q47164",
        "citizenship": "Q30"
    }
    result = validator.validate_entity("Author", valid_author)
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count}")
    
    # Test author with missing properties
    print("\n2. Testing author with missing properties:")
    incomplete_author = {
        "qid": "Q150905",
        "birthDate": "1927-03-06"
    }
    result = validator.validate_entity("Author", incomplete_author)
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count}")
    for issue in result.issues[:3]:
        print(f"   [{issue.severity.value:7}] {issue.field}: {issue.message}")
    
    # Test author with invalid date format
    print("\n3. Testing author with questionable date format:")
    bad_date_author = {
        "qid": "Q12345",
        "birthDate": "1899",  # Year only
        "birthPlace": "Q183287"
    }
    result = validator.validate_entity("Author", bad_date_author)
    print(f"   Valid: {result.valid}")
    for issue in result.issues[:3]:
        print(f"   [{issue.severity.value:7}] {issue.field}: {issue.message}")
    
    # Test batch validation
    print("\n4. Testing batch validation:")
    authors = [
        {"qid": "Q23434", "birthDate": "1899-07-21", "citizenship": "Q30"},
        {"qid": "Q150905", "birthDate": "1927-03-06", "citizenship": "Q96"},
        {"qid": "Q36322", "birthDate": "1896-09-24", "citizenship": "Q30"},
    ]
    batch_result = validator.validate_batch("Author", authors)
    print(f"   Total: {batch_result.total_entities}")
    print(f"   Valid: {batch_result.valid_entities}")
    print(f"   Invalid: {batch_result.invalid_entities}")
    print(f"   Total Errors: {batch_result.total_errors}")
    print(f"   Total Warnings: {batch_result.total_warnings}")
    print(f"   Issue Summary: {batch_result.summary}")
    
    # Test literary work validation
    print("\n5. Testing literary work validation:")
    literary_work = {
        "qid": "Q173169",
        "writtenBy": "Q23434",
        "publicationDate": "1952-09-01",
        "hasGenre": "Q149537"
    }
    result = validator.validate_entity("LiteraryWork", literary_work)
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.error_count}, Warnings: {result.warning_count}, Info: {result.info_count}")


def test_summary():
    """Test getting entity type summary."""
    print("\n" + "="*60)
    print("Testing Entity Type Summary")
    print("="*60)
    
    mapper = get_schema_mapper()
    
    for entity_type in ["Author", "LiteraryWork", "Genre"]:
        class_mapping = mapper.get_class_mapping(entity_type)
        if class_mapping:
            props = mapper.get_expected_properties_for_class(entity_type)
            print(f"\n{entity_type}:")
            print(f"  Wikidata ID: {class_mapping.wikidata_id}")
            print(f"  Properties: {len(props)}")
            for name, info in list(props.items())[:3]:
                print(f"    - {name} ({info['wikidata_property']})")


if __name__ == "__main__":
    print("="*60)
    print("ONTOLOGY VALIDATION SYSTEM - TEST SUITE")
    print("="*60)
    
    test_schema_mapper()
    test_sparql_generator()
    test_response_validator()
    test_summary()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED!")
    print("="*60)
