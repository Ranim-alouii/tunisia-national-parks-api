"""
Species management router
"""

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select
from database import get_engine
from models import SpeciesDB
from schemas import SpeciesCreate, SpeciesUpdate
from typing import List

# Create router
router = APIRouter()

# ---------- SPECIES ENDPOINTS ----------

@router.get("")
def list_species(
    type: str | None = None,
    search: str | None = None,
    park_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Get a list of all species with optional filtering and search."""
    with Session(get_engine()) as session:
        stmt = select(SpeciesDB)

        # Apply type filter
        if type:
            stmt = stmt.where(SpeciesDB.type == type)

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                (SpeciesDB.name.ilike(search_term)) |
                (SpeciesDB.scientific_name.ilike(search_term)) |
                (SpeciesDB.description.ilike(search_term))
            )

        # Apply park filter - join with ParkSpeciesLink
        if park_id is not None:
            from models import ParkSpeciesLink
            stmt = stmt.join(
                ParkSpeciesLink,
                ParkSpeciesLink.species_id == SpeciesDB.species_id
            ).where(ParkSpeciesLink.park_id == park_id)

        stmt = stmt.offset(skip).limit(limit)
        species_list = session.exec(stmt).all()

        # Convert to proper response format with id alias
        return [
            {
                "id": s.species_id,
                "name": s.name,
                "type": s.type,
                "scientific_name": s.scientific_name,
                "description": s.description,
                "threats": s.threats,
                "protection_measures": s.protection_measures,
                "safety_guidelines": s.safety_guidelines,
                "medicinal_use": s.medicinal_use,
                "image_url": s.image_url,
                "park_ids": []  # Simplified for now
            }
            for s in species_list
        ]

@router.get("/{species_id}")
def get_species(species_id: int):
    """Get a specific species by ID."""
    with Session(get_engine()) as session:
        species = session.get(SpeciesDB, species_id)
        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        return {
            "id": species.species_id,
            "name": species.name,
            "type": species.type,
            "scientific_name": species.scientific_name,
            "description": species.description,
            "threats": species.threats,
            "protection_measures": species.protection_measures,
            "safety_guidelines": species.safety_guidelines,
            "medicinal_use": species.medicinal_use,
            "image_url": species.image_url,
            "park_ids": []  # Simplified for now
        }

@router.post("", status_code=201)
def create_species(species_in: SpeciesCreate):
    """Create a new species."""
    with Session(get_engine()) as session:
        db_species = SpeciesDB(
            name=species_in.name,
            type=species_in.type,
            scientific_name=species_in.scientific_name,
            description=species_in.description,
            threats=species_in.threats or "",
            protection_measures=species_in.protection_measures or "",
            safety_guidelines=species_in.safety_guidelines or "",
            medicinal_use=species_in.medicinal_use,
            image_url=species_in.image_url,
        )
        session.add(db_species)
        session.commit()
        session.refresh(db_species)

        # Create park-species links if park_ids provided
        if species_in.park_ids:
            from models import ParkSpeciesLink
            for park_id in species_in.park_ids:
                link = ParkSpeciesLink(
                    park_id=park_id,
                    species_id=db_species.species_id
                )
                session.add(link)
            session.commit()

        return {
            "id": db_species.species_id,
            "name": db_species.name,
            "type": db_species.type,
            "scientific_name": db_species.scientific_name,
            "description": db_species.description,
            "threats": db_species.threats,
            "protection_measures": db_species.protection_measures,
            "safety_guidelines": db_species.safety_guidelines,
            "medicinal_use": db_species.medicinal_use,
            "image_url": db_species.image_url,
            "park_ids": species_in.park_ids
        }

@router.put("/{species_id}")
def update_species(species_id: int, species_in: SpeciesUpdate):
    """Update an existing species."""
    with Session(get_engine()) as session:
        species = session.get(SpeciesDB, species_id)
        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        update_data = species_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(species, key):
                setattr(species, key, value)

        session.add(species)
        session.commit()
        session.refresh(species)

        return {
            "id": species.species_id,
            "name": species.name,
            "type": species.type,
            "scientific_name": species.scientific_name,
            "description": species.description,
            "threats": species.threats,
            "protection_measures": species.protection_measures,
            "safety_guidelines": species.safety_guidelines,
            "medicinal_use": species.medicinal_use,
            "image_url": species.image_url,
            "park_ids": []  # Simplified for now
        }

@router.delete("/{species_id}", status_code=204)
def delete_species(species_id: int):
    """Delete a species."""
    with Session(get_engine()) as session:
        species = session.get(SpeciesDB, species_id)
        if not species:
            raise HTTPException(status_code=404, detail="Species not found")

        session.delete(species)
        session.commit()
        return None
