from sqlmodel import SQLModel, create_engine

DATABASE_URL = "sqlite:///./tunisia_parks.db"

engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    from models import ParkDB, SpeciesDB  # will create in next step

    SQLModel.metadata.create_all(engine)
