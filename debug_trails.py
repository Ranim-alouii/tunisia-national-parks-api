#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8001"

def check_trails_api():
    print("🔍 Checking Trails API...")

    # Get all parks
    try:
        parks_response = requests.get(f"{BASE_URL}/api/parks", timeout=10)
        parks = parks_response.json()
        print(f"✅ Found {len(parks)} parks")

        total_trails = 0
        for park in parks[:5]:  # Check first 5 parks
            try:
                trails_response = requests.get(f"{BASE_URL}/api/parks/{park['id']}/trails", timeout=5)
                trails = trails_response.json()
                print(f"  🥾 Park {park['name']}: {len(trails)} trails")
                if len(trails) > 0:
                    for trail in trails[:2]:  # Show first 2 trails
                        print(f"    - {trail['name']} ({trail['difficulty']}) - {trail['length_km']}km")
                total_trails += len(trails)
            except Exception as e:
                print(f"  ❌ Error getting trails for {park['name']}: {e}")

        print(f"\n📊 Total trails found: {total_trails}")

        if total_trails == 0:
            print("❌ No trails found in database!")
            return False
        else:
            print("✅ Trails exist in database")
            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_page_content():
    print("\n🔍 Checking Trails Page Content...")

    try:
        response = requests.get(f"{BASE_URL}/trails", timeout=10)
        content = response.text

        # Check if basic structure exists
        checks = [
            ("DOCTYPE", "<!DOCTYPE html>" in content),
            ("HTML tag", "<html" in content),
            ("Trails grid", 'id="trailsGrid"' in content),
            ("Load more button", 'id="loadMoreBtn"' in content),
            ("JavaScript loadTrails function", "loadTrails()" in content),
        ]

        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")

        return all(result for _, result in checks)

    except Exception as e:
        print(f"❌ Error checking page content: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Debugging Trails Page Issues")
    print("=" * 50)

    api_ok = check_trails_api()
    page_ok = check_page_content()

    print("\n" + "=" * 50)
    if api_ok and page_ok:
        print("✅ Both API and page structure look good")
        print("💡 If trails aren't showing, the issue is likely in the JavaScript data processing")
        print("   Check browser console for JavaScript errors")
    else:
        print("❌ Issues found - check the details above")
