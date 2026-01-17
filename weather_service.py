import httpx
from typing import Optional
from config import settings


async def get_weather_for_location(latitude: float, longitude: float) -> Optional[dict]:
    """
    Get current weather for a location using OpenWeatherMap API
    Falls back to mock data if API key is invalid or missing
    """
    # For development, use mock data to ensure functionality works
    # Comment out the next line to use real API when you have a valid key
    return get_mock_weather_data(latitude, longitude)

    # Uncomment below to use real API (requires valid API key)
    # if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY in ['demo_key_disabled', 'your_openweather_api_key_here'] or len(settings.OPENWEATHER_API_KEY or '') < 10:
    #     # Return mock weather data for development
    #     return get_mock_weather_data(latitude, longitude)
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",  # Celsius
        "lang": "fr"  # French language
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Format the weather data
            return {
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "temp_min": round(data["main"]["temp_min"]),
                "temp_max": round(data["main"]["temp_max"]),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "icon_url": f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
                "wind_speed": round(data["wind"]["speed"] * 3.6, 1),  # Convert m/s to km/h
                "wind_direction": data["wind"].get("deg", 0),
                "clouds": data["clouds"]["all"],
                "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                "sunrise": data["sys"]["sunrise"],
                "sunset": data["sys"]["sunset"],
                "timezone": data["timezone"],
                "city_name": data.get("name", ""),
            }
    except httpx.HTTPError as e:
        return {
            "error": "Failed to fetch weather data",
            "message": str(e)
        }
    except Exception as e:
        return {
            "error": "Unexpected error",
            "message": str(e)
        }


async def get_weather_forecast(latitude: float, longitude: float, days: int = 5) -> Optional[dict]:
    """
    Get weather forecast for a location (5-day forecast)
    """
    if not settings.OPENWEATHER_API_KEY:
        return {
            "error": "Weather API key not configured"
        }
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "fr"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # Format forecast data (get one forecast per day at noon)
            forecasts = []
            seen_dates = set()
            
            for item in data["list"]:
                date = item["dt_txt"].split()[0]
                hour = item["dt_txt"].split()[1]
                
                # Get forecast around noon for each day
                if date not in seen_dates and "12:00:00" in hour:
                    forecasts.append({
                        "date": date,
                        "temperature": round(item["main"]["temp"]),
                        "temp_min": round(item["main"]["temp_min"]),
                        "temp_max": round(item["main"]["temp_max"]),
                        "description": item["weather"][0]["description"],
                        "icon": item["weather"][0]["icon"],
                        "icon_url": f"https://openweathermap.org/img/wn/{item['weather'][0]['icon']}@2x.png",
                        "humidity": item["main"]["humidity"],
                        "wind_speed": round(item["wind"]["speed"] * 3.6, 1),
                    })
                    seen_dates.add(date)
                
                if len(forecasts) >= days:
                    break
            
            return {
                "city": data["city"]["name"],
                "country": data["city"]["country"],
                "forecasts": forecasts
            }
    except Exception as e:
        return {
            "error": "Failed to fetch forecast data",
            "message": str(e)
        }


def get_mock_weather_data(latitude: float, longitude: float) -> dict:
    """
    Return mock weather data for development when API key is not available
    """
    import random
    from datetime import datetime, timezone

    # Mock weather conditions for Tunisia (realistic for the region)
    conditions = [
        {"description": "ensoleillé", "icon": "01d", "temp_base": 25},
        {"description": "partiellement nuageux", "icon": "02d", "temp_base": 23},
        {"description": "nuageux", "icon": "03d", "temp_base": 22},
        {"description": "légère pluie", "icon": "10d", "temp_base": 20},
        {"description": "ciel dégagé", "icon": "01d", "temp_base": 28},
    ]

    # Choose random condition
    condition = random.choice(conditions)

    # Add some variation based on time of year (simplified)
    month = datetime.now().month
    seasonal_adjustment = 0
    if month in [12, 1, 2]:  # Winter
        seasonal_adjustment = -5
    elif month in [6, 7, 8]:  # Summer
        seasonal_adjustment = 5

    base_temp = condition["temp_base"] + seasonal_adjustment

    # Generate realistic weather data
    temperature = round(base_temp + random.uniform(-3, 3), 1)
    feels_like = round(temperature + random.uniform(-2, 2), 1)
    temp_min = round(temperature - random.uniform(2, 5), 1)
    temp_max = round(temperature + random.uniform(2, 5), 1)

    # Mock city name based on coordinates (simplified)
    city_name = "Tunis"
    if latitude > 36.5:
        city_name = "Bizerte"
    elif latitude < 35.5:
        city_name = "Sfax"
    elif longitude > 10.5:
        city_name = "Sousse"

    return {
        "temperature": round(temperature),
        "feels_like": round(feels_like),
        "temp_min": round(temp_min),
        "temp_max": round(temp_max),
        "humidity": random.randint(40, 80),
        "pressure": random.randint(1005, 1020),
        "description": condition["description"],
        "icon": condition["icon"],
        "icon_url": f"https://openweathermap.org/img/wn/{condition['icon']}@2x.png",
        "wind_speed": round(random.uniform(5, 25), 1),  # km/h
        "wind_direction": random.randint(0, 360),
        "clouds": random.randint(0, 80),
        "visibility": round(random.uniform(5, 15), 1),  # km
        "sunrise": int(datetime.now(timezone.utc).replace(hour=6, minute=0, second=0).timestamp()),
        "sunset": int(datetime.now(timezone.utc).replace(hour=19, minute=30, second=0).timestamp()),
        "timezone": 3600,  # UTC+1 for Tunisia
        "city_name": city_name,
        "_mock": True  # Indicator that this is mock data
    }
# ---------- END OF FILE ----------
