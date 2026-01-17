#!/usr/bin/env python3
"""
Test SerpApi as alternative to Google Places API
"""

import requests

# Your SerpApi key
SERP_API_KEY = "1e837cf0e27189e6710cd79e40350fd86b350d6b9ea1808b26c0443529784ea5"

def test_serpapi_google_places():
    """Test if SerpApi can provide Google Places data"""

    print("🔍 Testing SerpApi for Google Places functionality")
    print("=" * 60)

    # Test Google Places API via SerpApi
    # SerpApi supports Google Places through their API
    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_maps",
        "q": "parks near Tunis, Tunisia",
        "ll": "@36.8065,10.1815,15z",  # Latitude, Longitude, Zoom
        "type": "search",
        "api_key": SERP_API_KEY
    }

    try:
        print("📍 Testing Google Maps search via SerpApi...")
        response = requests.get(url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ SerpApi request successful!")

            # Check what data we got
            if 'local_results' in data:
                results = data['local_results']
                print(f"📊 Found {len(results)} local results")

                if results:
                    print("\n🏞️ Sample Results:")
                    for i, result in enumerate(results[:3]):
                        print(f"  {i+1}. {result.get('title', 'Unknown')}")
                        print(f"     Rating: {result.get('rating', 'N/A')}")
                        print(f"     Address: {result.get('address', 'N/A')[:50]}...")

                    return True
            else:
                print("❌ No local_results in response")
                print("Available keys:", list(data.keys()))
                return False
        else:
            print(f"❌ SerpApi request failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False

    except Exception as e:
        print(f"❌ Error testing SerpApi: {e}")
        return False

def test_serpapi_alternatives():
    """Test other SerpApi functionalities that might be useful"""

    print("\n🔄 Testing other SerpApi capabilities...")

    # Test Google Images (could replace Unsplash)
    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_images",
            "q": "Tunisia national park nature landscape",
            "api_key": SERP_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'images_results' in data:
                print(f"✅ SerpApi Google Images: {len(data['images_results'])} images found")
            else:
                print("⚠️ SerpApi Google Images: Limited results")
    except Exception as e:
        print(f"❌ SerpApi Google Images failed: {e}")

def main():
    """Test SerpApi functionality"""
    print("🧪 Testing SerpApi Key: 1e837cf0e27189e27189e6710cd79e40350fd86b350d6b9ea1808b26c0443529784ea5")
    print("=" * 80)

    # Test account status first
    try:
        url = "https://serpapi.com/account"
        params = {"api_key": SERP_API_KEY}

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            account_data = response.json()
            print("📊 SerpApi Account Status:")
            print(f"   Plan: {account_data.get('plan_name', 'Unknown')}")
            print(f"   Searches Left: {account_data.get('searches_left', 'Unknown')}")
            print(f"   Searches Used: {account_data.get('searches_used', 'Unknown')}")
        else:
            print("⚠️ Could not check account status")
    except Exception as e:
        print(f"⚠️ Account status check failed: {e}")

    print()

    # Test main functionality
    places_working = test_serpapi_google_places()
    test_serpapi_alternatives()

    print("\n" + "=" * 80)
    print("🎯 VERDICT:")

    if places_working:
        print("✅ **SerpApi CAN replace Google Places API!**")
        print("   • Provides Google Maps local search results")
        print("   • Returns places with ratings, addresses, etc.")
        print("   • Can be integrated into your existing code")
        print("\n💡 Recommendation: Use SerpApi for Google Places functionality")
    else:
        print("❌ **SerpApi cannot fully replace Google Places API**")
        print("   • May need different parameters or engine")
        print("   • Consider OpenStreetMap alternative instead")

    print(f"\n🔑 Your SerpApi Key: {SERP_API_KEY}")
    print("💰 SerpApi Pricing: Starts at $1 for 100 searches")

if __name__ == "__main__":
    main()
