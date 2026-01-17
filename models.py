from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON, CheckConstraint, Index, UniqueConstraint
from sqlmodel import SQLModel, Field


class ParkDB(SQLModel, table=True):
    __tablename__ = "parks"

    # Primary key with auto-increment
    id: Optional[int] = Field(default=None, primary_key=True)

    # Core fields with indexes
    name: str = Field(index=True, min_length=1, max_length=255)
    governorate: str = Field(index=True, min_length=1, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    latitude: float = Field(ge=-90, le=90)  # Valid latitude range
    longitude: float = Field(ge=-180, le=180)  # Valid longitude range

    # Area validation
    area_km2: Optional[float] = Field(default=None, ge=0.1, le=10000)

    # Image storage as JSON
    images: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    # URLs with validation
    google_maps_url: str = Field(min_length=10, max_length=1000)
    hero_image_url: Optional[str] = Field(default=None, max_length=1000)
    gallery_images: Optional[str] = Field(default=None, max_length=10000)  # JSON array

    # Categorical fields with constraints
    difficulty_level: Optional[str] = Field(
        default=None,
        regex="^(facile|modéré|difficile)$",
        max_length=20
    )

    # JSON fields for arrays
    accessibility: Optional[str] = Field(default=None, max_length=1000)  # JSON array
    best_months: Optional[str] = Field(default=None, max_length=500)  # JSON array
    activities: Optional[str] = Field(default=None, max_length=1000)  # JSON array
    facilities: Optional[str] = Field(default=None, max_length=1000)  # JSON array

    # Trekking circuits (GeoJSON for paths)
    circuit: Optional[str] = Field(default=None, max_length=50000)  # GeoJSON data for trekking paths

    # Practical details
    entrance_fee: Optional[str] = Field(default=None, max_length=100)
    opening_hours: Optional[str] = Field(default=None, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    contact_email: Optional[str] = Field(default=None, max_length=255)

    # Statistics with validation
    area_hectares: Optional[int] = Field(default=None, ge=1, le=100000)
    elevation_min: Optional[int] = Field(default=None, ge=0, le=5000)
    elevation_max: Optional[int] = Field(default=None, ge=0, le=5000)
    visitor_count_yearly: Optional[int] = Field(default=None, ge=0, le=10000000)

    # Ratings with validation
    average_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    total_reviews: Optional[int] = Field(default=0, ge=0)

    # Database constraints and indexes
    __table_args__ = (
        # Check constraints for data validation
        CheckConstraint('latitude >= -90 AND latitude <= 90', name='valid_latitude'),
        CheckConstraint('longitude >= -180 AND longitude <= 180', name='valid_longitude'),
        CheckConstraint('area_km2 > 0', name='positive_area'),
        CheckConstraint('elevation_min >= 0', name='positive_elevation_min'),
        CheckConstraint('elevation_max >= 0', name='positive_elevation_max'),
        CheckConstraint('elevation_max >= elevation_min', name='valid_elevation_range'),
        CheckConstraint('average_rating >= 0 AND average_rating <= 5', name='valid_rating'),
        CheckConstraint('total_reviews >= 0', name='positive_reviews'),

        # Unique constraint for park names within governorate
        UniqueConstraint('name', 'governorate', name='unique_park_per_governorate'),

        # Additional indexes for performance
        Index('idx_parks_governorate_area', 'governorate', 'area_km2'),
        Index('idx_parks_rating_reviews', 'average_rating', 'total_reviews'),
        Index('idx_parks_difficulty', 'difficulty_level'),
    )

    # NOTE: relationships are intentionally omitted here to avoid
    # SQLAlchemy 2.x relationship() annotation issues. Queries that
    # need links should join explicitly using foreign keys.
    # See ParkSpeciesLink, TrailDB, ReviewDB, SightingDB below.


class SpeciesDB(SQLModel, table=True):
    __tablename__ = "species"

    species_id: Optional[int] = Field(default=None, primary_key=True)

    # Core identification with indexes and validation
    name: str = Field(index=True, min_length=1, max_length=255)
    scientific_name: str = Field(index=True, min_length=1, max_length=255)
    type: str = Field(regex="^(animal|plant)$", max_length=20)  # Must be "animal" or "plant"
    description: str = Field(min_length=10, max_length=5000)

    # Conservation and safety fields
    threats: Optional[str] = Field(default=None, max_length=2000)
    protection_measures: Optional[str] = Field(default=None, max_length=2000)
    safety_guidelines: Optional[str] = Field(default=None, max_length=2000)
    medicinal_use: Optional[str] = Field(default=None, max_length=1000)
    toxicity_level: Optional[str] = Field(default=None, regex="^(none|low|medium|high)$", max_length=20)

    # Enhanced safety and interaction fields
    danger_level: Optional[str] = Field(default=None, regex="^(none|low|medium|high)$", max_length=20)
    interaction_guide: Optional[str] = Field(default=None, max_length=2000)
    first_aid: Optional[str] = Field(default=None, max_length=2000)  # First aid for injuries/stings/allergic reactions

    # Multimedia with URL validation
    image_url: Optional[str] = Field(default=None, max_length=1000)
    gallery_images: Optional[str] = Field(default=None, max_length=10000)  # JSON array
    audio_url: Optional[str] = Field(default=None, max_length=1000)
    video_url: Optional[str] = Field(default=None, max_length=1000)

    # Biological information
    conservation_status: Optional[str] = Field(
        default=None,
        regex="^(endangered|vulnerable|least_concern|near_threatened)$",
        max_length=50
    )
    habitat_type: Optional[str] = Field(default=None, max_length=100)
    diet: Optional[str] = Field(default=None, max_length=500)
    lifespan: Optional[str] = Field(default=None, max_length=100)
    size: Optional[str] = Field(default=None, max_length=100)
    weight: Optional[str] = Field(default=None, max_length=100)

    # Behavioral and sighting information
    best_viewing_months: Optional[str] = Field(default=None, max_length=500)  # JSON array
    activity_time: Optional[str] = Field(
        default=None,
        regex="^(diurne|nocturne|crépusculaire)$",
        max_length=50
    )
    rarity: Optional[str] = Field(
        default=None,
        regex="^(common|rare|very_rare)$",
        max_length=20
    )

    # Database constraints and indexes
    __table_args__ = (
        # Unique constraint for scientific names
        UniqueConstraint('scientific_name', name='unique_scientific_name'),

        # Additional indexes for performance
        Index('idx_species_type_rarity', 'type', 'rarity'),
        Index('idx_species_conservation', 'conservation_status'),
        Index('idx_species_habitat', 'habitat_type'),
        Index('idx_species_name_scientific', 'name', 'scientific_name'),
    )

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

    # Enhanced badge system
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    icon: str = Field(min_length=1, max_length=50)  # Emoji or icon class
    category: str = Field(regex="^(exploration|conservation|social|expert)$", max_length=20)
    requirement_type: str = Field(regex="^(parks_visited|species_seen|trails_completed|reviews_written|sightings_reported)$", max_length=30)
    requirement_value: int = Field(ge=1)  # Number required to unlock
    points: int = Field(ge=0, default=10)  # Gamification points awarded
    rarity: str = Field(regex="^(common|uncommon|rare|epic|legendary)$", default="common", max_length=20)

    # Uniqueness constraint
    __table_args__ = (
        UniqueConstraint('name', name='unique_badge_name'),
        Index('idx_badges_category_rarity', 'category', 'rarity'),
    )


class UserBadgeDB(SQLModel, table=True):
    __tablename__ = "user_badges"

    user_badge_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int  # Will be linked to user management system
    badge_id: int = Field(foreign_key="badges.badge_id")

    earned_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    progress: int = Field(default=0)  # Current progress toward badge
    completed: bool = Field(default=False)

    # Relationship to BadgeDB intentionally omitted


class UserStatsDB(SQLModel, table=True):
    __tablename__ = "user_stats"

    user_stats_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int  # Will be linked to user management system

    # Activity counters
    parks_visited: int = Field(default=0)
    species_seen: int = Field(default=0)
    trails_completed: int = Field(default=0)
    reviews_written: int = Field(default=0)
    sightings_reported: int = Field(default=0)

    # Points and levels
    total_points: int = Field(default=0)
    current_level: int = Field(default=1)
    experience_points: int = Field(default=0)

    # Achievements
    badges_earned: int = Field(default=0)
    consecutive_days_active: int = Field(default=0)

    # Timestamps
    last_activity_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


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


class HealthProfileDB(SQLModel, table=True):
    __tablename__ = "health_profiles"

    profile_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int  # Will be linked to user management system

    # Allergies and sensitivities
    allergies: Optional[str] = Field(default=None, max_length=1000)  # JSON array of allergies
    pollen_allergy: bool = Field(default=False)
    insect_sting_allergy: bool = Field(default=False)
    medication_allergy: Optional[str] = Field(default=None, max_length=500)

    # Physical conditions
    asthma: bool = Field(default=False)
    heart_condition: bool = Field(default=False)
    high_blood_pressure: bool = Field(default=False)
    diabetes: bool = Field(default=False)
    mobility_issues: bool = Field(default=False)

    # Physical capabilities
    physical_stamina: str = Field(regex="^(low|medium|high)$", default="medium", max_length=20)
    walking_distance_limit: Optional[int] = Field(default=None, ge=0, le=50000)  # meters
    preferred_terrain: Optional[str] = Field(default=None, regex="^(flat|hilly|mountainous)$", max_length=20)

    # Emergency contacts
    emergency_contact_name: Optional[str] = Field(default=None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=50)
    medical_notes: Optional[str] = Field(default=None, max_length=2000)

    # Medical information
    blood_type: Optional[str] = Field(default=None, regex="^(A\\+|A-|B\\+|B-|AB\\+|AB-|O\\+|O-)$", max_length=10)
    current_medications: Optional[str] = Field(default=None, max_length=1000)

    # Tracking
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Database constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='unique_user_health_profile'),
        CheckConstraint('walking_distance_limit >= 0', name='positive_walking_limit'),
    )
