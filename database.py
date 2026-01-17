from sqlmodel import SQLModel, create_engine, Session
from config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

def init_db():
    from models import ParkDB, SpeciesDB
    SQLModel.metadata.create_all(engine)

def get_db():
    """Database session dependency for FastAPI"""
    with Session(engine) as session:
        yield session
