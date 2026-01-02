from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class ParkDB(SQLModel, table=True):
    __tablename__ = "parks"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    governorate: str
    description: str
    latitude: float
    longitude: float
    area_km2: Optional[float] = None
    images: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    google_maps_url: str

    # Visual enhancements
    hero_image_url: Optional[str] = None
    gallery_images: Optional[str] = None  # JSON array: ["url1", "url2", ...]

    # Practical info
    difficulty_level: Optional[str] = None  # "facile", "modéré", "difficile"
    accessibility: Optional[str] = None  # JSON: ["wheelchair", "family_friendly", "pets_allowed"]
    best_months: Optional[str] = None  # JSON: ["3", "4", "5"] (March, April, May)

    # Activities & facilities
    activities: Optional[str] = None  # JSON: ["hiking", "birdwatching", "camping"]
    facilities: Optional[str] = None  # JSON: ["parking", "toilets", "restaurant"]

    # Practical details
    entrance_fee: Optional[str] = None  # "Gratuit" or "10 TND"
    opening_hours: Optional[str] = None  # "8h00 - 17h00"
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    # Statistics
    area_hectares: Optional[int] = None
    elevation_min: Optional[int] = None  # meters
    elevation_max: Optional[int] = None  # meters
    visitor_count_yearly: Optional[int] = None

    # Ratings
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = None

    # NOTE: relationships are intentionally omitted here to avoid
    # SQLAlchemy 2.x relationship() annotation issues. Queries that
    # need links should join explicitly using foreign keys.
    # See ParkSpeciesLink, TrailDB, ReviewDB, SightingDB below.


class SpeciesDB(SQLModel, table=True):
    __tablename__ = "species"

    species_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    scientific_name: str = Field(index=True)
    type: str  # "animal" or "plant"
    description: str

    # Existing fields
    threats: Optional[str] = None
    protection_measures: Optional[str] = None
    safety_guidelines: Optional[str] = None
    medicinal_use: Optional[str] = None
    toxicity_level: Optional[str] = None
    image_url: Optional[str] = None

    # Enhanced multimedia
    gallery_images: Optional[str] = None  # JSON array
    audio_url: Optional[str] = None  # Sound/call of the species
    video_url: Optional[str] = None  # Short video

    # Detailed info
    conservation_status: Optional[str] = None  # "endangered", "vulnerable", "least_concern"
    habitat_type: Optional[str] = None  # "forest", "desert", "wetland"
    diet: Optional[str] = None
    lifespan: Optional[str] = None
    size: Optional[str] = None
    weight: Optional[str] = None

    # Sighting info
    best_viewing_months: Optional[str] = None  # JSON: ["3", "4", "5"]
    activity_time: Optional[str] = None  # "diurne", "nocturne", "crépusculaire"
    rarity: Optional[str] = None  # "common", "rare", "very_rare"

    # NOTE: relationships omitted; use ParkSpeciesLink for joins.


class ParkSpeciesLink(SQLModel, table=True):
    __tablename__ = "park_species"

    park_id: int = Field(foreign_key="parks.id", primary_key=True)
    species_id: int = Field(foreign_key="species.species_id", primary_key=True)

    # Sighting-specific info
    population_estimate: Optional[str] = None  # "50-100 individuals"
    sighting_probability: Optional[str] = None  # "high", "medium", "low"
    best_spots: Optional[str] = None  # JSON: ["Trail A", "Viewpoint B"]

    # No relationship() attributes here; they caused SQLAlchemy 2.x errors.


class TrailDB(SQLModel, table=True):
    __tablename__ = "trails"

    trail_id: Optional[int] = Field(default=None, primary_key=True)
    park_id: int = Field(foreign_key="parks.id")

    name: str
    description: str
    difficulty: str  # "facile", "modéré", "difficile"
    length_km: float
    duration_hours: float
    elevation_gain: Optional[int] = None  # meters

    trail_type: str  # "loop", "out_and_back", "point_to_point"
    surface: Optional[str] = None  # "dirt", "rocky", "paved"

    # GPS data
    gpx_data: Optional[str] = None  # GeoJSON or GPX format
    waypoints: Optional[str] = None  # JSON array of coordinates

    # Features
    highlights: Optional[str] = None  # JSON: ["waterfall", "viewpoint", "ruins"]

    # Relationship to ParkDB intentionally omitted for compatibility.


class ReviewDB(SQLModel, table=True):
    __tablename__ = "reviews"

    review_id: Optional[int] = Field(default=None, primary_key=True)
    park_id: int = Field(foreign_key="parks.id")

    author_name: str
    rating: int  # 1-5 stars
    title: str
    comment: str
    visit_date: Optional[str] = None

    helpful_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Relationship to ParkDB intentionally omitted.


class BadgeDB(SQLModel, table=True):
    __tablename__ = "badges"

    badge_id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    description: str
    icon: str  # Emoji or icon class
    requirement: str  # What user must do to earn it
    points: int  # Gamification points


class SightingDB(SQLModel, table=True):
    __tablename__ = "sightings"

    sighting_id: Optional[int] = Field(default=None, primary_key=True)
    park_id: int = Field(foreign_key="parks.id")
    species_id: int = Field(foreign_key="species.species_id")

    reporter_name: str
    sighting_date: str
    location_lat: float
    location_lng: float

    photo_url: Optional[str] = None
    notes: Optional[str] = None

    verified: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
