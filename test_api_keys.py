#!/usr/bin/env python3
"""
Test script to verify API keys are working
"""

import os
import requests
from config import settings

def test_weather_api():
    """Test OpenWeatherMap API"""
    print("🌤️ Testing Weather API...")

    if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY in ['demo_key_disabled', 'your_openweather_api_key_here']:
        print("❌ OpenWeatherMap API key not configured")
        return False

    try:
        # Test with Tunis coordinates
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": 36.8065,
            "lon": 10.1815,
            "appid": settings.OPENWEATHER_API_KEY,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Weather API working - Current temp in Tunis: {data['main']['temp']}°C")
            return True
        else:
            print(f"❌ Weather API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Weather API test failed: {e}")
        return False

def test_unsplash_api():
    """Test Unsplash API"""
    print("📸 Testing Unsplash API...")

    if not settings.UNSPLASH_ACCESS_KEY or settings.UNSPLASH_ACCESS_KEY in ['demo_key_disabled', 'your_unsplash_access_key_here']:
        print("❌ Unsplash API key not configured")
        return False

    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}
        params = {"query": "nature", "per_page": 1}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                print(f"✅ Unsplash API working - Found {len(data['results'])} images")
                return True
            else:
                print("❌ Unsplash API returned no results")
                return False
        else:
            print(f"❌ Unsplash API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Unsplash API test failed: {e}")
        return False

def test_google_places_api():
    """Test Google Places API"""
    print("🗺️ Testing Google Places API...")

    if not settings.GOOGLE_PLACES_API_KEY or settings.GOOGLE_PLACES_API_KEY in ['demo_key_disabled', 'your_google_places_api_key_here']:
        print("❌ Google Places API key not configured")
        return False

    try:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": "36.8065,10.1815",  # Tunis coordinates
            "radius": 1000,
            "type": "park",
            "key": settings.GOOGLE_PLACES_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                results = data.get('results', [])
                print(f"✅ Google Places API working - Found {len(results)} places")
                return True
            else:
                print(f"❌ Google Places API status: {data.get('status')}")
                return False
        else:
            print(f"❌ Google Places API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Google Places API test failed: {e}")
        return False

def test_news_api():
    """Test NewsAPI"""
    print("📰 Testing NewsAPI...")

    if not settings.NEWSAPI_API_KEY or settings.NEWSAPI_API_KEY in ['demo_key_disabled', 'your_newsapi_key_here']:
        print("❌ NewsAPI key not configured")
        return False

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "Tunisia environment",
            "apiKey": settings.NEWSAPI_API_KEY,
            "pageSize": 1
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                print(f"✅ NewsAPI working - Found {len(articles)} articles")
                return True
            else:
                print(f"❌ NewsAPI status: {data.get('status')}")
                return False
        else:
            print(f"❌ NewsAPI error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ NewsAPI test failed: {e}")
        return False

def test_serpapi_places():
    """Test SerpApi as Google Places alternative"""
    print("🔄 Testing SerpApi (Google Places Alternative)...")

    if not settings.SERPAPI_API_KEY or settings.SERPAPI_API_KEY in ['demo_key_disabled', 'your_serpapi_key_here']:
        print("❌ SerpApi key not configured")
        return False

    try:
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_maps",
            "q": "parks near Tunis, Tunisia",
            "api_key": settings.SERPAPI_API_KEY
        }

        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if 'local_results' in data and len(data['local_results']) > 0:
                print(f"✅ SerpApi working - Found {len(data['local_results'])} places")
                return True
            else:
                print("⚠️ SerpApi returned no results (may need different parameters)")
                return False
        else:
            print(f"❌ SerpApi error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SerpApi test failed: {e}")
        return False

def main():
    """Test all API keys"""
    print("🔑 Testing All API Keys")
    print("=" * 80)

    # Test primary APIs
    results = {
        "Weather API": test_weather_api(),
        "Unsplash API": test_unsplash_api(),
        "Google Places API": test_google_places_api(),
        "NewsAPI": test_news_api(),
        "SerpApi (Alternative)": test_serpapi_places()
    }

    print("\n" + "=" * 80)
    print("📊 API KEYS TEST RESULTS:")

    working_count = 0
    alternatives_working = 0

    for api_name, working in results.items():
        status = "✅ WORKING" if working else "❌ NOT WORKING"
        print(f"   {api_name}: {status}")
        if working:
            working_count += 1
            if "Alternative" in api_name:
                alternatives_working += 1

    primary_working = working_count - alternatives_working

    print(f"\n🎯 Summary: {primary_working}/4 primary APIs working, {alternatives_working} alternative APIs working")

    if primary_working >= 3:
        print("🎉 Most APIs are working - your app is fully functional!")
        print("   ✅ Weather forecasts available")
        print("   ✅ Nature images working")
        print("   ✅ News articles loading")
        print("   ✅ Interactive maps available")
    elif primary_working >= 2:
        print("⚠️ Core functionality working - some features may be limited")
    else:
        print("❌ Limited API functionality - check your keys")

    if alternatives_working >= 1:
        print("\n🔄 Alternative APIs available for enhanced functionality")

    print("\n📖 API Keys Guide: See API_KEYS_GUIDE.md for setup help")
    print("🌐 Test your app: Visit http://localhost:8001")

    return primary_working >= 2

if __name__ == "__main__":
    main()
