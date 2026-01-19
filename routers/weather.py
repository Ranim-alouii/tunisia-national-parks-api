"""
Weather router - provides weather data and forecasts
"""

from fastapi import APIRouter
from weather_service import get_weather_for_location

# Create router
router = APIRouter()

# ---------- WEATHER ENDPOINTS ----------

@router.get("/status")
async def get_weather_status():
    """Get weather service status."""
    return {
        "status": "operational",
        "service": "Open-Meteo API",
        "features": [
            "Current weather",
            "Hourly forecasts",
            "Daily forecasts",
            "Tunisian timezone support"
        ]
    }
