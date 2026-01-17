#!/usr/bin/env python3
"""
Quick API test script to verify the application is working
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, url, method="GET", data=None):
    """Test an API endpoint"""
    print(f"🔍 Testing {name}...")
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)

        print(f"   ✅ Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and len(str(data)) < 200:
                    print(f"   📄 Response: {data}")
                else:
                    print(f"   📄 Response: {type(data)} (length: {len(str(data))} chars)")
            except:
                print(f"   📄 Response: {response.text[:100]}...")
        else:
            print(f"   ❌ Error: {response.text[:100]}...")

        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Tunisia National Parks API")
    print("=" * 50)

    # Wait a moment for server to be ready
    time.sleep(2)

    tests = [
        ("Health Check", f"{BASE_URL}/api/health"),
        ("Parks List", f"{BASE_URL}/api/parks?limit=3"),
        ("Species List", f"{BASE_URL}/api/species?limit=3"),
        ("Homepage", f"{BASE_URL}/"),
        ("Parks Page", f"{BASE_URL}/parks"),
        ("Species Page", f"{BASE_URL}/species"),
        ("Upload Page", f"{BASE_URL}/upload"),
        ("API Docs", f"{BASE_URL}/docs"),
    ]

    passed = 0
    total = len(tests)

    for name, url in tests:
        if test_endpoint(name, url):
            passed += 1
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! The application is working perfectly.")
        print()
        print("🌐 Access your application at:")
        print(f"   • Homepage: {BASE_URL}")
        print(f"   • API Docs: {BASE_URL}/docs")
        print(f"   • Parks: {BASE_URL}/parks")
        print(f"   • Species: {BASE_URL}/species")
        print(f"   • Upload Images: {BASE_URL}/upload")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")

if __name__ == "__main__":
    main()
