from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

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
