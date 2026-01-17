#!/usr/bin/env python3
"""
Simple script to test the frontend functionality
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_api_parks():
    """Test parks API"""
    try:
        response = requests.get(f"{BASE_URL}/api/parks")
        print(f"Parks API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Found {len(data)} parks")
            if data:
                park = data[0]
                print(f"  Sample park: {park.get('name')} ({park.get('governorate')})")
        return response.status_code == 200
    except Exception as e:
        print(f"Parks API failed: {e}")
        return False

def test_api_species():
    """Test species API"""
    try:
        response = requests.get(f"{BASE_URL}/api/species")
        print(f"Species API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Found {len(data)} species")
            if data:
                species = data[0]
                print(f"  Sample species: {species.get('name')} ({species.get('type')})")
        return response.status_code == 200
    except Exception as e:
        print(f"Species API failed: {e}")
        return False

def test_homepage():
    """Test homepage loading"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Homepage: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if "<!DOCTYPE html>" in content:
                print("  HTML content detected")
            if "Parcs Nationaux" in content:
                print("  Page title found")
            if "/static/css/main.css" in content:
                print("  CSS link found")
            if "/static/js/" in content:
                print("  JavaScript links found")
        return response.status_code == 200
    except Exception as e:
        print(f"Homepage failed: {e}")
        return False

def test_static_files():
    """Test static file serving"""
    try:
        response = requests.get(f"{BASE_URL}/static/css/main.css")
        print(f"CSS file: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if "/* Main CSS file */" in content or len(content) > 1000:
                print("  CSS content loaded successfully")
        return response.status_code == 200
    except Exception as e:
        print(f"CSS file failed: {e}")
        return False

def main():
    print("=== Frontend Testing Script ===")
    print(f"Testing server at: {BASE_URL}")
    print()

    # Wait a bit for server to be ready
    time.sleep(2)

    tests = [
        ("Health Check", test_health),
        ("Parks API", test_api_parks),
        ("Species API", test_api_species),
        ("Homepage", test_homepage),
        ("Static Files", test_static_files),
    ]

    results = []
    for name, test_func in tests:
        print(f"Testing {name}...")
        result = test_func()
        results.append((name, result))
        print(f"  Result: {'✅ PASS' if result else '❌ FAIL'}")
        print()

    print("=== Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Frontend is working correctly.")
        print("You can now open http://127.0.0.1:8001 in your browser to view the application.")
    else:
        print("⚠️  Some tests failed. Check the server logs for more details.")

if __name__ == "__main__":
    main()
