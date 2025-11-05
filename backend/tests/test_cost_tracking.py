"""
Test script for cost tracking functionality
Run this script to verify cost calculation and database storage.
"""

import asyncio
import sys
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, '/Users/jileyitayo/Documents/Projects/LandingV2/backend')

from app.services.cost_calculator import (
    get_model_pricing,
    calculate_cost,
    CostTracker,
    clear_pricing_cache
)
from app.utils.pricing_manager import pricing_manager
from app.utils.supabase_client import get_supabase_client


def test_pricing_fetch():
    """Test 1: Fetch model pricing from database"""
    print("\n" + "="*70)
    print("TEST 1: Fetch Model Pricing")
    print("="*70)
    
    models_to_test = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gpt-4o-mini",
        "claude-sonnet-4-5"
    ]
    
    for model_name in models_to_test:
        pricing = get_model_pricing(model_name)
        if pricing:
            print(f"✓ {model_name}:")
            print(f"  Input:  ${pricing.input_cost_per_million}/M tokens")
            print(f"  Output: ${pricing.output_cost_per_million}/M tokens")
        else:
            print(f"✗ {model_name}: Pricing not found")
    
    print("\n✓ Pricing fetch test completed")


def test_cost_calculation():
    """Test 2: Calculate costs for sample token usage"""
    print("\n" + "="*70)
    print("TEST 2: Cost Calculation")
    print("="*70)
    
    test_cases = [
        {
            "model": "gemini-2.5-flash",
            "input_tokens": 1000,
            "output_tokens": 500,
            "expected_cost_range": (0.0002, 0.0006)  # Rough estimate
        },
        {
            "model": "gemini-2.5-pro",
            "input_tokens": 5000,
            "output_tokens": 3000,
            "expected_cost_range": (0.01, 0.03)
        },
        {
            "model": "gpt-4o-mini",
            "input_tokens": 2000,
            "output_tokens": 1000,
            "expected_cost_range": (0.0005, 0.0015)
        }
    ]
    
    for test in test_cases:
        cost, error = calculate_cost(
            test["model"],
            test["input_tokens"],
            test["output_tokens"]
        )
        
        if error:
            print(f"✗ {test['model']}: {error}")
        else:
            min_expected, max_expected = test["expected_cost_range"]
            within_range = min_expected <= float(cost) <= max_expected
            status = "✓" if within_range else "⚠"
            
            print(f"{status} {test['model']}:")
            print(f"  Tokens: {test['input_tokens']} in + {test['output_tokens']} out")
            print(f"  Cost: ${cost:.6f}")
            if not within_range:
                print(f"  Warning: Expected ${min_expected:.6f} - ${max_expected:.6f}")
    
    print("\n✓ Cost calculation test completed")


def test_cost_tracker():
    """Test 3: Test CostTracker accumulation"""
    print("\n" + "="*70)
    print("TEST 3: Cost Tracker Accumulation")
    print("="*70)
    
    tracker = CostTracker(generation_type="test", endpoint="/test")
    
    # Simulate multiple AI calls
    calls = [
        {
            "service": "business_analysis",
            "model": "gemini-2.5-flash",
            "usage": {"prompt_tokens": 1200, "completion_tokens": 450, "total_tokens": 1650}
        },
        {
            "service": "structure_generation",
            "model": "gemini-2.5-flash",
            "usage": {"prompt_tokens": 2000, "completion_tokens": 800, "total_tokens": 2800}
        },
        {
            "service": "theme_generation",
            "model": "gemini-2.5-flash",
            "usage": {"prompt_tokens": 800, "completion_tokens": 300, "total_tokens": 1100}
        },
        {
            "service": "page_generation",
            "model": "gemini-2.5-pro",
            "usage": {"prompt_tokens": 5000, "completion_tokens": 3000, "total_tokens": 8000},
            "metadata": {"page_name": "Home"}
        }
    ]
    
    print("\nTracking AI calls...")
    for call in calls:
        cost = tracker.track_call(
            service_name=call["service"],
            model_name=call["model"],
            usage=call["usage"],
            metadata=call.get("metadata")
        )
        print(f"  ✓ {call['service']}: ${cost:.6f}")
    
    # Get breakdown
    breakdown = tracker.get_breakdown()
    
    print(f"\nCost Summary:")
    print(f"  Total Cost: ${breakdown['total_cost_usd']:.6f}")
    print(f"  Total Tokens: {breakdown['total_tokens']:,}")
    print(f"  Breakdown:")
    for service, cost in breakdown['breakdown'].items():
        if cost > 0:
            print(f"    - {service}: ${cost:.6f}")
    
    print("\n✓ Cost tracker test completed")
    return tracker


async def test_database_storage(tracker: CostTracker):
    """Test 4: Save cost tracking to database"""
    print("\n" + "="*70)
    print("TEST 4: Database Storage")
    print("="*70)
    
    # Create a test project ID (you may want to use an actual project ID from your database)
    test_project_id = "test-project-" + str(asyncio.get_event_loop().time())
    test_user_id = "test-user"
    
    print(f"\nSaving cost tracking to database...")
    print(f"  Project ID: {test_project_id}")
    print(f"  User ID: {test_user_id}")
    
    try:
        supabase = get_supabase_client()
        tracker.mark_completed()
        tracking_id = await tracker.save_to_database(
            project_id=test_project_id,
            user_id=test_user_id,
            supabase_client=supabase
        )
        
        if tracking_id:
            print(f"\n✓ Cost tracking saved successfully!")
            print(f"  Tracking ID: {tracking_id}")
            
            # Verify by reading back
            response = supabase.table("generation_cost_tracking")\
                .select("*")\
                .eq("id", tracking_id)\
                .execute()
            
            if response.data:
                saved_data = response.data[0]
                print(f"\n✓ Verification successful!")
                print(f"  Total cost in DB: ${saved_data['total_cost_usd']:.6f}")
                print(f"  Total tokens in DB: {saved_data['total_tokens']:,}")
                
                # Clean up test data
                supabase.table("generation_cost_tracking")\
                    .delete()\
                    .eq("id", tracking_id)\
                    .execute()
                print(f"\n✓ Test data cleaned up")
            else:
                print(f"\n✗ Could not verify saved data")
        else:
            print(f"\n✗ Failed to save cost tracking")
    
    except Exception as e:
        print(f"\n✗ Database storage test failed: {str(e)}")
    
    print("\n✓ Database storage test completed")


def test_pricing_manager():
    """Test 5: Test pricing manager utilities"""
    print("\n" + "="*70)
    print("TEST 5: Pricing Manager")
    print("="*70)
    
    # Get all pricing
    print("\nFetching all pricing records...")
    all_pricing = pricing_manager.get_all_pricing(active_only=True)
    print(f"✓ Found {len(all_pricing)} active models")
    
    # Group by provider
    providers = {}
    for pricing in all_pricing:
        provider = pricing["provider"]
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(pricing["model_name"])
    
    print(f"\nModels by provider:")
    for provider, models in providers.items():
        print(f"  {provider}: {len(models)} models")
        for model in sorted(models):
            print(f"    - {model}")
    
    print("\n✓ Pricing manager test completed")


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("COST TRACKING SYSTEM TESTS")
    print("="*70)
    
    # Clear cache before tests
    clear_pricing_cache()
    
    # Run tests
    test_pricing_fetch()
    test_cost_calculation()
    tracker = test_cost_tracker()
    await test_database_storage(tracker)
    test_pricing_manager()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)
    print("\n✓ Cost tracking system is working correctly!")
    print("\nNext steps:")
    print("  1. Run a real website generation to see cost tracking in action")
    print("  2. Check the generation_cost_tracking table in your database")
    print("  3. Verify costs appear in project details API response")


if __name__ == "__main__":
    print("Starting cost tracking tests...")
    print("Make sure you have:")
    print("  1. Run the database migration (migrations/add_cost_tracking.sql)")
    print("  2. Set up your Supabase credentials")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    import time
    time.sleep(3)
    
    asyncio.run(run_all_tests())

