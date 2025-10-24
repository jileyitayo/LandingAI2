"""
Test React Website Generation with Validation
"""

import pytest
from app.services.react_website_generator import react_website_generator
from app.services.deployments.vercel_deployer import VercelDeployer
from app.services.validators.code_validator import code_validator
from app.services.validators.build_tester import build_tester
from app.services.validators.error_fixer import error_fixer


def test_generate_react_website_with_validation():
    """Test React website generation with validation enabled"""
    
    prompt = "Create an ecommerce website for books"
    
    # Generate website with validation (but disable build validation for speed in tests)
    result = react_website_generator.generate_website_structure(
        prompt,
        enable_build_validation=False  # Disable for faster testing
    )
    
    # Verify structure
    assert "website_structure" in result
    assert "business_analysis" in result
    assert "files" in result
    assert "validation" in result
    assert "retry_count" in result
    assert "fixed_errors" in result
    assert "generation_time" in result
    
    website_structure = result["website_structure"]
    business_analysis = result["business_analysis"]
    files = result["files"]
    validation = result["validation"]
    
    # Check validation results
    assert validation["total_files_validated"] > 0
    print(f"\n✓ Validation: {validation['total_files_validated']} files validated")
    print(f"✓ Errors: {len(validation['errors'])}")
    print(f"✓ Warnings: {len(validation['warnings'])}")
    print(f"✓ Retries: {result['retry_count']}")
    print(f"✓ Fixed errors: {len(result['fixed_errors'])}")
    print(f"✓ Generation time: {result['generation_time']:.2f}s")
    
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
    print(f"✓ Business Type: {business_analysis['business_type']}")
    print(f"✓ Pages: {', '.join([p['name'] for p in website_structure['pages']])}")
    print(f"✓ Website Name: {website_structure['name']}")
    
    # Validation should pass or have minimal errors after auto-fix
    if validation["errors"]:
        print(f"\n⚠ Remaining validation errors:")
        for error in validation["errors"][:5]:  # Show first 5
            print(f"  - {error['file_path']}: {error['message']}")

    # print(f"\nDeploying website to Vercel...")
    # try:
    #     deployer = VercelDeployer()
    #     deployment = deployer.deploy(
    #         project_files=files,
    #         project_name=website_structure["name"]
    #     )
        
    #     # Optionally check deployment status
    #     deployment_id = deployment.get('id')
    #     status = deployer.get_deployment_status(deployment_id)
    #     print(f"\nDeployment Status: {status.get('readyState')}")

    #     # Wait for deployment to complete
    #     deployer.wait_for_deployment(deployment_id)
        
    #     print(f"✓ Website deployed to Vercel successfully")
        
    # except Exception as e:
    #     print(f"Deployment error: {e}")
    #     raise


# def test_generate_react_website():
#     """Test React website generation with deployment (original test)"""
    
#     prompt = "Create a photography website that has portfolio of a carousel of photos and a contact form. It should also include about section"
    
#     # Generate website (with validation but no build test for speed)
#     result = react_website_generator.generate_website_structure(
#         prompt,
#         enable_build_validation=False
#     )
    
#     website_structure = result["website_structure"]
#     files = result["files"]
    
#     print(f"\n✓ Generated {len(files)} files")
#     print(f"✓ Website Name: {website_structure['name']}")

#     print(f"\nDeploying website to Vercel...")
#     deployer = VercelDeployer()
#     try:
#         deployment = deployer.deploy(
#             project_files=files,
#             project_name=website_structure["name"]
#         )
        
#         # Optionally check deployment status
#         deployment_id = deployment.get('id')
#         status = deployer.get_deployment_status(deployment_id)
#         print(f"\nDeployment Status: {status.get('readyState')}")

#         # Wait for deployment to complete
#         deployer.wait_for_deployment(deployment_id)
        
#         print(f"✓ Website deployed to Vercel successfully")
        
#     except Exception as e:
#         print(f"Deployment error: {e}")
#         raise


# def test_code_validator():
#     """Test code validator with sample files"""
    
#     test_files = {
#         "src/components/Hero.tsx": """
# import { Button } from '@/components/ui/button'
# import { ArrowRight } from 'lucide-react'

# interface HeroProps {
#   title: string
#   subtitle?: string
# }

# export function Hero({ title, subtitle }: HeroProps) {
#   return (
#     <section className="hero">
#       <h1>{title}</h1>
#       {subtitle && <p>{subtitle}</p>}
#       <Button>Get Started <ArrowRight /></Button>
#     </section>
#   )
# }
# """,
#         "src/pages/home-page.tsx": """
# import { Hero } from '@/components/Hero'

# export default function HomePage() {
#   return (
#     <main>
#       <Hero title="Welcome" subtitle="My website" />
#     </main>
#   )
# }
# """,
#         "src/components/ui/button.tsx": """
# interface ButtonProps {
#   children: React.ReactNode
#   onClick?: () => void
# }

# export function Button({ children, onClick }: ButtonProps) {
#   return <button onClick={onClick}>{children}</button>
# }
# """
#     }
    
#     errors, warnings = code_validator.validate_all_files(test_files)
    
#     print(f"\n✓ Code validation test")
#     print(f"  Errors: {len(errors)}")
#     print(f"  Warnings: {len(warnings)}")
    
#     if errors:
#         print("  Error details:")
#         for error in errors[:3]:
#             print(f"    - {error}")
    
#     # Should have minimal or no errors in valid code
#     assert len(errors) < 5  # Allow some minor issues

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

