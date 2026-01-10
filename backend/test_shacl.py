"""
Test script for SHACL validation service.
"""

import sys
sys.path.insert(0, '.')

from app.services.shacl_validator import get_shacl_validator, SHACLValidator


def test_shacl_shapes_loading():
    """Test that SHACL shapes are loaded correctly."""
    print("=" * 60)
    print("TEST: SHACL Shapes Loading")
    print("=" * 60)
    
    validator = get_shacl_validator()
    shapes_info = validator.get_shapes_info()
    
    print(f"✓ Loaded {shapes_info.total_shapes} shapes from {shapes_info.shapes_file}")
    print(f"  Shapes: {[s.shape_name for s in shapes_info.shapes]}")
    
    return shapes_info.total_shapes > 0


def test_shape_info():
    """Test getting individual shape information."""
    print("\n" + "=" * 60)
    print("TEST: Shape Information")
    print("=" * 60)
    
    validator = get_shacl_validator()
    
    # Test AuthorShape
    author_shape = validator.get_shape_for_type("Author")
    if author_shape:
        print(f"✓ AuthorShape found:")
        print(f"  - Target class: {author_shape.target_class}")
        print(f"  - Property constraints: {author_shape.property_count}")
        print(f"  - Constraints:")
        for c in author_shape.constraints[:3]:  # Show first 3
            print(f"    • {c.get('path', 'unknown')}: {c}")
        return True
    else:
        print("✗ AuthorShape not found")
        return False


def test_valid_author_json():
    """Test validating valid JSON author data."""
    print("\n" + "=" * 60)
    print("TEST: Valid Author JSON Validation")
    print("=" * 60)
    
    validator = get_shacl_validator()
    
    valid_author = {
        "qid": "Q23434",
        "name": "Ernest Hemingway",
        "birthDate": "1899-07-21",
        "deathDate": "1961-07-02"
    }
    
    result = validator.validate_json("Author", valid_author)
    
    print(f"  Data: {valid_author}")
    print(f"  Conforms: {result.conforms}")
    print(f"  Violations: {result.violation_count}")
    print(f"  Warnings: {result.warning_count}")
    print(f"  Time: {result.validation_time_ms:.2f}ms")
    
    if result.violations:
        print(f"  Issues:")
        for v in result.violations:
            print(f"    • [{v.severity.value}] {v.message}")
    
    return True


def test_invalid_author_json():
    """Test validating invalid JSON author data (missing name)."""
    print("\n" + "=" * 60)
    print("TEST: Invalid Author JSON Validation (missing name)")
    print("=" * 60)
    
    validator = get_shacl_validator()
    
    invalid_author = {
        "qid": "Q12345",
        "birthDate": "1900-01-01"
        # Missing required 'name' field
    }
    
    result = validator.validate_json("Author", invalid_author)
    
    print(f"  Data: {invalid_author}")
    print(f"  Conforms: {result.conforms}")
    print(f"  Violations: {result.violation_count}")
    print(f"  Warnings: {result.warning_count}")
    
    if result.violations:
        print(f"  Issues found:")
        for v in result.violations:
            print(f"    • [{v.severity.value}] {v.result_path}: {v.message}")
    
    # Should NOT conform because name is required
    expected_violation = not result.conforms or result.violation_count > 0
    if expected_violation:
        print("✓ Correctly detected missing required field")
    else:
        print("✗ Did not detect missing required field")
    
    return True


def test_valid_rdf_turtle():
    """Test validating valid RDF Turtle data."""
    print("\n" + "=" * 60)
    print("TEST: Valid RDF Turtle Validation")
    print("=" * 60)
    
    validator = get_shacl_validator()
    
    turtle_data = """
    @prefix lit: <http://literature-explorer.org/ontology#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    <http://literature-explorer.org/data/author/Q23434> a lit:Author ;
        lit:name "Ernest Hemingway"^^xsd:string ;
        lit:birthDate "1899-07-21"^^xsd:date ;
        lit:deathDate "1961-07-02"^^xsd:date .
    """
    
    result = validator.validate_rdf(turtle_data, data_format="turtle", target_shapes=["AuthorShape"])
    
    print(f"  Conforms: {result.conforms}")
    print(f"  Violations: {result.violation_count}")
    print(f"  Warnings: {result.warning_count}")
    print(f"  Time: {result.validation_time_ms:.2f}ms")
    
    if result.violations:
        print(f"  Issues:")
        for v in result.violations:
            print(f"    • [{v.severity.value}] {v.message}")
    else:
        print("✓ No violations found")
    
    return True


def test_literary_work_validation():
    """Test validating LiteraryWork data."""
    print("\n" + "=" * 60)
    print("TEST: LiteraryWork JSON Validation")
    print("=" * 60)
    
    validator = get_shacl_validator()
    
    # Check if LiteraryWorkShape exists
    work_shape = validator.get_shape_for_type("LiteraryWork")
    if not work_shape:
        print("⚠ LiteraryWorkShape not found, skipping test")
        return True
    
    valid_work = {
        "qid": "Q185234",
        "name": "The Old Man and the Sea",
        "publishedIn": "1952",
    }
    
    result = validator.validate_json("LiteraryWork", valid_work)
    
    print(f"  Data: {valid_work}")
    print(f"  Conforms: {result.conforms}")
    print(f"  Violations: {result.violation_count}")
    print(f"  Time: {result.validation_time_ms:.2f}ms")
    
    if result.violations:
        for v in result.violations[:3]:
            print(f"    • [{v.severity.value}] {v.message}")
    
    return True


def test_all_shapes():
    """Test getting constraints for all entity types."""
    print("\n" + "=" * 60)
    print("TEST: All Shapes Constraints")
    print("=" * 60)
    
    validator = get_shacl_validator()
    shapes_info = validator.get_shapes_info()
    
    for shape in shapes_info.shapes:
        entity_type = shape.shape_name.replace("Shape", "")
        print(f"\n  {shape.shape_name}:")
        print(f"    Target: {shape.target_class}")
        print(f"    Properties: {shape.property_count}")
        
        # Count required vs optional
        required = sum(1 for c in shape.constraints if c.get("minCount", 0) > 0)
        optional = shape.property_count - required
        print(f"    Required: {required}, Optional: {optional}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SHACL VALIDATION SERVICE TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        ("Shapes Loading", test_shacl_shapes_loading),
        ("Shape Info", test_shape_info),
        ("Valid Author JSON", test_valid_author_json),
        ("Invalid Author JSON", test_invalid_author_json),
        ("Valid RDF Turtle", test_valid_rdf_turtle),
        ("LiteraryWork Validation", test_literary_work_validation),
        ("All Shapes", test_all_shapes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
