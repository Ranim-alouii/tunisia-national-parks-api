from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal


app = FastAPI(title="Tunisia National Parks API")

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
parks_db: List[Park] = [
    Park(
        id=1,
        name="Parc national de l'Ichkeul",
        governorate="Bizerte",
        description="Parc national autour du lac Ichkeul, zone humide importante pour les oiseaux migrateurs.",
        latitude=37.169,
        longitude=9.672,
        area_km2=126.0,
        images=[]
    ),
    Park(
        id=2,
        name="Parc national de Chaambi",
        governorate="Kasserine",
        description="Parc de montagne autour du Djebel Chaambi, abritant une faune et flore de haute altitude.",
        latitude=35.233,
        longitude=8.672,
        area_km2=67.0,
        images=[]
    ),
]
@app.get("/api/parks", response_model=List[Park])
def list_parks():
    return parks_db

@app.get("/api/parks", response_model=List[Park])
def list_parks():
    return parks_db

@app.get("/api/parks/{park_id}", response_model=Park)
def get_park(park_id: int):
    for park in parks_db:
        if park.id == park_id:
            return park
    raise HTTPException(status_code=404, detail="Park not found")
class Species(BaseModel):
    id: int
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    image_url: str | None = None
    park_ids: List[int]  # ids of parks where this species is present
species_db: List[Species] = [
    Species(
        id=1,
        name="Gazelle de Cuvier",
        type="animal",
        scientific_name="Gazella cuvieri",
        description="Antilope saharienne présente dans certains parcs du centre et du sud tunisien.",
        threats="Braconnage, perte d'habitat, dérangement par les activités humaines.",
        protection_measures="Renforcer la surveillance, limiter le pâturage illégal, sensibiliser les visiteurs à ne pas poursuivre les animaux.",
        image_url=None,
        park_ids=[2],  # Chaambi (exemple)
    ),
    Species(
        id=2,
        name="Cerf de Barbarie",
        type="animal",
        scientific_name="Cervus elaphus barbarus",
        description="Sous-espèce de cerf présente dans les massifs forestiers du nord-ouest tunisien.",
        threats="Fragmentation des forêts, braconnage, incendies.",
        protection_measures="Protéger les forêts, lutter contre les incendies et renforcer la législation contre la chasse illégale.",
        image_url=None,
        park_ids=[1],  # Ichkeul (exemple)
    ),
    Species(
        id=3,
        name="Pin d'Alep",
        type="plant",
        scientific_name="Pinus halepensis",
        description="Espèce de pin très répandue dans les forêts tunisiennes.",
        threats="Incendies répétés, sécheresse, coupes abusives.",
        protection_measures="Prévenir les incendies, contrôler l'exploitation du bois, sensibiliser à ne pas allumer de feux en forêt.",
        image_url=None,
        park_ids=[1, 2],
    ),
]
@app.get("/api/species", response_model=List[Species])
def list_species(
    type: Literal["animal", "plant"] | None = None,
    park_id: int | None = None,
):
    results = species_db

    if type is not None:
        results = [s for s in results if s.type == type]

    if park_id is not None:
        results = [s for s in results if park_id in s.park_ids]

    return results


@app.get("/api/species/{species_id}", response_model=Species)
def get_species(species_id: int):
    for s in species_db:
        if s.id == species_id:
            return s
    raise HTTPException(status_code=404, detail="Species not found")
@app.get("/api/parks/{park_id}/species", response_model=List[Species])
def list_species_for_park(park_id: int):
    # verify park exists
    if not any(p.id == park_id for p in parks_db):
        raise HTTPException(status_code=404, detail="Park not found")

    return [s for s in species_db if park_id in s.park_ids]
@app.get("/api/species/{species_id}/parks", response_model=List[Park])
def list_parks_for_species(species_id: int):
    species = next((s for s in species_db if s.id == species_id), None)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")

    return [p for p in parks_db if p.id in species.park_ids]
