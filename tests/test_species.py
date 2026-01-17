"""
Unit tests for species API endpoints
"""

import pytest
from fastapi.testclient import TestClient

from models import SpeciesDB, ParkSpeciesLink


class TestSpeciesAPI:
    """Test suite for species API endpoints"""

    def test_list_species_empty(self, client: TestClient):
        """Test listing species when database is empty"""
        response = client.get("/api/species")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_species(self, client: TestClient, auth_headers: dict, sample_species_data: dict):
        """Test creating a new species"""
        response = client.post(
            "/api/species",
            json=sample_species_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["name"] == sample_species_data["name"]
        assert data["scientific_name"] == sample_species_data["scientific_name"]
        assert data["type"] == sample_species_data["type"]
        assert data["description"] == sample_species_data["description"]
        assert data["threats"] == sample_species_data["threats"]
        assert data["protection_measures"] == sample_species_data["protection_measures"]
        assert data["safety_guidelines"] == sample_species_data["safety_guidelines"]
        assert "park_ids" in data
        assert isinstance(data["park_ids"], list)

    def test_get_species(self, client: TestClient, auth_headers: dict, sample_species_data: dict):
        """Test getting a specific species by ID"""
        # First create a species
        create_response = client.post(
            "/api/species",
            json=sample_species_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        species_id = create_response.json()["id"]

        # Now get the species
        response = client.get(f"/api/species/{species_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == species_id
        assert data["name"] == sample_species_data["name"]
        assert data["scientific_name"] == sample_species_data["scientific_name"]
        assert data["type"] == sample_species_data["type"]

    def test_get_species_not_found(self, client: TestClient):
        """Test getting a species that doesn't exist"""
        response = client.get("/api/species/999")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["message"] == "Species not found"

    def test_update_species(self, client: TestClient, auth_headers: dict, sample_species_data: dict):
        """Test updating an existing species"""
        # Create a species first
        create_response = client.post(
            "/api/species",
            json=sample_species_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        species_id = create_response.json()["id"]

        # Update the species
        update_data = {
            "name": "Updated Test Animal",
            "description": "Updated description",
        }
        response = client.put(
            f"/api/species/{species_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == species_id
        assert data["name"] == "Updated Test Animal"
        assert data["description"] == "Updated description"
        # Other fields should remain unchanged
        assert data["scientific_name"] == sample_species_data["scientific_name"]

    def test_delete_species(self, client: TestClient, auth_headers: dict, sample_species_data: dict):
        """Test deleting a species"""
        # Create a species first
        create_response = client.post(
            "/api/species",
            json=sample_species_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        species_id = create_response.json()["id"]

        # Delete the species
        response = client.delete(f"/api/species/{species_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/species/{species_id}")
        assert get_response.status_code == 404

    def test_list_species_with_filters(self, client: TestClient, auth_headers: dict):
        """Test listing species with filters"""
        # Create multiple species
        species_data = [
            {
                "name": "Lion",
                "scientific_name": "Panthera leo",
                "type": "animal",
                "description": "A large cat",
                "threats": "Habitat loss",
                "protection_measures": "Conservation",
                "safety_guidelines": "Keep distance",
            },
            {
                "name": "Oak Tree",
                "scientific_name": "Quercus robur",
                "type": "plant",
                "description": "A tree",
                "threats": "Deforestation",
                "protection_measures": "Protection",
                "safety_guidelines": "None",
            },
        ]

        for species in species_data:
            response = client.post("/api/species", json=species, headers=auth_headers)
            assert response.status_code == 201

        # Test filtering by type
        response = client.get("/api/species?type=animal")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Lion"
        assert data[0]["type"] == "animal"

        # Test filtering by type - plants
        response = client.get("/api/species?type=plant")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Oak Tree"
        assert data[0]["type"] == "plant"

    def test_species_search(self, client: TestClient, auth_headers: dict):
        """Test species search functionality"""
        # Create test species
        species_data = {
            "name": "African Elephant",
            "scientific_name": "Loxodonta africana",
            "type": "animal",
            "description": "Large mammal",
            "threats": "Poaching",
            "protection_measures": "Anti-poaching",
            "safety_guidelines": "Observe from distance",
        }

        client.post("/api/species", json=species_data, headers=auth_headers)

        # Search by name
        response = client.get("/api/species?search=elephant")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "African Elephant"

        # Search by scientific name
        response = client.get("/api/species?search=loxodonta")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["scientific_name"] == "Loxodonta africana"

    def test_species_park_relationship(self, client: TestClient, auth_headers: dict):
        """Test species-park relationships"""
        # Create a park
        park_data = {
            "name": "Test Park",
            "governorate": "Test Gov",
            "description": "Test park",
            "latitude": 36.8065,
            "longitude": 10.1815,
            "area_km2": 100.0,
        }
        park_response = client.post("/api/parks", json=park_data, headers=auth_headers)
        assert park_response.status_code == 201
        park_id = park_response.json()["id"]

        # Create species linked to the park
        species_data = {
            "name": "Park Animal",
            "scientific_name": "Parkus animalus",
            "type": "animal",
            "description": "Animal in park",
            "threats": "None",
            "protection_measures": "Protected",
            "safety_guidelines": "Safe",
            "park_ids": [park_id],
        }

        species_response = client.post("/api/species", json=species_data, headers=auth_headers)
        assert species_response.status_code == 201
        species_id = species_response.json()["id"]

        # Get species for the park
        response = client.get(f"/api/parks/{park_id}/species")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == species_id
        assert data[0]["name"] == "Park Animal"

        # Filter species by park
        response = client.get(f"/api/species?park_id={park_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == species_id

    def test_species_validation(self, client: TestClient, auth_headers: dict):
        """Test species data validation"""
        # Test invalid type
        invalid_data = {
            "name": "Test Animal",
            "scientific_name": "Testus animalus",
            "type": "invalid_type",  # Should be 'animal' or 'plant'
            "description": "A test animal species",
            "threats": "Habitat loss",
            "protection_measures": "Conservation efforts",
            "safety_guidelines": "Keep distance",
        }

        response = client.post("/api/species", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_species_pagination(self, client: TestClient, auth_headers: dict):
        """Test species pagination"""
        # Create multiple species
        for i in range(5):
            species_data = {
                "name": f"Species {i}",
                "scientific_name": f"Species {i} scientific",
                "type": "animal",
                "description": f"Description {i}",
                "threats": "None",
                "protection_measures": "None",
                "safety_guidelines": "None",
            }
            response = client.post("/api/species", json=species_data, headers=auth_headers)
            assert response.status_code == 201

        # Test pagination
        response = client.get("/api/species?limit=2&skip=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Verify different results
        response2 = client.get("/api/species?limit=2&skip=3")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2) == 2

        # Ensure different results
        assert data[0]["id"] != data2[0]["id"]
