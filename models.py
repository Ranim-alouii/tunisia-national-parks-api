from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column, Text
from sqlalchemy import Enum as SQLAlchemyEnum


class ParkSpeciesLink(SQLModel, table=True):
    park_id: int = Field(foreign_key="parkdb.id", primary_key=True)
    species_id: int = Field(foreign_key="speciesdb.id", primary_key=True)


class ParkDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    governorate: str = Field(max_length=100)
    description: str = Field(sa_column=Column(Text))
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    area_km2: float = Field(gt=0)
    images: Optional[List[str]] = Field(default=None, sa_column=Column(Text, nullable=True))

    species: List["SpeciesDB"] = Relationship(
        back_populates="parks", link_model=ParkSpeciesLink
    )


class SpeciesType(str, Enum):
    animal = "animal"
    plant = "plant"


class SpeciesDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    type: SpeciesType = Field(sa_column=Column(SQLAlchemyEnum(SpeciesType)))
    scientific_name: str = Field(max_length=150)
    description: str = Field(sa_column=Column(Text))
    threats: str = Field(sa_column=Column(Text))
    protection_measures: str = Field(sa_column=Column(Text))
    safety_guidelines: str = Field(default="", sa_column=Column(Text))
    medicinal_use: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    image_url: Optional[str] = None

    parks: List[ParkDB] = Relationship(
        back_populates="species", link_model=ParkSpeciesLink
    )
# ---------- END OF FILE ----------