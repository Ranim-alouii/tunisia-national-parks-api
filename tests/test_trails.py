"""
Unit tests for trails API endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestTrailsAPI:
    """Test suite for trails endpoints"""

    def test_list_trails_for_park(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test listing trails for a park"""
        # Create a park first
        park_response = client.post("/api/parks", json=sample_park_data, headers=auth_headers)
        park_id = park_response.json()["id"]

        # Initially no trails
        response = client.get(f"/api/parks/{park_id}/trails")
        assert response.status_code == 200
        assert response.json() == []

        # Create a trail
        trail_data = {
            "park_id": park_id,
            "name": "Mountain Trail",
            "description": "A scenic mountain trail",
            "difficulty": "modéré",
            "length_km": 5.5,
            "duration_hours": 3.0,
            "elevation_gain": 300,
            "trail_type": "loop",
            "highlights": ["Mountain views", "Waterfall"]
        }

        client.post("/api/trails", json=trail_data, headers=auth_headers)

        # Now should have one trail
        response = client.get(f"/api/parks/{park_id}/trails")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Mountain Trail"
        assert data[0]["difficulty"] == "modéré"
        assert data[0]["length_km"] == 5.5

    def test_create_trail(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test creating a trail"""
        # Create a park first
        park_response = client.post("/api/parks", json=sample_park_data, headers=auth_headers)
        park_id = park_response.json()["id"]

        trail_data = {
            "park_id": park_id,
            "name": "Forest Path",
            "description": "A peaceful forest walking path",
            "difficulty": "facile",
            "length_km": 2.0,
            "duration_hours": 1.0,
            "elevation_gain": 50,
            "trail_type": "out_and_back",
            "highlights": ["Forest scenery", "Bird watching"]
        }

        response = client.post("/api/trails", json=trail_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Forest Path"
        assert data["difficulty"] == "facile"
        assert data["length_km"] == 2.0
        assert data["trail_type"] == "out_and_back"
        assert data["highlights"] == ["Forest scenery", "Bird watching"]

    def test_get_trail(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test getting a specific trail"""
        # Create park and trail
        park_response = client.post("/api/parks", json=sample_park_data, headers=auth_headers)
        park_id = park_response.json()["id"]

        trail_data = {
            "park_id": park_id,
            "name": "Test Trail",
            "description": "Test trail description",
            "difficulty": "modéré",
            "length_km": 3.0,
            "duration_hours": 2.0,
            "trail_type": "loop"
        }

        create_response = client.post("/api/trails", json=trail_data, headers=auth_headers)
        trail_id = create_response.json()["trail_id"]

        # Get the trail
        response = client.get(f"/api/trails/{trail_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["trail_id"] == trail_id
        assert data["name"] == "Test Trail"
        assert data["park_id"] == park_id

    def test_get_nonexistent_trail(self, client: TestClient):
        """Test getting a trail that doesn't exist"""
        response = client.get("/api/trails/999")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == 404
        assert "Trail not found" in data["error"]["message"]

    def test_update_trail(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test updating a trail"""
        # Create park and trail
        park_response = client.post("/api/parks", json=sample_park_data, headers=auth_headers)
        park_id = park_response.json()["id"]

        trail_data = {
            "park_id": park_id,
            "name": "Original Trail",
            "description": "Original description",
            "difficulty": "facile",
            "length_km": 2.0,
            "duration_hours": 1.0,
            "trail_type": "loop"
        }

        create_response = client.post("/api/trails", json=trail_data, headers=auth_headers)
        trail_id = create_response.json()["trail_id"]

        # Update the trail
        update_data = {
            "name": "Updated Trail",
            "description": "Updated description",
            "length_km": 3.5,
            "highlights": ["New highlight"]
        }

        response = client.put(f"/api/trails/{trail_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Trail"
        assert data["description"] == "Updated description"
        assert data["length_km"] == 3.5
        assert data["highlights"] == ["New highlight"]

    def test_delete_trail(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test deleting a trail"""
        # Create park and trail
        park_response = client.post("/api/parks", json=sample_park_data, headers=auth_headers)
        park_id = park_response.json()["id"]

        trail_data = {
            "park_id": park_id,
            "name": "Trail to Delete",
            "description": "This trail will be deleted",
            "difficulty": "facile",
            "length_km": 1.0,
            "duration_hours": 0.5,
            "trail_type": "loop"
        }

        create_response = client.post("/api/trails", json=trail_data, headers=auth_headers)
        trail_id = create_response.json()["trail_id"]

        # Delete the trail
        response = client.delete(f"/api/trails/{trail_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/trails/{trail_id}")
        assert get_response.status_code == 404

    def test_create_trail_for_nonexistent_park(self, client: TestClient, auth_headers: dict):
        """Test creating trail for park that doesn't exist"""
        trail_data = {
            "park_id": 999,
            "name": "Invalid Trail",
            "description": "Trail for invalid park",
            "difficulty": "facile",
            "length_km": 1.0,
            "duration_hours": 0.5,
            "trail_type": "loop"
        }

        response = client.post("/api/trails", json=trail_data, headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == 404
        assert "Park not found" in data["error"]["message"]

    def test_trail_validation(self, client: TestClient, auth_headers: dict, sample_park_data: dict):
        """Test trail input validation"""
        # Create a park first
        park_response = client.post("/api/parks", json=sample_park_data, headers=auth_headers)
        park_id = park_response.json()["id"]

        # Test invalid difficulty
        invalid_data = {
            "park_id": park_id,
            "name": "Test Trail",
            "description": "Test description",
            "difficulty": "invalid_difficulty",  # Should be facile/modéré/difficile
            "length_km": 1.0,
            "duration_hours": 0.5,
            "trail_type": "loop"
        }

        response = client.post("/api/trails", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

        # Test negative length
        invalid_data = {
            "park_id": park_id,
            "name": "Test Trail",
            "description": "Test description",
            "difficulty": "facile",
            "length_km": -1.0,  # Invalid
            "duration_hours": 0.5,
            "trail_type": "loop"
        }

        response = client.post("/api/trails", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_update_trail_park_change(self, client: TestClient, auth_headers: dict):
        """Test updating trail to change park"""
        # Create two parks
        park_data1 = {
            "name": "Park 1",
            "governorate": "Governorate 1",
            "description": "First park",
            "latitude": 36.8065,
            "longitude": 10.1815,
            "area_km2": 100.0,
            "google_maps_url": "https://maps.google.com/?q=36.8065,10.1815",
        }

        park_data2 = {
            "name": "Park 2",
            "governorate": "Governorate 2",
            "description": "Second park",
            "latitude": 37.8065,
            "longitude": 11.1815,
            "area_km2": 150.0,
            "google_maps_url": "https://maps.google.com/?q=37.8065,11.1815",
        }

        park1_response = client.post("/api/parks", json=park_data1, headers=auth_headers)
        park1_id = park1_response.json()["id"]

        park2_response = client.post("/api/parks", json=park_data2, headers=auth_headers)
        park2_id = park2_response.json()["id"]

        # Create trail in park 1
        trail_data = {
            "park_id": park1_id,
            "name": "Test Trail",
            "description": "Test trail",
            "difficulty": "facile",
            "length_km": 1.0,
            "duration_hours": 0.5,
            "trail_type": "loop"
        }

        create_response = client.post("/api/trails", json=trail_data, headers=auth_headers)
        trail_id = create_response.json()["trail_id"]

        # Update to park 2
        update_data = {"park_id": park2_id}
        response = client.put(f"/api/trails/{trail_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["park_id"] == park2_id

        # Verify trail appears in park 2's trails
        response = client.get(f"/api/parks/{park2_id}/trails")
        assert response.status_code == 200
        trails = response.json()
        assert len(trails) == 1
        assert trails[0]["trail_id"] == trail_id
