#!/usr/bin/env python3
import requests
import time
import json

BASE_URL = "http://localhost:8001"

def check_page(url, expected_status=200, description=""):
    """Check a single page and return status"""
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == expected_status:
            status = f"✅ {description}: {response.status_code}"
            success = True
        else:
            status = f"❌ {description}: {response.status_code} (expected {expected_status})"
            success = False

        # Check for basic HTML structure
        content = response.text.lower()
        has_html = "<!doctype html>" in content or "<html" in content
        has_body = "<body" in content

        if has_html and has_body:
            status += " (HTML OK)"
        elif response.status_code == 200:
            status += " (⚠️  Missing HTML structure)"

        return success, status

    except requests.exceptions.RequestException as e:
        return False, f"❌ {description}: Connection failed - {str(e)}"

def check_api_endpoint(url, description=""):
    """Check an API endpoint"""
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    status = f"✅ {description}: {len(data)} items"
                elif isinstance(data, dict):
                    status = f"✅ {description}: OK ({len(data)} keys)"
                else:
                    status = f"✅ {description}: OK"
            except:
                status = f"✅ {description}: {response.status_code}"
            success = True
        else:
            status = f"❌ {description}: {response.status_code}"
            success = False

        return success, status

    except requests.exceptions.RequestException as e:
        return False, f"❌ {description}: Connection failed - {str(e)}"

def main():
    print("🌐 Comprehensive Localhost Page Check")
    print("=" * 60)

    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server health check: {health_response.status_code}")
    except:
        print("❌ Server not responding - make sure it's running on localhost:8001")
        return

    print("\n📄 Checking Frontend Pages:")
    print("-" * 30)

    frontend_pages = [
        ("/", "Home Page"),
        ("/parks", "Parks Page"),
        ("/species", "Species Page"),
        ("/trails", "Trails Page"),
        ("/comparison", "Comparison Page"),
        ("/emergency", "Emergency Page"),
        ("/chat", "Chat Page"),
        ("/upload", "Upload Page"),
        ("/map", "Map Page"),
    ]

    frontend_results = []
    for path, description in frontend_pages:
        success, status = check_page(BASE_URL + path, 200, description)
        print(status)
        frontend_results.append(success)

    print(f"\n📊 Frontend Summary: {sum(frontend_results)}/{len(frontend_results)} working")

    print("\n🔌 Checking API Endpoints:")
    print("-" * 30)

    api_endpoints = [
        ("/api/health", "Health Check"),
        ("/api/parks", "Parks API"),
        ("/api/species", "Species API"),
        ("/api/parks/compare", "Park Comparison API"),
    ]

    api_results = []
    for path, description in api_endpoints:
        success, status = check_api_endpoint(BASE_URL + path, description)
        print(status)
        api_results.append(success)

    # Test specific park and species endpoints
    try:
        parks_response = requests.get(f"{BASE_URL}/api/parks", timeout=5)
        if parks_response.status_code == 200:
            parks_data = parks_response.json()
            if len(parks_data) > 0:
                first_park_id = parks_data[0]['id']
                success, status = check_page(f"{BASE_URL}/parks/{first_park_id}", 200, "Individual Park Page")
                print(status)
                frontend_results.append(success)

                success, status = check_api_endpoint(f"{BASE_URL}/api/parks/{first_park_id}", "Individual Park API")
                print(status)
                api_results.append(success)
    except:
        print("❌ Could not test individual park endpoints")

    print(f"\n📊 API Summary: {sum(api_results)}/{len(api_results)} working")

    print("\n🎨 Checking Static Files:")
    print("-" * 30)

    static_files = [
        ("/static/css/main.css", "Main CSS"),
        ("/static/js/app.js", "Main JS"),
        ("/static/js/enhanced-nav.js", "Navigation JS"),
    ]

    static_results = []
    for path, description in static_files:
        success, status = check_page(BASE_URL + path, 200, description)
        print(status)
        static_results.append(success)

    print(f"\n📊 Static Files Summary: {sum(static_results)}/{len(static_results)} working")

    # Overall summary
    total_working = sum(frontend_results + api_results + static_results)
    total_total = len(frontend_results + api_results + static_results)

    print("\n" + "=" * 60)
    print(f"🎯 OVERALL SUMMARY: {total_working}/{total_total} components working")

    if total_working == total_total:
        print("🎉 All pages and APIs are working perfectly!")
    elif total_working >= total_total * 0.8:
        print("✅ Most components are working - minor issues detected")
    else:
        print("⚠️  Several issues detected - check the details above")

    print("\n🔗 Key URLs to test manually:")
    print(f"   🌐 Main Site: {BASE_URL}")
    print(f"   🏞️  Parks: {BASE_URL}/parks")
    print(f"   🦌 Species: {BASE_URL}/species")
    print(f"   🥾 Trails: {BASE_URL}/trails")
    print(f"   ⚖️  Compare: {BASE_URL}/comparison")
    print(f"   📊 API Docs: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
