"""
Test React Website Generation
"""

import pytest
import asyncio
from app.services.react_website_generator import react_website_generator


def test_generate_react_website():
    """Test React website generation from a simple prompt"""
    
    prompt = "Create a photography website that has portfolio of a carosel of photos and a contact form. It should also include about section"
    
    # Generate website
    result = react_website_generator.generate_website_structure(prompt)
    
    # Verify structure
    assert "website_structure" in result
    assert "business_analysis" in result
    assert "files" in result
    
    website_structure = result["website_structure"]
    business_analysis = result["business_analysis"]
    files = result["files"]
    
    # Check business analysis
    assert business_analysis["business_type"]
    assert business_analysis["industry"]
    assert business_analysis["key_pages"]
    assert len(business_analysis["key_pages"]) > 0
    
    # Check website structure
    assert website_structure["name"]
    assert website_structure["pages"]
    assert len(website_structure["pages"]) > 0
    
    # Check files generated
    assert len(files) > 0
    assert "package.json" in files
    assert "src/App.tsx" in files
    assert "src/main.tsx" in files
    assert "index.html" in files
    
    # Check page files
    for page in website_structure["pages"]:
        page_filename = page["name"].lower().replace(" ", "-")
        assert f"src/pages/{page_filename}.tsx" in files
    
    print(f"\n✓ Generated {len(files)} files")
    print(f"✓ Files: {', '.join(files.keys())}")
    print(f"✓ Business Type: {business_analysis['business_type']}")
    print(f"✓ Pages: {', '.join([p['name'] for p in website_structure['pages']])}")
    print(f"✓ Website Name: {website_structure['name']}")


# def test_complex_react_website():
#     """Test React website generation with a more complex prompt"""
    
#     prompt = """
#     I need a professional website for my law firm specializing in family law.
#     We offer divorce consultation, child custody, and estate planning services.
#     The site should be professional, trustworthy, and easy to navigate.
#     Include a contact form and team member profiles.
#     """
    
#     result = react_website_generator.generate_website_structure(prompt)
    
#     website_structure = result["website_structure"]
#     business_analysis = result["business_analysis"]
    
#     # Verify business understanding
#     assert "law" in business_analysis["business_type"].lower() or "legal" in business_analysis["business_type"].lower()
#     assert "family law" in business_analysis["industry"].lower() or "legal" in business_analysis["industry"].lower()
    
#     # Verify appropriate pages
#     page_names = [p["name"].lower() for p in website_structure["pages"]]
#     assert any("home" in name for name in page_names)
#     assert any("service" in name or "practice" in name for name in page_names)
#     assert any("contact" in name for name in page_names)
    
#     print(f"\n✓ Law Firm Website Generated")
#     print(f"✓ Pages: {', '.join([p['name'] for p in website_structure['pages']])}")
#     print(f"✓ Key Pages: {', '.join(business_analysis['key_pages'])}")


# if __name__ == "__main__":
#     print("=" * 70)
#     print("TESTING REACT WEBSITE GENERATION")
#     print("=" * 70)
    
#     print("\n[TEST 1] Simple Coffee Shop Website")
#     print("-" * 70)
#     test_generate_react_website()
    
#     print("\n" + "=" * 70)
#     print("[TEST 2] Complex Law Firm Website")
#     print("-" * 70)
#     test_complex_react_website()
    
#     print("\n" + "=" * 70)
#     print("ALL TESTS PASSED ✓")
#     print("=" * 70)

