from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship



class ParkSpeciesLink(SQLModel, table=True):
    park_id: int = Field(foreign_key="parkdb.id", primary_key=True)
    species_id: int = Field(foreign_key="speciesdb.id", primary_key=True)


class ParkDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    governorate: str
    description: str
    latitude: float
    longitude: float
    area_km2: float

    species: List["SpeciesDB"] = Relationship(
        back_populates="parks", link_model=ParkSpeciesLink
    )

class SpeciesType(str, Enum):
    animal = "animal"
    plant = "plant"


class SpeciesDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: SpeciesType
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    image_url: Optional[str] = None

    parks: List[ParkDB] = Relationship(
        back_populates="species", link_model=ParkSpeciesLink
    )
