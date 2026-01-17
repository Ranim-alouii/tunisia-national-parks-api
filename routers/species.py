"""
Species management router
"""

from typing import List, Literal
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, or_

from models import SpeciesDB, ParkSpeciesLink, ParkDB
from database import engine
from utils import get_file_url

# Create router
router = APIRouter(prefix="/api/species", tags=["Species"])

# ---------- SPECIES MODELS ----------

from pydantic import BaseModel

class Species(BaseModel):
    id: int
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

# ---------- SPECIES ENDPOINTS ----------

@router.get("/", response_model=List[Species])
def list_species(
    type: Literal["animal", "plant"] | None = None,
    park_id: int | None = None,
    conservation_status: str | None = None,
    rarity: str | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    skip: int = 0,
    limit: int = 50,
):
    """Get a list of all species with advanced filtering and sorting."""
    with Session(engine) as session:
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

@router.get("/{species_id}", response_model=Species)
def get_species(species_id: int):
    """Get details of a specific species."""
    with Session(engine) as session:
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

@router.post("/", response_model=Species, status_code=201)
def create_species(species_in: SpeciesCreate):
    """Create a new species."""
    with Session(engine) as session:
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

@router.put("/{species_id}", response_model=Species)
def update_species(species_id: int, species_in: SpeciesUpdate):
    """Update an existing species."""
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        data = species_in.model_dump(exclude_unset=True)

        simple_fields = {
            "name", "type", "scientific_name", "description",
            "threats", "protection_measures", "safety_guidelines",
            "medicinal_use", "image_url",
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

@router.delete("/{species_id}", status_code=204)
def delete_species(species_id: int):
    """Delete a species."""
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        session.exec(
            select(ParkSpeciesLink)
            .where(ParkSpeciesLink.species_id == species_db.species_id)
        )
        session.query(ParkSpeciesLink).filter(
            ParkSpeciesLink.species_id == species_db.species_id
        ).delete(synchronize_session=False)

        session.delete(species_db)
        session.commit()
        return None
