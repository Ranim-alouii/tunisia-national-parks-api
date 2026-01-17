#!/usr/bin/env python3
import requests
import sys

BASE_URL = "http://localhost:8001"

pages_to_test = [
    "/",
    "/parks",
    "/species",
    "/trails",
    "/comparison",
    "/emergency",
    "/chat",
    "/upload",
    "/map"
]

print("Testing all localhost pages...")
print("=" * 50)

for page in pages_to_test:
    try:
        url = BASE_URL + page
        response = requests.get(url, timeout=10)
        status = f"✅ {response.status_code}" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{page:<12} {status}")
    except requests.exceptions.RequestException as e:
        print(f"{page:<12} ❌ ERROR: {str(e)[:50]}")

print("\nTesting API endpoints...")
print("=" * 30)

api_endpoints = [
    "/api/parks",
    "/api/species",
    "/api/health",
    "/api/languages",
    "/api/badges"
]

for endpoint in api_endpoints:
    try:
        url = BASE_URL + endpoint
        response = requests.get(url, timeout=10)
        status = f"✅ {response.status_code}" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{endpoint:<15} {status}")
    except requests.exceptions.RequestException as e:
        print(f"{endpoint:<15} ❌ ERROR: {str(e)[:50]}")

print("\nTesting park detail pages...")
print("=" * 30)

# Test a few park detail pages if parks exist
try:
    parks_response = requests.get(BASE_URL + "/api/parks", timeout=10)
    if parks_response.status_code == 200:
        parks_data = parks_response.json()
        if parks_data and len(parks_data) > 0:
            # Test first 3 parks
            for i, park in enumerate(parks_data[:3]):
                park_url = f"/parks/{park['id']}"
                try:
                    response = requests.get(BASE_URL + park_url, timeout=10)
                    status = f"✅ {response.status_code}" if response.status_code == 200 else f"❌ {response.status_code}"
                    print(f"{park_url:<15} {status}")
                except requests.exceptions.RequestException as e:
                    print(f"{park_url:<15} ❌ ERROR: {str(e)[:50]}")
        else:
            print("No parks found in database")
    else:
        print("Could not fetch parks list")
except Exception as e:
    print(f"Error testing park details: {e}")

print("\nTesting static files...")
print("=" * 25)

static_files = [
    "/static/css/main.css",
    "/static/js/app.js",
    "/static/js/enhanced-nav.js"
]

for static_file in static_files:
    try:
        url = BASE_URL + static_file
        response = requests.get(url, timeout=10)
        status = f"✅ {response.status_code}" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{static_file:<25} {status}")
    except requests.exceptions.RequestException as e:
        print(f"{static_file:<25} ❌ ERROR: {str(e)[:50]}")

print("\n" + "=" * 50)
print("Page testing complete!")
