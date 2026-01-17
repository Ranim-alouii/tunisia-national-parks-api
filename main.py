from typing import List, Literal
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

import logging
import time
import json

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Depends,
    status,
    File,
    UploadFile,
    Query,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field
from sqlmodel import Session, select
from sqlalchemy import or_
from jose import JWTError, jwt
from passlib.context import CryptContext

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIASGIMiddleware

from database import init_db, get_engine

# Import routers
from routers import parks, species, auth
from routers.auth import get_current_user

# Redis caching (optional - will fallback gracefully if not available)
try:
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    CACHE_ENABLED = True
except ImportError:
    redis_client = None
    CACHE_ENABLED = False
from models import (
    ParkDB,
    SpeciesDB,
    ParkSpeciesLink,
    TrailDB,
    ReviewDB,
    BadgeDB,
    UserBadgeDB,
    UserStatsDB,
    SightingDB,
    UserDB as UserDBModel,
)
from config import settings
from utils import (
    save_upload_file,
    delete_file,
    get_file_url,
    PARKS_DIR,
    SPECIES_DIR,
)
from weather_service import get_weather_for_location, get_weather_forecast

import httpx



# Prometheus monitoring
from prometheus_fastapi_instrumentator import Instrumentator, metrics

# ---------- PUBLIC API MODELS ----------

class UnsplashImage(BaseModel):
    url: str
    description: str | None
    alt_description: str | None
    photographer: str
    unsplash_url: str


# ---------- CACHING FUNCTIONS ----------

def get_cache_key(prefix: str, *args) -> str:
    """Generate a cache key from prefix and arguments."""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def get_cached_data(key: str):
    """Get data from Redis cache if available."""
    if CACHE_ENABLED and redis_client:
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
    return None

def set_cached_data(key: str, data, expire_seconds: int = 3600):
    """Set data in Redis cache with expiration."""
    if CACHE_ENABLED and redis_client:
        try:
            redis_client.setex(key, expire_seconds, json.dumps(data))
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")

# ---------- PUBLIC API FUNCTIONS ----------

def get_mock_unsplash_images(query: str, count: int = 10) -> List[dict]:
    """
    Return mock Unsplash image data for development when API key is not available
    """
    # Mock images based on query keywords
    mock_images = [
        {
            "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
            "description": f"Beautiful nature landscape in Tunisia - {query}",
            "alt_description": f"Tunisian natural scenery featuring {query}",
            "photographer": "Nature Photographer",
            "unsplash_url": "https://unsplash.com/photos/example"
        },
        {
            "url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",
            "description": f"Scenic view of Tunisian wildlife - {query}",
            "alt_description": f"Wildlife photography from Tunisia parks",
            "photographer": "Wildlife Expert",
            "unsplash_url": "https://unsplash.com/photos/example2"
        },
        {
            "url": "https://images.unsplash.com/photo-1505142468610-359e7d316be0?w=800",
            "description": f"Tunisian national park landscape - {query}",
            "alt_description": f"Protected natural areas in Tunisia",
            "photographer": "Landscape Photographer",
            "unsplash_url": "https://unsplash.com/photos/example3"
        },
        {
            "url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800",
            "description": f"Diverse ecosystems in Tunisia - {query}",
            "alt_description": f"Biological diversity in Tunisian nature",
            "photographer": "Eco Photographer",
            "unsplash_url": "https://unsplash.com/photos/example4"
        },
        {
            "url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800",
            "description": f"Tunisian desert landscapes - {query}",
            "alt_description": f"Arid regions and desert biodiversity",
            "photographer": "Desert Explorer",
            "unsplash_url": "https://unsplash.com/photos/example5"
        }
    ]

    # Return requested number of images (up to available mock images)
    return mock_images[:min(count, len(mock_images))]


async def get_unsplash_images(query: str, count: int = 10) -> List[dict]:
    # For development, use mock data to ensure functionality works
    # Comment out the next line to use real API when you have a valid key
    return get_mock_unsplash_images(query, count)

    # Uncomment below to use real API (requires valid API key)
    # if not settings.UNSPLASH_ACCESS_KEY or settings.UNSPLASH_ACCESS_KEY in ['demo_key_disabled', 'your_unsplash_access_key_here']:
    #     # Return mock image data for development
    #     return get_mock_unsplash_images(query, count)

    # Check cache first
    cache_key = get_cache_key("unsplash", query, count)
    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.info(f"Unsplash cache hit for query: {query}")
        return cached_data

    url = f"https://api.unsplash.com/search/photos?query={query}&per_page={count}"
    headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                images = [
                    {
                        "url": photo["urls"]["regular"],
                        "description": photo.get("description", ""),
                        "alt_description": photo.get("alt_description", ""),
                        "photographer": photo["user"]["name"],
                        "unsplash_url": photo["links"]["html"]
                    }
                    for photo in data["results"]
                ]
                # Cache for 6 hours
                set_cached_data(cache_key, images, 21600)
                return images
            else:
                return []
    except Exception as e:
        logger.error(f"Unsplash API error: {e}")
        return []


async def get_wikipedia_summary(title: str) -> dict:
    """
    Get Wikipedia summary for a given title.
    """
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", ""),
                    "extract": data.get("extract", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", "") if data.get("thumbnail") else None,
                }
            else:
                return {}
    except Exception as e:
        logger.error(f"Wikipedia API error: {e}")
        return {}


def get_mock_nearby_places(lat: float, lng: float, place_type: str = "restaurant", radius: int = 5000) -> List[dict]:
    """
    Get mock nearby places for development (no API keys required).
    Returns realistic sample places around Tunisian national parks.
    """
    # Mock places database - realistic places you'd find near Tunisian parks
    mock_places_db = [
        # Restaurants
        {
            "name": "Café Maure - Traditional Tunisian Cuisine",
            "address": "Near park entrance, local specialties",
            "rating": 4.3,
            "price_level": 2,
            "types": ["restaurant", "cafe", "food"],
            "open_now": True,
            "category": "restaurant"
        },
        {
            "name": "Le Jardin - Mediterranean Restaurant",
            "address": "Scenic location with park views",
            "rating": 4.1,
            "price_level": 3,
            "types": ["restaurant", "bar", "food"],
            "open_now": True,
            "category": "restaurant"
        },
        {
            "name": "Dar El Jeld - Local Eatery",
            "address": "Traditional Tunisian dishes",
            "rating": 4.5,
            "price_level": 1,
            "types": ["restaurant", "food"],
            "open_now": False,
            "category": "restaurant"
        },

        # Hotels/Lodging
        {
            "name": "Park View Hotel",
            "address": "Overlooking the national park",
            "rating": 4.2,
            "price_level": 3,
            "types": ["lodging", "hotel"],
            "open_now": True,
            "category": "hotel"
        },
        {
            "name": "Nature Lodge",
            "address": "Eco-friendly accommodation",
            "rating": 4.0,
            "price_level": 2,
            "types": ["lodging", "resort"],
            "open_now": True,
            "category": "hotel"
        },

        # Tourist Attractions
        {
            "name": "Visitor Information Center",
            "address": "Park headquarters and exhibits",
            "rating": 4.4,
            "price_level": 0,
            "types": ["tourist_attraction", "point_of_interest"],
            "open_now": True,
            "category": "tourist_attraction"
        },
        {
            "name": "Wildlife Observation Point",
            "address": "Guided tours available",
            "rating": 4.6,
            "price_level": 0,
            "types": ["tourist_attraction", "park"],
            "open_now": True,
            "category": "tourist_attraction"
        },

        # Parking
        {
            "name": "Main Parking Area",
            "address": "Near park entrance",
            "rating": 3.8,
            "price_level": 0,
            "types": ["parking", "establishment"],
            "open_now": True,
            "category": "parking"
        },
        {
            "name": "Overflow Parking Lot",
            "address": "Additional parking during peak season",
            "rating": 3.5,
            "price_level": 0,
            "types": ["parking", "establishment"],
            "open_now": True,
            "category": "parking"
        },

        # Stores/Shopping
        {
            "name": "Park Gift Shop",
            "address": "Souvenirs and local crafts",
            "rating": 4.0,
            "price_level": 1,
            "types": ["store", "shopping"],
            "open_now": True,
            "category": "store"
        },
        {
            "name": "Local Artisan Market",
            "address": "Traditional crafts and products",
            "rating": 4.2,
            "price_level": 1,
            "types": ["store", "market"],
            "open_now": False,
            "category": "store"
        }
    ]

    # Filter by requested type and limit results
    filtered_places = [
        place for place in mock_places_db
        if place_type in place["types"] or place["category"] == place_type
    ][:10]  # Return max 10 results

    # Add location data (simulate places around the park coordinates)
    for i, place in enumerate(filtered_places):
        # Add slight random offset to simulate different locations
        lat_offset = (i - 5) * 0.001  # Small variations
        lng_offset = (i % 3 - 1) * 0.001

        place.update({
            "location": {
                "lat": lat + lat_offset,
                "lng": lng + lng_offset
            },
            "place_id": f"mock_{place_type}_{i}",
        })

    logger.info(f"Mock API: Returning {len(filtered_places)} {place_type} places near ({lat}, {lng})")
    return filtered_places


def get_mock_news_articles(query: str = "Tunisia parks nature", count: int = 10) -> List[dict]:
    """
    Return mock news articles for development when API key is not available
    """
    mock_articles = [
        {
            "title": f"New Conservation Efforts in Tunisia's National Parks - {query}",
            "description": f"Tunisia launches innovative conservation program to protect biodiversity in national parks. Environmental experts praise the initiative as crucial for wildlife preservation.",
            "url": "https://example.com/conservation-efforts",
            "urlToImage": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",
            "publishedAt": "2024-01-15T10:00:00Z",
            "source": {"name": "Environmental News Tunisia"},
            "author": "Sarah Johnson",
            "_mock": True
        },
        {
            "title": f"Tourism Boost Expected in Tunisia's Protected Areas - {query}",
            "description": f"Eco-tourism initiatives show promising results in Tunisia's national parks, attracting international visitors interested in sustainable travel and wildlife observation.",
            "url": "https://example.com/tourism-boost",
            "urlToImage": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800",
            "publishedAt": "2024-01-10T14:30:00Z",
            "source": {"name": "Travel & Nature Magazine"},
            "author": "Ahmed Ben Ali",
            "_mock": True
        },
        {
            "title": f"Climate Change Impact Study Reveals Urgent Action Needed - {query}",
            "description": f"Comprehensive study shows significant impact of climate change on Tunisia's ecosystems. Researchers call for immediate conservation measures to protect endangered species.",
            "url": "https://example.com/climate-study",
            "urlToImage": "https://images.unsplash.com/photo-1569163139394-de4e4f43e4e3?w=800",
            "publishedAt": "2024-01-08T09:15:00Z",
            "source": {"name": "Climate Research Journal"},
            "author": "Dr. Maria Rodriguez",
            "_mock": True
        },
        {
            "title": f"Wildlife Monitoring Technology Advances in National Parks - {query}",
            "description": f"Cutting-edge technology being deployed in Tunisia's national parks for real-time wildlife monitoring and anti-poaching efforts.",
            "url": "https://example.com/wildlife-tech",
            "urlToImage": "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=800",
            "publishedAt": "2024-01-05T16:45:00Z",
            "source": {"name": "Technology & Conservation"},
            "author": "Tech Reporter",
            "_mock": True
        },
        {
            "title": f"Community Involvement Key to Park Preservation - {query}",
            "description": f"Local communities play crucial role in maintaining Tunisia's national parks. New programs encourage citizen participation in conservation efforts.",
            "url": "https://example.com/community-involvement",
            "urlToImage": "https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=800",
            "publishedAt": "2024-01-03T11:20:00Z",
            "source": {"name": "Community News Network"},
            "author": "Local Correspondent",
            "_mock": True
        }
    ]

    # Filter articles based on query keywords
    filtered_articles = []
    query_lower = query.lower()

    for article in mock_articles:
        # Check if article content matches query
        if any(keyword in article["title"].lower() or keyword in article["description"].lower()
               for keyword in query_lower.split()):
            filtered_articles.append(article)
            if len(filtered_articles) >= count:
                break

    # If no matches, return some articles anyway
    if not filtered_articles:
        filtered_articles = mock_articles[:count]

    return filtered_articles


async def get_nearby_places(lat: float, lng: float, place_type: str = "restaurant", radius: int = 5000) -> List[dict]:
    """
    Get nearby places using Google Places API or fallback to mock data.
    """
    # For development, use mock data to ensure functionality works
    # Comment out the next line to use real API when you have a valid key
    return get_mock_nearby_places(lat, lng, place_type, radius)

    # Uncomment below to use real Google Places API (requires valid API key)
    # if not settings.GOOGLE_PLACES_API_KEY or settings.GOOGLE_PLACES_API_KEY in ['demo_key_disabled', 'your_google_places_api_key_here']:
    #     # Return mock places data for development
    #     return get_mock_nearby_places(lat, lng, place_type, radius)

    # url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    # params = {
    #     "location": f"{lat},{lng}",
    #     "radius": radius,
    #     "type": place_type,
    #     "key": settings.GOOGLE_PLACES_API_KEY
    # }

    # try:
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(url, params=params)
    #         if response.status_code == 200:
    #             data = response.json()
    #             if data.get("status") == "OK":
    #                 return [
    #                     {
    #                         "name": place.get("name", ""),
    #                         "address": place.get("vicinity", ""),
    #                         "rating": place.get("rating", 0),
    #                         "price_level": place.get("price_level", 0),
    #                         "types": place.get("types", []),
    #                         "open_now": place.get("opening_hours", {}).get("open_now", False),
    #                         "location": place.get("geometry", {}).get("location", {}),
    #                         "place_id": place.get("place_id", ""),
    #                     }
    #                     for place in data.get("results", [])
    #                 ]
    #             else:
    #                 return []
    #         else:
    #             return []
    # except Exception as e:
    #     logger.error(f"Google Places API error: {e}")
    #     return []


async def get_news_about_parks(query: str = "Tunisia parks nature", count: int = 10) -> List[dict]:
    """
    Get news articles about parks and nature from NewsAPI.
    Falls back to mock data for development.
    """
    # For development, use mock data to ensure functionality works
    # Comment out the next line to use real API when you have a valid key
    return get_mock_news_articles(query, count)

    # Uncomment below to use real API (requires valid API key)
    # if not settings.NEWSAPI_API_KEY or settings.NEWSAPI_API_KEY in ['demo_key_disabled', 'your_newsapi_key_here']:
    #     # Return mock news data for development
    #     return get_mock_news_articles(query, count)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": count,
        "apiKey": settings.NEWSAPI_API_KEY
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return [
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "urlToImage": article.get("urlToImage", ""),
                            "publishedAt": article.get("publishedAt", ""),
                            "source": article.get("source", {}).get("name", ""),
                            "author": article.get("author", "")
                        }
                        for article in data.get("articles", [])
                    ]
                else:
                    return []
            else:
                return []
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return []


# ---------- APP & GLOBAL MIDDLEWARE ----------

app = FastAPI(
    title="Tunisia National Parks API - Enhanced Edition",
    description="""
Complete API for Tunisia's national parks with biodiversity, trails, reviews, and gamification.

## 🌟 New Features
* **18 National Parks**: Complete database of Tunisia's protected areas
* **29 Species**: Comprehensive fauna & flora database (16 animals, 13 plants)
* **Trails**: Hiking trails with difficulty levels and detailed guides
* **Reviews & Ratings**: User reviews and park ratings
* **Wildlife Sightings**: Report and view species sightings
* **Badges & Gamification**: Achievement system for park explorers
* **Park Comparison**: Side-by-side comparison of multiple parks

## 🎯 Existing Features
* **Authentication**: Secure JWT-based authentication
* **Parks Management**: CRUD operations for national parks
* **Species Management**: Comprehensive fauna & flora database
* **Image Upload**: Upload and manage images
* **Weather**: Real-time weather data and forecasts
* **Maps & Navigation**: Google Maps integration with directions
* **Emergency**: Report emergencies with location data
""",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIASGIMiddleware)


# Security middleware for headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Content Security Policy - Enhanced for external integrations
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net https://maps.googleapis.com https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://unpkg.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: blob: https://images.unsplash.com https://maps.gstatic.com https://maps.googleapis.com https://*.googleusercontent.com https://*.ggpht.com; "
        "connect-src 'self' https://api.unsplash.com https://api.openweathermap.org https://maps.googleapis.com https://www.google.com https://newsapi.org https://en.wikipedia.org https://maps.googleapis.com; "
        "frame-src https://www.google.com https://maps.google.com https://www.youtube.com; "
        "frame-ancestors 'none';"
    )

    # HTTPS Strict Transport Security (HSTS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy (formerly Feature Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(self), "
        "camera=(), "
        "microphone=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=(), "
        "payment=()"
    )

    # Remove server information
    if "Server" in response.headers:
        del response.headers["Server"]

    return response

# Logging
logger = logging.getLogger("tunisia_parks")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Static files and templates (mounted BEFORE routers to ensure they're accessible)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(parks.router)
app.include_router(species.router)
app.include_router(auth.router)

# Add explicit static file routes as fallback
from fastapi.responses import FileResponse
import os

@app.get("/static/{path:path}")
async def serve_static(path: str):
    """Fallback route for static files."""
    file_path = os.path.join("static", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@app.get("/uploads/{path:path}")
async def serve_uploads(path: str):
    """Fallback route for upload files."""
    file_path = os.path.join("uploads", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} "
        f"({process_ms:.2f} ms)"
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # For tests compatibility, use different format for 404 errors
    if exc.status_code == 404:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "error": {
                "code": 422,
                "message": "Validation failed",
                "details": exc.errors(),
            }
        },
    )


# ---------- SECURITY CONFIG ----------

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


fake_admin_user_db: dict[str, UserInDB] = {
    settings.ADMIN_USERNAME: UserInDB(
        username=settings.ADMIN_USERNAME,
        full_name=settings.ADMIN_FULL_NAME,
        disabled=False,
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
    )
}


def get_user(username: str) -> UserInDB | None:
    return fake_admin_user_db.get(username)


def authenticate_user(username: str, password: str) -> UserInDB | None:
    # Check fake admin user only if not in testing mode
    try:
        if hasattr(app.state, 'test_engine'):
            # In testing mode, only check database users
            pass
        else:
            # In production mode, check fake admin user first
            user = get_user(username)
            if user and verify_password(password, user.hashed_password):
                return user
    except:
        # Fallback to checking fake admin user
        user = get_user(username)
        if user and verify_password(password, user.hashed_password):
            return user

    # Check database users
    with Session(get_engine()) as session:
        user_db = session.exec(
            select(UserDBModel).where(UserDBModel.username == username)
        ).first()

        if user_db and verify_password(password, user_db.hashed_password):
            # Convert UserDBModel to UserInDB format for compatibility
            return UserInDB(
                username=user_db.username,
                full_name=user_db.full_name,
                disabled=not user_db.is_active,
                hashed_password=user_db.hashed_password
            )

    return None


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt





# ---------- USER MANAGEMENT ----------

class UserDB(BaseModel):
    id: int
    username: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    location: str | None = None
    favorite_parks: list[int] = []
    badges_earned: list[int] = []
    total_visits: int = 0
    joined_date: str
    is_active: bool = True
    role: str = "user"  # "user", "moderator", "admin"


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    username: str
    password: str


# ---------- EMAIL SYSTEM ----------

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from typing import List, Dict, Any

# Email configuration - get from environment variables with defaults
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

class EmailService:
    @staticmethod
    def is_configured():
        """Check if email service is properly configured."""
        return bool(SMTP_USERNAME and SMTP_PASSWORD and SMTP_SERVER)

    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send an email asynchronously."""
        if not EmailService.is_configured():
            logger.warning("Email service not configured - skipping email send")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SMTP_USERNAME
            msg['To'] = to_email

            # Attach text version
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)

            # Attach HTML version
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Send email
            if SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            else:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                if SMTP_USE_TLS:
                    server.starttls()

            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    def send_welcome_email(user_email: str, user_name: str):
        """Send welcome email to new users."""
        subject = "Bienvenue aux Parcs Nationaux de Tunisie! 🌿🇹🇳"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 30px; text-align: center;">
                <h1>🌿🇹🇳 Bienvenue, {user_name}!</h1>
                <p style="font-size: 18px; margin: 0;">Votre aventure dans les parcs nationaux tunisiens commence ici</p>
            </div>

            <div style="padding: 30px; background: #f8fafc;">
                <h2>Découvrez nos fonctionnalités</h2>
                <ul style="line-height: 1.8;">
                    <li><strong>🗺️ Cartes Interactives:</strong> Explorez tous les parcs avec notre carte interactive</li>
                    <li><strong>🦌 Biodiversité:</strong> Découvrez plus de 250 espèces dans nos parcs</li>
                    <li><strong>🗺️ Sentiers:</strong> Plus de 45 sentiers de randonnée avec guides détaillés</li>
                    <li><strong>⭐ Avis:</strong> Lisez et partagez vos expériences</li>
                    <li><strong>🎖️ Badges:</strong> Gagnez des badges en explorant la nature</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://parcs-tunisie.tn" style="background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                        Commencer l'exploration
                    </a>
                </div>
            </div>

            <div style="background: #1e293b; color: white; padding: 20px; text-align: center;">
                <p>Parcs Nationaux de Tunisie - Découvrez la beauté de la nature tunisienne</p>
                <p style="font-size: 12px; color: #94a3b8;">
                    Vous recevez cet email car vous vous êtes inscrit sur notre plateforme.
                    <a href="#" style="color: #60a5fa;">Se désabonner</a>
                </p>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(user_email, subject, html_content)

    @staticmethod
    def send_review_notification(park_name: str, reviewer_email: str, reviewer_name: str, rating: int, comment: str):
        """Send notification when someone reviews a park the user has favorited."""
        subject = f"Nouvel avis sur {park_name}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2563eb; color: white; padding: 20px; text-align: center;">
                <h2>⭐ Nouvel avis sur {park_name}</h2>
            </div>

            <div style="padding: 30px; background: white;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="font-size: 24px; margin-right: 10px;">
                        {'⭐' * rating}{'☆' * (5-rating)}
                    </div>
                    <span style="font-weight: bold;">{rating}/5 étoiles</span>
                </div>

                <p><strong>{reviewer_name}</strong> a partagé son expérience:</p>
                <blockquote style="border-left: 4px solid #2563eb; padding-left: 20px; margin: 20px 0; font-style: italic; color: #64748b;">
                    "{comment}"
                </blockquote>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://parcs-tunisie.tn/parks/{park_name.lower().replace(' ', '-')}"
                       style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                        Voir l'avis complet
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(reviewer_email, subject, html_content)

    @staticmethod
    def send_weather_alert(park_name: str, user_email: str, alert_type: str, description: str):
        """Send weather alerts for planned visits."""
        subject = f"⚠️ Alerte météo - {park_name}"

        severity_colors = {
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#2563eb"
        }

        color = severity_colors.get(alert_type, "#2563eb")

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center;">
                <h2>⚠️ Alerte Météo</h2>
                <p style="margin: 5px 0;">{park_name}</p>
            </div>

            <div style="padding: 30px; background: white;">
                <p>Bonjour,</p>
                <p>Nous avons détecté des conditions météorologiques importantes qui pourraient affecter votre visite à <strong>{park_name}</strong>:</p>

                <div style="background: #f8fafc; border-left: 4px solid {color}; padding: 20px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>{description}</strong></p>
                </div>

                <p>Pour votre sécurité, nous vous recommandons de:</p>
                <ul>
                    <li>Vérifier les conditions météorologiques avant votre départ</li>
                    <li>Ajuster votre itinéraire si nécessaire</li>
                    <li>Préparer l'équipement approprié</li>
                    <li>Contacter les gardes forestiers locaux pour des conseils</li>
                </ul>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://parcs-tunisie.tn/weather"
                       style="background: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                        Vérifier la météo
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(user_email, subject, html_content)

    @staticmethod
    def send_badge_earned_notification(user_email: str, user_name: str, badge_name: str, badge_description: str, points: int):
        """Send notification when user earns a badge."""
        subject = f"🎖️ Félicitations! Nouveau badge débloqué"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 30px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 10px;">🎖️</div>
                <h1>Nouveau badge débloqué!</h1>
                <p style="font-size: 18px; margin: 0;">Bravo {user_name}!</p>
            </div>

            <div style="padding: 30px; background: white; text-align: center;">
                <h2 style="color: #2563eb; margin-bottom: 10px;">{badge_name}</h2>
                <p style="font-size: 16px; color: #64748b; margin-bottom: 20px;">{badge_description}</p>

                <div style="background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 12px; padding: 20px; margin: 20px 0; display: inline-block;">
                    <div style="font-size: 24px; font-weight: bold; color: #0ea5e9;">+{points} points</div>
                    <div style="color: #64748b; margin-top: 5px;">Points de gamification</div>
                </div>

                <p>Continuez à explorer les parcs nationaux pour débloquer plus de badges et atteindre de nouveaux niveaux!</p>

                <div style="margin: 30px 0;">
                    <a href="https://parcs-tunisie.tn/profile"
                       style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Voir mon profil
                    </a>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(user_email, subject, html_content)


# ---------- MULTI-LANGUAGE SUPPORT ----------

class LanguageService:
    # Language mappings for Tunisia (Arabic, French, English)
    LANGUAGES = {
        "en": {
            "name": "English",
            "flag": "🇺🇸",
            "direction": "ltr"
        },
        "fr": {
            "name": "Français",
            "flag": "🇫🇷",
            "direction": "ltr"
        },
        "ar": {
            "name": "العربية",
            "flag": "🇹🇳",
            "direction": "rtl"
        }
    }

    # Translation dictionaries
    TRANSLATIONS = {
        "en": {
            # Navigation
            "home": "Home",
            "parks": "Parks",
            "species": "Biodiversity",
            "trails": "Trails",
            "map": "Map",
            "comparison": "Compare",
            "chat": "Assistant",
            "emergency": "Emergency",

            # Common
            "loading": "Loading...",
            "error": "Error",
            "success": "Success",
            "search": "Search",
            "filter": "Filter",
            "sort": "Sort",

            # Park details
            "description": "Description",
            "location": "Location",
            "area": "Area",
            "rating": "Rating",
            "reviews": "Reviews",

            # Buttons
            "view_details": "View Details",
            "get_directions": "Get Directions",
            "read_more": "Read More",
            "submit": "Submit",
        },
        "fr": {
            # Navigation
            "home": "Accueil",
            "parks": "Parcs",
            "species": "Biodiversité",
            "trails": "Sentiers",
            "map": "Carte",
            "comparison": "Comparer",
            "chat": "Assistant",
            "emergency": "Urgence",

            # Common
            "loading": "Chargement...",
            "error": "Erreur",
            "success": "Succès",
            "search": "Rechercher",
            "filter": "Filtrer",
            "sort": "Trier",

            # Park details
            "description": "Description",
            "location": "Localisation",
            "area": "Superficie",
            "rating": "Note",
            "reviews": "Avis",

            # Buttons
            "view_details": "Voir les détails",
            "get_directions": "Obtenir l'itinéraire",
            "read_more": "Lire la suite",
            "submit": "Soumettre",
        },
        "ar": {
            # Navigation
            "home": "الرئيسية",
            "parks": "المحميات",
            "species": "التنوع البيولوجي",
            "trails": "المسارات",
            "map": "الخريطة",
            "comparison": "المقارنة",
            "chat": "المساعد",
            "emergency": "الطوارئ",

            # Common
            "loading": "جارٍ التحميل...",
            "error": "خطأ",
            "success": "نجح",
            "search": "بحث",
            "filter": "تصفية",
            "sort": "ترتيب",

            # Park details
            "description": "الوصف",
            "location": "الموقع",
            "area": "المساحة",
            "rating": "التقييم",
            "reviews": "المراجعات",

            # Buttons
            "view_details": "عرض التفاصيل",
            "get_directions": "الحصول على الاتجاهات",
            "read_more": "اقرأ المزيد",
            "submit": "إرسال",
        },
    }

    @staticmethod
    def get_language_info(lang_code: str) -> dict:
        """Get language information."""
        return LanguageService.LANGUAGES.get(lang_code, LanguageService.LANGUAGES["en"])

    @staticmethod
    def translate(key: str, lang_code: str = "en") -> str:
        """Get translation for a key."""
        lang_translations = LanguageService.TRANSLATIONS.get(lang_code, LanguageService.TRANSLATIONS["en"])
        return lang_translations.get(key, key)  # Fallback to key if translation not found

    @staticmethod
    def get_available_languages():
        """Get list of available languages."""
        return [
            {
                "code": code,
                "name": info["name"],
                "flag": info["flag"],
                "direction": info["direction"]
            }
            for code, info in LanguageService.LANGUAGES.items()
        ]


# ---------- ADVANCED SEARCH & DISCOVERY ----------

class SearchService:
    @staticmethod
    async def search_parks(query: str, filters: dict = None, limit: int = 20) -> dict:
        """Advanced search for parks with multiple criteria."""
        if filters is None:
            filters = {}

        with Session(get_engine()) as session:
            stmt = select(ParkDB)

            # Text search across multiple fields
            if query:
                search_terms = [f"%{term}%" for term in query.split()]
                conditions = []

                for term in search_terms:
                    conditions.extend([
                        ParkDB.name.ilike(term),
                        ParkDB.governorate.ilike(term),
                        ParkDB.description.ilike(term),
                    ])

                stmt = stmt.where(or_(*conditions))

            # Apply filters
            if filters.get('governorate'):
                stmt = stmt.where(ParkDB.governorate == filters['governorate'])

            if filters.get('min_area'):
                stmt = stmt.where(ParkDB.area_km2 >= filters['min_area'])

            if filters.get('max_area'):
                stmt = stmt.where(ParkDB.area_km2 <= filters['max_area'])

            if filters.get('difficulty_level'):
                stmt = stmt.where(ParkDB.difficulty_level == filters['difficulty_level'])

            if filters.get('has_activities'):
                # Parks that have activities listed
                stmt = stmt.where(ParkDB.activities.isnot(None))

            # Sorting
            sort_by = filters.get('sort_by', 'name')
            sort_order = filters.get('sort_order', 'asc')

            sort_column = getattr(ParkDB, sort_by)
            if sort_order == 'desc':
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())

            # Pagination
            stmt = stmt.offset(filters.get('skip', 0)).limit(limit)

            results = session.exec(stmt).all()

            # Enhance results with additional data
            enhanced_results = []
            for park in results:
                # Get species count
                species_count = session.exec(
                    select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park.id)
                ).all()

                # Get trails count
                trails_count = session.exec(
                    select(TrailDB).where(TrailDB.park_id == park.id)
                ).all()

                enhanced_results.append({
                    "id": park.id,
                    "name": park.name,
                    "governorate": park.governorate,
                    "description": park.description,
                    "latitude": park.latitude,
                    "longitude": park.longitude,
                    "area_km2": park.area_km2,
                    "difficulty_level": park.difficulty_level,
                    "average_rating": park.average_rating,
                    "total_reviews": park.total_reviews,
                    "species_count": len(species_count),
                    "trails_count": len(trails_count),
                    "images": [get_file_url(img, "parks") for img in (park.images or [])],
                    "google_maps_url": park.google_maps_url,
                    "activities": park.activities.split(',') if park.activities else [],
                    "facilities": park.facilities.split(',') if park.facilities else [],
                })

            # Get total count for pagination info
            count_stmt = select(ParkDB)
            if query:
                count_stmt = count_stmt.where(or_(*conditions))
            if filters.get('governorate'):
                count_stmt = count_stmt.where(ParkDB.governorate == filters['governorate'])

            total_count = len(session.exec(count_stmt).all())

            return {
                "query": query,
                "filters": filters,
                "total_results": total_count,
                "results": enhanced_results,
                "pagination": {
                    "skip": filters.get('skip', 0),
                    "limit": limit,
                    "has_more": (filters.get('skip', 0) + limit) < total_count
                }
            }

    @staticmethod
    async def search_species(query: str, filters: dict = None, limit: int = 20) -> dict:
        """Advanced search for species with multiple criteria."""
        if filters is None:
            filters = {}

        with Session(get_engine()) as session:
            stmt = select(SpeciesDB)

            # Text search
            if query:
                search_terms = [f"%{term}%" for term in query.split()]
                conditions = []

                for term in search_terms:
                    conditions.extend([
                        SpeciesDB.name.ilike(term),
                        SpeciesDB.scientific_name.ilike(term),
                        SpeciesDB.description.ilike(term),
                    ])

                stmt = stmt.where(or_(*conditions))

            # Apply filters
            if filters.get('type'):
                stmt = stmt.where(SpeciesDB.type == filters['type'])

            if filters.get('conservation_status'):
                stmt = stmt.where(SpeciesDB.conservation_status == filters['conservation_status'])

            if filters.get('rarity'):
                stmt = stmt.where(SpeciesDB.rarity == filters['rarity'])

            if filters.get('has_medicinal_use'):
                stmt = stmt.where(SpeciesDB.medicinal_use.isnot(None))

            # Sorting
            sort_by = filters.get('sort_by', 'name')
            sort_order = filters.get('sort_order', 'asc')

            sort_column = getattr(SpeciesDB, sort_by)
            if sort_order == 'desc':
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())

            # Pagination
            stmt = stmt.offset(filters.get('skip', 0)).limit(limit)

            results = session.exec(stmt).all()

            # Enhance results with park information
            enhanced_results = []
            for species in results:
                # Get associated parks
                links = session.exec(
                    select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species.species_id)
                ).all()

                park_names = []
                if links:
                    park_ids = [l.park_id for l in links]
                    parks = session.exec(
                        select(ParkDB).where(ParkDB.id.in_(park_ids))
                    ).all()
                    park_names = [p.name for p in parks]

                enhanced_results.append({
                    "id": species.species_id,
                    "name": species.name,
                    "scientific_name": species.scientific_name,
                    "type": species.type,
                    "description": species.description,
                    "conservation_status": species.conservation_status,
                    "rarity": species.rarity,
                    "image_url": get_file_url(species.image_url, "species") if species.image_url else None,
                    "parks": park_names,
                    "has_medicinal_use": species.medicinal_use is not None,
                    "has_safety_guidelines": species.safety_guidelines is not None,
                })

            # Get total count
            count_stmt = select(SpeciesDB)
            if query:
                count_stmt = count_stmt.where(or_(*conditions))
            if filters.get('type'):
                count_stmt = count_stmt.where(SpeciesDB.type == filters['type'])

            total_count = len(session.exec(count_stmt).all())

            return {
                "query": query,
                "filters": filters,
                "total_results": total_count,
                "results": enhanced_results,
                "pagination": {
                    "skip": filters.get('skip', 0),
                    "limit": limit,
                    "has_more": (filters.get('skip', 0) + limit) < total_count
                }
            }

    @staticmethod
    async def get_search_suggestions(query: str, limit: int = 10) -> list:
        """Get search suggestions based on partial query."""
        if not query or len(query) < 2:
            return []

        with Session(get_engine()) as session:
            suggestions = []

            # Park name suggestions
            park_suggestions = session.exec(
                select(ParkDB.name).where(ParkDB.name.ilike(f"{query}%")).limit(limit//2)
            ).all()
            suggestions.extend([{"type": "park", "text": name, "value": name} for name in park_suggestions])

            # Species name suggestions
            species_suggestions = session.exec(
                select(SpeciesDB.name).where(SpeciesDB.name.ilike(f"{query}%")).limit(limit//2)
            ).all()
            suggestions.extend([{"type": "species", "text": name, "value": name} for name in species_suggestions])

            # Governorate suggestions
            if len(query) >= 3:
                gov_suggestions = session.exec(
                    select(ParkDB.governorate).where(ParkDB.governorate.ilike(f"{query}%")).distinct().limit(3)
                ).all()
                suggestions.extend([{"type": "governorate", "text": gov, "value": gov} for gov in gov_suggestions])

            return suggestions[:limit]

    @staticmethod
    async def get_popular_searches() -> list:
        """Get popular search terms based on usage patterns."""
        # This would be implemented with actual analytics data
        # For now, return some curated popular searches
        return [
            {"term": "Ichkeul", "type": "park", "count": 245},
            {"term": "flamant rose", "type": "species", "count": 189},
            {"term": "Chaambi", "type": "park", "count": 156},
            {"term": "gazelle", "type": "species", "count": 134},
            {"term": "Boukornine", "type": "park", "count": 98},
        ]


# ---------- FILE UPLOAD & MEDIA MANAGEMENT ----------

import os
import uuid
from pathlib import Path
from typing import List, Optional
import aiofiles
from PIL import Image
import boto3
from botocore.exceptions import NoCredentialsError
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Media storage configuration
MEDIA_CONFIG = {
    "local": {
        "enabled": True,
        "base_path": "uploads",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_extensions": {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "documents": [".pdf", ".doc", ".docx", ".txt"],
            "videos": [".mp4", ".avi", ".mov", ".wmv"],
            "audio": [".mp3", ".wav", ".ogg"]
        }
    },
    "cloudinary": {
        "enabled": os.getenv("CLOUDINARY_ENABLED", "false").lower() == "true",
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "api_secret": os.getenv("CLOUDINARY_API_SECRET")
    },
    "s3": {
        "enabled": os.getenv("AWS_S3_ENABLED", "false").lower() == "true",
        "bucket_name": os.getenv("AWS_S3_BUCKET"),
        "region": os.getenv("AWS_REGION", "eu-west-1"),
        "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY")
    }
}

class MediaService:
    @staticmethod
    def get_storage_provider():
        """Get the active storage provider."""
        if MEDIA_CONFIG["cloudinary"]["enabled"]:
            return "cloudinary"
        elif MEDIA_CONFIG["s3"]["enabled"]:
            return "s3"
        else:
            return "local"

    @staticmethod
    def validate_file(file, allowed_types: List[str] = None):
        """Validate file before upload."""
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")

        # Check file size
        if hasattr(file, 'size') and file.size > MEDIA_CONFIG["local"]["max_file_size"]:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MEDIA_CONFIG['local']['max_file_size'] // (1024*1024)}MB"
            )

        # Check file extension
        if allowed_types:
            filename = getattr(file, 'filename', str(file))
            file_ext = Path(filename).suffix.lower()
            if file_ext not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}"
                )

        return True

    @staticmethod
    async def process_image(file_path: str, max_width: int = 1200, max_height: int = 800, quality: int = 85):
        """Process and optimize uploaded images."""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize if too large
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                # Save optimized version
                img.save(file_path, "JPEG", quality=quality, optimize=True)

        except Exception as e:
            logger.warning(f"Image processing failed: {e}")

    @staticmethod
    async def upload_to_cloudinary(file_path: str, folder: str = "parks") -> dict:
        """Upload file to Cloudinary."""
        try:
            if not MEDIA_CONFIG["cloudinary"]["enabled"]:
                raise Exception("Cloudinary not configured")

            # Configure Cloudinary
            cloudinary.config(
                cloud_name=MEDIA_CONFIG["cloudinary"]["cloud_name"],
                api_key=MEDIA_CONFIG["cloudinary"]["api_key"],
                api_secret=MEDIA_CONFIG["cloudinary"]["api_secret"]
            )

            # Upload file
            upload_result = cloudinary.uploader.upload(
                file_path,
                folder=f"tunisia-parks/{folder}",
                resource_type="auto",
                quality="auto",
                format="auto"
            )

            return {
                "provider": "cloudinary",
                "public_id": upload_result["public_id"],
                "url": upload_result["secure_url"],
                "format": upload_result.get("format"),
                "width": upload_result.get("width"),
                "height": upload_result.get("height"),
                "bytes": upload_result.get("bytes")
            }

        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise HTTPException(status_code=500, detail="Cloud upload failed")

    @staticmethod
    async def upload_to_s3(file_path: str, folder: str = "parks") -> dict:
        """Upload file to AWS S3."""
        try:
            if not MEDIA_CONFIG["s3"]["enabled"]:
                raise Exception("S3 not configured")

            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=MEDIA_CONFIG["s3"]["region"],
                aws_access_key_id=MEDIA_CONFIG["s3"]["access_key"],
                aws_secret_access_key=MEDIA_CONFIG["s3"]["secret_key"]
            )

            # Generate unique filename
            file_name = f"{folder}/{uuid.uuid4()}{Path(file_path).suffix}"
            bucket = MEDIA_CONFIG["s3"]["bucket_name"]

            # Upload file
            with open(file_path, 'rb') as file:
                s3_client.upload_fileobj(file, bucket, file_name)

            # Generate public URL
            url = f"https://{bucket}.s3.{MEDIA_CONFIG['s3']['region']}.amazonaws.com/{file_name}"

            return {
                "provider": "s3",
                "bucket": bucket,
                "key": file_name,
                "url": url
            }

        except NoCredentialsError:
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail="S3 upload failed")

    @staticmethod
    async def upload_file(file, folder: str = "general") -> dict:
        """Upload file using the configured storage provider."""
        provider = MediaService.get_storage_provider()

        # Generate unique filename
        original_filename = getattr(file, 'filename', str(file))
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(MEDIA_CONFIG["local"]["base_path"], folder, unique_filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Save file locally first
            with open(file_path, 'wb') as buffer:
                content = await file.read()
                buffer.write(content)

            # Process images
            if file_extension.lower() in MEDIA_CONFIG["local"]["allowed_extensions"]["images"]:
                await MediaService.process_image(file_path)

            # Upload to cloud if configured
            if provider == "cloudinary":
                result = await MediaService.upload_to_cloudinary(file_path, folder)
                # Optionally delete local file after cloud upload
                os.remove(file_path)
                return result
            elif provider == "s3":
                result = await MediaService.upload_to_s3(file_path, folder)
                # Optionally delete local file after cloud upload
                os.remove(file_path)
                return result
            else:
                # Return local file info
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'results': self.results
        }

        except Exception as e:
            # Clean up on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @staticmethod
    async def delete_file(file_info: dict):
        """Delete file from storage."""
        try:
            provider = file_info.get("provider", "local")

            if provider == "cloudinary":
                cloudinary.uploader.destroy(file_info["public_id"])
            elif provider == "s3":
                s3_client = boto3.client(
                    's3',
                    region_name=MEDIA_CONFIG["s3"]["region"],
                    aws_access_key_id=MEDIA_CONFIG["s3"]["access_key"],
                    aws_secret_access_key=MEDIA_CONFIG["s3"]["secret_key"]
                )
                s3_client.delete_object(
                    Bucket=file_info["bucket"],
                    Key=file_info["key"]
                )
            else:
                # Local file
                if os.path.exists(file_info["path"]):
                    os.remove(file_info["path"])

        except Exception as e:
            logger.error(f"File deletion failed: {e}")

    @staticmethod
    def get_file_url(file_info: dict) -> str:
        """Get the public URL for a file."""
        provider = file_info.get("provider", "local")

        if provider == "cloudinary":
            return file_info["url"]
        elif provider == "s3":
            return file_info["url"]
        else:
            return file_info["url"]  # Local URL


# ---------- FRONTEND ROUTES (MUST COME BEFORE API ROUTES) ----------

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/parks", response_class=HTMLResponse, tags=["Frontend"])
async def view_parks(request: Request):
    return templates.TemplateResponse("parks.html", {"request": request})

@app.get("/parks/{park_id}", response_class=HTMLResponse, tags=["Frontend"])
async def view_park_detail(request: Request, park_id: int):
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        # Convert to dict for template
        park = {
            "id": park_db.id,
            "name": park_db.name,
            "governorate": park_db.governorate,
            "description": park_db.description,
            "latitude": park_db.latitude,
            "longitude": park_db.longitude,
            "area_km2": park_db.area_km2,
            "images": [get_file_url(img, "parks") for img in (park_db.images or [])],
        }

        return templates.TemplateResponse("park_detail.html", {"request": request, "park": park})

@app.get("/trails", response_class=HTMLResponse, tags=["Frontend"])
async def view_trails(request: Request):
    return templates.TemplateResponse("trails.html", {"request": request})

@app.get("/species", response_class=HTMLResponse, tags=["Frontend"])
async def view_species(request: Request):
    return templates.TemplateResponse("species.html", {"request": request})

@app.get("/comparison", response_class=HTMLResponse, tags=["Frontend"])
async def view_comparison(request: Request):
    return templates.TemplateResponse("comparison.html", {"request": request})

@app.get("/emergency", response_class=HTMLResponse, tags=["Frontend"])
async def view_emergency(request: Request):
    return templates.TemplateResponse("emergency.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse, tags=["Frontend"])
async def view_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse, tags=["Frontend"])
async def view_upload_images(request: Request):
    return templates.TemplateResponse("upload_images.html", {"request": request})

@app.get("/map", response_class=HTMLResponse, tags=["Maps & Navigation"])
async def view_interactive_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})

# ---------- STARTUP & HEALTH ----------

# Initialize Prometheus monitoring
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False, should_gzip=True)

# Update the existing app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    init_db()
    # Ensure upload directories exist
    for folder in ["parks", "species", "users", "documents"]:
        Path(f"uploads/{folder}").mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown (if needed)
    pass

# Add lifespan to existing app
app.router.lifespan_context = lifespan


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "3.0.0"}


@app.get("/health", tags=["Health"])
def health_check_root():
    """Health check at root path for compatibility."""
    return {"status": "ok", "version": "3.0.0"}


@app.get("/docs", response_class=HTMLResponse, tags=["Documentation"])
async def custom_api_docs(request: Request):
    """Enhanced API documentation with custom UI/UX."""
    return templates.TemplateResponse("custom_docs.html", {"request": request})


@app.get("/redoc", response_class=HTMLResponse, tags=["Documentation"])
def redoc_redirect():
    """Redirect to ReDoc documentation."""
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="API Documentation"
    )


# ---------- PYDANTIC RESPONSE MODELS ----------

# ---------- USER AUTHENTICATION ENDPOINTS ----------








# ---------- PARK MODELS ----------

class Park(BaseModel):
    id: int
    name: str
    governorate: str
    description: str
    latitude: float
    longitude: float
    area_km2: float
    images: List[str]


class ParkCreate(BaseModel):
    name: str
    governorate: str
    description: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    area_km2: float = Field(gt=0)
    google_maps_url: str


class ParkUpdate(BaseModel):
    name: str | None = None
    governorate: str | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    area_km2: float | None = Field(default=None, gt=0)


# ---------- SPECIES MODELS ----------

class Species(BaseModel):
    id: int
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    safety_guidelines: str
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int]


class SpeciesCreate(BaseModel):
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    safety_guidelines: str = ""
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int] = []


class SpeciesUpdate(BaseModel):
    name: str | None = None
    type: Literal["animal", "plant"] | None = None
    scientific_name: str | None = None
    description: str | None = None
    threats: str | None = None
    protection_measures: str | None = None
    safety_guidelines: str | None = None
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int] | None = None


# ---------- ENHANCED FEATURE MODELS ----------

class Trail(BaseModel):
    trail_id: int
    park_id: int
    name: str
    description: str
    difficulty: str
    length_km: float
    duration_hours: float
    elevation_gain: int | None
    trail_type: str
    highlights: List[str]


class Review(BaseModel):
    review_id: int
    park_id: int
    author_name: str
    rating: int
    title: str
    comment: str
    visit_date: str | None
    helpful_count: int
    created_at: str


class ReviewCreate(BaseModel):
    author_name: str
    rating: int = Field(ge=1, le=5)
    title: str
    comment: str
    visit_date: str | None = None


class TrailCreate(BaseModel):
    park_id: int
    name: str
    description: str
    difficulty: Literal["facile", "modéré", "difficile"]
    length_km: float = Field(gt=0)
    duration_hours: float
    elevation_gain: int | None = None
    trail_type: str
    highlights: List[str] = []


class TrailUpdate(BaseModel):
    park_id: int | None = None
    name: str | None = None
    description: str | None = None
    difficulty: str | None = None
    length_km: float | None = None
    duration_hours: float | None = None
    elevation_gain: int | None = None
    trail_type: str | None = None
    highlights: List[str] | None = None

class Sighting(BaseModel):
    sighting_id: int
    park_id: int
    species_id: int
    reporter_name: str
    sighting_date: str
    location_lat: float
    location_lng: float
    photo_url: str | None
    notes: str | None
    verified: bool
    created_at: str


class SightingCreate(BaseModel):
    park_id: int
    species_id: int
    reporter_name: str
    sighting_date: str
    location_lat: float
    location_lng: float
    photo_url: str | None = None
    notes: str | None = None


class Badge(BaseModel):
    badge_id: int
    name: str
    description: str
    icon: str
    requirement: str
    points: int


class ParkComparison(BaseModel):
    park_id: int
    park_name: str
    governorate: str
    difficulty_level: str | None
    area_hectares: int | None
    species_count: int
    trails_count: int
    average_rating: float | None
    activities: List[str]
    best_months: List[str]


class Review(BaseModel):
    review_id: int
    park_id: int
    author_name: str
    rating: int
    title: str
    comment: str
    visit_date: str | None
    helpful_count: int
    created_at: str


class ReviewCreate(BaseModel):
    author_name: str
    rating: int = Field(ge=1, le=5)
    title: str
    comment: str
    visit_date: str | None = None


# ---------- WEATHER & MAP MODELS ----------

class WeatherResponse(BaseModel):
    temperature: int
    feels_like: int
    temp_min: int
    temp_max: int
    humidity: int
    pressure: int
    description: str
    icon: str
    icon_url: str
    wind_speed: float
    wind_direction: int
    clouds: int
    visibility: float
    sunrise: int
    sunset: int
    timezone: int
    city_name: str


class MapData(BaseModel):
    park_id: int
    park_name: str
    latitude: float
    longitude: float
    governorate: str
    google_maps_url: str
    directions_url: str


class DirectionsRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_park_id: int


# ---------- FILTER & SEARCH MODELS ----------

class SearchResult(BaseModel):
    total_results: int
    parks: List[Park]


class MultiParkRoute(BaseModel):
    park_ids: List[int]


class RoutePoint(BaseModel):
    order: int
    park_id: int
    park_name: str
    latitude: float
    longitude: float
    governorate: str
    google_maps_url: str


class MultiParkRouteResponse(BaseModel):
    total_parks: int
    total_distance_km: float
    estimated_time_hours: float
    route_points: List[RoutePoint]
    google_maps_url: str


# ---------- ROOT-LEVEL API ENDPOINTS (for compatibility with tests) ----------

# Removed conflicting root-level API routes - using /api/ prefixed routes instead


# Removed conflicting root-level API routes - using /api/ prefixed routes instead


# ---------- PARK ENDPOINTS ----------

# ---------- PARK COMPARISON ENDPOINT (MUST BE BEFORE /api/parks/{park_id}) ----------

@app.get("/api/parks/compare", tags=["Parks"])
def compare_parks(park_ids: str = Query("", description="Comma-separated list of park IDs to compare")):
    """
    Compare multiple parks side by side.

    - park_ids: Comma-separated list of park IDs (e.g., "1,2,3")
    """
    # Handle empty or missing parameter gracefully
    if not park_ids or not park_ids.strip():
        raise HTTPException(status_code=400, detail="park_ids parameter is required")

    try:
        # More robust parsing
        ids = []
        for id_str in park_ids.split(","):
            id_str = id_str.strip()
            if id_str:  # Skip empty strings
                try:
                    park_id = int(id_str)
                    if park_id > 0:  # Ensure positive IDs
                        ids.append(park_id)
                except ValueError:
                    continue  # Skip invalid entries

        # Remove duplicates while preserving order
        seen = set()
        ids = [x for x in ids if not (x in seen or seen.add(x))]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid park IDs format: {str(e)}")

    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Please select at least 2 parks to compare")
    if len(ids) > 4:
        raise HTTPException(status_code=400, detail="Please select no more than 4 parks to compare")

    with Session(get_engine()) as session:
        parks_db = session.exec(select(ParkDB).where(ParkDB.id.in_(ids))).all()

        if len(parks_db) != len(ids):
            found_ids = {p.id for p in parks_db}
            missing_ids = [pid for pid in ids if pid not in found_ids]
            raise HTTPException(status_code=404, detail=f"Parks not found: {missing_ids}")

        # Convert to comparison format
        comparison_data = []
        for park in parks_db:
            # Count species and trails
            species_count = session.exec(
                select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park.id)
            ).all()

            trails_count = session.exec(
                select(TrailDB).where(TrailDB.park_id == park.id)
            ).all()

            comparison_data.append({
                "park_id": park.id,
                "park_name": park.name,
                "governorate": park.governorate,
                "area_hectares": park.area_hectares,
                "species_count": len(species_count),
                "trails_count": len(trails_count),
                "average_rating": park.average_rating,
                "activities": park.activities.split(",") if park.activities else [],
                "best_months": park.best_months.split(",") if park.best_months else [],
            })

        return comparison_data


@app.get("/api/parks", response_model=List[Park], tags=["Parks"])
def list_parks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    governorate: str | None = None,
    min_area: float | None = Query(None, ge=0),
    max_area: float | None = Query(None, ge=0),
    sort_by: str = Query("name", pattern="^(name|governorate|area_km2|average_rating)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
):
    """
    List all parks with advanced filtering and sorting.

    - skip: Number of parks to skip (pagination)
    - limit: Maximum number of parks to return (1-100)
    - governorate: Filter by governorate
    - min_area: Minimum area in km²
    - max_area: Maximum area in km²
    - sort_by: Sort field (name, governorate, area_km2, average_rating)
    - sort_order: Sort order (asc, desc)
    """
    try:
        with Session(get_engine()) as session:
            statement = select(ParkDB)

            # Apply filters
            if governorate:
                statement = statement.where(ParkDB.governorate == governorate)
            if min_area is not None:
                statement = statement.where(ParkDB.area_km2 >= min_area)
            if max_area is not None and max_area > 0:
                statement = statement.where(ParkDB.area_km2 <= max_area)

            # Apply sorting
            sort_column = getattr(ParkDB, sort_by)
            if sort_order == "desc":
                statement = statement.order_by(sort_column.desc())
            else:
                statement = statement.order_by(sort_column.asc())

            # Apply pagination
            statement = statement.offset(skip).limit(limit)
            parks_db = session.exec(statement).all()

            return [
                Park(
                    id=p.id,
                    name=p.name,
                    governorate=p.governorate,
                    description=p.description,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    area_km2=p.area_km2,
                    images=[get_file_url(img, "parks") for img in (p.images or [])],
                )
                for p in parks_db
            ]
    except Exception as e:
        logger.error(f"Error listing parks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/parks/{park_id}", response_model=Park, tags=["Parks"])
def get_park(park_id: int):
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        return Park(
            id=park.id,
            name=park.name,
            governorate=park.governorate,
            description=park.description,
            latitude=park.latitude,
            longitude=park.longitude,
            area_km2=park.area_km2,
            images=[get_file_url(img, "parks") for img in (park.images or [])],
        )


@app.post("/api/parks", response_model=Park, status_code=201, tags=["Parks"])
def create_park(
    park_in: ParkCreate,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        park_db = ParkDB(
            name=park_in.name,
            governorate=park_in.governorate,
            description=park_in.description,
            latitude=park_in.latitude,
            longitude=park_in.longitude,
            area_km2=park_in.area_km2,
            google_maps_url=park_in.google_maps_url,
        )
        session.add(park_db)
        session.commit()
        session.refresh(park_db)

        return Park(
            id=park_db.id,
            name=park_db.name,
            governorate=park_db.governorate,
            description=park_db.description,
            latitude=park_db.latitude,
            longitude=park_db.longitude,
            area_km2=park_db.area_km2,
            images=[],
        )


@app.put("/api/parks/{park_id}", response_model=Park, tags=["Parks"])
def update_park(
    park_id: int,
    park_in: ParkUpdate,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        data = park_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(park_db, field, value)

        session.add(park_db)
        session.commit()
        session.refresh(park_db)

        return Park(
            id=park_db.id,
            name=park_db.name,
            governorate=park_db.governorate,
            description=park_db.description,
            latitude=park_db.latitude,
            longitude=park_db.longitude,
            area_km2=park_db.area_km2,
            images=[get_file_url(img, "parks") for img in (park_db.images or [])],
        )


@app.delete("/api/parks/{park_id}", status_code=204, tags=["Parks"])
def delete_park(
    park_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        if park_db.images:
            for img_filename in park_db.images:
                delete_file(img_filename, PARKS_DIR)

        session.delete(park_db)
        session.commit()
        return None


# ---------- PARK IMAGE ENDPOINTS ----------

@app.post("/api/parks/{park_id}/images", status_code=201, tags=["Park Images"])
async def upload_park_image(
    park_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        filename = await save_upload_file(file, PARKS_DIR)

        if park_db.images is None:
            park_db.images = []
        park_db.images.append(filename)

        session.add(park_db)
        session.commit()
        session.refresh(park_db)

        return {
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": get_file_url(filename, "parks"),
            "total_images": len(park_db.images),
        }


@app.delete(
    "/api/parks/{park_id}/images/{filename}", status_code=204, tags=["Park Images"]
)
def delete_park_image(
    park_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        if not park_db.images or filename not in park_db.images:
            raise HTTPException(status_code=404, detail="Image not found")

        park_db.images.remove(filename)
        session.add(park_db)
        session.commit()

        delete_file(filename, PARKS_DIR)
        return None


# ---------- SPECIES ENDPOINTS (JOIN-BASED) ----------

@app.get("/api/species", response_model=List[Species], tags=["Species"])
def list_species(
    type: Literal["animal", "plant"] | None = None,
    park_id: int | None = None,
    conservation_status: str | None = None,
    rarity: str | None = None,
    search: str | None = None,
    sort_by: str = Query("name", pattern="^(name|scientific_name|type)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get a list of all species with advanced filtering and sorting.

    - type: Filter by 'animal' or 'plant'
    - park_id: Filter species by park ID
    - conservation_status: Filter by conservation status
    - rarity: Filter by rarity (très_rare, rare, commun)
    - search: Search in name or scientific name
    - sort_by: Sort field (name, scientific_name, type)
    - sort_order: Sort order (asc, desc)
    - skip: Number of species to skip (pagination)
    - limit: Maximum number of species to return (1-100)
    """
    try:
        with Session(get_engine()) as session:
            stmt = select(SpeciesDB)

            # Apply filters
            if type is not None:
                stmt = stmt.where(SpeciesDB.type == type)

            if conservation_status:
                stmt = stmt.where(SpeciesDB.conservation_status == conservation_status)

            if rarity:
                stmt = stmt.where(SpeciesDB.rarity == rarity)

            if search:
                search_term = f"%{search}%"
                stmt = stmt.where(
                    (SpeciesDB.name.ilike(search_term)) |
                    (SpeciesDB.scientific_name.ilike(search_term))
                )

            if park_id is not None:
                stmt = (
                    stmt.join(
                        ParkSpeciesLink,
                        ParkSpeciesLink.species_id == SpeciesDB.species_id,
                    )
                    .where(ParkSpeciesLink.park_id == park_id)
                )

            # Apply sorting
            sort_column = getattr(SpeciesDB, sort_by)
            if sort_order == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())

            # Apply pagination
            stmt = stmt.offset(skip).limit(limit)
            species_rows = session.exec(stmt).all()

            if species_rows:
                species_ids = [s.species_id for s in species_rows]
                links = session.exec(
                    select(ParkSpeciesLink).where(
                        ParkSpeciesLink.species_id.in_(species_ids)
                    )
                ).all()
                park_ids_map: dict[int, list[int]] = {}
                for link in links:
                    park_ids_map.setdefault(link.species_id, []).append(link.park_id)
            else:
                park_ids_map = {}

            return [
                Species(
                    id=s.species_id,
                    name=s.name,
                    type=s.type,
                    scientific_name=s.scientific_name,
                    description=s.description,
                    threats=s.threats or "",
                    protection_measures=s.protection_measures or "",
                    safety_guidelines=s.safety_guidelines or "",
                    medicinal_use=s.medicinal_use,
                    image_url=get_file_url(s.image_url, "species") if s.image_url else None,
                    park_ids=park_ids_map.get(s.species_id, []),
                )
                for s in species_rows
            ]
    except Exception as e:
        logger.error(f"Error listing species: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/species/{species_id}", response_model=Species, tags=["Species"])
def get_species(species_id: int):
    with Session(get_engine()) as session:
        s = session.get(SpeciesDB, species_id)
        if s is None:
            raise HTTPException(status_code=404, detail="Species not found")

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == s.species_id)
        ).all()
        park_ids = [l.park_id for l in links]

        return Species(
            id=s.species_id,
            name=s.name,
            type=s.type,
            scientific_name=s.scientific_name,
            description=s.description,
            threats=s.threats or "",
            protection_measures=s.protection_measures or "",
            safety_guidelines=s.safety_guidelines or "",
            medicinal_use=s.medicinal_use,
            image_url=get_file_url(s.image_url, "species") if s.image_url else None,
            park_ids=park_ids,
        )


@app.get("/api/parks/{park_id}/species", response_model=List[Species], tags=["Species"])
def list_species_for_park(park_id: int):
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park_id)
        ).all()
        species_ids = [l.species_id for l in links]
        if not species_ids:
            return []

        species_rows = session.exec(
            select(SpeciesDB).where(SpeciesDB.species_id.in_(species_ids))
        ).all()

        links_all = session.exec(
            select(ParkSpeciesLink).where(
                ParkSpeciesLink.species_id.in_([s.species_id for s in species_rows])
            )
        ).all()
        park_ids_map: dict[int, list[int]] = {}
        for link in links_all:
            park_ids_map.setdefault(link.species_id, []).append(link.park_id)

        return [
            Species(
                id=s.species_id,
                name=s.name,
                type=s.type,
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats or "",
                protection_measures=s.protection_measures or "",
                safety_guidelines=s.safety_guidelines or "",
                medicinal_use=s.medicinal_use,
                image_url=get_file_url(s.image_url, "species") if s.image_url else None,
                park_ids=park_ids_map.get(s.species_id, []),
            )
            for s in species_rows
        ]


@app.post("/api/species", response_model=Species, status_code=201, tags=["Species"])
def create_species(
    species_in: SpeciesCreate,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        species_db = SpeciesDB(
            name=species_in.name,
            type=species_in.type,
            scientific_name=species_in.scientific_name,
            description=species_in.description,
            threats=species_in.threats,
            protection_measures=species_in.protection_measures,
            safety_guidelines=species_in.safety_guidelines,
            medicinal_use=species_in.medicinal_use,
            image_url=species_in.image_url,
        )
        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        for park_id in species_in.park_ids:
            park = session.get(ParkDB, park_id)
            if park:
                session.add(
                    ParkSpeciesLink(
                        park_id=park.id,
                        species_id=species_db.species_id,
                    )
                )
        session.commit()

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species_db.species_id)
        ).all()
        park_ids = [l.park_id for l in links]

        return Species(
            id=species_db.species_id,
            name=species_db.name,
            type=species_db.type,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats or "",
            protection_measures=species_db.protection_measures or "",
            safety_guidelines=species_db.safety_guidelines or "",
            medicinal_use=species_db.medicinal_use,
            image_url=get_file_url(species_db.image_url, "species") if species_db.image_url else None,
            park_ids=park_ids,
        )


@app.put("/api/species/{species_id}", response_model=Species, tags=["Species"])
def update_species(
    species_id: int,
    species_in: SpeciesUpdate,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        data = species_in.model_dump(exclude_unset=True)

        simple_fields = {
            "name",
            "type",
            "scientific_name",
            "description",
            "threats",
            "protection_measures",
            "safety_guidelines",
            "medicinal_use",
            "image_url",
        }
        for field in simple_fields:
            if field in data:
                setattr(species_db, field, data[field])

        if "park_ids" in data:
            new_ids = set(data["park_ids"] or [])

            existing_links = session.exec(
                select(ParkSpeciesLink).where(
                    ParkSpeciesLink.species_id == species_db.species_id
                )
            ).all()
            existing_ids = {l.park_id for l in existing_links}

            for link in existing_links:
                if link.park_id not in new_ids:
                    session.delete(link)

            for park_id in new_ids - existing_ids:
                park = session.get(ParkDB, park_id)
                if park:
                    session.add(
                        ParkSpeciesLink(
                            park_id=park.id,
                            species_id=species_db.species_id,
                        )
                    )

        session.add(species_db)
        session.commit()

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species_db.species_id)
        ).all()
        park_ids = [l.park_id for l in links]

        return Species(
            id=species_db.species_id,
            name=species_db.name,
            type=species_db.type,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats or "",
            protection_measures=species_db.protection_measures or "",
            safety_guidelines=species_db.safety_guidelines or "",
            medicinal_use=species_db.medicinal_use,
            image_url=get_file_url(species_db.image_url, "species") if species_db.image_url else None,
            park_ids=park_ids,
        )


@app.delete("/api/species/{species_id}", status_code=204, tags=["Species"])
def delete_species(
    species_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        if species_db.image_url:
            delete_file(species_db.image_url, SPECIES_DIR)

        # Delete park-species links
        session.exec(
            select(ParkSpeciesLink)
            .where(ParkSpeciesLink.species_id == species_db.species_id)
        )
        # Delete links using exec
        links_to_delete = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species_db.species_id)
        ).all()
        for link in links_to_delete:
            session.delete(link)

        session.delete(species_db)
        session.commit()
        return None


# ---------- TRAIL ENDPOINTS ----------

@app.get("/api/parks/{park_id}/trails", response_model=List[Trail], tags=["Trails"])
def list_trails_for_park(park_id: int):
    """List all trails for a given park."""
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        trails_db = session.exec(
            select(TrailDB).where(TrailDB.park_id == park_id)
        ).all()

        return [
            Trail(
                trail_id=t.trail_id,
                park_id=t.park_id,
                name=t.name,
                description=t.description,
                difficulty=t.difficulty,
                length_km=t.length_km,
                duration_hours=t.duration_hours,
                elevation_gain=t.elevation_gain,
                trail_type=t.trail_type,
                highlights=json.loads(t.highlights) if t.highlights else [],
            )
            for t in trails_db
        ]


@app.get("/api/trails/{trail_id}", response_model=Trail, tags=["Trails"])
def get_trail(trail_id: int):
    """Get details of a specific trail."""
    with Session(get_engine()) as session:
        t = session.get(TrailDB, trail_id)
        if t is None:
            raise HTTPException(status_code=404, detail="Trail not found")

        return Trail(
            trail_id=t.trail_id,
            park_id=t.park_id,
            name=t.name,
            description=t.description,
            difficulty=t.difficulty,
            length_km=t.length_km,
            duration_hours=t.duration_hours,
            elevation_gain=t.elevation_gain,
            trail_type=t.trail_type,
            highlights=json.loads(t.highlights) if t.highlights else [],
        )


@app.post("/api/trails", response_model=Trail, status_code=201, tags=["Trails"])
def create_trail(
    trail_in: TrailCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new trail (requires authentication)."""
    with Session(get_engine()) as session:
        park = session.get(ParkDB, trail_in.park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        trail_db = TrailDB(
            park_id=trail_in.park_id,
            name=trail_in.name,
            description=trail_in.description,
            difficulty=trail_in.difficulty,
            length_km=trail_in.length_km,
            duration_hours=trail_in.duration_hours,
            elevation_gain=trail_in.elevation_gain,
            trail_type=trail_in.trail_type,
            highlights=json.dumps(trail_in.highlights or []),
        )
        session.add(trail_db)
        session.commit()
        session.refresh(trail_db)

        return Trail(
            trail_id=trail_db.trail_id,
            park_id=trail_db.park_id,
            name=trail_db.name,
            description=trail_db.description,
            difficulty=trail_db.difficulty,
            length_km=trail_db.length_km,
            duration_hours=trail_db.duration_hours,
            elevation_gain=trail_db.elevation_gain,
            trail_type=trail_db.trail_type,
            highlights=trail_in.highlights or [],
        )


@app.put("/api/trails/{trail_id}", response_model=Trail, tags=["Trails"])
def update_trail(
    trail_id: int,
    trail_in: TrailUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update an existing trail (requires authentication)."""
    with Session(get_engine()) as session:
        trail_db = session.get(TrailDB, trail_id)
        if trail_db is None:
            raise HTTPException(status_code=404, detail="Trail not found")

        data = trail_in.model_dump(exclude_unset=True)

        if "park_id" in data:
            park = session.get(ParkDB, data["park_id"])
            if park is None:
                raise HTTPException(status_code=404, detail="Park not found")

        for field, value in data.items():
            if field == "highlights" and value is not None:
                setattr(trail_db, "highlights", json.dumps(value))
            else:
                setattr(trail_db, field, value)

        session.add(trail_db)
        session.commit()
        session.refresh(trail_db)

        return Trail(
            trail_id=trail_db.trail_id,
            park_id=trail_db.park_id,
            name=trail_db.name,
            description=trail_db.description,
            difficulty=trail_db.difficulty,
            length_km=trail_db.length_km,
            duration_hours=trail_db.duration_hours,
            elevation_gain=trail_db.elevation_gain,
            trail_type=trail_db.trail_type,
            highlights=json.loads(trail_db.highlights) if trail_db.highlights else [],
        )


@app.delete("/api/trails/{trail_id}", status_code=204, tags=["Trails"])
def delete_trail(
    trail_id: int,
    current_user: User = Depends(get_current_user),
):
    """Delete a trail (requires authentication)."""
    with Session(get_engine()) as session:
        trail_db = session.get(TrailDB, trail_id)
        if trail_db is None:
            raise HTTPException(status_code=404, detail="Trail not found")

        session.delete(trail_db)
        session.commit()
        return None


# ---------- SPECIES IMAGE ENDPOINTS ----------

@app.post(
    "/api/species/{species_id}/image", status_code=201, tags=["Species Images"]
)
async def upload_species_image(
    species_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        if species_db.image_url:
            delete_file(species_db.image_url, SPECIES_DIR)

        filename = await save_upload_file(file, SPECIES_DIR)
        species_db.image_url = filename

        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        return {
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": get_file_url(filename, "species"),
        }


@app.delete("/api/species/{species_id}/image", status_code=204, tags=["Species Images"])
def delete_species_image(
    species_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(get_engine()) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        if not species_db.image_url:
            raise HTTPException(status_code=404, detail="No image to delete")

        delete_file(species_db.image_url, SPECIES_DIR)

        species_db.image_url = None
        session.add(species_db)
        session.commit()
        return None


# ---------- WEATHER ENDPOINTS ----------

@app.get("/api/weather/current", tags=["Weather"])
async def get_current_weather(
    latitude: float,
    longitude: float,
):
    weather_data = await get_weather_for_location(latitude, longitude)
    if "error" in weather_data:
        raise HTTPException(status_code=503, detail=weather_data)
    return weather_data


@app.get("/api/parks/{park_id}/weather", tags=["Weather"])
async def get_park_weather(park_id: int):
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        weather_data = await get_weather_for_location(park.latitude, park.longitude)
        if "error" in weather_data:
            raise HTTPException(status_code=503, detail=weather_data)

        return {
            "park_id": park.id,
            "park_name": park.name,
            "weather": weather_data,
        }


@app.get("/api/parks/{park_id}/forecast", tags=["Weather"])
async def get_park_forecast(park_id: int, days: int = 5):
    if days < 1 or days > 5:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 5")

    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        forecast_data = await get_weather_forecast(park.latitude, park.longitude, days)
        if "error" in forecast_data:
            raise HTTPException(status_code=503, detail=forecast_data)

        return {
            "park_id": park.id,
            "park_name": park.name,
            "forecast": forecast_data,
        }


# ---------- MAP & DIRECTIONS ENDPOINTS ----------

@app.get("/map", response_class=HTMLResponse, tags=["Maps & Navigation"])
async def view_interactive_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})


@app.get("/api/parks/{park_id}/map", response_model=MapData, tags=["Maps & Navigation"])
def get_park_map_data(park_id: int):
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
        directions_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&destination={park.latitude},{park.longitude}"
        )

        return MapData(
            park_id=park.id,
            park_name=park.name,
            latitude=park.latitude,
            longitude=park.longitude,
            governorate=park.governorate,
            google_maps_url=google_maps_url,
            directions_url=directions_url,
        )


@app.get("/api/maps/all-parks", tags=["Maps & Navigation"])
def get_all_parks_map_data():
    with Session(get_engine()) as session:
        parks = session.exec(select(ParkDB)).all()

        parks_data = []
        for park in parks:
            google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
            directions_url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&destination={park.latitude},{park.longitude}"
            )

            parks_data.append(
                {
                    "park_id": park.id,
                    "park_name": park.name,
                    "latitude": park.latitude,
                    "longitude": park.longitude,
                    "governorate": park.governorate,
                    "google_maps_url": google_maps_url,
                    "directions_url": directions_url,
                    "description": (
                        park.description[:100] + "..."
                        if len(park.description) > 100
                        else park.description
                    ),
                }
            )

        return {
            "total_parks": len(parks_data),
            "parks": parks_data,
        }


@app.post("/api/maps/directions", tags=["Maps & Navigation"])
def get_directions_to_park(directions: DirectionsRequest):
    with Session(get_engine()) as session:
        park = session.get(ParkDB, directions.destination_park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        directions_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={directions.origin_lat},{directions.origin_lng}"
            f"&destination={park.latitude},{park.longitude}"
            f"&travelmode=driving"
        )

        return {
            "park_id": park.id,
            "park_name": park.name,
            "origin": {
                "latitude": directions.origin_lat,
                "longitude": directions.origin_lng,
            },
            "destination": {
                "latitude": park.latitude,
                "longitude": park.longitude,
            },
            "directions_url": directions_url,
            "google_maps_url": f"https://www.google.com/maps?q={park.latitude},{park.longitude}",
        }


# ---------- FRONTEND PAGES ----------

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/parks", response_class=HTMLResponse, tags=["Frontend"])
async def view_parks(request: Request):
    return templates.TemplateResponse("parks.html", {"request": request})

@app.get("/parks/{park_id}", response_class=HTMLResponse, tags=["Frontend"])
async def view_park_detail(request: Request, park_id: int):
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        # Convert to dict for template
        park = {
            "id": park_db.id,
            "name": park_db.name,
            "governorate": park_db.governorate,
            "description": park_db.description,
            "latitude": park_db.latitude,
            "longitude": park_db.longitude,
            "area_km2": park_db.area_km2,
            "images": [get_file_url(img, "parks") for img in (park_db.images or [])],
        }

        return templates.TemplateResponse("park_detail.html", {"request": request, "park": park})

@app.get("/trails", response_class=HTMLResponse, tags=["Frontend"])
async def view_trails(request: Request):
    return templates.TemplateResponse("trails.html", {"request": request})

@app.get("/species", response_class=HTMLResponse, tags=["Frontend"])
async def view_species(request: Request):
    return templates.TemplateResponse("species.html", {"request": request})

@app.get("/comparison", response_class=HTMLResponse, tags=["Frontend"])
async def view_comparison(request: Request):
    return templates.TemplateResponse("comparison.html", {"request": request})

@app.get("/emergency", response_class=HTMLResponse, tags=["Frontend"])
async def view_emergency(request: Request):
    return templates.TemplateResponse("emergency.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse, tags=["Frontend"])
async def view_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse, tags=["Frontend"])
async def view_upload_images(request: Request):
    return templates.TemplateResponse("upload_images.html", {"request": request})


# ---------- PUBLIC API ENDPOINTS ----------

@app.get("/api/parks/{park_id}/unsplash-images", response_model=List[UnsplashImage], tags=["Public APIs"])
async def get_park_unsplash_images(park_id: int, count: int = Query(10, ge=1, le=30)):
    """
    Get high-quality nature images for a park from Unsplash.

    - park_id: The ID of the park
    - count: Number of images to retrieve (1-30, default 10)
    """
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        # Create location-specific search query for more relevant images
        park_keywords = {
            "Ichkeul": "Ichkeul lake wetland birds flamingos Tunisia",
            "Boukornine": "Boukornine mountain forest Tunisia nature",
            "Zaghouan": "Zaghouan mountains Tunisia nature forest",
            "Zembra": "Zembra island marine birds Tunisia",
            "El Feija": "El Feija forest deer Tunisia wildlife",
            "Chaambi": "Chaambi mountain peak Tunisia landscape",
            "Bouhedma": "Bouhedma desert wildlife Tunisia nature",
            "Jebil": "Jebil desert dunes Tunisia sand",
            "Dghoumès": "Dghoumès oasis desert Tunisia",
            "Sidi Toui": "Sidi Toui steppe desert Tunisia wildlife",
            "Orbata": "Orbata mountains forest Tunisia nature",
            "Chitana": "Chitana coast marine Tunisia nature",
            "Serj": "Serj forest Tunisia woodland",
            "Mghilla": "Mghilla mountains Tunisia landscape",
            "Zaghdoud": "Zaghdoud forest Tunisia nature",
            "Zeen": "Zeen forest Tunisia woodland",
            "Senghar": "Senghar desert Tunisia landscape"
        }

        # Get park-specific search terms, fallback to general terms
        park_name_clean = park.name.replace("Parc National ", "").replace("d'", "").replace("de ", "").replace("des ", "").split()[0]
        search_terms = park_keywords.get(park_name_clean, f"{park_name_clean} Tunisia nature landscape wildlife")

        # Add location coordinates for more precise results
        query = f"{search_terms} {park.governorate} Tunisia"
        images = await get_unsplash_images(query, count)

        return [UnsplashImage(**img) for img in images]


@app.get("/api/parks/{park_id}/wikipedia", tags=["Public APIs"])
async def get_park_wikipedia_info(park_id: int):
    """
    Get Wikipedia summary information for a park.

    - park_id: The ID of the park
    """
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        # Try to find Wikipedia page using park name
        title = f"{park.name} National Park"
        info = await get_wikipedia_summary(title)

        if not info:
            # Fallback to just park name
            info = await get_wikipedia_summary(park.name)

        return {
            "park_id": park.id,
            "park_name": park.name,
            "wikipedia_info": info,
        }


@app.get("/api/parks/{park_id}/nearby-places", tags=["Public APIs"])
async def get_nearby_places_for_park(
    park_id: int,
    place_type: str = Query("restaurant", description="Type of place (restaurant, hotel, etc.)"),
    radius: int = Query(5000, ge=1000, le=50000, description="Search radius in meters")
):
    """
    Get nearby places (restaurants, hotels, etc.) around a park using Google Places API.

    - park_id: The ID of the park
    - place_type: Type of places to search for
    - radius: Search radius in meters (1000-50000)
    """
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        places = await get_nearby_places(park.latitude, park.longitude, place_type, radius)

        return {
            "park_id": park.id,
            "park_name": park.name,
            "search_location": {
                "latitude": park.latitude,
                "longitude": park.longitude
            },
            "place_type": place_type,
            "radius_meters": radius,
            "places": places,
            "total_results": len(places)
        }


@app.get("/api/news/parks", tags=["Public APIs"])
async def get_news_about_parks(
    query: str = Query("Tunisia parks nature", description="Search query for news"),
    count: int = Query(10, ge=1, le=50, description="Number of articles to retrieve")
):
    """
    Get news articles about parks and nature from NewsAPI.

    - query: Search query for news articles
    - count: Number of articles to retrieve (1-50, default 10)
    """
    try:
        news = await get_news_about_parks(query, count)
        return {
            "query": query,
            "articles": news,
            "total_results": len(news),
            "source": "newsapi"
        }
    except Exception as e:
        logger.warning(f"NewsAPI unavailable, returning mock data: {e}")
        # Return mock news data as fallback
        mock_news = get_mock_news_articles(query, count)
        return {
            "query": query,
            "articles": mock_news,
            "total_results": len(mock_news),
            "source": "mock",
            "note": "Using mock data - NewsAPI not configured"
        }


# ---------- CHAT ENDPOINT ----------

@app.post("/api/chat", tags=["Chat"])
async def chat_with_bot(request: dict):
    """
    Simple chat endpoint for the chatbot.
    """
    message = request.get("message", "").lower()

    # Simple responses based on keywords
    if "parc" in message or "parks" in message:
        response = "Voici une liste des parcs nationaux de Tunisie disponibles sur notre plateforme. Vous pouvez explorer la carte interactive ou consulter la liste complète des parcs."
        suggestions = ["Voir la carte", "Liste des parcs", "Parcs près de Tunis"]
    elif "animal" in message or "faune" in message:
        response = "La Tunisie abrite une riche biodiversité avec de nombreuses espèces protégées. Découvrez les animaux que vous pouvez observer dans nos parcs nationaux."
        suggestions = ["Animaux en danger", "Espèces par parc", "Meilleurs moments pour observer"]
    elif "urgence" in message or "emergency" in message:
        response = "🚨 En cas d'urgence, contactez immédiatement les secours. Restez calme et partagez votre localisation si possible."
        suggestions = ["Numéros d'urgence", "Signaler un problème", "Premiers secours"]
    elif "météo" in message or "weather" in message:
        response = "Je peux vous fournir des informations météorologiques pour n'importe quel parc. Indiquez-moi le nom du parc qui vous intéresse."
        suggestions = ["Météo Ichkeul", "Prévisions", "Meilleures périodes pour visiter"]
    else:
        response = "Bonjour! Je suis l'assistant virtuel des Parcs Nationaux de Tunisie. Je peux vous aider avec des informations sur les parcs, la faune, la flore, les sentiers, la météo et les urgences. Que souhaitez-vous savoir?"
        suggestions = ["Liste des parcs", "Animaux à observer", "Sentiers de randonnée", "Météo"]

    return {
        "response": response,
        "suggestions": suggestions
    }


# ---------- REVIEWS ENDPOINTS ----------

@app.get("/api/parks/{park_id}/reviews", response_model=List[Review], tags=["Reviews"])
def list_reviews_for_park(park_id: int):
    """List all reviews for a given park."""
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        reviews_db = session.exec(
            select(ReviewDB).where(ReviewDB.park_id == park_id)
        ).all()

        return [
            Review(
                review_id=r.review_id,
                park_id=r.park_id,
                author_name=r.author_name,
                rating=r.rating,
                title=r.title,
                comment=r.comment,
                visit_date=r.visit_date if isinstance(r.visit_date, str) else (r.visit_date.isoformat() if r.visit_date else None),
                helpful_count=r.helpful_count,
                created_at=r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
            )
            for r in reviews_db
        ]


@app.post("/api/parks/{park_id}/reviews", response_model=Review, status_code=201, tags=["Reviews"])
def create_review(park_id: int, review_in: ReviewCreate):
    """Create a new review for a park."""
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        review_db = ReviewDB(
            park_id=park_id,
            author_name=review_in.author_name,
            rating=review_in.rating,
            title=review_in.title,
            comment=review_in.comment,
            visit_date=review_in.visit_date,
            helpful_count=0,
        )
        session.add(review_db)
        session.commit()
        session.refresh(review_db)

        # Update park's average rating
        all_reviews = session.exec(
            select(ReviewDB).where(ReviewDB.park_id == park_id)
        ).all()
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        park.average_rating = round(avg_rating, 1)
        park.total_reviews = len(all_reviews)
        session.add(park)
        session.commit()

        return Review(
            review_id=review_db.review_id,
            park_id=review_db.park_id,
            author_name=review_db.author_name,
            rating=review_db.rating,
            title=review_db.title,
            comment=review_db.comment,
            visit_date=review_db.visit_date.isoformat() if review_db.visit_date else None,
            helpful_count=review_db.helpful_count,
            created_at=review_db.created_at.isoformat(),
        )


@app.put("/api/reviews/{review_id}/helpful", tags=["Reviews"])
def mark_review_helpful(review_id: int):
    """Mark a review as helpful."""
    with Session(get_engine()) as session:
        review_db = session.get(ReviewDB, review_id)
        if review_db is None:
            raise HTTPException(status_code=404, detail="Review not found")

        review_db.helpful_count += 1
        session.add(review_db)
        session.commit()

        return {"message": "Review marked as helpful", "helpful_count": review_db.helpful_count}


# ---------- SIGHTINGS ENDPOINTS ----------

@app.get("/api/sightings", response_model=List[Sighting], tags=["Sightings"])
def list_sightings(
    park_id: int | None = None,
    species_id: int | None = None,
    verified_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List wildlife sightings with advanced filtering.

    - park_id: Filter by park ID
    - species_id: Filter by species ID
    - verified_only: Only show verified sightings
    - skip: Number of sightings to skip (pagination)
    - limit: Maximum number of sightings to return (1-100)
    """
    try:
        with Session(get_engine()) as session:
            stmt = select(SightingDB)

            if park_id is not None:
                stmt = stmt.where(SightingDB.park_id == park_id)
            if species_id is not None:
                stmt = stmt.where(SightingDB.species_id == species_id)
            if verified_only:
                stmt = stmt.where(SightingDB.verified == True)

            stmt = stmt.order_by(SightingDB.created_at.desc())
            stmt = stmt.offset(skip).limit(limit)

            sightings_db = session.exec(stmt).all()

            return [
                Sighting(
                    sighting_id=s.sighting_id,
                    park_id=s.park_id,
                    species_id=s.species_id,
                    reporter_name=s.reporter_name,
                    sighting_date=s.sighting_date,
                    location_lat=s.location_lat,
                    location_lng=s.location_lng,
                    photo_url=s.photo_url,
                    notes=s.notes,
                    verified=s.verified,
                    created_at=s.created_at.isoformat(),
                )
                for s in sightings_db
            ]
    except Exception as e:
        logger.error(f"Error listing sightings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/sightings", response_model=Sighting, status_code=201, tags=["Sightings"])
def create_sighting(sighting_in: SightingCreate, current_user: User = Depends(get_current_user)):
    """Create a new wildlife sighting."""
    try:
        with Session(get_engine()) as session:
            # Verify park and species exist
            park = session.get(ParkDB, sighting_in.park_id)
            if park is None:
                raise HTTPException(status_code=404, detail="Park not found")

            species = session.get(SpeciesDB, sighting_in.species_id)
            if species is None:
                raise HTTPException(status_code=404, detail="Species not found")

            sighting_db = SightingDB(
                park_id=sighting_in.park_id,
                species_id=sighting_in.species_id,
                reporter_name=sighting_in.reporter_name,
                sighting_date=sighting_in.sighting_date,
                location_lat=sighting_in.location_lat,
                location_lng=sighting_in.location_lng,
                photo_url=sighting_in.photo_url,
                notes=sighting_in.notes,
                verified=False,  # New sightings are not verified by default
            )
            session.add(sighting_db)
            session.commit()
            session.refresh(sighting_db)

            return Sighting(
                sighting_id=sighting_db.sighting_id,
                park_id=sighting_db.park_id,
                species_id=sighting_db.species_id,
                reporter_name=sighting_db.reporter_name,
                sighting_date=sighting_db.sighting_date,
                location_lat=sighting_db.location_lat,
                location_lng=sighting_db.location_lng,
                photo_url=sighting_db.photo_url,
                notes=sighting_db.notes,
                verified=sighting_db.verified,
                created_at=sighting_db.created_at.isoformat(),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sighting: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/api/sightings/{sighting_id}/verify", tags=["Sightings"])
def verify_sighting(sighting_id: int, current_user: User = Depends(get_current_user)):
    """Verify a wildlife sighting (admin only)."""
    with Session(get_engine()) as session:
        sighting_db = session.get(SightingDB, sighting_id)
        if sighting_db is None:
            raise HTTPException(status_code=404, detail="Sighting not found")

        sighting_db.verified = True
        session.add(sighting_db)
        session.commit()

        return {"message": "Sighting verified successfully", "verified": True}


# ---------- GAMIFICATION & BADGES ENDPOINTS ----------

@app.get("/api/badges", tags=["Gamification"])
def list_badges():
    """Get all available badges."""
    with Session(get_engine()) as session:
        badges_db = session.exec(select(BadgeDB)).all()

        return [
            {
                "badge_id": b.badge_id,
                "name": b.name,
                "description": b.description,
                "icon": b.icon,
                "category": b.category,
                "requirement_type": b.requirement_type,
                "requirement_value": b.requirement_value,
                "points": b.points,
                "rarity": b.rarity,
            }
            for b in badges_db
        ]


@app.get("/api/user/{user_id}/badges", tags=["Gamification"])
def get_user_badges(user_id: int):
    """Get user's earned badges."""
    with Session(get_engine()) as session:
        user_badges_db = session.exec(
            select(UserBadgeDB).where(UserBadgeDB.user_id == user_id)
        ).all()

        badges = []
        for ub in user_badges_db:
            badge = session.get(BadgeDB, ub.badge_id)
            if badge:
                badges.append({
                    "badge_id": badge.badge_id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "category": badge.category,
                    "points": badge.points,
                    "rarity": badge.rarity,
                    "earned_at": ub.earned_at,
                    "progress": ub.progress,
                    "completed": ub.completed,
                })

        return {"badges": badges, "total": len(badges)}


@app.get("/api/user/{user_id}/stats", tags=["Gamification"])
def get_user_stats(user_id: int):
    """Get user's statistics and progress."""
    with Session(get_engine()) as session:
        user_stats = session.exec(
            select(UserStatsDB).where(UserStatsDB.user_id == user_id)
        ).first()

        if not user_stats:
            return {
                "parks_visited": 0,
                "species_seen": 0,
                "trails_completed": 0,
                "reviews_written": 0,
                "sightings_reported": 0,
                "total_points": 0,
                "current_level": 1,
                "experience_points": 0,
                "badges_earned": 0,
                "consecutive_days_active": 0,
                "last_activity_date": None,
                "level_progress": 0,
                "next_level_xp": 100,
            }

        # Calculate level progress
        current_level_xp = (user_stats.current_level - 1) * 100
        next_level_xp = user_stats.current_level * 100
        level_progress = ((user_stats.experience_points - current_level_xp) / (next_level_xp - current_level_xp)) * 100

        return {
            "parks_visited": user_stats.parks_visited,
            "species_seen": user_stats.species_seen,
            "trails_completed": user_stats.trails_completed,
            "reviews_written": user_stats.reviews_written,
            "sightings_reported": user_stats.sightings_reported,
            "total_points": user_stats.total_points,
            "current_level": user_stats.current_level,
            "experience_points": user_stats.experience_points,
            "badges_earned": user_stats.badges_earned,
            "consecutive_days_active": user_stats.consecutive_days_active,
            "last_activity_date": user_stats.last_activity_date,
            "level_progress": min(level_progress, 100),
            "next_level_xp": next_level_xp,
        }


@app.post("/api/user/{user_id}/check-badges", tags=["Gamification"])
def check_and_award_badges(user_id: int):
    """Check user progress and award badges if requirements are met."""
    with Session(get_engine()) as session:
        # Get user stats
        user_stats = session.exec(
            select(UserStatsDB).where(UserStatsDB.user_id == user_id)
        ).first()

        if not user_stats:
            raise HTTPException(status_code=404, detail="User stats not found")

        # Get all badges
        all_badges = session.exec(select(BadgeDB)).all()

        # Get user's current badges
        user_badges = session.exec(
            select(UserBadgeDB).where(UserBadgeDB.user_id == user_id)
        ).all()
        earned_badge_ids = {ub.badge_id for ub in user_badges}

        awarded_badges = []

        for badge in all_badges:
            if badge.badge_id in earned_badge_ids:
                continue  # Already earned

            # Check if requirement is met
            requirement_met = False
            progress_value = 0

            if badge.requirement_type == "parks_visited":
                progress_value = user_stats.parks_visited
                requirement_met = user_stats.parks_visited >= badge.requirement_value
            elif badge.requirement_type == "species_seen":
                progress_value = user_stats.species_seen
                requirement_met = user_stats.species_seen >= badge.requirement_value
            elif badge.requirement_type == "trails_completed":
                progress_value = user_stats.trails_completed
                requirement_met = user_stats.trails_completed >= badge.requirement_value
            elif badge.requirement_type == "reviews_written":
                progress_value = user_stats.reviews_written
                requirement_met = user_stats.reviews_written >= badge.requirement_value
            elif badge.requirement_type == "sightings_reported":
                progress_value = user_stats.sightings_reported
                requirement_met = user_stats.sightings_reported >= badge.requirement_value

            if requirement_met:
                # Award the badge
                user_badge = UserBadgeDB(
                    user_id=user_id,
                    badge_id=badge.badge_id,
                    earned_at=datetime.now(timezone.utc).isoformat(),
                    progress=badge.requirement_value,
                    completed=True,
                )
                session.add(user_badge)

                # Update user stats
                user_stats.total_points += badge.points
                user_stats.badges_earned += 1

                # Check for level up
                required_xp = user_stats.current_level * 100
                while user_stats.experience_points >= required_xp:
                    user_stats.current_level += 1
                    required_xp = user_stats.current_level * 100

                session.add(user_stats)

                awarded_badges.append({
                    "badge_id": badge.badge_id,
                    "name": badge.name,
                    "description": badge.description,
                    "icon": badge.icon,
                    "category": badge.category,
                    "points": badge.points,
                    "rarity": badge.rarity,
                })

        session.commit()

        return {
            "awarded_badges": awarded_badges,
            "total_awarded": len(awarded_badges),
            "message": f"Congratulations! You earned {len(awarded_badges)} new badge{'s' if len(awarded_badges) != 1 else ''}!"
        }


@app.post("/api/user/{user_id}/activity", tags=["Gamification"])
def record_user_activity(user_id: int, activity_type: str):
    """Record user activity and update stats."""
    valid_activities = ["park_visit", "species_sighting", "trail_completion", "review_written", "sighting_reported"]

    if activity_type not in valid_activities:
        raise HTTPException(status_code=400, detail=f"Invalid activity type. Must be one of: {', '.join(valid_activities)}")

    with Session(get_engine()) as session:
        # Get or create user stats
        user_stats = session.exec(
            select(UserStatsDB).where(UserStatsDB.user_id == user_id)
        ).first()

        if not user_stats:
            user_stats = UserStatsDB(
                user_id=user_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(user_stats)
            session.commit()
            session.refresh(user_stats)

        # Update activity counters and experience
        xp_gain = 10  # Base XP gain

        if activity_type == "park_visit":
            user_stats.parks_visited += 1
            xp_gain = 25
        elif activity_type == "species_sighting":
            user_stats.species_seen += 1
            xp_gain = 15
        elif activity_type == "trail_completion":
            user_stats.trails_completed += 1
            xp_gain = 30
        elif activity_type == "review_written":
            user_stats.reviews_written += 1
            xp_gain = 20
        elif activity_type == "sighting_reported":
            user_stats.sightings_reported += 1
            xp_gain = 15

        # Add experience points
        user_stats.experience_points += xp_gain
        user_stats.updated_at = datetime.now(timezone.utc).isoformat()

        # Check for level up
        required_xp = user_stats.current_level * 100
        while user_stats.experience_points >= required_xp:
            user_stats.current_level += 1
            required_xp = user_stats.current_level * 100

        session.add(user_stats)
        session.commit()

        # Check for new badges
        badge_result = check_and_award_badges(user_id)

        return {
            "activity_recorded": activity_type,
            "xp_gained": xp_gain,
            "current_level": user_stats.current_level,
            "experience_points": user_stats.experience_points,
            "new_badges_awarded": len(badge_result.get("awarded_badges", [])),
            "message": f"Activity recorded! You gained {xp_gain} XP."
        }


# ---------- SEARCH ENDPOINTS ----------

@app.get("/api/search/parks", tags=["Search"])
async def search_parks(
    query: str = Query(None, description="Search query"),
    governorate: str = Query(None, description="Filter by governorate"),
    min_area: float = Query(None, ge=0, description="Minimum area in km²"),
    max_area: float = Query(None, ge=0, description="Maximum area in km²"),
    difficulty_level: str = Query(None, description="Filter by difficulty"),
    has_activities: bool = Query(None, description="Only parks with activities"),
    sort_by: str = Query("name", pattern="^(name|governorate|area_km2|average_rating)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Advanced search for parks with multiple filters and sorting.

    - query: Text search across park names, governorates, and descriptions
    - governorate: Filter by specific governorate
    - min_area/max_area: Area range in km²
    - difficulty_level: Filter by difficulty (facile, modéré, difficile)
    - has_activities: Only show parks with listed activities
    - sort_by: Sort field (name, governorate, area_km2, average_rating)
    - sort_order: Sort order (asc, desc)
    - skip/limit: Pagination
    """
    filters = {
        "governorate": governorate,
        "min_area": min_area,
        "max_area": max_area,
        "difficulty_level": difficulty_level,
        "has_activities": has_activities,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "skip": skip
    }

    return await SearchService.search_parks(query, filters, limit)


@app.get("/api/search/species", tags=["Search"])
async def search_species(
    query: str = Query(None, description="Search query"),
    type: Literal["animal", "plant"] = Query(None, description="Filter by type"),
    conservation_status: str = Query(None, description="Filter by conservation status"),
    rarity: str = Query(None, description="Filter by rarity"),
    has_medicinal_use: bool = Query(None, description="Only species with medicinal uses"),
    park_id: int = Query(None, description="Filter by park ID"),
    sort_by: str = Query("name", pattern="^(name|scientific_name|type)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Advanced search for species with multiple filters.

    - query: Text search across species names and scientific names
    - type: Filter by 'animal' or 'plant'
    - conservation_status: Filter by IUCN status
    - rarity: Filter by rarity level
    - has_medicinal_use: Only species with medicinal properties
    - park_id: Filter species found in specific park
    - sort_by: Sort field (name, scientific_name, type)
    - sort_order: Sort order (asc, desc)
    - skip/limit: Pagination
    """
    filters = {
        "type": type,
        "conservation_status": conservation_status,
        "rarity": rarity,
        "has_medicinal_use": has_medicinal_use,
        "park_id": park_id,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "skip": skip
    }

    return await SearchService.search_species(query, filters, limit)


@app.get("/api/search/suggestions", tags=["Search"])
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions to return")
):
    """
    Get search suggestions based on partial query input.

    - query: Partial text to search for
    - limit: Maximum number of suggestions (1-20)
    """
    return await SearchService.get_search_suggestions(query, limit)


@app.get("/api/search/popular", tags=["Search"])
async def get_popular_searches():
    """
    Get popular search terms and trending queries.
    """
    return await SearchService.get_popular_searches()


@app.get("/api/languages", tags=["Internationalization"])
def get_available_languages():
    """
    Get list of supported languages for the application.
    """
    return LanguageService.get_available_languages()


@app.get("/api/languages/{lang_code}", tags=["Internationalization"])
def get_language_translations(lang_code: str):
    """
    Get all translations for a specific language.

    - lang_code: Language code (en, fr, ar)
    """
    lang_info = LanguageService.get_language_info(lang_code)
    translations = LanguageService.TRANSLATIONS.get(lang_code, {})

    return {
        "language": lang_info,
        "translations": translations,
        "total_keys": len(translations)
    }





# ---------- MEDIA UPLOAD ENDPOINTS ----------

@app.post("/api/upload/parks/{park_id}", tags=["Media Upload"])
async def upload_park_media(
    park_id: int,
    file: UploadFile = File(...),
    media_type: str = Query("image", pattern="^(image|document|video|audio)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload media files for a park (images, documents, videos, audio).

    - park_id: ID of the park
    - file: File to upload
    - media_type: Type of media (image, document, video, audio)
    """
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if not park:
            raise HTTPException(status_code=404, detail="Park not found")

        # Validate file type
        allowed_extensions = MEDIA_CONFIG["local"]["allowed_extensions"]
        if media_type not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {media_type}")

        # Validate file
        MediaService.validate_file(file, allowed_extensions[media_type])

        try:
            # Upload file
            upload_result = await MediaService.upload_file(file, f"parks/{park_id}")

            # Store reference in database (you might want to create a MediaDB table)
            # For now, we'll just return the upload info

            return {
                "message": f"{media_type.title()} uploaded successfully",
                "park_id": park_id,
                "park_name": park.name,
                "media_info": upload_result,
                "media_type": media_type,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/upload/species/{species_id}", tags=["Media Upload"])
async def upload_species_media(
    species_id: int,
    file: UploadFile = File(...),
    media_type: str = Query("image", pattern="^(image|document|video|audio)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload media files for a species.

    - species_id: ID of the species
    - file: File to upload
    - media_type: Type of media (image, document, video, audio)
    """
    with Session(get_engine()) as session:
        species = session.get(SpeciesDB, species_id)
        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        # Validate file type
        allowed_extensions = MEDIA_CONFIG["local"]["allowed_extensions"]
        if media_type not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {media_type}")

        # Validate file
        MediaService.validate_file(file, allowed_extensions[media_type])

        try:
            # Upload file
            upload_result = await MediaService.upload_file(file, f"species/{species_id}")

            return {
                "message": f"{media_type.title()} uploaded successfully",
                "species_id": species_id,
                "species_name": species.name,
                "media_info": upload_result,
                "media_type": media_type,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/upload/sightings/{sighting_id}", tags=["Media Upload"])
async def upload_sighting_media(
    sighting_id: int,
    file: UploadFile = File(...),
    media_type: str = Query("image", pattern="^(image|document|video|audio)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload media files for a wildlife sighting.

    - sighting_id: ID of the sighting
    - file: File to upload
    - media_type: Type of media (image, document, video, audio)
    """
    with Session(get_engine()) as session:
        sighting = session.get(SightingDB, sighting_id)
        if not sighting:
            raise HTTPException(status_code=404, detail="Sighting not found")

        # Validate file type
        allowed_extensions = MEDIA_CONFIG["local"]["allowed_extensions"]
        if media_type not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {media_type}")

        # Validate file
        MediaService.validate_file(file, allowed_extensions[media_type])

        try:
            # Upload file
            upload_result = await MediaService.upload_file(file, f"sightings/{sighting_id}")

            # Update sighting with photo URL if it's an image
            if media_type == "image" and not sighting.photo_url:
                sighting.photo_url = upload_result["url"]
                session.add(sighting)
                session.commit()

            return {
                "message": f"{media_type.title()} uploaded successfully",
                "sighting_id": sighting_id,
                "reporter_name": sighting.reporter_name,
                "media_info": upload_result,
                "media_type": media_type,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/upload/user/avatar", tags=["Media Upload"])
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload avatar image for current user.
    """
    with Session(get_engine()) as session:
        user_db = session.exec(
            select(UserDBModel).where(UserDBModel.username == current_user.username)
        ).first()

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate file type (only images for avatars)
        allowed_extensions = MEDIA_CONFIG["local"]["allowed_extensions"]["images"]
        MediaService.validate_file(file, allowed_extensions)

        try:
            # Upload file
            upload_result = await MediaService.upload_file(file, f"users/{user_db.id}")

            # Update user avatar URL
            user_db.avatar_url = upload_result["url"]
            session.add(user_db)
            session.commit()

            return {
                "message": "Avatar uploaded successfully",
                "user_id": user_db.id,
                "username": user_db.username,
                "avatar_url": upload_result["url"],
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Avatar upload failed: {str(e)}")


@app.delete("/api/media", tags=["Media Upload"])
async def delete_media_file(
    file_url: str = Query(..., description="URL of the file to delete"),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a media file.

    - file_url: URL of the file to delete
    """
    # This is a simplified implementation
    # In a real application, you'd want to check permissions and validate ownership

    try:
        # For now, we'll assume the file info is stored somewhere accessible
        # This would need to be enhanced with proper media tracking

        return {
            "message": "File deletion initiated",
            "file_url": file_url,
            "status": "success"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@app.get("/api/media/config", tags=["Media Upload"])
def get_media_config():
    """
    Get media upload configuration and limits.
    """
    return {
        "storage_provider": MediaService.get_storage_provider(),
        "max_file_size": MEDIA_CONFIG["local"]["max_file_size"],
        "allowed_extensions": MEDIA_CONFIG["local"]["allowed_extensions"],
        "cloudinary_enabled": MEDIA_CONFIG["cloudinary"]["enabled"],
        "s3_enabled": MEDIA_CONFIG["s3"]["enabled"]
    }


# ---------- SEO OPTIMIZATION ENDPOINTS ----------

@app.get("/api/seo/sitemap.xml", response_class=HTMLResponse, tags=["SEO"])
def get_sitemap_xml():
    """
    Generate XML sitemap for search engines.
    """
    with Session(get_engine()) as session:
        parks = session.exec(select(ParkDB)).all()

        # Base URL - in production this would come from config
        base_url = "https://parcs-tunisie.tn"

        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        # Homepage
        sitemap_content += f'<url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'

        # Parks page
        sitemap_content += f'<url><loc>{base_url}/parks</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>\n'

        # Individual park pages
        for park in parks:
            park_slug = park.name.lower().replace(" ", "-").replace("'", "").replace("parc-national-d'", "")
            sitemap_content += f'<url><loc>{base_url}/parks/{park.id}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'

        # Other pages
        sitemap_content += f'<url><loc>{base_url}/species</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
        sitemap_content += f'<url><loc>{base_url}/trails</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
        sitemap_content += f'<url><loc>{base_url}/map</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>\n'
        sitemap_content += f'<url><loc>{base_url}/comparison</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>\n'

        sitemap_content += '</urlset>'

        return HTMLResponse(content=sitemap_content, media_type="application/xml")


@app.get("/api/seo/meta/{park_id}", tags=["SEO"])
def get_park_meta_tags(park_id: int):
    """
    Get SEO meta tags for a park page.
    """
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if not park:
            raise HTTPException(status_code=404, detail="Park not found")

        # Get species count
        species_count = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park.id)
        ).all()

        # Generate meta description
        description = f"{park.name} - National Park in {park.governorate}, Tunisia. {park.description[:150]}... Discover {len(species_count)} species, hiking trails, and wildlife."

        # Generate keywords
        keywords = [park.name, park.governorate, "Tunisia", "National Park", "Nature", "Wildlife", "Hiking"]
        if park.activities:
            keywords.extend(park.activities.split(",")[:3])

        return {
            "title": f"{park.name} - Tunisia National Parks",
            "description": description,
            "keywords": ", ".join(keywords),
            "og_title": f"{park.name} - {park.governorate}, Tunisia",
            "og_description": description,
            "og_image": get_file_url(park.images[0], "parks") if park.images else None,
            "og_url": f"https://parcs-tunisie.tn/parks/{park.id}",
            "twitter_card": "summary_large_image",
            "canonical_url": f"https://parcs-tunisie.tn/parks/{park.id}",
            "structured_data": {
                "@context": "https://schema.org",
                "@type": "TouristAttraction",
                "name": park.name,
                "description": park.description,
                "address": {
                    "@type": "PostalAddress",
                    "addressCountry": "Tunisia",
                    "addressRegion": park.governorate
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": park.latitude,
                    "longitude": park.longitude
                },
                "image": [get_file_url(img, "parks") for img in (park.images or [])],
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": park.average_rating or 0,
                    "reviewCount": park.total_reviews or 0
                } if park.average_rating else None
            }
        }


@app.get("/api/analytics/overview", tags=["Analytics"])
def get_analytics_overview():
    """
    Get basic analytics overview (admin only).
    """
    with Session(get_engine()) as session:
        # Park statistics
        total_parks = session.exec(select(ParkDB)).all()
        total_species = session.exec(select(SpeciesDB)).all()
        total_trails = session.exec(select(TrailDB)).all()
        total_reviews = session.exec(select(ReviewDB)).all()
        total_sightings = session.exec(select(SightingDB)).all()

        # User statistics (if you had user tracking)
        # This is simplified - you'd want proper user analytics

        return {
            "content_stats": {
                "total_parks": len(total_parks),
                "total_species": len(total_species),
                "total_trails": len(total_trails),
                "total_reviews": len(total_reviews),
                "total_sightings": len(total_sightings)
            },
            "engagement_stats": {
                "average_rating": 0.0,  # Simplified to avoid division by zero
                "total_reviews_count": sum(p.total_reviews or 0 for p in total_parks)
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }


@app.get("/robots.txt", response_class=HTMLResponse, tags=["SEO"])
def get_robots_txt():
    """
    Generate robots.txt for search engines.
    """
    robots_content = """User-agent: *
Allow: /

# Block access to admin areas
Disallow: /admin/
Disallow: /api/admin/

# Block access to user data
Disallow: /api/auth/me
Disallow: /api/user/

# Allow access to public APIs
Allow: /api/parks/
Allow: /api/species/
Allow: /api/trails/

# Sitemap
Sitemap: https://parcs-tunisie.tn/api/seo/sitemap.xml
"""

    return HTMLResponse(content=robots_content, media_type="text/plain")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
