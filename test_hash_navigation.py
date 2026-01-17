#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://localhost:8001"

def test_hash_navigation():
    """Test hash-based navigation on trails page"""
    print("🧭 Testing Hash Navigation on Trails Page")
    print("=" * 50)

    # Test basic trails page
    try:
        response = requests.get(f"{BASE_URL}/trails", timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            print("✅ Trails page loads successfully")

            # Check for safety section
            if 'id="safety"' in content:
                print("✅ Safety section (#safety) exists in HTML")
            else:
                print("❌ Safety section (#safety) not found")

            # Check for conservation section
            if 'id="conservation"' in content:
                print("✅ Conservation section (#conservation) exists in HTML")
            else:
                print("❌ Conservation section (#conservation) not found")

            # Check for hash navigation JavaScript
            if 'handlehashnavigation' in content:
                print("✅ Hash navigation JavaScript function exists")
            else:
                print("❌ Hash navigation JavaScript not found")

            # Check for hashchange event listener
            if 'hashchange' in content:
                print("✅ Hash change event listener exists")
            else:
                print("❌ Hash change event listener not found")

        else:
            print(f"❌ Trails page failed to load: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing trails page: {e}")
        return False

    print("\n🔗 Hash Navigation URLs to Test:")
    print(f"   🌐 Main Trails: {BASE_URL}/trails")
    print(f"   🛡️  Safety: {BASE_URL}/trails#safety")
    print(f"   🌿 Conservation: {BASE_URL}/trails#conservation")

    print("\n💡 Manual Testing Instructions:")
    print("   1. Open browser and navigate to the trails page")
    print("   2. Try appending #safety to the URL")
    print("   3. Try appending #conservation to the URL")
    print("   4. Page should smoothly scroll to the respective sections")

    return True

if __name__ == "__main__":
    test_hash_navigation()
