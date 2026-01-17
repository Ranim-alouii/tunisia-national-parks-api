"""
Unit tests for parks API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from models import ParkDB


class TestParksAPI:
    """Test suite for parks API endpoints"""

    def test_list_parks_empty(self, client: TestClient):
        """Test listing parks when database is empty"""
        response = client.get("/api/parks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_park(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test creating a new park"""
        response = client.post(
            "/api/parks",
            json=sample_park_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["name"] == sample_park_data["name"]
        assert data["governorate"] == sample_park_data["governorate"]
        assert data["description"] == sample_park_data["description"]
        assert data["latitude"] == sample_park_data["latitude"]
        assert data["longitude"] == sample_park_data["longitude"]
        assert data["area_km2"] == sample_park_data["area_km2"]
        assert "images" in data

    def test_get_park(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test getting a specific park by ID"""
        # First create a park
        create_response = client.post(
            "/api/parks",
            json=sample_park_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        park_id = create_response.json()["id"]

        # Now get the park
        response = client.get(f"/api/parks/{park_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == park_id
        assert data["name"] == sample_park_data["name"]
        assert data["governorate"] == sample_park_data["governorate"]

    def test_get_park_not_found(self, client: TestClient):
        """Test getting a park that doesn't exist"""
        response = client.get("/api/parks/999")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["message"] == "Park not found"

    def test_update_park(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test updating an existing park"""
        # Create a park first
        create_response = client.post(
            "/api/parks",
            json=sample_park_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        park_id = create_response.json()["id"]

        # Update the park
        update_data = {
            "name": "Updated Test Park",
            "description": "Updated description",
        }
        response = client.put(
            f"/api/parks/{park_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == park_id
        assert data["name"] == "Updated Test Park"
        assert data["description"] == "Updated description"
        # Other fields should remain unchanged
        assert data["governorate"] == sample_park_data["governorate"]

    def test_delete_park(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test deleting a park"""
        # Create a park first
        create_response = client.post(
            "/api/parks",
            json=sample_park_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        park_id = create_response.json()["id"]

        # Delete the park
        response = client.delete(f"/api/parks/{park_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/parks/{park_id}")
        assert get_response.status_code == 404

    def test_list_parks_with_filters(self, client: TestClient, auth_headers: dict):
        """Test listing parks with filters"""
        # Create multiple parks
        parks_data = [
            {
                "name": "Park A",
                "governorate": "Governorate A",
                "description": "Description A",
                "latitude": 36.8065,
                "longitude": 10.1815,
                "area_km2": 50.0,
            },
            {
                "name": "Park B",
                "governorate": "Governorate B",
                "description": "Description B",
                "latitude": 37.8065,
                "longitude": 11.1815,
                "area_km2": 100.0,
            },
        ]

        for park_data in parks_data:
            response = client.post("/api/parks", json=park_data, headers=auth_headers)
            assert response.status_code == 201

        # Test filtering by governorate
        response = client.get("/api/parks?governorate=Governorate A")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Park A"

        # Test filtering by area
        response = client.get("/api/parks?min_area=75")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Park B"

    def test_park_validation(self, client: TestClient, auth_headers: dict):
        """Test park data validation"""
        # Test invalid latitude
        invalid_data = {
            "name": "Test Park",
            "governorate": "Test Governorate",
            "description": "Test description",
            "latitude": 100,  # Invalid latitude (> 90)
            "longitude": 10.1815,
            "area_km2": 100.0,
        }

        response = client.post("/api/parks", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_unauthorized_access(self, client: TestClient, sample_park_data: dict):
        """Test that protected endpoints require authentication"""
        # Try to create park without auth
        response = client.post("/api/parks", json=sample_park_data)
        assert response.status_code == 401

        # Try to update park without auth
        response = client.put("/api/parks/1", json=sample_park_data)
        assert response.status_code == 401

        # Try to delete park without auth
        response = client.delete("/api/parks/1")
        assert response.status_code == 401
