import httpx
from typing import Optional
from config import settings


async def get_weather_for_location(latitude: float, longitude: float) -> Optional[dict]:
    """
    Get current weather for a location using OpenWeatherMap API
    """
    if not settings.OPENWEATHER_API_KEY:
        return {
            "error": "Weather API key not configured",
            "message": "Please configure OPENWEATHER_API_KEY in .env file"
        }
    
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
# ---------- END OF FILE ----------