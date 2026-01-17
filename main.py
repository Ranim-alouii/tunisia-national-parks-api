"""
Minimal FastAPI application for Tunisia National Parks
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi import Query

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIASGIMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from database import init_db
from config import settings

from database import get_engine

from sqlmodel import select, or_, Session
import json
from pathlib import Path
from models import ParkDB, TrailDB, ParkSpeciesLink, SpeciesDB, ReviewDB, SightingDB
from weather_service import get_weather_for_location
# Import routers
from routers import parks, species, trails, auth

# API Documentation Metadata
tags_metadata = [
    {
        "name": "Parks",
        "description": "Operations related to Tunisia's national parks - listing, details, comparisons, and management.",
        "externalDocs": {
            "description": "Learn more about Tunisia's National Parks",
            "url": "https://en.wikipedia.org/wiki/National_parks_of_Tunisia",
        },
    },
    {
        "name": "Species",
        "description": "Biodiversity data - wildlife species, conservation status, park-species relationships.",
        "externalDocs": {
            "description": "IUCN Red List",
            "url": "https://www.iucnredlist.org/",
        },
    },
    {
        "name": "Authentication",
        "description": "User authentication and authorization endpoints.",
    },
    {
        "name": "Weather",
        "description": "Real-time weather data and forecasts for parks.",
    },
    {
        "name": "Reviews",
        "description": "User reviews and ratings for parks.",
    },
    {
        "name": "Trails",
        "description": "Hiking trails and outdoor activities.",
    },
    {
        "name": "Sightings",
        "description": "Wildlife sighting reports and verification.",
    },
    {
        "name": "Gamification",
        "description": "Badges, achievements, and user progress tracking.",
    },
    {
        "name": "Search",
        "description": "Advanced search and discovery features.",
    },
    {
        "name": "Maps & Navigation",
        "description": "Interactive maps and directions.",
    },
    {
        "name": "Public APIs",
        "description": "Third-party API integrations (Unsplash, Wikipedia, etc.).",
    },
    {
        "name": "Media Upload",
        "description": "File upload and media management.",
    },
    {
        "name": "SEO",
        "description": "Search engine optimization endpoints.",
    },
    {
        "name": "Analytics",
        "description": "Usage analytics and reporting.",
    },
    {
        "name": "Internationalization",
        "description": "Multi-language support.",
    },
    {
        "name": "Frontend",
        "description": "Web application routes and templates.",
    },
    {
        "name": "Health",
        "description": "System health checks and monitoring.",
    },
]

# Create FastAPI app
app = FastAPI(
    title="Tunisia National Parks Professional API",
    description="""
# 🌿 Tunisia National Parks API

A comprehensive REST API for exploring Tunisia's magnificent national parks, biodiversity, and outdoor activities.

## 🌟 Features

* **18 National Parks** - Complete database of Tunisia's protected areas
* **Biodiversity Data** - 250+ species with conservation status
* **Weather Integration** - Real-time forecasts for all parks
* **Interactive Maps** - Google Maps integration with directions
* **User Reviews** - Community-driven park ratings and experiences
* **Gamification** - Achievement system with badges and progress tracking
* **Multi-language** - Support for Arabic, French, and English
* **Media Management** - Image uploads and gallery management

## 🚀 Quick Start

```bash
# Get all parks
GET /api/parks

# Search species
GET /api/species?type=animal&conservation_status=endangered

# Get weather for a park
GET /api/parks/{park_id}/weather

# Compare parks
GET /api/parks/compare?park_ids=1,2,3
```

## 📋 API Endpoints by Category

* **Core Data**: Parks, Species, Trails
* **User Features**: Reviews, Sightings, Badges
* **External Services**: Weather, Maps, Media
* **System**: Health, Analytics, Search

## 🔐 Authentication

Some endpoints require authentication. Use JWT tokens obtained from `/auth/token`.

## 📞 Contact

**Developer**: Tunisia National Parks Team
**Email**: contact@parcs-tunisie.tn
**Website**: https://parcs-tunisie.tn
**API Version**: 3.0.0

---

*Built by Ranim ALOUI with FastAPI, SQLAlchemy, and ❤️ for Tunisia's natural heritage*
    """,
    version="3.0.0",
    contact={
        "name": "Tunisia National Parks API Support",
        "url": "https://parcs-tunisie.tn/contact",
        "email": "api@parcs-tunisie.tn",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Include routers immediately after app creation
app.include_router(parks.router)
app.include_router(species.router)
app.include_router(trails.router)
app.include_router(auth.router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIASGIMiddleware)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.unsplash.com;"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Logging
logger = logging.getLogger("tunisia_parks")
logging.basicConfig(level=logging.INFO)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Fallback static file routes
@app.get("/static/{path:path}")
async def serve_static(path: str):
    from fastapi.responses import FileResponse
    import os
    file_path = os.path.join("static", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@app.get("/uploads/{path:path}")
async def serve_uploads(path: str):
    from fastapi.responses import FileResponse
    import os
    file_path = os.path.join("uploads", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# Request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_ms = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({process_ms:.2f}ms)")
    return response

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": "Validation failed", "details": exc.errors()}},
    )

# Frontend routes - SPA routing: serve index.html for all non-API routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Health check
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "3.0.0"}

# Park comparison endpoint
@app.get("/api/parks/compare")
def compare_parks(park_ids: str = Query("", description="Comma-separated list of park IDs to compare")):
    """Compare multiple parks side by side."""
    if not park_ids or not park_ids.strip():
        raise HTTPException(status_code=400, detail="park_ids parameter is required")

    try:
        ids = []
        for id_str in park_ids.split(","):
            id_str = id_str.strip()
            if id_str:
                try:
                    park_id = int(id_str)
                    if park_id > 0:
                        ids.append(park_id)
                except ValueError:
                    continue

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

        comparison_data = []
        for park in parks_db:
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

# Weather endpoints
@app.get("/api/parks/{park_id}/weather")
async def get_park_weather(park_id: int):
    """Get weather for a park."""
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

# Search endpoints
@app.get("/api/search/parks")
async def search_parks(
    query: str = Query(None, description="Search query"),
    governorate: str = Query(None, description="Filter by governorate"),
    min_area: float = Query(None, ge=0, description="Minimum area in km²"),
    max_area: float = Query(None, ge=0, description="Maximum area in km²"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    """Advanced search for parks."""
    filters = {
        "governorate": governorate,
        "min_area": min_area,
        "max_area": max_area,
        "skip": skip
    }

    with Session(get_engine()) as session:
        stmt = select(ParkDB)

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

        if filters.get('governorate'):
            stmt = stmt.where(ParkDB.governorate == filters['governorate'])

        if filters.get('min_area'):
            stmt = stmt.where(ParkDB.area_km2 >= filters['min_area'])

        if filters.get('max_area') and filters['max_area'] > 0:
            stmt = stmt.where(ParkDB.area_km2 <= filters['max_area'])

        stmt = stmt.offset(filters.get('skip', 0)).limit(limit)
        results = session.exec(stmt).all()

        enhanced_results = []
        for park in results:
            enhanced_results.append({
                "id": park.id,
                "name": park.name,
                "governorate": park.governorate,
                "description": park.description,
                "latitude": park.latitude,
                "longitude": park.longitude,
                "area_km2": park.area_km2,
                "images": [f"/uploads/parks/{img}" for img in (json.loads(park.images) if park.images else [])],
            })

        total_count = len(session.exec(select(ParkDB)).all())

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

# Analytics endpoint
@app.get("/api/analytics/overview")
def get_analytics_overview():
    """Get analytics overview."""
    with Session(get_engine()) as session:
        total_parks = len(session.exec(select(ParkDB)).all())
        total_species = len(session.exec(select(SpeciesDB)).all())
        total_trails = len(session.exec(select(TrailDB)).all())
        total_reviews = len(session.exec(select(ReviewDB)).all())
        total_sightings = len(session.exec(select(SightingDB)).all())

        return {
            "content_stats": {
                "total_parks": total_parks,
                "total_species": total_species,
                "total_trails": total_trails,
                "total_reviews": total_reviews,
                "total_sightings": total_sightings
            },
            "engagement_stats": {
                "average_rating": 0.0,
                "total_reviews_count": sum(p.total_reviews or 0 for p in session.exec(select(ParkDB)).all())
            }
        }

# Languages endpoint
@app.get("/api/languages")
def get_available_languages():
    """Get available languages."""
    return [
        {
            "code": "en",
            "name": "English",
            "flag": "🇺🇸",
            "direction": "ltr"
        },
        {
            "code": "fr",
            "name": "Français",
            "flag": "🇫🇷",
            "direction": "ltr"
        },
        {
            "code": "ar",
            "name": "العربية",
            "flag": "🇹🇳",
            "direction": "rtl"
        }
    ]

# Media config endpoint
@app.get("/api/media/config")
def get_media_config():
    """Get media configuration."""
    return {
        "storage_provider": "local",
        "max_file_size": 10 * 1024 * 1024,
        "allowed_extensions": {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
            "documents": [".pdf", ".doc", ".docx", ".txt"],
            "videos": [".mp4", ".avi", ".mov", ".wmv"],
            "audio": [".mp3", ".wav", ".ogg"]
        },
        "cloudinary_enabled": False,
        "s3_enabled": False
    }

# Chat endpoint
@app.post("/api/chat")
async def chat_with_bot(request: dict):
    """Simple chat endpoint."""
    message = request.get("message", "").lower()

    if "parc" in message or "parks" in message:
        response = "Here is a list of Tunisia's national parks."
        suggestions = ["View map", "List parks", "Parks near Tunis"]
    else:
        response = "Hello! I'm the Tunisia National Parks assistant."
        suggestions = ["List parks", "Species", "Trails", "Weather"]

    return {
        "response": response,
        "suggestions": suggestions
    }

# Catch-all frontend route - MUST be at the absolute bottom to prevent stealing API requests
@app.get("/{full_path:path}")
async def catch_all_frontend(full_path: str):
    # Serve index.html for all non-API routes to enable SPA routing
    if full_path.startswith("api/") or full_path in ["static", "uploads"]:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse("templates/index.html")

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    for folder in ["parks", "species", "users", "documents"]:
        Path(f"uploads/{folder}").mkdir(parents=True, exist_ok=True)
    yield

app.router.lifespan_context = lifespan

# Initialize monitoring
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False, should_gzip=True)

# Run server
if __name__ == '__main__':
    import uvicorn
    import sys
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        try:
            port = int(sys.argv[2])
        except (IndexError, ValueError):
            pass
    uvicorn.run(app, host='0.0.0.0', port=port, log_level='info')
