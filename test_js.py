#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8001"

def test_page_content(url, description):
    print(f"\n🔍 Testing {description}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return False

        content = response.text

        # Check for basic HTML structure
        if "<!DOCTYPE html>" not in content:
            print("❌ No HTML DOCTYPE found")
            return False

        # Check for JavaScript includes
        if "/static/js/app.js" not in content:
            print("❌ app.js not included")
            return False

        # Check for specific page content
        if "parks" in url:
            if "parksGrid" not in content:
                print("❌ parksGrid element not found")
                return False
            print("✅ Parks page structure OK")

        elif "species" in url:
            if "speciesGrid" not in content:
                print("❌ speciesGrid element not found")
                return False
            print("✅ Species page structure OK")

        # Check for API calls in JavaScript
        if "window.API.getParks" not in content and "parks" in url:
            print("⚠️  API calls might not be working")

        print("✅ Page structure looks good")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_endpoints():
    print("\n🔌 Testing API Endpoints")

    endpoints = [
        "/api/parks",
        "/api/species",
        "/api/health"
    ]

    for endpoint in endpoints:
        try:
            url = BASE_URL + endpoint
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"✅ {endpoint}: {len(data)} items")
                else:
                    print(f"⚠️  {endpoint}: Empty response")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def test_static_files():
    print("\n📁 Testing Static Files")

    static_files = [
        "/static/css/main.css",
        "/static/js/app.js",
        "/static/js/enhanced-nav.js"
    ]

    for file_path in static_files:
        try:
            url = BASE_URL + file_path
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path}: Error - {e}")

if __name__ == "__main__":
    print("🚀 Testing Tunisia Parks Frontend")
    print("=" * 50)

    test_static_files()
    test_api_endpoints()

    # Test the problematic pages
    test_page_content(BASE_URL + "/parks", "Parks Page")
    test_page_content(BASE_URL + "/parks?sort_by=average_rating&sort_order=desc", "Parks Sorted Page")
    test_page_content(BASE_URL + "/parks?min_area=100", "Parks Filtered Page")
    test_page_content(BASE_URL + "/species", "Species Page")
    test_page_content(BASE_URL + "/species?type=animal", "Species Animal Page")
    test_page_content(BASE_URL + "/species?type=plant", "Species Plant Page")

    print("\n" + "=" * 50)
    print("🎯 Analysis Complete")
    print("\n💡 If pages show no interactive content, the issue is likely:")
    print("   1. JavaScript not loading/executing")
    print("   2. API calls failing")
    print("   3. DOM manipulation not working")
    print("   4. CSS not applying interactive styles")
