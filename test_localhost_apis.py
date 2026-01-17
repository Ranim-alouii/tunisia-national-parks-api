#!/usr/bin/env python3
"""
Test APIs on localhost to see if they're working
"""

import requests

BASE_URL = "http://localhost:8002"

def test_weather_api():
    """Test weather API on localhost"""
    print("🌤️ Testing Weather API on localhost...")

    try:
        response = requests.get(f"{BASE_URL}/api/parks/1/weather", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "weather" in data and "temperature" in data["weather"]:
                temp = data["weather"]["temperature"]
                print(f"✅ Weather API working: {temp}°C in {data['park_name']}")
                return True
            else:
                print("❌ Weather API response missing data")
                return False
        else:
            print(f"❌ Weather API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Weather API failed: {e}")
        return False

def test_unsplash_api():
    """Test Unsplash API on localhost"""
    print("📸 Testing Unsplash API on localhost...")

    try:
        response = requests.get(f"{BASE_URL}/api/parks/1/unsplash-images", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Unsplash API working: Got {len(data)} images")
                return True
            else:
                print("❌ Unsplash API returned empty or invalid data")
                return False
        else:
            print(f"❌ Unsplash API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Unsplash API failed: {e}")
        return False

def test_news_api():
    """Test NewsAPI on localhost"""
    print("📰 Testing NewsAPI on localhost...")

    try:
        response = requests.get(f"{BASE_URL}/api/news/parks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "articles" in data and len(data["articles"]) > 0:
                print(f"✅ NewsAPI working: Got {len(data['articles'])} articles")
                return True
            else:
                print("❌ NewsAPI returned no articles")
                return False
        else:
            print(f"❌ NewsAPI error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ NewsAPI failed: {e}")
        return False

def test_parks_api():
    """Test basic parks API"""
    print("🏞️ Testing Parks API on localhost...")

    try:
        response = requests.get(f"{BASE_URL}/api/parks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ Parks API working: Got {len(data)} parks")
                # Check if first park has images
                if data[0].get("images") and len(data[0]["images"]) > 0:
                    print("✅ Parks have images loaded")
                else:
                    print("⚠️ Parks missing images")
                return True
            else:
                print("❌ Parks API returned empty data")
                return False
        else:
            print(f"❌ Parks API error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Parks API failed: {e}")
        return False

def main():
    """Test all localhost APIs"""
    print("🌐 Testing APIs on Localhost")
    print("=" * 50)

    # Test if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("💡 Make sure to run: python main.py")
        return

    print()

    # Test each API
    results = {
        "Parks API": test_parks_api(),
        "Weather API": test_weather_api(),
        "Unsplash API": test_unsplash_api(),
        "NewsAPI": test_news_api()
    }

    print("\n" + "=" * 50)
    print("📊 LOCALHOST API TEST RESULTS:")

    working_count = 0
    for api_name, working in results.items():
        status = "✅ WORKING" if working else "❌ NOT WORKING"
        print(f"   {api_name}: {status}")
        if working:
            working_count += 1

    print(f"\n🎯 Summary: {working_count}/4 APIs working on localhost")

    if working_count == 4:
        print("🎉 ALL APIs are working perfectly on localhost!")
        print("\n🚀 Your Tunisia Parks API is fully functional!")
        print("   🌐 Visit: http://localhost:8001")
    elif working_count >= 2:
        print("✅ Most APIs are working - core functionality available")
    else:
        print("❌ Limited API functionality")
        print("💡 Check your API keys in .env file")

if __name__ == "__main__":
    main()
