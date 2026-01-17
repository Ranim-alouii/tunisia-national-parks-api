"""
Parks management router
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from models import ParkDB
from database import get_engine
from utils import get_file_url

# Create router
router = APIRouter(prefix="/api/parks", tags=["Parks"])

# ---------- PARK MODELS ----------

from pydantic import BaseModel, Field

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

class ParkUpdate(BaseModel):
    name: str | None = None
    governorate: str | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    area_km2: float | None = Field(default=None, gt=0)

# ---------- PARK ENDPOINTS ----------

@router.get("/", response_model=List[Park])
def list_parks(
    skip: int = 0,
    limit: int = 50,
    governorate: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
):
    """List all parks with filtering and pagination."""
    with Session(get_engine()) as session:
        query = session.query(ParkDB)

        # Apply filters
        if governorate:
            query = query.filter(ParkDB.governorate == governorate)
        if min_area is not None:
            query = query.filter(ParkDB.area_km2 >= min_area)
        if max_area is not None and max_area > 0:
            query = query.filter(ParkDB.area_km2 <= max_area)

        # Apply pagination
        parks_db = query.offset(skip).limit(limit).all()

        import json
        result = []
        for p in parks_db:
            try:
                images_list = json.loads(p.images) if p.images else []
                processed_images = [get_file_url(img, "parks") for img in images_list]
                result.append(Park(
                    id=p.id,
                    name=p.name,
                    governorate=p.governorate,
                    description=p.description,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    area_km2=p.area_km2,
                    images=processed_images,
                ))
            except Exception as e:
                print(f"Error processing park {p.id}: {e}")
                # Fallback: return empty images list
                result.append(Park(
                    id=p.id,
                    name=p.name,
                    governorate=p.governorate,
                    description=p.description,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    area_km2=p.area_km2,
                    images=[],
                ))
        return result

@router.get("/{park_id}", response_model=Park)
def get_park(park_id: int):
    """Get a specific park by ID."""
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        import json
        return Park(
            id=park.id,
            name=park.name,
            governorate=park.governorate,
            description=park.description,
            latitude=park.latitude,
            longitude=park.longitude,
            area_km2=park.area_km2,
            images=[get_file_url(img, "parks") for img in (json.loads(park.images) if park.images else [])],
        )

@router.post("/", response_model=Park, status_code=201)
def create_park(park_in: ParkCreate):
    """Create a new park."""
    with Session(get_engine()) as session:
        park_db = ParkDB(
            name=park_in.name,
            governorate=park_in.governorate,
            description=park_in.description,
            latitude=park_in.latitude,
            longitude=park_in.longitude,
            area_km2=park_in.area_km2,
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

@router.put("/{park_id}", response_model=Park)
def update_park(park_id: int, park_in: ParkUpdate):
    """Update an existing park."""
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

        import json
        return Park(
            id=park_db.id,
            name=park_db.name,
            governorate=park_db.governorate,
            description=park_db.description,
            latitude=park_db.latitude,
            longitude=park_db.longitude,
            area_km2=park_db.area_km2,
            images=[get_file_url(img, "parks") for img in (json.loads(park_db.images) if park_db.images else [])],
        )

@router.delete("/{park_id}", status_code=204)
def delete_park(park_id: int):
    """Delete a park."""
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        session.delete(park_db)
        session.commit()
        return None
