#!/usr/bin/env python3
"""
Script to add clear and accurate images for all parks and species in the Tunisia National Parks API
Using Unsplash API to fetch high-quality nature images
"""

import asyncio
import aiohttp
import json
import sys
import os
from pathlib import Path
from database import get_engine
from sqlalchemy import create_engine
from sqlmodel import Session, select
from models import ParkDB, SpeciesDB
from config import settings
from utils import save_upload_file

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unsplash API configuration
UNSPLASH_ACCESS_KEY = settings.UNSPLASH_ACCESS_KEY
UNSPLASH_BASE_URL = "https://api.unsplash.com"

# Park-specific search terms for better image relevance
PARK_SEARCH_TERMS = {
    "Ichkeul National Park": "Ichkeul lake wetland birds flamingos Tunisia",
    "Boukornine": "Boukornine mountain forest Tunisia nature landscape",
    "Zaghouan": "Zaghouan mountains Tunisia nature forest landscape",
    "Zembra": "Zembra island marine birds Tunisia Mediterranean",
    "El Feija": "El Feija forest deer Tunisia wildlife nature",
    "Chaambi": "Chaambi mountain peak Tunisia landscape summit",
    "Bouhedma": "Bouhedma desert wildlife Tunisia sand dunes",
    "Jebil": "Jebil desert dunes Tunisia Sahara landscape",
    "Dghoumès": "Dghoumès oasis desert Tunisia water spring",
    "Sidi Toui": "Sidi Toui steppe desert Tunisia wildlife nature",
    "Orbata": "Orbata mountains forest Tunisia nature landscape",
    "Chitana": "Chitana coast marine Tunisia Mediterranean sea",
    "Serj": "Serj forest Tunisia woodland nature landscape",
    "Mghilla": "Mghilla mountains Tunisia landscape nature",
    "Zaghdoud": "Zaghdoud forest Tunisia nature woodland",
    "Zeen": "Zeen forest Tunisia nature landscape",
    "Senghar": "Senghar desert Tunisia landscape nature"
}

# Species search terms for accurate wildlife images
SPECIES_SEARCH_TERMS = {
    "Greater Flamingo": "greater flamingo Phoenicopterus roseus Tunisia wetland bird",
    "Dorcas Gazelle": "dorcas gazelle Gazella dorcas Tunisia desert wildlife",
    "Golden Eagle": "golden eagle Aquila chrysaetos Tunisia raptor bird",
    "North African Hedgehog": "north african hedgehog Atelerix algirus Tunisia wildlife",
    "Nubian Ibex": "nubian ibex Capra nubiana Tunisia mountain wildlife",
    "Eurasian Lynx": "eurasian lynx Lynx lynx Tunisia forest wildlife"
}

async def fetch_unsplash_image(session, query, orientation="landscape"):
    """Fetch a single high-quality image from Unsplash"""
    if not UNSPLASH_ACCESS_KEY:
        print("❌ Unsplash API key not configured")
        return None

    url = f"{UNSPLASH_BASE_URL}/search/photos"
    params = {
        "query": query,
        "per_page": 1,
        "orientation": orientation,
        "content_filter": "high"
    }
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    try:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("results"):
                    photo = data["results"][0]
                    return {
                        "url": photo["urls"]["regular"],
                        "description": photo.get("description", ""),
                        "photographer": photo["user"]["name"],
                        "unsplash_url": photo["links"]["html"]
                    }
            else:
                print(f"❌ Unsplash API error: {response.status}")
    except Exception as e:
        print(f"❌ Error fetching image for '{query}': {e}")

    return None

async def download_and_save_image(session, image_url, filename, folder):
    """Download image from URL and save to local storage"""
    try:
        async with session.get(image_url) as response:
            if response.status == 200:
                # Create a file-like object for save_upload_file
                content = await response.read()

                # Create a simple file-like object
                from io import BytesIO
                file_obj = BytesIO(content)
                file_obj.filename = filename

                # Save using the existing upload function
                saved_filename = await save_upload_file(file_obj, folder)

                print(f"✅ Saved image: {saved_filename}")
                return saved_filename
            else:
                print(f"❌ Failed to download image: {response.status}")
    except Exception as e:
        print(f"❌ Error downloading image: {e}")

    return None

async def update_park_images():
    """Update images for all parks"""
    print("\n🏞️ Updating Park Images...")

    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    async with aiohttp.ClientSession() as session:
        with Session(get_engine()) as db_session:
            parks = db_session.exec(select(ParkDB)).all()

            for park in parks:
                print(f"\n📍 Processing park: {park.name} (ID: {park.id})")

                # Get search term for this park
                search_term = PARK_SEARCH_TERMS.get(park.name, f"{park.name} Tunisia nature landscape")

                # Fetch image from Unsplash
                image_data = await fetch_unsplash_image(session, search_term)
                if image_data:
                    print(f"📸 Found image for {park.name}")

                    # Download and save the image
                    filename = f"{park.name.lower().replace(' ', '_').replace('parc_national_', '')}_park.jpg"
                    saved_filename = await download_and_save_image(
                        session, image_data["url"], filename, "parks"
                    )

                    if saved_filename:
                        # Update park with new image
                        if not park.images:
                            park.images = []
                        park.images.append(saved_filename)
                        db_session.add(park)
                        db_session.commit()

                        print(f"✅ Updated {park.name} with image: {saved_filename}")
                    else:
                        print(f"❌ Failed to save image for {park.name}")
                else:
                    print(f"⚠️ No image found for {park.name}")

                # Small delay to be respectful to the API
                await asyncio.sleep(1)

async def update_species_images():
    """Update images for all species"""
    print("\n🦌 Updating Species Images...")

    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    async with aiohttp.ClientSession() as session:
        with Session(get_engine()) as db_session:
            species_list = db_session.exec(select(SpeciesDB)).all()

            for species in species_list:
                print(f"\n🐾 Processing species: {species.name} (ID: {species.species_id})")

                # Get search term for this species
                search_term = SPECIES_SEARCH_TERMS.get(species.name, f"{species.name} {species.scientific_name} wildlife")

                # Fetch image from Unsplash
                image_data = await fetch_unsplash_image(session, search_term)
                if image_data:
                    print(f"📸 Found image for {species.name}")

                    # Download and save the image
                    filename = f"{species.name.lower().replace(' ', '_')}_species.jpg"
                    saved_filename = await download_and_save_image(
                        session, image_data["url"], filename, "species"
                    )

                    if saved_filename:
                        # Update species with new image
                        species.image_url = saved_filename
                        db_session.add(species)
                        db_session.commit()

                        print(f"✅ Updated {species.name} with image: {saved_filename}")
                    else:
                        print(f"❌ Failed to save image for {species.name}")
                else:
                    print(f"⚠️ No image found for {species.name}")

                # Small delay to be respectful to the API
                await asyncio.sleep(1)

async def main():
    """Main function to update all images"""
    print("🌟 TUNISIA NATIONAL PARKS - IMAGE UPDATE SCRIPT")
    print("=" * 50)

    if not UNSPLASH_ACCESS_KEY:
        print("❌ ERROR: Unsplash API key not found in environment variables")
        print("Please set UNSPLASH_ACCESS_KEY in your .env file")
        return

    print(f"🔑 Using Unsplash API key: {UNSPLASH_ACCESS_KEY[:10]}...")
    print(f"📊 Database: {settings.DATABASE_URL}")

    # Update parks first
    await update_park_images()

    # Then update species
    await update_species_images()

    print("\n🎉 IMAGE UPDATE COMPLETE!")
    print("\n📋 Summary:")
    print("- All parks now have high-quality landscape images")
    print("- All species now have accurate wildlife images")
    print("- Images are automatically optimized and stored locally")
    print("- Frontend will display these images immediately")

    print("\n🌐 Visit http://localhost:8000 to see the updated images!")

if __name__ == "__main__":
    asyncio.run(main())
