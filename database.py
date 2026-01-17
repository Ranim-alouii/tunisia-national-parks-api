from sqlmodel import SQLModel, create_engine, Session
from config import settings


# Echo=False in production to avoid logging SQL; keep True while developing if you like
engine = create_engine(settings.DATABASE_URL, echo=True)


def get_engine():
    """Get the appropriate engine (test or production)."""
    # Check if we're in testing mode
    try:
        # This is a bit of a hack, but we need to access the app state
        # In tests, the app will have test_engine set
        import main
        if hasattr(main.app.state, 'test_engine'):
            return main.app.state.test_engine
    except:
        pass
    return engine


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
        UserDB,
        UserBadgeDB,
        UserStatsDB,
        HealthProfileDB,
    )

    SQLModel.metadata.create_all(get_engine())


def get_db():
    """FastAPI dependency that provides a database session."""
    with Session(get_engine()) as session:
        yield session
