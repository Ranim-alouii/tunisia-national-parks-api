import httpx
from typing import Optional
from config import settings


async def get_weather_for_location(latitude: float, longitude: float) -> Optional[dict]:
    """
    Get current weather for a location using Open-Meteo API (no API key required)
    Falls back to mock data if API call fails
    """
    try:
        # Use Open-Meteo API which doesn't require an API key
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "timezone": "Africa/Tunis",
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min",
            "forecast_days": 1
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            current = data["current_weather"]
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})

            # Map weather codes to descriptions and icons
            weather_info = map_weather_code(current.get("weathercode", 0))

            # Get current hour data
            current_time = current["time"]
            hour_index = None
            if hourly.get("time"):
                try:
                    hour_index = hourly["time"].index(current_time)
                except ValueError:
                    hour_index = 0

            humidity = 50  # default
            if hour_index is not None and hourly.get("relative_humidity_2m"):
                humidity = int(hourly["relative_humidity_2m"][hour_index])

            wind_speed = 0.0  # default
            if hour_index is not None and hourly.get("wind_speed_10m"):
                wind_speed = float(hourly["wind_speed_10m"][hour_index])

            # Get daily min/max
            temp_min = temp_max = current["temperature"]
            if daily.get("temperature_2m_min") and daily.get("temperature_2m_max"):
                temp_min = float(daily["temperature_2m_min"][0])
                temp_max = float(daily["temperature_2m_max"][0])

            return {
                "temperature": round(current["temperature"]),
                "feels_like": round(current["temperature"]),  # Open-Meteo doesn't provide feels_like
                "temp_min": round(temp_min),
                "temp_max": round(temp_max),
                "humidity": humidity,
                "pressure": 1013,  # Default pressure, Open-Meteo doesn't provide current pressure
                "description": weather_info["description"],
                "icon": weather_info["icon"],
                "icon_url": weather_info["icon_url"],
                "wind_speed": round(wind_speed, 1),
                "wind_direction": current.get("winddirection", 0),
                "clouds": 0,  # Open-Meteo doesn't provide cloud cover in current_weather
                "visibility": 10.0,  # Default visibility
                "sunrise": None,  # Open-Meteo doesn't provide sunrise/sunset in current_weather
                "sunset": None,
                "timezone": 3600,  # UTC+1 for Tunisia
                "city_name": get_city_name_from_coords(latitude, longitude),
                "_source": "open-meteo"
            }

    except Exception as e:
        # Fallback to mock data if API fails
        print(f"Open-Meteo API failed: {e}, falling back to mock data")
        return get_mock_weather_data(latitude, longitude)


def map_weather_code(code: int) -> dict:
    """
    Map Open-Meteo weather codes to descriptions and icons
    """
    weather_codes = {
        0: {"description": "ciel dégagé", "icon": "01d", "icon_url": "https://openweathermap.org/img/wn/01d@2x.png"},
        1: {"description": "principalement dégagé", "icon": "01d", "icon_url": "https://openweathermap.org/img/wn/01d@2x.png"},
        2: {"description": "partiellement nuageux", "icon": "02d", "icon_url": "https://openweathermap.org/img/wn/02d@2x.png"},
        3: {"description": "couvert", "icon": "03d", "icon_url": "https://openweathermap.org/img/wn/03d@2x.png"},
        45: {"description": "brume", "icon": "50d", "icon_url": "https://openweathermap.org/img/wn/50d@2x.png"},
        48: {"description": "brume givante", "icon": "50d", "icon_url": "https://openweathermap.org/img/wn/50d@2x.png"},
        51: {"description": "bruine légère", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        53: {"description": "bruine modérée", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        55: {"description": "bruine dense", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        56: {"description": "bruine verglaçante légère", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        57: {"description": "bruine verglaçante dense", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        61: {"description": "pluie légère", "icon": "10d", "icon_url": "https://openweathermap.org/img/wn/10d@2x.png"},
        63: {"description": "pluie modérée", "icon": "10d", "icon_url": "https://openweathermap.org/img/wn/10d@2x.png"},
        65: {"description": "pluie forte", "icon": "10d", "icon_url": "https://openweathermap.org/img/wn/10d@2x.png"},
        66: {"description": "pluie verglaçante légère", "icon": "10d", "icon_url": "https://openweathermap.org/img/wn/10d@2x.png"},
        67: {"description": "pluie verglaçante forte", "icon": "10d", "icon_url": "https://openweathermap.org/img/wn/10d@2x.png"},
        71: {"description": "neige légère", "icon": "13d", "icon_url": "https://openweathermap.org/img/wn/13d@2x.png"},
        73: {"description": "neige modérée", "icon": "13d", "icon_url": "https://openweathermap.org/img/wn/13d@2x.png"},
        75: {"description": "neige forte", "icon": "13d", "icon_url": "https://openweathermap.org/img/wn/13d@2x.png"},
        77: {"description": "grains de neige", "icon": "13d", "icon_url": "https://openweathermap.org/img/wn/13d@2x.png"},
        80: {"description": "averse légère", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        81: {"description": "averse modérée", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        82: {"description": "averse violente", "icon": "09d", "icon_url": "https://openweathermap.org/img/wn/09d@2x.png"},
        85: {"description": "averse de neige légère", "icon": "13d", "icon_url": "https://openweathermap.org/img/wn/13d@2x.png"},
        86: {"description": "averse de neige forte", "icon": "13d", "icon_url": "https://openweathermap.org/img/wn/13d@2x.png"},
        95: {"description": "orage", "icon": "11d", "icon_url": "https://openweathermap.org/img/wn/11d@2x.png"},
        96: {"description": "orage avec grêle légère", "icon": "11d", "icon_url": "https://openweathermap.org/img/wn/11d@2x.png"},
        99: {"description": "orage avec grêle forte", "icon": "11d", "icon_url": "https://openweathermap.org/img/wn/11d@2x.png"},
    }

    return weather_codes.get(code, {"description": "conditions météorologiques inconnues", "icon": "01d", "icon_url": "https://openweathermap.org/img/wn/01d@2x.png"})


def get_city_name_from_coords(latitude: float, longitude: float) -> str:
    """
    Get approximate city name from coordinates (simplified)
    """
    # Simple coordinate-to-city mapping for Tunisia
    if 37.0 <= latitude <= 37.5 and 9.5 <= longitude <= 10.0:
        return "Bizerte"
    elif 36.7 <= latitude <= 37.0 and 9.0 <= longitude <= 9.5:
        return "Tunis Nord"
    elif 36.5 <= latitude <= 36.9 and 10.0 <= longitude <= 10.5:
        return "Ariana"
    elif 36.0 <= latitude <= 36.5 and 9.5 <= longitude <= 10.5:
        return "Ben Arous"
    elif 35.5 <= latitude <= 36.0 and 8.5 <= longitude <= 9.5:
        return "Kasserine"
    elif 34.5 <= latitude <= 35.5 and 8.5 <= longitude <= 9.5:
        return "Sidi Bouzid"
    elif 33.5 <= latitude <= 34.5 and 7.5 <= longitude <= 8.5:
        return "Tozeur"
    else:
        return "Tunisie"


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
