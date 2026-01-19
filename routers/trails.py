"""
Trails management router
"""

from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from models import TrailDB, ParkDB
from database import get_engine
from schemas import Trail, TrailCreate, TrailUpdate

# Create router
router = APIRouter()

# ---------- TRAIL ENDPOINTS ----------

@router.get("")
def list_trails(
    park_id: int | None = None,
    difficulty: str | None = None,
    trail_type: str | None = None,
    min_length: float | None = None,
    max_length: float | None = None,
    skip: int = 0,
    limit: int = 50,
):
    """List all trails with filtering and pagination."""
    with Session(get_engine()) as session:
        query = session.query(TrailDB)

        # Apply filters
        if park_id is not None:
            query = query.filter(TrailDB.park_id == park_id)
        if difficulty:
            query = query.filter(TrailDB.difficulty == difficulty)
        if trail_type:
            query = query.filter(TrailDB.trail_type == trail_type)
        if min_length is not None:
            query = query.filter(TrailDB.length_km >= min_length)
        if max_length is not None and max_length > 0:
            query = query.filter(TrailDB.length_km <= max_length)

        # Apply pagination
        trails_db = query.offset(skip).limit(limit).all()

        return [
            Trail(
                id=t.trail_id,
                park_id=t.park_id,
                name=t.name,
                description=t.description,
                difficulty=t.difficulty,
                length_km=t.length_km,
                duration_hours=t.duration_hours,
                elevation_gain=t.elevation_gain,
                trail_type=t.trail_type,
                surface=t.surface,
                highlights=t.highlights.split(",") if t.highlights else None,
            )
            for t in trails_db
        ]

@router.get("/{trail_id}", response_model=Trail)
def get_trail(trail_id: int):
    """Get a specific trail by ID."""
    with Session(get_engine()) as session:
        trail = session.get(TrailDB, trail_id)
        if trail is None:
            raise HTTPException(status_code=404, detail="Trail not found")

        return Trail(
            id=trail.trail_id,
            park_id=trail.park_id,
            name=trail.name,
            description=trail.description,
            difficulty=trail.difficulty,
            length_km=trail.length_km,
            duration_hours=trail.duration_hours,
            elevation_gain=trail.elevation_gain,
            trail_type=trail.trail_type,
            surface=trail.surface,
            highlights=trail.highlights.split(",") if trail.highlights else None,
        )

@router.post("", response_model=Trail, status_code=201)
def create_trail(trail_in: TrailCreate):
    """Create a new trail."""
    # Validate difficulty level
    allowed_difficulties = ["facile", "modéré", "difficile"]
    if trail_in.difficulty not in allowed_difficulties:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid difficulty level. Must be one of: {', '.join(allowed_difficulties)}"
        )

    with Session(get_engine()) as session:
        # Verify park exists
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
            surface=trail_in.surface,
            highlights=",".join(trail_in.highlights) if trail_in.highlights else None,
        )
        session.add(trail_db)
        session.commit()
        session.refresh(trail_db)

        return Trail(
            id=trail_db.trail_id,
            park_id=trail_db.park_id,
            name=trail_db.name,
            description=trail_db.description,
            difficulty=trail_db.difficulty,
            length_km=trail_db.length_km,
            duration_hours=trail_db.duration_hours,
            elevation_gain=trail_db.elevation_gain,
            trail_type=trail_db.trail_type,
            surface=trail_db.surface,
            highlights=trail_db.highlights.split(",") if trail_db.highlights else None,
        )

@router.put("/{trail_id}", response_model=Trail)
def update_trail(trail_id: int, trail_in: TrailUpdate):
    """Update an existing trail."""
    with Session(get_engine()) as session:
        trail_db = session.get(TrailDB, trail_id)
        if trail_db is None:
            raise HTTPException(status_code=404, detail="Trail not found")

        # Verify park exists if park_id is being updated
        if trail_in.park_id is not None:
            park = session.get(ParkDB, trail_in.park_id)
            if park is None:
                raise HTTPException(status_code=404, detail="Park not found")

        data = trail_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            if field == "highlights":
                setattr(trail_db, field, ",".join(value) if value else None)
            else:
                setattr(trail_db, field, value)

        session.add(trail_db)
        session.commit()
        session.refresh(trail_db)

        return Trail(
            id=trail_db.trail_id,
            park_id=trail_db.park_id,
            name=trail_db.name,
            description=trail_db.description,
            difficulty=trail_db.difficulty,
            length_km=trail_db.length_km,
            duration_hours=trail_db.duration_hours,
            elevation_gain=trail_db.elevation_gain,
            trail_type=trail_db.trail_type,
            surface=trail_db.surface,
            highlights=trail_db.highlights.split(",") if trail_db.highlights else None,
        )

@router.delete("/{trail_id}", status_code=204)
def delete_trail(trail_id: int):
    """Delete a trail."""
    with Session(get_engine()) as session:
        trail_db = session.get(TrailDB, trail_id)
        if trail_db is None:
            raise HTTPException(status_code=404, detail="Trail not found")

        session.delete(trail_db)
        session.commit()
        return None
