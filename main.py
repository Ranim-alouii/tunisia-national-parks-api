from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal

from database import init_db, engine
from models import ParkDB, SpeciesDB
from sqlmodel import Session, select

app = FastAPI(title="Tunisia National Parks API")

@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


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
    latitude: float
    longitude: float
    area_km2: float


class ParkUpdate(BaseModel):
    name: str | None = None
    governorate: str | None = None
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    area_km2: float | None = None

@app.get("/api/parks", response_model=List[Park])
def list_parks():
    with Session(engine) as session:
        parks_db = session.exec(select(ParkDB)).all()
        return [
            Park(
                id=p.id,
                name=p.name,
                governorate=p.governorate,
                description=p.description,
                latitude=p.latitude,
                longitude=p.longitude,
                area_km2=p.area_km2,
                images=[],  # we will fill later
            )
            for p in parks_db
        ]


@app.get("/api/parks/{park_id}", response_model=Park)
def get_park(park_id: int):
    with Session(engine) as session:
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
            images=[],
        )

@app.post("/api/parks", response_model=Park, status_code=201)
def create_park(park_in: ParkCreate):
    with Session(engine) as session:
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
    
@app.put("/api/parks/{park_id}", response_model=Park)
def update_park(park_id: int, park_in: ParkUpdate):
    with Session(engine) as session:
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
            images=[],
        )
    
@app.delete("/api/parks/{park_id}", status_code=204)
def delete_park(park_id: int):
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        session.delete(park_db)
        session.commit()
        return None

class Species(BaseModel):
    id: int
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    image_url: str | None = None
    park_ids: List[int]

class SpeciesCreate(BaseModel):
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    image_url: str | None = None
    park_ids: List[int] = []  # parks where the species lives


class SpeciesUpdate(BaseModel):
    name: str | None = None
    type: Literal["animal", "plant"] | None = None
    scientific_name: str | None = None
    description: str | None = None
    threats: str | None = None
    protection_measures: str | None = None
    image_url: str | None = None
    park_ids: List[int] | None = None

@app.get("/api/species", response_model=List[Species])
def list_species(
    type: Literal["animal", "plant"] | None = None,
    park_id: int | None = None,
):
    with Session(engine) as session:
        statement = select(SpeciesDB)

        if type is not None:
            statement = statement.where(SpeciesDB.type == type)

        species_db = session.exec(statement).all()

        # if park filter, filter in Python using relationship
        if park_id is not None:
            species_db = [
                s for s in species_db
                if any(p.id == park_id for p in s.parks)
            ]

        return [
            Species(
                id=s.id,
                name=s.name,
                type=s.type.value,  # Enum to str
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats,
                protection_measures=s.protection_measures,
                image_url=s.image_url,
                park_ids=[p.id for p in s.parks],
            )
            for s in species_db
        ]


@app.get("/api/species/{species_id}", response_model=Species)
def get_species(species_id: int):
    with Session(engine) as session:
        s = session.get(SpeciesDB, species_id)
        if s is None:
            raise HTTPException(status_code=404, detail="Species not found")

        return Species(
            id=s.id,
            name=s.name,
            type=s.type.value,
            scientific_name=s.scientific_name,
            description=s.description,
            threats=s.threats,
            protection_measures=s.protection_measures,
            image_url=s.image_url,
            park_ids=[p.id for p in s.parks],
        )
    
@app.get("/api/parks/{park_id}/species", response_model=List[Species])
def list_species_for_park(park_id: int):
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        return [
            Species(
                id=s.id,
                name=s.name,
                type=s.type.value,
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats,
                protection_measures=s.protection_measures,
                image_url=s.image_url,
                park_ids=[p.id for p in s.parks],
            )
            for s in park.species
        ]

from models import ParkDB, SpeciesDB, ParkSpeciesLink
# make sure ParkSpeciesLink is imported

@app.post("/api/species", response_model=Species, status_code=201)
def create_species(species_in: SpeciesCreate):
    with Session(engine) as session:
        species_db = SpeciesDB(
            name=species_in.name,
            type=species_in.type,  # Enum field, Literal values match Enum names
            scientific_name=species_in.scientific_name,
            description=species_in.description,
            threats=species_in.threats,
            protection_measures=species_in.protection_measures,
            image_url=species_in.image_url,
        )
        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        # link to parks
        if species_in.park_ids:
            for park_id in species_in.park_ids:
                park = session.get(ParkDB, park_id)
                if park:
                    link = ParkSpeciesLink(park_id=park.id, species_id=species_db.id)
                    session.add(link)
            session.commit()
            session.refresh(species_db)

        return Species(
            id=species_db.id,
            name=species_db.name,
            type=species_db.type.value,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats,
            protection_measures=species_db.protection_measures,
            image_url=species_db.image_url,
            park_ids=[p.id for p in species_db.parks],
        )
    
@app.put("/api/species/{species_id}", response_model=Species)
def update_species(species_id: int, species_in: SpeciesUpdate):
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        data = species_in.model_dump(exclude_unset=True)

        # update simple fields
        simple_fields = {
            "name",
            "type",
            "scientific_name",
            "description",
            "threats",
            "protection_measures",
            "image_url",
        }
        for field in simple_fields:
            if field in data:
                setattr(species_db, field, data[field])

        # update park links if provided
        if "park_ids" in data:
            new_ids = set(data["park_ids"] or [])
            current_ids = {p.id for p in species_db.parks}

            # remove links not in new_ids
            for park in list(species_db.parks):
                if park.id not in new_ids:
                    species_db.parks.remove(park)

            # add new links
            for park_id in new_ids - current_ids:
                park = session.get(ParkDB, park_id)
                if park:
                    species_db.parks.append(park)

        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        return Species(
            id=species_db.id,
            name=species_db.name,
            type=species_db.type.value,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats,
            protection_measures=species_db.protection_measures,
            image_url=species_db.image_url,
            park_ids=[p.id for p in species_db.parks],
        )
    
@app.delete("/api/species/{species_id}", status_code=204)
def delete_species(species_id: int):
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        session.delete(species_db)
        session.commit()
        return None

class RouteInfo(BaseModel):
    park_id: int
    park_name: str
    governorate: str
    latitude: float
    longitude: float
    nearest_city: str
    travel_advice: str
    safety_tips: List[str]

def build_route_info(park: ParkDB) -> RouteInfo:
    # Very simple mapping; you can extend later
    if "Ichkeul" in park.name:
        nearest_city = "Bizerte"
        travel_advice = (
            "From Tunis, drive north towards Bizerte (A4), then follow signs to "
            "Ichkeul National Park. Plan 1.5–2 hours by car."
        )
    elif "Chaambi" in park.name:
        nearest_city = "Kasserine"
        travel_advice = (
            "From Kasserine, follow the main road south-west towards Chaambi National Park. "
            "Check current security advice before travelling in this region."
        )
    else:
        nearest_city = park.governorate
        travel_advice = (
            "Use a navigation app or local directions to reach the park from the nearest town."
        )

    safety_tips = [
        "Check current security and access rules for the park before your trip.",  # [web:192][web:203]
        "Tell someone your route and expected return time.",
        "Take enough water, sun protection, and a fully charged phone.",
        "Stay on marked trails and respect park rules about waste and wildlife.",  # [web:200][web:203]
        "Avoid hiking alone late in the day; plan to leave before dark where parks have closing hours.",  # [web:191][web:203]
    ]

    return RouteInfo(
        park_id=park.id,
        park_name=park.name,
        governorate=park.governorate,
        latitude=park.latitude,
        longitude=park.longitude,
        nearest_city=nearest_city,
        travel_advice=travel_advice,
        safety_tips=safety_tips,
    )

@app.get("/api/parks/{park_id}/route", response_model=RouteInfo)
def get_route_for_park(park_id: int):
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        return build_route_info(park_db)

class EmergencyRequest(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    park_id: int | None = None
    situation: str  # short free-text description from the user


class EmergencyResponse(BaseModel):
    message: str
    recommended_actions: List[str]
    emergency_numbers: dict
    park_info: dict | None = None

@app.post("/api/emergency", response_model=EmergencyResponse)
def handle_emergency(payload: EmergencyRequest):
    # Base emergency numbers in Tunisia
    emergency_numbers = {
        "international": 112,
        "ambulance_samu": 190,   # SAMU / ambulance [web:186][web:188]
        "police": 197,           # Police de secours [web:186][web:188]
        "fire": 198,             # Protection civile / pompiers [web:186][web:188]
    }

    # Build context about park if provided
    park_info = None
    message_prefix = "Emergency reported."

    with Session(engine) as session:
        if payload.park_id is not None:
            park = session.get(ParkDB, payload.park_id)
            if park:
                park_info = {
                    "park_id": park.id,
                    "park_name": park.name,
                    "governorate": park.governorate,
                    "latitude": park.latitude,
                    "longitude": park.longitude,
                }
                message_prefix = f"Emergency near {park.name}."

    # General recommended actions based on hiking safety guidance
    recommended_actions = [
        "If you or someone with you is in immediate danger or has a serious injury, call the appropriate emergency number now (190 ambulance, 197 police, 198 fire, or 112).",  # [web:186][web:187][web:188]
        "Describe your location as clearly as possible: nearest town or road, park name, and any visible landmarks.",
        "If you have a GPS location on your phone or app, read the coordinates slowly to the operator.",
        "Unless you are in immediate danger (rockfall, fire, flooding), stay where you are after calling so rescuers can find you more easily.",  # [web:210]
        "Conserve phone battery: close non-essential apps, lower screen brightness, and keep the phone for emergency calls and navigation only.",  # [web:207][web:211]
        "Keep warm, hydrated, and sheltered while you wait for help; use extra clothes or a space blanket if you have one.",
    ]

    if payload.latitude is not None and payload.longitude is not None:
        recommended_actions.append(
            "Write down or screenshot your GPS coordinates so you can repeat them to emergency services if the call drops."
        )

    if park_info:
        recommended_actions.append(
            "Tell the operator you are in or near this park, and mention any official trail names or access roads you used."
        )

    message = f"{message_prefix} Stay calm and contact local emergency services."

    return EmergencyResponse(
        message=message,
        recommended_actions=recommended_actions,
        emergency_numbers=emergency_numbers,
        park_info=park_info,
    )

