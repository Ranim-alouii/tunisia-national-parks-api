"""
Pydantic schemas for API request/response models
"""

from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict

# ========== PARK SCHEMAS ==========

class Park(BaseModel):
    """Park response model"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    governorate: str
    description: str
    latitude: float
    longitude: float
    area_km2: float
    images: List[str]

class ParkCreate(BaseModel):
    """Park creation model"""
    name: str
    governorate: str
    description: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    area_km2: float = Field(gt=0)
    google_maps_url: str = Field(min_length=10, max_length=1000)

class ParkUpdate(BaseModel):
    """Park update model"""
    name: str | None = None
    governorate: str | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    area_km2: float | None = Field(default=None, gt=0)

# ========== SPECIES SCHEMAS ==========

class Species(BaseModel):
    """Species response model"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    species_id: int = Field(alias="id", serialization_alias="species_id")
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str | None = None
    protection_measures: str | None = None
    safety_guidelines: str | None = None
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int]

class SpeciesCreate(BaseModel):
    """Species creation model"""
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str = ""
    protection_measures: str = ""
    safety_guidelines: str = ""
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int] = []

class SpeciesUpdate(BaseModel):
    """Species update model"""
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

# ========== TRAIL SCHEMAS ==========

class Trail(BaseModel):
    """Trail response model"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    trail_id: int = Field(alias="id", serialization_alias="trail_id")
    park_id: int
    name: str
    description: str
    difficulty: str
    length_km: float
    duration_hours: float
    elevation_gain: int | None = None
    trail_type: str
    surface: str | None = None
    highlights: List[str] | None = None

class TrailCreate(BaseModel):
    """Trail creation model"""
    park_id: int
    name: str
    description: str
    difficulty: str
    length_km: float = Field(gt=0)
    duration_hours: float = Field(gt=0)
    elevation_gain: int | None = None
    trail_type: str
    surface: str | None = None
    highlights: List[str] | None = None

class TrailUpdate(BaseModel):
    """Trail update model"""
    park_id: int | None = None
    name: str | None = None
    description: str | None = None
    difficulty: str | None = None
    length_km: float | None = None
    duration_hours: float | None = None
    elevation_gain: int | None = None
    trail_type: str | None = None
    surface: str | None = None
    highlights: List[str] | None = None

# ========== AUTH SCHEMAS ==========

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str

class User(BaseModel):
    """User base model"""
    username: str
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    """User with hashed password"""
    hashed_password: str

class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(min_length=8)
    full_name: str | None = Field(default=None, max_length=255)

class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str
