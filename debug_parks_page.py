#!/usr/bin/env python3
"""
Debug the parks page to see what's being rendered
"""

import requests

BASE_URL = "http://localhost:8001"

def debug_parks_page():
    """Debug what's happening on the parks page"""
    print("🔍 Debugging Parks Page Rendering")
    print("=" * 50)

    try:
        # Get the parks page
        response = requests.get(f"{BASE_URL}/parks", timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to load parks page: {response.status_code}")
            return

        html_content = response.text

        # Check for skeleton cards
        if 'skeleton' in html_content.lower():
            print("⚠️  Page contains skeleton loading cards")
        else:
            print("✅ No skeleton loading cards found")

        # Check for actual park cards
        card_count = html_content.count('class="card"')
        print(f"📋 Found {card_count} card elements")

        # Check for JavaScript errors or API calls
        if 'window.API' in html_content:
            print("✅ Frontend API code is present")
        else:
            print("❌ Frontend API code not found")

        # Check if images are in the HTML
        img_count = html_content.count('<img')
        print(f"🖼️  Found {img_count} image tags in HTML")

        # Check for specific park names in the HTML
        park_names = ["Ichkeul", "Chaambi", "Bouhedma", "Boukornine"]
        found_parks = []

        for park in park_names:
            if park in html_content:
                found_parks.append(park)

        if found_parks:
            print(f"✅ Found park names in HTML: {', '.join(found_parks)}")
        else:
            print("❌ No park names found in rendered HTML")

        # Check API directly
        print("\n🔌 Testing API directly:")
        api_response = requests.get(f"{BASE_URL}/api/parks", timeout=5)

        if api_response.status_code == 200:
            parks_data = api_response.json()
            print(f"✅ API returned {len(parks_data)} parks")

            if len(parks_data) > 0:
                first_park = parks_data[0]
                images = first_park.get('images', [])
                print(f"   First park has {len(images)} images")
                if images and len(images) > 0:
                    print(f"   Sample image URL: {images[0][:80]}...")
        else:
            print(f"❌ API failed: {api_response.status_code}")

    except Exception as e:
        print(f"❌ Error debugging parks page: {e}")

if __name__ == "__main__":
    debug_parks_page()
