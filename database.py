from sqlmodel import SQLModel, create_engine, Session
from config import settings


# Echo=False in production to avoid logging SQL; keep True while developing if you like
engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db() -> None:
    """
    Initialize database tables.

    In production, prefer Alembic migrations instead of create_all.
    """
    from models import (
        ParkDB,
        SpeciesDB,
        ParkSpeciesLink,
        TrailDB,
        ReviewDB,
        BadgeDB,
        SightingDB,
    )

    SQLModel.metadata.create_all(engine)


def get_db():
    """FastAPI dependency that provides a database session."""
    with Session(engine) as session:
        yield session
