"""
Minimal FastAPI application for Tunisia National Parks
"""

from contextlib import asynccontextmanager
import logging
from datetime import datetime
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from utils import create_access_token
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI, Request, Query, HTTPException

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIASGIMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from database import init_db
from config import settings

from database import get_engine

from sqlmodel import select, or_, Session, func, SQLModel
import json
from pathlib import Path
from models import ParkDB, TrailDB, ParkSpeciesLink, SpeciesDB, ReviewDB, SightingDB, UserDB, BadgeDB, UserStatsDB, UserBadgeDB, AdminUser
from weather_service import get_weather_for_location
# Import routers
from routers import parks, species, trails, auth, weather, gamification

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Force-refresh database - drop all tables and recreate
    from models import ParkDB, TrailDB, ParkSpeciesLink, SpeciesDB, ReviewDB, SightingDB, UserDB, BadgeDB, UserBadgeDB, UserStatsDB, HealthProfileDB
    engine = get_engine()
    print("🔄 Force-refreshing database - dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    print("✅ Tables dropped. Recreating...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tables recreated.")

    # Seed with fresh data
    print("🌱 Seeding database with complete 17-park data...")
    seed_database()

    # Create/update admin user
    print("👤 Creating/updating admin user...")
    create_or_update_admin_user()

    for folder in ["parks", "species", "users", "documents"]:
        Path(f"uploads/{folder}").mkdir(parents=True, exist_ok=True)
    yield

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
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_security=[],
    lifespan=lifespan
)

# Static files and templates - BEFORE API routers to prevent routing conflicts
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

def create_or_update_admin_user():
    """Create or update the admin user with credentials from environment variables."""
    from utils import get_password_hash

    admin_username = settings.ADMIN_USERNAME
    admin_password = settings.ADMIN_PASSWORD

    print(f"👤 Creating/updating admin user: {admin_username}")

    try:
        with Session(get_engine()) as session:
            # Check if admin user already exists
            existing_admin = session.exec(
                select(AdminUser).where(AdminUser.username == admin_username)
            ).first()

            hashed_password = get_password_hash(admin_password)

            if existing_admin:
                # Update existing admin user
                existing_admin.hashed_password = hashed_password
                existing_admin.is_active = True
                existing_admin.last_login = None  # Reset last login
                print(f"🔄 Updated existing admin user: {admin_username}")
            else:
                # Create new admin user
                admin_user = AdminUser(
                    username=admin_username,
                    email=f"{admin_username}@admin.local",
                    hashed_password=hashed_password,
                    is_active=True,
                    role="admin"
                )
                session.add(admin_user)
                print(f"✅ Created new admin user: {admin_username}")

            session.commit()
            print(f"🎯 Admin user {admin_username} is ready for login")

    except Exception as e:
        print(f"❌ Error creating/updating admin user: {e}")

# Seed data function
def seed_database():
    """Seed the database with initial Tunisian parks data."""
    with Session(get_engine()) as session:
        # Check if we already have data
        existing_parks = session.exec(select(ParkDB)).all()
        if existing_parks:
            return  # Database already has data

        # Seed all 17 Tunisian National Parks
        parks_data = [
            {
                "id": 1,
                "name": "Parc National de l'Ichkeul",
                "governorate": "Bizerte",
                "description": "Un site Ramsar exceptionnel avec des marais et des forêts, abritant une biodiversité remarquable.",
                "latitude": 37.1667,
                "longitude": 9.6833,
                "area_km2": 126.0,
                "area_hectares": 12600,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "hero_image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800",
                "google_maps_url": "https://maps.google.com/?q=37.1667,9.6833",
                "activities": json.dumps(["Observation des oiseaux", "randonnée", "kayak"]),
                "best_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre", "Novembre"]),
                "average_rating": 4.8,
                "total_reviews": 156,
                "accessibility": json.dumps(["Accessible avec guide"]),
                "entrance_fee": "5.0 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_phone": "+216 72 123 456"
            },
            {
                "id": 2,
                "name": "Parc National de Boukornine",
                "governorate": "Ariana",
                "description": "Un parc urbain offrant des sentiers de randonnée et une vue panoramique sur Tunis.",
                "latitude": 36.8667,
                "longitude": 10.2000,
                "area_km2": 19.39,
                "area_hectares": 1939,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "hero_image_url": "https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800",
                "google_maps_url": "https://maps.google.com/?q=36.8667,10.2000",
                "activities": json.dumps(["Randonnée", "pique-nique", "observation de la faune"]),
                "best_months": json.dumps(["Toute l'année"]),
                "average_rating": 4.6,
                "total_reviews": 89,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "3.0 DT",
                "opening_hours": "7h00 - 19h00",
                "contact_phone": "+216 71 234 567"
            },
            {
                "id": 3,
                "name": "Parc National de Zaghouan",
                "governorate": "Zaghouan",
                "description": "Célèbre pour ses sources d'eau et ses vestiges romains, offrant des paysages variés.",
                "latitude": 36.4000,
                "longitude": 10.1333,
                "area_km2": 25.0,
                "area_hectares": 2500,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=36.4000,10.1333",
                "activities": json.dumps(["Randonnée", "visite historique", "observation de la nature"]),
                "best_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre", "Novembre"]),
                "average_rating": 4.4,
                "total_reviews": 67,
                "accessibility": json.dumps(["Accessible avec guide"]),
                "entrance_fee": "4.0 DT",
                "opening_hours": "8h00 - 16h00",
                "contact_phone": "+216 72 345 678"
            },
            {
                "id": 4,
                "name": "Parc National de Chambi",
                "governorate": "Kasserine",
                "description": "Le plus haut sommet de Tunisie avec une flore alpine unique et des sentiers de randonnée.",
                "latitude": 35.1667,
                "longitude": 8.7833,
                "area_km2": 67.19,
                "area_hectares": 6719,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=35.1667,8.7833",
                "activities": json.dumps(["Randonnée en montagne", "observation des étoiles", "camping"]),
                "best_months": json.dumps(["Mai", "Juin", "Juillet", "Août", "Septembre"]),
                "average_rating": 4.7,
                "total_reviews": 134,
                "accessibility": json.dumps(["Difficile d'accès"]),
                "entrance_fee": "6.0 DT",
                "opening_hours": "7h00 - 18h00",
                "contact_phone": "+216 77 456 789"
            },
            {
                "id": 5,
                "name": "Parc National de Bou-Hedma",
                "governorate": "Sidi Bouzid",
                "description": "Un parc désertique avec des chotts et une biodiversité adaptée aux conditions arides.",
                "latitude": 34.8000,
                "longitude": 9.5500,
                "area_km2": 165.0,
                "area_hectares": 16500,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=34.8000,9.5500",
                "activities": json.dumps(["Observation des gazelles", "randonnée dans le désert", "camping"]),
                "best_months": json.dumps(["Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars"]),
                "average_rating": 4.5,
                "total_reviews": 92,
                "accessibility": json.dumps(["Accessible avec véhicule 4x4"]),
                "entrance_fee": "7.0 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_phone": "+216 76 567 890"
            },
            {
                "id": 6,
                "name": "Parc National de Jebel Zaghdoud",
                "governorate": "Béja",
                "description": "Une réserve naturelle avec des forêts de chênes et une faune diversifiée.",
                "latitude": 36.6500,
                "longitude": 9.2167,
                "area_km2": 20.0,
                "area_hectares": 2000,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=36.6500,9.2167",
                "activities": json.dumps(["Randonnée", "observation des oiseaux", "pique-nique"]),
                "best_months": json.dumps(["Avril", "Mai", "Juin", "Septembre", "Octobre"]),
                "average_rating": 4.3,
                "total_reviews": 45,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "3.5 DT",
                "opening_hours": "7h30 - 17h30",
                "contact_info": "+216 78 678 901",
                "website": "https://parcs-tunisie.tn/zaghdoud"
            },
            {
                "id": 7,
                "name": "Parc National d'El Feidja",
                "governorate": "Bizerte",
                "description": "Un parc côtier avec des plages, des dunes et une biodiversité méditerranéenne unique.",
                "latitude": 37.1833,
                "longitude": 9.8833,
                "area_km2": 63.0,
                "area_hectares": 6300,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=37.1833,9.8833",
                "activities": json.dumps(["Plage", "observation des oiseaux", "randonnée côtière"]),
                "best_months": json.dumps(["Mai", "Juin", "Juillet", "Août", "Septembre"]),
                "average_rating": 4.2,
                "total_reviews": 78,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "4.5 DT",
                "opening_hours": "8h00 - 18h00",
                "contact_info": "+216 72 111 222",
                "website": "https://parcs-tunisie.tn/el-feidja"
            },
            {
                "id": 8,
                "name": "Parc National de Jbil",
                "governorate": "Kasserine",
                "description": "Un parc montagneux avec des forêts de pins et des cascades impressionnantes.",
                "latitude": 35.0333,
                "longitude": 8.6167,
                "area_km2": 150.0,
                "area_hectares": 15000,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=35.0333,8.6167",
                "activities": json.dumps(["Randonnée", "camping", "observation des cascades"]),
                "best_months": json.dumps(["Avril", "Mai", "Juin", "Septembre", "Octobre"]),
                "average_rating": 4.5,
                "total_reviews": 112,
                "accessibility": json.dumps(["Accessible avec guide"]),
                "entrance_fee": "5.5 DT",
                "opening_hours": "7h00 - 17h00",
                "contact_info": "+216 77 222 333",
                "website": "https://parcs-tunisie.tn/jbil"
            },
            {
                "id": 9,
                "name": "Parc National de Sidi Toui",
                "governorate": "Kasserine",
                "description": "Un parc national avec des lacs artificiels et une flore diversifiée.",
                "latitude": 35.0167,
                "longitude": 8.6833,
                "area_km2": 7.0,
                "area_hectares": 700,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=35.0167,8.6833",
                "activities": json.dumps(["Pêche", "randonnée", "observation de la nature"]),
                "best_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre", "Novembre"]),
                "average_rating": 4.1,
                "total_reviews": 34,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "3.0 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 77 333 444",
                "website": "https://parcs-tunisie.tn/sidi-toui"
            },
            {
                "id": 10,
                "name": "Parc National de Dghoumes",
                "governorate": "Tozeur",
                "description": "Un parc saharien avec des dunes, des oasis et une biodiversité désertique.",
                "latitude": 33.9833,
                "longitude": 8.2167,
                "area_km2": 7000.0,
                "area_hectares": 700000,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=33.9833,8.2167",
                "activities": json.dumps(["Observation du désert", "camping saharien", "photographie"]),
                "best_months": json.dumps(["Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars"]),
                "average_rating": 4.6,
                "total_reviews": 156,
                "accessibility": json.dumps(["Accessible avec véhicule 4x4"]),
                "entrance_fee": "8.0 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 76 444 555",
                "website": "https://parcs-tunisie.tn/dghoumes"
            },
            {
                "id": 11,
                "name": "Parc National d'Aïn Zana",
                "governorate": "Bizerte",
                "description": "Un parc naturel avec des forêts méditerranéennes et des sources d'eau naturelle.",
                "latitude": 37.0833,
                "longitude": 9.2167,
                "area_km2": 20.0,
                "area_hectares": 2000,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=37.0833,9.2167",
                "activities": json.dumps(["Randonnée", "observation de la nature", "pique-nique"]),
                "best_months": json.dumps(["Toute l'année"]),
                "average_rating": 4.2,
                "total_reviews": 45,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "2.5 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 72 789 012",
                "website": "https://parcs-tunisie.tn/ain-zana"
            },
            {
                "id": 12,
                "name": "Parc National de Zembra et Zembretta",
                "governorate": "Nabeul",
                "description": "Un archipel avec des îles inhabitées offrant une biodiversité marine unique.",
                "latitude": 37.1167,
                "longitude": 10.8167,
                "area_km2": 15.0,
                "area_hectares": 1500,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=37.1167,10.8167",
                "activities": json.dumps(["Observation des oiseaux marins", "plongée", "kayak"]),
                "best_months": json.dumps(["Mai", "Juin", "Juillet", "Août", "Septembre"]),
                "average_rating": 4.5,
                "total_reviews": 78,
                "accessibility": json.dumps(["Accessible par bateau"]),
                "entrance_fee": "8.0 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 72 345 678",
                "website": "https://parcs-tunisie.tn/zembra"
            },
            {
                "id": 13,
                "name": "Parc National de Jebel Ressas",
                "governorate": "Ariana",
                "description": "Un parc avec des forêts méditerranéennes et des points de vue panoramiques.",
                "latitude": 36.7833,
                "longitude": 10.2833,
                "area_km2": 18.0,
                "area_hectares": 1800,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=36.7833,10.2833",
                "activities": json.dumps(["Randonnée", "observation de la nature", "pique-nique"]),
                "best_months": json.dumps(["Toute l'année"]),
                "average_rating": 4.2,
                "total_reviews": 67,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "3.0 DT",
                "opening_hours": "8h00 - 18h00",
                "contact_info": "+216 71 777 888",
                "website": "https://parcs-tunisie.tn/jebel-ressas"
            },
            {
                "id": 14,
                "name": "Parc National de Jebel Chitana",
                "governorate": "Bizerte",
                "description": "Un parc côtier avec des falaises spectaculaires et une flore endémique.",
                "latitude": 37.2833,
                "longitude": 9.8833,
                "area_km2": 15.0,
                "area_hectares": 1500,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=37.2833,9.8833",
                "activities": json.dumps(["Randonnée côtière", "observation des falaises", "plongée"]),
                "best_months": json.dumps(["Mai", "Juin", "Juillet", "Août", "Septembre"]),
                "average_rating": 4.4,
                "total_reviews": 89,
                "accessibility": json.dumps(["Accessible avec guide"]),
                "entrance_fee": "4.0 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 72 888 999",
                "website": "https://parcs-tunisie.tn/jebel-chitana"
            },
            {
                "id": 15,
                "name": "Parc National de Jebel Serj",
                "governorate": "Bizerte",
                "description": "Un parc forestier avec des chênes-lièges et une biodiversité exceptionnelle.",
                "latitude": 37.0667,
                "longitude": 9.2833,
                "area_km2": 35.0,
                "area_hectares": 3500,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=37.0667,9.2833",
                "activities": json.dumps(["Randonnée", "observation des arbres", "photographie"]),
                "best_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre", "Novembre"]),
                "average_rating": 4.3,
                "total_reviews": 56,
                "accessibility": json.dumps(["Accessible"]),
                "entrance_fee": "3.5 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 72 999 000",
                "website": "https://parcs-tunisie.tn/jebel-serj"
            },
            {
                "id": 16,
                "name": "Parc National de Jebel Mghilla",
                "governorate": "Kasserine",
                "description": "Un parc montagneux avec des forêts de cèdres et des vues panoramiques.",
                "latitude": 35.2833,
                "longitude": 8.7167,
                "area_km2": 17.0,
                "area_hectares": 1700,
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=35.2833,8.7167",
                "activities": json.dumps(["Randonnée en montagne", "observation des cèdres", "camping"]),
                "best_months": json.dumps(["Mai", "Juin", "Juillet", "Août", "Septembre"]),
                "average_rating": 4.5,
                "total_reviews": 78,
                "accessibility": json.dumps(["Accessible avec guide"]),
                "entrance_fee": "5.0 DT",
                "opening_hours": "7h00 - 18h00",
                "contact_info": "+216 77 000 111",
                "website": "https://parcs-tunisie.tn/jebel-mghilla"
            },
            {
                "id": 17,
                "name": "Parc National de Jebel Orbata",
                "governorate": "Kasserine",
                "description": "Un parc avec des paysages karstiques et une flore adaptée aux climats extrêmes.",
                "latitude": 35.2333,
                "longitude": 8.7833,
                "area_km2": 57.0,
                "area_hectares": 5700,
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"]),
                "google_maps_url": "https://maps.google.com/?q=35.2333,8.7833",
                "activities": json.dumps(["Randonnée", "géologie", "observation de la flore"]),
                "best_months": json.dumps(["Avril", "Mai", "Juin", "Septembre", "Octobre"]),
                "average_rating": 4.1,
                "total_reviews": 45,
                "accessibility": json.dumps(["Difficile d'accès"]),
                "entrance_fee": "4.5 DT",
                "opening_hours": "8h00 - 17h00",
                "contact_info": "+216 77 111 222",
                "website": "https://parcs-tunisie.tn/jebel-orbata"
            }
        ]

        for park_data in parks_data:
            park = ParkDB(**park_data)
            session.add(park)

        # Seed species - Fixed to match SpeciesDB model fields
        species_data = [
            # Animals
            {
                "species_id": 1,
                "name": "Flamant Rose",
                "scientific_name": "Phoenicopterus roseus",
                "type": "animal",
                "description": "Un échassier majestueux avec un plumage rose, symbole de la biodiversité tunisienne.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Marais, lacs salés",
                "diet": "Petits crustacés, algues",
                "lifespan": "40 ans",
                "size": "130 cm",
                "weight": "2.5 kg",
                "best_viewing_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre", "Novembre"]),
                "activity_time": "diurne",
                "rarity": "rare"
            },
            {
                "species_id": 2,
                "name": "Gazelle Dorcas",
                "scientific_name": "Gazella dorcas",
                "type": "animal",
                "description": "Une antilope gracieuse adaptée aux environnements arides du désert tunisien.",
                "conservation_status": "Vulnérable",
                "habitat_type": "Désert, steppes arides",
                "diet": "Herbes, feuilles, graines",
                "lifespan": "12 ans",
                "size": "90 cm",
                "weight": "25 kg",
                "best_viewing_months": json.dumps(["Octobre", "Novembre", "Décembre", "Janvier", "Février", "Mars"]),
                "activity_time": "crépusculaire",
                "rarity": "rare",
                "danger_level": "low",
                "emergency_protocol": "Gardez une distance de sécurité. Ne pas nourrir. En cas de contact accidentel, consultez un vétérinaire pour vérifier les maladies transmissibles."
            },
            {
                "species_id": 3,
                "name": "Aigle de Bonelli",
                "scientific_name": "Aquila fasciata",
                "type": "animal",
                "description": "Un rapace majestueux avec une envergure impressionnante, chasseur des montagnes.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Montagnes, falaises",
                "diet": "Petits mammifères, oiseaux",
                "lifespan": "25 ans",
                "size": "75 cm",
                "weight": "2.0 kg",
                "best_viewing_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre"]),
                "activity_time": "diurne",
                "rarity": "rare"
            },
            {
                "species_id": 4,
                "name": "Hérisson d'Algérie",
                "scientific_name": "Atelerix algirus",
                "type": "animal",
                "description": "Un petit mammifère nocturne avec des piquants défensifs, commun en Tunisie.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Forêts, jardins, zones urbaines",
                "diet": "Insectes, vers, fruits",
                "lifespan": "6 ans",
                "size": "25 cm",
                "weight": "0.5 kg",
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": "nocturne",
                "rarity": "common"
            },
            {
                "species_id": 5,
                "name": "Bouquetin des Alpes",
                "scientific_name": "Capra ibex",
                "type": "animal",
                "description": "Un caprin majestueux adapté aux terrains escarpés des montagnes tunisiennes.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Montagnes rocheuses",
                "diet": "Herbes, feuilles, bourgeons",
                "lifespan": "18 ans",
                "size": "140 cm",
                "weight": "80 kg",
                "best_viewing_months": json.dumps(["Mai", "Juin", "Juillet", "Août", "Septembre"]),
                "activity_time": "diurne",
                "rarity": "rare"
            },
            {
                "species_id": 6,
                "name": "Lynx Pardelle",
                "scientific_name": "Lynx pardinus",
                "type": "animal",
                "description": "Un félin rare et mystérieux, symbole de la préservation de la biodiversité.",
                "conservation_status": "En danger critique",
                "habitat_type": "Forêts de montagne",
                "diet": "Petits mammifères, oiseaux",
                "lifespan": "13 ans",
                "size": "85 cm",
                "weight": "12 kg",
                "best_viewing_months": json.dumps(["Avril", "Mai", "Juin", "Septembre", "Octobre"]),
                "activity_time": "crépusculaire",
                "rarity": "très_rare",
                "danger_level": "low",
                "emergency_protocol": "Ne pas approcher. Signaler immédiatement aux gardes du parc si vu."
            },
            # Dangerous species with emergency protocols
            {
                "species_id": 17,
                "name": "Sanglier",
                "scientific_name": "Sus scrofa",
                "type": "animal",
                "description": "Un mammifère sauvage robuste aux défenses impressionnantes, commun dans les forêts tunisiennes.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Forêts, maquis, zones agricoles",
                "diet": "Racines, glands, petits animaux",
                "lifespan": "10 ans",
                "size": "140 cm",
                "weight": "150 kg",
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": "crépusculaire",
                "rarity": "common",
                "danger_level": "high",
                "emergency_protocol": "En cas de morsure: Laver la plaie avec du savon pendant 15 minutes, consulter immédiatement un médecin pour vaccins contre la rage et le tétanos. Ne pas tuer l'animal."
            },
            {
                "species_id": 18,
                "name": "Vipère Cornue",
                "scientific_name": "Cerastes cerastes",
                "type": "animal",
                "description": "Un serpent venimeux adapté aux environnements désertiques, reconnaissable par ses cornes au-dessus des yeux.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Déserts, zones arides",
                "diet": "Petits rongeurs, lézards",
                "lifespan": "12 ans",
                "size": "50 cm",
                "weight": "0.2 kg",
                "best_viewing_months": json.dumps(["Mars", "Avril", "Mai", "Septembre", "Octobre", "Novembre"]),
                "activity_time": "nocturne",
                "rarity": "rare",
                "danger_level": "high",
                "emergency_protocol": "Immobiliser le membre mordu, appeler immédiatement le 190 (SAMU). NE PAS inciser, aspirer ou appliquer de garrot. Garder au repos et transporter à l'hôpital."
            },
            {
                "species_id": 19,
                "name": "Laurier Rose",
                "scientific_name": "Nerium oleander",
                "type": "plant",
                "description": "Un arbuste ornemental aux fleurs roses, très toxique si ingéré, commun dans les jardins et parcs tunisiens.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Jardins, parcs, zones urbaines",
                "diet": None,
                "lifespan": "20 ans",
                "size": "2-6 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "common",
                "danger_level": "high",
                "emergency_protocol": "Toxique si ingéré. En cas d'ingestion: Ne pas vomir. Appeler immédiatement le centre antipoison (23 10 90 90) ou les urgences (190). Surveiller les signes de toxicité cardiaque."
            },
            # Plants
            {
                "species_id": 7,
                "name": "Olivier de Tunisie",
                "scientific_name": "Olea europaea",
                "type": "plant",
                "description": "L'olivier, arbre emblématique de la Méditerranée, symbole de paix et de longévité.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Collines méditerranéennes, sols calcaires",
                "diet": None,
                "lifespan": "Plus de 2000 ans",
                "size": "10-15 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "common"
            },
            {
                "species_id": 8,
                "name": "Pin d'Alep",
                "scientific_name": "Pinus halepensis",
                "type": "plant",
                "description": "Un pin résineux adapté aux climats secs, formant des forêts denses en Tunisie.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Montagnes, sols pauvres",
                "diet": None,
                "lifespan": "200 ans",
                "size": "15-25 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "common"
            },
            {
                "species_id": 9,
                "name": "Chêne-liège",
                "scientific_name": "Quercus suber",
                "type": "plant",
                "description": "Arbre à liège précieux, essentiel pour l'écosystème méditerranéen.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Forêts méditerranéennes",
                "diet": None,
                "lifespan": "150-250 ans",
                "size": "10-20 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "rare"
            },
            {
                "species_id": 10,
                "name": "Palmier nain",
                "scientific_name": "Chamaerops humilis",
                "type": "plant",
                "description": "Le seul palmier indigène d'Europe, résistant à la sécheresse.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Garrigues, sols rocailleux",
                "diet": None,
                "lifespan": "100 ans",
                "size": "2-5 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Avril", "Mai", "Juin", "Septembre", "Octobre"]),
                "activity_time": None,
                "rarity": "rare"
            },
            {
                "species_id": 11,
                "name": "Genévrier de Phénicie",
                "scientific_name": "Juniperus phoenicea",
                "type": "plant",
                "description": "Arbre résineux antique, symbole de longévité et de résistance.",
                "conservation_status": "Vulnérable",
                "habitat_type": "Montagnes côtières",
                "diet": None,
                "lifespan": "500 ans",
                "size": "6-10 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "rare"
            },
            {
                "species_id": 12,
                "name": "Ciste à feuilles de sauge",
                "scientific_name": "Cistus salviifolius",
                "type": "plant",
                "description": "Arbuste méditerranéen aux fleurs roses, essentiel pour les pollinisateurs.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Garrigues, maquis",
                "diet": None,
                "lifespan": "20-30 ans",
                "size": "1-2 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Mars", "Avril", "Mai", "Juin"]),
                "activity_time": None,
                "rarity": "common"
            },
            {
                "species_id": 13,
                "name": "Romarin officinal",
                "scientific_name": "Rosmarinus officinalis",
                "type": "plant",
                "description": "Arbuste aromatique aux propriétés médicinales, emblème de la flore tunisienne.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Collines sèches, garrigues",
                "diet": None,
                "lifespan": "20 ans",
                "size": "1-2 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "common"
            },
            {
                "species_id": 14,
                "name": "Lavande stéchade",
                "scientific_name": "Lavandula stoechas",
                "type": "plant",
                "description": "Plante aromatique aux fleurs violettes, attirant les papillons et abeilles.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Collines calcaires",
                "diet": None,
                "lifespan": "10 ans",
                "size": "0.5-1 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Mars", "Avril", "Mai", "Juin"]),
                "activity_time": None,
                "rarity": "common"
            },
            {
                "species_id": 15,
                "name": "Thym sauvage",
                "scientific_name": "Thymus vulgaris",
                "type": "plant",
                "description": "Plante aromatique aux propriétés antiseptiques, couvrant les sols secs de Tunisie.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Sols rocailleux, garrigues",
                "diet": None,
                "lifespan": "5-10 ans",
                "size": "0.2-0.4 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Toute l'année"]),
                "activity_time": None,
                "rarity": "common"
            },
            {
                "species_id": 16,
                "name": "Orchidée sauvage",
                "scientific_name": "Orchis mascula",
                "type": "plant",
                "description": "Fleur délicate aux couleurs vives, indicateur de la santé des sols.",
                "conservation_status": "Préoccupation mineure",
                "habitat_type": "Prairies humides, sous-bois",
                "diet": None,
                "lifespan": "Plusieurs années",
                "size": "0.2-0.6 m",
                "weight": None,
                "best_viewing_months": json.dumps(["Février", "Mars", "Avril", "Mai"]),
                "activity_time": None,
                "rarity": "rare"
            }
        ]

        for species_data_item in species_data:
            species = SpeciesDB(**species_data_item)
            session.add(species)

        # Create park-species relationships
        park_species_links = [
            {"park_id": 1, "species_id": 1},  # Ichkeul - Flamingo
            {"park_id": 1, "species_id": 3},  # Ichkeul - Eagle
            {"park_id": 2, "species_id": 4},  # Boukornine - Hedgehog
            {"park_id": 3, "species_id": 2},  # Zaghouan - Gazelle
            {"park_id": 4, "species_id": 5},  # Chambi - Ibex
            {"park_id": 5, "species_id": 2},  # Bou-Hedma - Gazelle
            {"park_id": 6, "species_id": 6},  # Zaghdoud - Lynx
        ]

        for link_data in park_species_links:
            link = ParkSpeciesLink(**link_data)
            session.add(link)

        # Seed trails
        trails_data = [
            {
                "id": 1,
                "park_id": 1,
                "name": "Ichkeul Lake Loop",
                "description": "A scenic loop trail around the famous Ichkeul Lake, perfect for birdwatching and nature observation.",
                "difficulty": "facile",
                "length_km": 8.5,
                "duration_hours": 3.5,
                "elevation_gain": 50,
                "trail_type": "loop",
                "surface": "dirt",
                "images": json.dumps(["https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?q=80&w=800"])
            },
            {
                "id": 2,
                "park_id": 1,
                "name": "Forest Path to the Dam",
                "description": "A moderate trail through dense forest leading to the historic dam with panoramic views.",
                "difficulty": "modéré",
                "length_km": 12.0,
                "duration_hours": 4.0,
                "elevation_gain": 120,
                "trail_type": "out_and_back",
                "surface": "dirt",
                "images": json.dumps(["https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=800"])
            },
            {
                "id": 3,
                "park_id": 2,
                "name": "Boukornine Summit Trail",
                "description": "Challenging climb to the summit of Jebel Boukornine with stunning views of Tunis.",
                "difficulty": "difficile",
                "length_km": 6.0,
                "duration_hours": 4.5,
                "elevation_gain": 350,
                "trail_type": "out_and_back",
                "surface": "rocky",
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"])
            },
            {
                "id": 4,
                "park_id": 2,
                "name": "Urban Nature Walk",
                "description": "Easy walking path through urban forest, perfect for families and casual hikers.",
                "difficulty": "facile",
                "length_km": 3.5,
                "duration_hours": 1.5,
                "elevation_gain": 80,
                "trail_type": "loop",
                "surface": "dirt",
                "images": json.dumps(["https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=800"])
            },
            {
                "id": 5,
                "park_id": 3,
                "name": "Roman Ruins Discovery",
                "description": "Historical trail passing through ancient Roman ruins and olive groves.",
                "difficulty": "modéré",
                "length_km": 9.0,
                "duration_hours": 3.0,
                "elevation_gain": 90,
                "trail_type": "loop",
                "surface": "mixed",
                "images": json.dumps(["https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?q=80&w=800"])
            },
            {
                "id": 6,
                "park_id": 4,
                "name": "Chambi Mountain Ascent",
                "description": "Epic climb to the highest peak in Tunisia, requiring good physical condition.",
                "difficulty": "difficile",
                "length_km": 15.0,
                "duration_hours": 8.0,
                "elevation_gain": 800,
                "trail_type": "out_and_back",
                "surface": "rocky",
                "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"])
            },
            {
                "id": 7,
                "park_id": 4,
                "name": "Alpine Meadows Trail",
                "description": "Scenic trail through high-altitude meadows with unique alpine flora.",
                "difficulty": "modéré",
                "length_km": 7.0,
                "duration_hours": 2.5,
                "elevation_gain": 150,
                "trail_type": "loop",
                "surface": "grass",
                "images": json.dumps(["https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=800"])
            },
            {
                "id": 8,
                "park_id": 5,
                "name": "Desert Oasis Circuit",
                "description": "Desert trail leading to hidden oases and traditional water sources.",
                "difficulty": "modéré",
                "length_km": 11.0,
                "duration_hours": 4.0,
                "elevation_gain": 60,
                "trail_type": "loop",
                "surface": "sand",
                "images": json.dumps(["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=800"])
            },
            {
                "id": 9,
                "park_id": 6,
                "name": "Oak Forest Path",
                "description": "Peaceful walk through ancient oak forests with wildlife viewing opportunities.",
                "difficulty": "facile",
                "length_km": 5.5,
                "duration_hours": 2.0,
                "elevation_gain": 100,
                "trail_type": "loop",
                "surface": "dirt",
                "images": json.dumps(["https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=800"])
            }
        ]

        for trail_data in trails_data:
            trail = TrailDB(**trail_data)
            session.add(trail)

        session.commit()
        print("DEBUG: 17 parks now in database")

# Frontend routes - MUST be BEFORE API routers to prevent conflicts
# /docs route moved to top to avoid routing conflicts


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with Session(get_engine()) as session:
        # Get basic stats for homepage
        parks_count = len(session.exec(select(ParkDB)).all())
        species_count = len(session.exec(select(SpeciesDB)).all())
        trails_count = len(session.exec(select(TrailDB)).all())

        return templates.TemplateResponse("index.html", {
            "request": request,
            "parks_count": parks_count,
            "species_count": species_count,
            "trails_count": trails_count
        })

@app.get("/parks", response_class=HTMLResponse)
async def parks_page(request: Request):
    try:
        with Session(get_engine()) as session:
            parks = session.exec(select(ParkDB)).all()
            print(f"DEBUG: Retrieved {len(parks)} parks from database")

            # Convert to dict format for template
            parks_data = []
            for park in parks:
                try:
                    parks_data.append({
                        "id": park.id,
                        "name": park.name,
                        "governorate": park.governorate,
                        "description": park.description,
                        "latitude": park.latitude,
                        "longitude": park.longitude,
                        "area_km2": park.area_km2,
                        "area_hectares": park.area_hectares,
                        "images": json.loads(park.images) if park.images else [],
                        "activities": json.loads(park.activities) if park.activities else [],
                        "best_months": json.loads(park.best_months) if park.best_months else [],
                        "average_rating": park.average_rating,
                        "total_reviews": park.total_reviews,
                        "accessibility": json.loads(park.accessibility) if park.accessibility else [],
                        "entrance_fee": park.entrance_fee,
                        "opening_hours": park.opening_hours,
                        "contact_info": park.contact_phone,  # Correct field name
                        "website": park.google_maps_url  # Use available URL field
                    })
                except Exception as e:
                    logger.error(f"Error processing park {park.id}: {e}")
                    continue

            print(f"DEBUG: Sending {len(parks_data)} parks to template")
            logger.info(f"Successfully processed {len(parks_data)} parks for template")
            return templates.TemplateResponse("parks.html", {
                "request": request,
                "parks": parks_data,  # Template expects 'parks' variable
                "total_parks": len(parks_data)
            })
    except Exception as e:
        logger.error(f"Error in parks_page: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/species", response_class=HTMLResponse)
async def species_page(request: Request):
    try:
        with Session(get_engine()) as session:
            species = session.exec(select(SpeciesDB)).all()
            print(f"DEBUG: Retrieved {len(species)} species from database")

            # Convert to dict format for template
            species_data = []
            for specie in species:
                try:
                    species_data.append({
                        "id": specie.species_id,  # Correct field name
                        "name": specie.name,
                        "scientific_name": specie.scientific_name,
                        "type": specie.type,
                        "description": specie.description,
                        "conservation_status": specie.conservation_status,
                        "habitat": specie.habitat_type,  # Correct field name
                        "image_url": specie.image_url,
                        "diet": specie.diet,
                        "lifespan_years": specie.lifespan,  # Correct field name
                        "size_cm": specie.size,  # Correct field name
                        "weight_kg": specie.weight,  # Correct field name
                        "rarity": specie.rarity,
                        "activity_time": specie.activity_time,
                        "best_viewing_months": specie.best_viewing_months
                    })
                except Exception as e:
                    logger.error(f"Error processing species {getattr(specie, 'species_id', 'unknown')}: {e}")
                    continue

            print(f"DEBUG: Sending {len(species_data)} species to template")
            logger.info(f"Successfully processed {len(species_data)} species for template")
            return templates.TemplateResponse("species.html", {
                "request": request,
                "species": species_data,  # Template expects 'species' variable
                "total_species": len(species_data)
            })
    except Exception as e:
        logger.error(f"Error in species_page: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/trails", response_class=HTMLResponse)
async def trails_page(request: Request):
    try:
        with Session(get_engine()) as session:
            trails = session.exec(select(TrailDB)).all()
            print(f"DEBUG: Retrieved {len(trails)} trails from database")

            # Force seed trails if none exist (for development/testing)
            if len(trails) == 0:
                print("DEBUG: No trails found, force seeding trails...")
                # Seed trails directly here if missing
                trails_data_seed = [
                    {
                        "id": 1,
                        "park_id": 1,
                        "name": "Ichkeul Lake Loop",
                        "description": "A scenic loop trail around the famous Ichkeul Lake, perfect for birdwatching and nature observation.",
                        "difficulty": "facile",
                        "length_km": 8.5,
                        "duration_hours": 3.5,
                        "elevation_gain": 50,
                        "trail_type": "loop",
                        "surface": "dirt",
                        "images": json.dumps(["https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?q=80&w=800"])
                    },
                    {
                        "id": 2,
                        "park_id": 2,
                        "name": "Boukornine Summit Trail",
                        "description": "Challenging climb to the summit of Jebel Boukornine with stunning views of Tunis.",
                        "difficulty": "difficile",
                        "length_km": 6.0,
                        "duration_hours": 4.5,
                        "elevation_gain": 350,
                        "trail_type": "out_and_back",
                        "surface": "rocky",
                        "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"])
                    },
                    {
                        "id": 3,
                        "park_id": 3,
                        "name": "Roman Ruins Discovery",
                        "description": "Historical trail passing through ancient Roman ruins and olive groves.",
                        "difficulty": "modéré",
                        "length_km": 9.0,
                        "duration_hours": 3.0,
                        "elevation_gain": 90,
                        "trail_type": "loop",
                        "surface": "mixed",
                        "images": json.dumps(["https://images.unsplash.com/photo-1551632436-cbf8dd35adfa?q=80&w=800"])
                    },
                    {
                        "id": 4,
                        "park_id": 4,
                        "name": "Chambi Mountain Ascent",
                        "description": "Epic climb to the highest peak in Tunisia, requiring good physical condition.",
                        "difficulty": "difficile",
                        "length_km": 15.0,
                        "duration_hours": 8.0,
                        "elevation_gain": 800,
                        "trail_type": "out_and_back",
                        "surface": "rocky",
                        "images": json.dumps(["https://images.unsplash.com/photo-1464822759844-d150f39b80aa?q=80&w=800"])
                    }
                ]

                for trail_data in trails_data_seed:
                    trail = TrailDB(**trail_data)
                    session.add(trail)

                session.commit()
                trails = session.exec(select(TrailDB)).all()
                print(f"DEBUG: After force seeding, now have {len(trails)} trails")

            # Convert to dict format for template
            trails_data = []
            for trail in trails:
                try:
                    trails_data.append({
                        "id": trail.trail_id,  # Correct field name
                        "name": trail.name,
                        "park_id": trail.park_id,
                        "difficulty": trail.difficulty,
                        "distance_km": trail.length_km,  # Correct field name
                        "duration_hours": trail.duration_hours,
                        "elevation_gain_m": trail.elevation_gain,  # Correct field name
                        "description": trail.description,
                        "images": [],  # TrailDB doesn't have images field - use empty array
                        "trail_type": trail.trail_type,
                        "surface": trail.surface
                    })
                except Exception as e:
                    logger.error(f"Error processing trail {trail.trail_id}: {e}")
                    continue

            print(f"DEBUG: Sending {len(trails_data)} trails to template")
            logger.info(f"Successfully processed {len(trails_data)} trails for template")
            return templates.TemplateResponse("trails.html", {
                "request": request,
                "trails": trails_data,  # Template expects 'trails' variable
                "total_trails": len(trails_data)
            })
    except Exception as e:
        logger.error(f"Error in trails_page: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    with Session(get_engine()) as session:
        parks = session.exec(select(ParkDB)).all()

        # Prepare map data
        map_data = []
        for park in parks:
            map_data.append({
                "id": park.id,
                "name": park.name,
                "latitude": park.latitude,
                "longitude": park.longitude,
                "governorate": park.governorate,
                "description": park.description,
                "images": json.loads(park.images) if park.images else []
            })

        return templates.TemplateResponse("map.html", {
            "request": request,
            "parks": map_data
        })

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/comparison", response_class=HTMLResponse)
async def comparison_page(request: Request):
    return templates.TemplateResponse("comparison.html", {"request": request})

@app.get("/emergency", response_class=HTMLResponse)
async def emergency_page(request: Request):
    return templates.TemplateResponse("emergency.html", {"request": request})

@app.get("/species/{species_id}", response_class=HTMLResponse)
async def species_detail_page(request: Request, species_id: int):
    """Individual species page."""
    with Session(get_engine()) as session:
        specie = session.get(SpeciesDB, species_id)
        if specie is None:
            return HTMLResponse("<h1>Species not found</h1><p>The requested species could not be found.</p>", status_code=404)

        # Get parks where this species is found
        species_links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species_id)
        ).all()

        parks_data = []
        for link in species_links:
            park = session.get(ParkDB, link.park_id)
            if park:
                parks_data.append({
                    "id": park.id,
                    "name": park.name,
                    "governorate": park.governorate,
                    "latitude": park.latitude,
                    "longitude": park.longitude
                })

        species_data = {
            "id": specie.species_id,
            "name": specie.name,
            "scientific_name": specie.scientific_name,
            "type": specie.type,
            "description": specie.description or "Description non disponible.",
            "conservation_status": specie.conservation_status,
            "habitat_type": specie.habitat_type,
            "diet": specie.diet,
            "lifespan": specie.lifespan,
            "size": specie.size,
            "weight": specie.weight,
            "best_viewing_months": specie.best_viewing_months,
            "activity_time": specie.activity_time,
            "rarity": specie.rarity,
            "image_url": specie.image_url,
            "danger_level": specie.danger_level or "none",
            "emergency_protocol": specie.emergency_protocol or "",
            "parks": parks_data
        }

        # Create a simple HTML response for species detail
        danger_badge = f'<div class="danger-badge"><i class="fas fa-exclamation-triangle"></i>Niveau de Danger Élevé</div>' if species_data.get('danger_level') == 'high' else ''

        emergency_section = f'<div class="emergency-protocol"><i class="fas fa-medkit"></i><strong>Protocole d\'Urgence:</strong> {species_data.get("emergency_protocol", "Aucune information disponible.")}</div>' if species_data.get('emergency_protocol') else ''

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{species_data['name']} - Parcs Nationaux de Tunisie</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .species-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .species-header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .species-name {{
            font-size: 2.5rem;
            color: #2c5530;
            margin-bottom: 10px;
        }}
        .species-scientific {{
            font-style: italic;
            color: #666;
            font-size: 1.2rem;
        }}
        .danger-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #dc3545;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            margin: 1rem 0;
        }}
        .emergency-protocol {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            color: #856404;
        }}
        .species-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }}
        .info-label {{
            font-weight: 600;
            color: #2c5530;
            margin-bottom: 5px;
        }}
        .info-value {{
            color: #666;
        }}
        .back-link {{
            display: inline-block;
            color: #2c5530;
            text-decoration: none;
            font-weight: 600;
            padding: 10px 20px;
            border: 2px solid #2c5530;
            border-radius: 6px;
            transition: all 0.3s;
        }}
        .back-link:hover {{
            background: #2c5530;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="species-card">
        <div class="species-header">
            <h1 class="species-name">{species_data['name']}</h1>
            <p class="species-scientific">{species_data['scientific_name']}</p>
            {danger_badge}
        </div>

        <div class="species-info">
            <div class="info-item">
                <div class="info-label">Type</div>
                <div class="info-value">{species_data['type'].title()}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Statut de Conservation</div>
                <div class="info-value">{species_data.get('conservation_status', 'Non évalué')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Habitat</div>
                <div class="info-value">{species_data.get('habitat_type', 'Non spécifié')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Alimentation</div>
                <div class="info-value">{species_data.get('diet', 'Non spécifié')}</div>
            </div>
        </div>

        <div class="info-item" style="grid-column: 1 / -1;">
            <div class="info-label">Description</div>
            <div class="info-value">{species_data.get('description', 'Description non disponible.')}</div>
        </div>

        {emergency_section}
    </div>

    <a href="/species" class="back-link">
        <i class="fas fa-arrow-left"></i> Retour à la Biodiversité
    </a>
</body>
</html>"""
        return HTMLResponse(html_content)

@app.get("/parks/{park_slug}", response_class=HTMLResponse)
async def park_detail_page(request: Request, park_slug: str):
    """Individual park page that accepts string slugs instead of IDs."""
    try:
        with Session(get_engine()) as session:
            # Try to find park by ID first
            try:
                park_id = int(park_slug)
                park = session.get(ParkDB, park_id)
            except ValueError:
                # If not a number, search by name (slugified)
                park = None
                parks = session.exec(select(ParkDB)).all()
                for p in parks:
                    # Simple slug matching - convert name to slug format
                    slug_candidate = p.name.lower().replace(' ', '-').replace("'", '').replace('é', 'e')
                    if slug_candidate == park_slug.lower():
                        park = p
                        break

            if not park:
                return HTMLResponse("<h1>Park not found</h1><p>The requested park could not be found.</p>", status_code=404)

            # Get related species for this park
            species_links = session.exec(
                select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park.id)
            ).all()

            species_data = []
            for link in species_links:
                specie = session.get(SpeciesDB, link.species_id)
                if specie:
                    species_data.append({
                        "id": specie.species_id,
                        "name": specie.name,
                        "scientific_name": specie.scientific_name,
                        "type": specie.type,
                        "image_url": specie.image_url or ""
                    })

            # Get related trails for this park
            trails = session.exec(
                select(TrailDB).where(TrailDB.park_id == park.id)
            ).all()

            trails_data = []
            for trail in trails:
                trails_data.append({
                    "id": trail.trail_id,
                    "name": trail.name,
                    "difficulty": trail.difficulty,
                    "distance_km": trail.length_km,
                    "duration_hours": trail.duration_hours
                })

            park_data = {
                "id": park.id,
                "name": park.name,
                "governorate": park.governorate,
                "description": park.description,
                "latitude": park.latitude,
                "longitude": park.longitude,
                "area_km2": park.area_km2,
                "area_hectares": park.area_hectares,
                "images": json.loads(park.images) if park.images else [],
                "activities": json.loads(park.activities) if park.activities else [],
                "best_months": json.loads(park.best_months) if park.best_months else [],
                "average_rating": park.average_rating,
                "total_reviews": park.total_reviews,
                "accessibility": json.loads(park.accessibility) if park.accessibility else [],
                "entrance_fee": park.entrance_fee or "",
                "opening_hours": park.opening_hours or "",
                "contact_info": park.contact_phone or "",
                "website": park.google_maps_url or "",
                "related_species": species_data,
                "related_trails": trails_data
            }

            try:
                return templates.TemplateResponse("park_detail.html", {
                    "request": request,
                    "park": park_data
                })
            except Exception as template_error:
                logger.error(f"Template rendering error: {template_error}")
                raise HTTPException(status_code=500, detail="Template rendering failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in park_detail_page: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Include API routers BEFORE catch-all route - CRITICAL ORDER FIX
# Support both /api and direct paths to match test expectations
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(weather.router, prefix="/weather", tags=["weather"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["gamification"])
app.include_router(species.router, prefix="/species", tags=["species"])
app.include_router(species.router, prefix="/api/species", tags=["species"])
app.include_router(parks.router, prefix="/parks", tags=["parks"])
app.include_router(parks.router, prefix="/api/parks", tags=["parks"])
app.include_router(trails.router, prefix="/trails", tags=["trails"])
app.include_router(trails.router, prefix="/api/trails", tags=["trails"])

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
        "script-src 'self' 'unsafe-inline' blob: https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://unpkg.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: https://images.unsplash.com; "
        "connect-src 'self' https://api.unsplash.com https://unpkg.com https://cdn.jsdelivr.net; "
        "worker-src 'self' blob:;"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Logging
logger = logging.getLogger("tunisia_parks")
logging.basicConfig(level=logging.INFO)

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

# Health profile page
@app.get("/health")
async def health_form(request: Request):
    """Serve the health profile form page."""
    return templates.TemplateResponse("health.html", {"request": request})

# Legacy health check endpoint for API compatibility
@app.get("/api/health")
def health_check():
    """Legacy health check endpoint for API monitoring tools."""
    return {"status": "ok", "version": "3.0.0"}

# User stats endpoint for gamification
@app.get("/api/user/stats")
async def get_user_stats(user_id: str):
    """Get user stats and progress for gamification."""
    try:
        with Session(get_engine()) as session:
            # First, check if it's a registered user
            try:
                user_id_int = int(user_id)
                user = session.get(UserDB, user_id_int)
                if user:
                    # Registered user - use their stored stats
                    # Get badge details for unlocked badges
                    unlocked_badges = []
                    if user.badges_earned:
                        for badge_id in user.badges_earned:
                            badge = session.get(BadgeDB, badge_id)
                            if badge:
                                unlocked_badges.append({
                                    "id": badge.badge_id,
                                    "name": badge.name,
                                    "description": badge.description,
                                    "icon": badge.icon,
                                    "category": badge.category,
                                    "rarity": badge.rarity
                                })

                    # Calculate level based on XP
                    level = (user.xp_points // 100) + 1
                    xp_for_next_level = (level * 100) - user.xp_points
                    xp_progress_percent = ((user.xp_points % 100) / 100) * 100

                    return {
                        "user_id": user.id,
                        "xp_points": user.xp_points,
                        "level": level,
                        "xp_progress_percent": xp_progress_percent,
                        "xp_for_next_level": xp_for_next_level,
                        "badges_earned": user.badges_earned or [],
                        "unlocked_badges": unlocked_badges,
                        "total_visits": user.total_visits,
                        "joined_date": user.joined_date
                    }
            except ValueError:
                # Guest user - user_id is a string like "user_1234567890"
                pass

            # Handle guest user - check if stats exist
            user_stats = session.exec(
                select(UserStatsDB).where(UserStatsDB.user_id == user_id)
            ).first()

            if not user_stats:
                # Create new stats for guest user
                user_stats = UserStatsDB(
                    user_id=user_id,
                    experience_points=0,
                    total_points=0,
                    current_level=1,
                    badges_earned=0,
                    parks_visited=0,
                    species_seen=0,
                    trails_completed=0,
                    reviews_written=0,
                    sightings_reported=0,
                    consecutive_days_active=0
                )
                session.add(user_stats)
                session.commit()
                session.refresh(user_stats)

            # Get badge details for unlocked badges
            unlocked_badges = []
            user_badges = session.exec(
                select(UserBadgeDB).where(
                    (UserBadgeDB.user_id == user_id) & (UserBadgeDB.completed == True)
                )
            ).all()

            for user_badge in user_badges:
                badge = session.get(BadgeDB, user_badge.badge_id)
                if badge:
                    unlocked_badges.append({
                        "id": badge.badge_id,
                        "name": badge.name,
                        "description": badge.description,
                        "icon": badge.icon,
                        "category": badge.category,
                        "rarity": badge.rarity
                    })

            # Calculate level based on XP
            level = (user_stats.experience_points // 100) + 1
            xp_for_next_level = (level * 100) - user_stats.experience_points
            xp_progress_percent = ((user_stats.experience_points % 100) / 100) * 100

            return {
                "user_id": user_id,
                "xp_points": user_stats.experience_points,
                "level": level,
                "xp_progress_percent": xp_progress_percent,
                "xp_for_next_level": xp_for_next_level,
                "badges_earned": len(unlocked_badges),
                "unlocked_badges": unlocked_badges,
                "total_visits": user_stats.parks_visited,  # Use parks_visited as proxy for visits
                "joined_date": user_stats.created_at
            }

    except Exception as e:
        logger.error(f"Error getting user stats for {user_id}: {e}")
        return {"error": "Failed to load user stats"}

# Park comparison endpoint
@app.get("/parks/compare")
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



# Search endpoints
@app.get("/search/parks")
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

# API version of search endpoints
@app.get("/api/search/parks")
async def api_search_parks(
    query: str = Query(None, description="Search query"),
    governorate: str = Query(None, description="Filter by governorate"),
    min_area: float = Query(None, ge=0, description="Minimum area in km²"),
    max_area: float = Query(None, ge=0, description="Maximum area in km²"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    """API version of advanced search for parks."""
    return await search_parks(query, governorate, min_area, max_area, skip, limit)

# Analytics endpoint
@app.get("/analytics/overview")
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
@app.get("/languages")
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
@app.get("/media/config")
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

# Gamification helper functions
def award_xp_points(user_id, points: int):
    """Safely award XP points to a user. Works for both int and str user_ids."""
    print(f"🎯 Awarding {points} XP to user: {user_id}")
    try:
        with Session(get_engine()) as session:
            # Handle registered users (int user_id)
            if isinstance(user_id, int):
                user = session.get(UserDB, user_id)
                if user:
                    user.xp_points += points
                    session.commit()
                    session.refresh(user)
                    logger.info(f"Awarded {points} XP to registered user {user_id}")
                return

            # Handle guest users (str user_id)
            user_stats = session.exec(
                select(UserStatsDB).where(UserStatsDB.user_id == user_id)
            ).first()

            if not user_stats:
                user_stats = UserStatsDB(
                    user_id=user_id,
                    experience_points=points,
                    total_points=points,
                    current_level=1,
                    badges_earned=0,
                    parks_visited=0,
                    species_seen=0,
                    trails_completed=0,
                    reviews_written=0,
                    sightings_reported=0,
                    consecutive_days_active=0
                )
                session.add(user_stats)
                print(f"🆕 Created new UserStatsDB for guest user: {user_id}")
            else:
                user_stats.experience_points += points
                user_stats.total_points += points
                print(f"📈 Updated existing UserStatsDB for guest user: {user_id}, new XP: {user_stats.experience_points}")

            session.commit()
            session.refresh(user_stats)
            logger.info(f"Awarded {points} XP to guest user {user_id}")
    except Exception as e:
        logger.error(f"Failed to award XP to user {user_id}: {e}")
        print(f"❌ ERROR awarding XP to user {user_id}: {e}")
        # Don't break the main functionality

def award_badge(user_id, badge_id: int):
    """Safely award a badge to a user. Works for both int and str user_ids."""
    try:
        with Session(get_engine()) as session:
            # Handle registered users (int user_id)
            if isinstance(user_id, int):
                user = session.get(UserDB, user_id)
                if not user:
                    return

                # Check if badge already earned
                current_badges = user.badges_earned or []
                if badge_id in current_badges:
                    return  # Already has this badge

                # Add badge to list
                current_badges.append(badge_id)
                user.badges_earned = current_badges
                session.commit()
                logger.info(f"Awarded badge {badge_id} to registered user {user_id}")
                return

            # Handle guest users (str user_id)
            user_badge = session.exec(
                select(UserBadgeDB).where(
                    (UserBadgeDB.user_id == user_id) & (UserBadgeDB.badge_id == badge_id)
                )
            ).first()

            if user_badge and user_badge.completed:
                return  # Already has this badge

            if not user_badge:
                user_badge = UserBadgeDB(
                    user_id=user_id,
                    badge_id=badge_id,
                    completed=True
                )
                session.add(user_badge)
            else:
                user_badge.completed = True

            session.commit()
            logger.info(f"Awarded badge {badge_id} to guest user {user_id}")
    except Exception as e:
        logger.error(f"Failed to award badge {badge_id} to user {user_id}: {e}")
        # Don't break the main functionality

def check_badge_eligibility(user_id: int, activity_type: str):
    """Check if user qualifies for badges based on their activity. Returns newly earned badge names."""
    newly_earned_badges = []

    try:
        with Session(get_engine()) as session:
            user = session.get(UserDB, user_id)
            if not user:
                return newly_earned_badges

            # Check for conversation starter badge (first chat message)
            if activity_type == "chat_message":
                if not user.badges_earned or 1 not in user.badges_earned:
                    award_badge(user_id, 1)  # Conversation Starter badge
                    newly_earned_badges.append("Conversation Starter")

            # Check for explorer badge (asked about parks)
            elif activity_type == "asked_parks":
                if not user.badges_earned or 2 not in user.badges_earned:
                    award_badge(user_id, 2)  # Park Explorer badge
                    newly_earned_badges.append("Explorateur des Parcs")

            # Check for naturalist badge (asked about species)
            elif activity_type == "asked_species":
                if not user.badges_earned or 3 not in user.badges_earned:
                    award_badge(user_id, 3)  # Naturalist badge
                    newly_earned_badges.append("Naturaliste")

    except Exception as e:
        logger.error(f"Badge eligibility check failed for user {user_id}: {e}")

    return newly_earned_badges

# Chat endpoint
@app.post("/chat")
async def chat_with_bot(request: dict):
    """Intelligent chat endpoint with keyword analysis and database integration."""
    message = request.get("message", "").strip().lower()
    user_id = request.get("user_id", "anonymous")  # Get user identifier

    print(f"💬 Chat request received - Message: '{message[:50]}...', User ID: '{user_id}'")

    # Parse user_id (handle both registered users and guest visitors)
    actual_user_id = None
    if user_id.startswith("web_user_"):
        try:
            actual_user_id = int(user_id.replace("web_user_", ""))
        except:
            # It's a guest visitor ID like "user_1234567890"
            actual_user_id = user_id
    else:
        # It's a guest visitor ID like "user_1234567890"
        actual_user_id = user_id

    print(f"🎯 Parsed user_id: '{actual_user_id}' (type: {type(actual_user_id)})")

    # Keyword detection for different topics
    keywords = {
        'parks': ['parc', 'parks', 'national', 'réserve', 'réserves'],
        'species': ['animal', 'espèce', 'espèces', 'faune', 'flore', 'biodiversité', 'oiseau', 'mammifère'],
        'trails': ['sentier', 'randonnée', 'marche', 'chemin', 'trail', 'hiking'],
        'weather': ['météo', 'temps', 'climat', 'pluie', 'soleil'],
        'emergency': ['urgence', 'danger', 'accident', 'aide', 'secours']
    }

    # Determine the topic based on keywords
    detected_topic = None
    for topic, words in keywords.items():
        if any(word in message for word in words):
            detected_topic = topic
            break

    try:
        # Generate response based on detected topic
        with Session(get_engine()) as session:
            if detected_topic == 'parks':
                # Query database for parks info
                parks = session.exec(select(ParkDB).limit(5)).all()
                total_parks = len(session.exec(select(ParkDB)).all())

                response_lines = [
                    f"🌿 Nous avons {total_parks} parcs nationaux en Tunisie!",
                    "Voici quelques exemples remarquables :"
                ]

                for park in parks[:3]:
                    response_lines.append(f"• {park.name} ({park.governorate}) - {park.area_km2} km²")

                response = "\n".join(response_lines)
                suggestions = ["Voir la carte", "Liste complète", "Parcs près de Tunis"]

            elif detected_topic == 'species':
                # Query database for species info
                species = session.exec(select(SpeciesDB).limit(5)).all()
                total_species = len(session.exec(select(SpeciesDB)).all())

                response_lines = [
                    f"🦋 Notre base de données contient {total_species} espèces!",
                    "Découvrez quelques-unes de nos espèces rares :"
                ]

                # Get some rare species
                rare_species = session.exec(
                    select(SpeciesDB).where(SpeciesDB.rarity.in_(['rare', 'très_rare'])).limit(3)
                ).all()

                for specie in rare_species:
                    rarity_text = "Rare" if specie.rarity == 'rare' else "Très rare"
                    response_lines.append(f"• {specie.name} ({rarity_text}) - {specie.conservation_status or 'Statut à déterminer'}")

                response = "\n".join(response_lines)
                suggestions = ["Voir toutes les espèces", "Espèces en danger", "Guide d'observation"]

            elif detected_topic == 'trails':
                # Query database for trails info
                trails = session.exec(select(TrailDB).limit(3)).all()
                total_trails = len(session.exec(select(TrailDB)).all())

                response_lines = [
                    f"🥾 Plus de {total_trails} sentiers de randonnée vous attendent!",
                    "Quelques suggestions de parcours :"
                ]

                for trail in trails:
                    difficulty_text = {
                        'facile': 'Facile',
                        'modéré': 'Modéré',
                        'difficile': 'Difficile'
                    }.get(trail.difficulty, trail.difficulty)
                    response_lines.append(f"• {trail.name} - {trail.length_km} km ({difficulty_text})")

                response = "\n".join(response_lines)
                suggestions = ["Tous les sentiers", "Par difficulté", "Carte des randonnées"]

            elif detected_topic == 'weather':
                response = "🌤️ Je peux vous aider avec les informations météorologiques!\n\nSélectionnez un parc pour connaître la météo actuelle :\n• Ichkeul\n• Boukornine\n• Chambi\n• Zaghouan"
                suggestions = ["Météo Ichkeul", "Prévisions", "Conditions actuelles"]

            elif detected_topic == 'emergency':
                response = "🚨 URGENCE DÉTECTÉE\n\nJe vais vous guider pour obtenir de l'aide immédiate :\n\n1. Restez calme et en sécurité\n2. Appelez le 190 (SAMU) pour les urgences médicales\n3. Police: 197\n4. Partagez votre localisation si possible\n\nQuelle est votre situation d'urgence ?"
                suggestions = ["Appeler SAMU", "Contacter Police", "Partager position"]

            else:
                # Fallback for unrecognized queries
                response = "🤔 Je peux vous renseigner sur les parcs nationaux, la faune et la flore, les sentiers de randonnée, la météo et les situations d'urgence.\n\nQue souhaitez-vous savoir ?"
                suggestions = ["Liste des parcs", "Espèces rares", "Sentiers de marche", "Météo", "Numéros d'urgence"]

    except Exception as e:
        # Database error handling
        logger.error(f"Chat database error: {e}")
        response = "🤖 Désolé, je rencontre un problème technique. Veuillez réessayer dans quelques instants."
        suggestions = ["Réessayer", "Contacter support"]

    # Award XP points for user interaction (safe - only affects user rows)
    if actual_user_id:
        try:
            award_xp_points(actual_user_id, 5)  # 5 XP per message

            # Check for badge eligibility based on activity
            if detected_topic == 'parks':
                check_badge_eligibility(actual_user_id, "asked_parks")
            elif detected_topic == 'species':
                check_badge_eligibility(actual_user_id, "asked_species")

            # Always check for conversation starter
            check_badge_eligibility(actual_user_id, "chat_message")

        except Exception as e:
            logger.error(f"Gamification error for user {actual_user_id}: {e}")
            # Gamification failures don't break the chat

    # Log the final response for debugging
    logger.info(f"Chat response: {response[:100]}...")

    return {
        "response": response,
        "suggestions": suggestions
    }

# Admin login routes - secret routes for backend management
@app.get("/admin/login")
async def admin_login_page(request: Request):
    """Secret admin login page for backend management."""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
async def admin_login_auth(request: Request):
    """Admin login authentication endpoint."""
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")

        print(f"DEBUG: Received admin login attempt for username='{username}'")

        # Check database for admin user
        with Session(get_engine()) as session:
            admin_user = session.exec(
                select(AdminUser).where(AdminUser.username == username)
            ).first()

            if not admin_user:
                print(f"DEBUG: Admin user '{username}' not found in database")
                return {"error": "Invalid credentials"}

            # Verify password
            from utils import verify_password
            if not verify_password(password, admin_user.hashed_password):
                print(f"DEBUG: Password verification failed for user '{username}'")
                print(f"DEBUG: Expected hash: {admin_user.hashed_password}")
                return {"error": "Invalid credentials"}

            print(f"DEBUG: Admin login successful for user '{username}'")
            access_token = create_access_token(data={"sub": username, "role": "admin"})

            # Update last login
            admin_user.last_login = datetime.now().isoformat()
            session.add(admin_user)
            session.commit()

            return {"access_token": access_token, "token_type": "bearer", "success": True}

    except Exception as e:
        print(f"DEBUG: Admin login error: {e}")
        return {"error": "Login failed"}

# Catch-all frontend route - MUST be at the absolute bottom for SPA routing
@app.get("/{full_path:path}")
async def catch_all_frontend(full_path: str, request: Request):
    # For SPA routing, serve index.html for all unmatched routes
    # API routes are handled by routers above, so this only catches frontend routes
    return templates.TemplateResponse("index.html", {"request": request})

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
