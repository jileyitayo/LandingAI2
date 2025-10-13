"""
Test Improved React Website Generator
Tests the enhanced generator with validation and error prevention.
"""
# -*- coding: utf-8 -*-

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.react_website_generator import react_website_generator
from app.services.icon_validator import is_valid_icon, get_safe_icons
from app.services.code_validator import code_validator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_icon_validator():
    """Test the icon validator"""
    print("\n" + "="*80)
    print("TEST 1: Icon Validator")
    print("="*80)
    
    # Test valid icons
    valid_icons = ["ArrowRight", "Mail", "Phone", "User", "Heart"]
    print("\nTesting valid icons:")
    for icon in valid_icons:
        result = is_valid_icon(icon)
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {icon}: {result}")
    
    # Test invalid icons
    invalid_icons = ["Handshake", "InvalidIcon", "FakeIcon"]
    print("\nTesting invalid icons (should be False):")
    for icon in invalid_icons:
        result = is_valid_icon(icon)
        status = "[OK]" if not result else "[FAIL]"
        print(f"  {status} {icon}: {result}")
    
    # Get safe icons count
    safe_icons = get_safe_icons()
    print(f"\nTotal safe icons available: {len(safe_icons)}")
    print(f"Example icons: {', '.join(safe_icons[:10])}")


def test_code_validator():
    """Test the code validator"""
    print("\n" + "="*80)
    print("TEST 2: Code Validator")
    print("="*80)
    
    # Test with code that has invalid icons
    test_code = """
import React from 'react'
import { Handshake, Heart } from 'lucide-react'

export function TestComponent() {
    return <div>Test</div>
}
"""
    
    print("\nTesting code with invalid icons:")
    validator = code_validator
    validator.errors = []
    validator.warnings = []
    validator._validate_typescript_file("test.tsx", test_code)
    
    print(f"Errors found: {len(validator.errors)}")
    for error in validator.errors:
        print(f"  - {error}")
    
    # Test with duplicate exports
    duplicate_export_code = """
export function MyComponent() {
    return <div>Test</div>
}

export default MyComponent
"""
    
    print("\nTesting code with duplicate exports:")
    validator.errors = []
    validator._validate_typescript_file("test2.tsx", duplicate_export_code)
    
    print(f"Errors found: {len(validator.errors)}")
    for error in validator.errors:
        print(f"  - {error}")


def test_website_generation(prompt: str, test_name: str):
    """Test complete website generation"""
    print("\n" + "="*80)
    print(f"TEST: {test_name}")
    print("="*80)
    print(f"Prompt: {prompt}")
    print("-"*80)
    
    try:
        # Generate website
        result = react_website_generator.generate_website_structure(prompt)
        
        # Get results
        website_structure = result['website_structure']
        files = result['files']
        
        print(f"\n[SUCCESS] Generation successful!")
        print(f"Website Name: {website_structure['name']}")
        print(f"Pages: {len(website_structure['pages'])}")
        print(f"Files Generated: {len(files)}")
        
        # List page names
        print("\nPages generated:")
        for page in website_structure['pages']:
            print(f"  - {page['name']} ({page['path']})")
        
        # List component files
        component_files = [f for f in files.keys() if f.startswith('src/components/') and not f.startswith('src/components/ui/')]
        print(f"\nSection components ({len(component_files)}):")
        for comp in sorted(component_files)[:10]:
            print(f"  - {comp}")
        if len(component_files) > 10:
            print(f"  ... and {len(component_files) - 10} more")
        
        # Check for icon imports
        print("\nValidating lucide-react icon imports...")
        icon_issues = []
        for file_path, content in files.items():
            if 'lucide-react' in content:
                # Extract icon imports
                import re
                matches = re.findall(r'import\s+\{([^}]+)\}\s+from\s+[\'"]lucide-react[\'"]', content)
                for match in matches:
                    icons = [icon.strip() for icon in match.split(',')]
                    for icon in icons:
                        if icon and not is_valid_icon(icon):
                            icon_issues.append(f"{file_path}: Invalid icon '{icon}'")
        
        if icon_issues:
            print(f"  [FAIL] Found {len(icon_issues)} icon issues:")
            for issue in icon_issues[:5]:
                print(f"    - {issue}")
        else:
            print("  [PASS] All icons are valid!")
        
        # Check for export/import consistency
        print("\nValidating exports and imports...")
        validator = code_validator
        errors, warnings = validator.validate_all_files(files)
        
        if errors:
            print(f"  [FAIL] Found {len(errors)} validation errors:")
            for error in errors[:5]:
                print(f"    - {error}")
        else:
            print("  [PASS] No validation errors!")
        
        if warnings:
            print(f"  [WARN] Found {len(warnings)} warnings:")
            for warning in warnings[:3]:
                print(f"    - {warning}")
        
        # Summary
        print("\n" + "-"*80)
        if not icon_issues and not errors:
            print("[PASS] TEST PASSED - No critical errors found!")
        else:
            print(f"[FAIL] TEST FAILED - Found {len(icon_issues)} icon issues and {len(errors)} validation errors")
        
        return len(icon_issues) == 0 and len(errors) == 0
        
    except Exception as e:
        print(f"\n[ERROR] Generation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("="*80)
    print("IMPROVED REACT GENERATOR - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Test 1: Icon Validator
    test_icon_validator()
    
    # Test 2: Code Validator
    test_code_validator()
    
    # Test 3: Generate a coffee shop website
    test_3_result = test_website_generation(
        "Create a modern coffee shop website",
        "Coffee Shop Website"
    )
    
    # Test 4: Generate a law firm website
    test_4_result = test_website_generation(
        "Create a professional family law firm website with services, team, and contact pages",
        "Law Firm Website"
    )
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    print(f"Coffee Shop Test: {'[PASSED]' if test_3_result else '[FAILED]'}")
    print(f"Law Firm Test: {'[PASSED]' if test_4_result else '[FAILED]'}")
    
    if test_3_result and test_4_result:
        print("\n*** ALL TESTS PASSED! ***")
        print("The improved generator is producing error-free code!")
    else:
        print("\n[WARNING] SOME TESTS FAILED")
        print("Review the errors above and make necessary adjustments.")
    
    print("="*80)


if __name__ == "__main__":
    main()

