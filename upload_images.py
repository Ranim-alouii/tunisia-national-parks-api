#!/usr/bin/env python3
"""
Script to upload images to parks and species
Usage: python upload_images.py
"""

import requests
import os
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TOKEN = "YOUR_JWT_TOKEN_HERE"  # Get this from /auth/token endpoint

def get_auth_header():
    """Get authorization header for API requests."""
    return {"Authorization": f"Bearer {TOKEN}"}

def upload_park_image(park_id: int, image_path: str):
    """Upload an image for a specific park."""
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return

    url = f"{BASE_URL}/api/upload/parks/{park_id}"

    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
        response = requests.post(url, files=files, headers=get_auth_header())

    if response.status_code == 201:
        data = response.json()
        print(f"✅ Successfully uploaded image to park {park_id}")
        print(f"   URL: {data['media_info']['url']}")
        return data
    else:
        print(f"❌ Failed to upload image: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def upload_species_image(species_id: int, image_path: str):
    """Upload an image for a specific species."""
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return

    url = f"{BASE_URL}/api/upload/species/{species_id}/image"

    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
        response = requests.post(url, files=files, headers=get_auth_header())

    if response.status_code == 201:
        data = response.json()
        print(f"✅ Successfully uploaded image to species {species_id}")
        print(f"   URL: {data['url']}")
        return data
    else:
        print(f"❌ Failed to upload image: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def main():
    """Main function to demonstrate image uploads."""

    # First, get authentication token
    print("🔑 Getting authentication token...")

    # You need to login first to get the token
    login_data = {
        "username": "admin",  # Use your admin credentials
        "password": "admin123"
    }

    token_response = requests.post(f"{BASE_URL}/auth/token", data=login_data)

    if token_response.status_code == 200:
        global TOKEN
        TOKEN = token_response.json()["access_token"]
        print("✅ Authentication successful!")
    else:
        print("❌ Authentication failed. Please check your credentials.")
        return

    # Example: Upload images to parks
    print("\n🏞️  Uploading park images...")

    # Create some sample image mappings (replace with your actual images)
    park_images = {
        1: "sample_park_ichkeul.jpg",
        2: "sample_park_boukornine.jpg",
        3: "sample_park_zaghouan.jpg",
    }

    for park_id, image_file in park_images.items():
        upload_park_image(park_id, image_file)

    # Example: Upload images to species
    print("\n🦌 Uploading species images...")

    species_images = {
        1: "sample_species_flamingo.jpg",
        2: "sample_species_gazelle.jpg",
        5: "sample_species_eagle.jpg",
    }

    for species_id, image_file in species_images.items():
        upload_species_image(species_id, image_file)

    print("\n📋 Upload Summary:")
    print("- Park images are stored in: uploads/parks/{park_id}/")
    print("- Species images are stored in: uploads/species/{species_id}/")
    print("- Images are automatically optimized and resized")
    print("- URLs are returned and can be viewed in the API responses")

if __name__ == "__main__":
    main()
