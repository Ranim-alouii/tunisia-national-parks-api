"""
Test configuration and fixtures for the Tunisia National Parks API
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

# Add the parent directory to the path to import main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import init_db, engine
from config import settings


@pytest.fixture(scope="session")
def test_db():
    """Create a test database with tables"""
    # Create in-memory SQLite database for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    SQLModel.metadata.create_all(test_engine)

    yield test_engine

    # Clean up
    test_engine.dispose()


@pytest.fixture
def client(test_db):
    """FastAPI test client with test database"""
    # Override the database engine for testing
    app.state.test_engine = test_db

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(test_db):
    """Database session for testing"""
    with Session(test_db) as session:
        yield session


@pytest.fixture
def sample_park_data():
    """Sample park data for testing"""
    return {
        "name": "Test Park",
        "governorate": "Test Governorate",
        "description": "A beautiful test park",
        "latitude": 36.8065,
        "longitude": 10.1815,
        "area_km2": 100.0,
    }


@pytest.fixture
def sample_species_data():
    """Sample species data for testing"""
    return {
        "name": "Test Animal",
        "scientific_name": "Testus animalus",
        "type": "animal",
        "description": "A test animal species",
        "threats": "Habitat loss",
        "protection_measures": "Conservation efforts",
        "safety_guidelines": "Keep distance",
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers(client, sample_user_data):
    """Authentication headers for testing protected endpoints"""
    # Register user
    client.post("/auth/register", json=sample_user_data)

    # Login to get token
    login_response = client.post(
        "/auth/token",
        data={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
