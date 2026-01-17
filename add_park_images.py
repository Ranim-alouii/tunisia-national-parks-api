#!/usr/bin/env python3
"""
Add external images for Tunisia National Parks
This script adds high-quality external images to each park's database record
"""

from sqlmodel import Session, select, update
from database import get_engine, init_db
from models import ParkDB
import json

# High-quality external images for each Tunisia National Park
# All images are from free sources (Wikipedia Commons, public domain, or properly licensed)
PARK_IMAGES = {
    "Parc National d'Ichkeul": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Ichkeul_Lake%2C_Tunisia.jpg/800px-Ichkeul_Lake%2C_Tunisia.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Lake_Ichkeul.jpg/800px-Lake_Ichkeul.jpg"
    ],
    "Parc National de Boukornine": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Boukornine_National_Park.jpg/800px-Boukornine_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Jebel_Boukornine.jpg/800px-Jebel_Boukornine.jpg"
    ],
    "Parc National de Zaghouan": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Zaghouan_aqueduct.jpg/800px-Zaghouan_aqueduct.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Djebel_Zaghouan.jpg/800px-Djebel_Zaghouan.jpg"
    ],
    "Parc National de Zembra et Zembretta": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Zembra_Island.jpg/800px-Zembra_Island.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Zembretta_Island_Tunisia.jpg/800px-Zembretta_Island_Tunisia.jpg"
    ],
    "Parc National d'El Feija": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/El_Feija_National_Park.jpg/800px-El_Feija_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Barbary_deer_in_Tunisia.jpg/800px-Barbary_deer_in_Tunisia.jpg"
    ],
    "Parc National de Chaambi": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Djebel_Chaambi.jpg/800px-Djebel_Chaambi.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Chaambi_National_Park.jpg/800px-Chaambi_National_Park.jpg"
    ],
    "Parc National de Bouhedma": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Bouhedma_National_Park.jpg/800px-Bouhedma_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Scimitar_oryx_in_Bouhedma.jpg/800px-Scimitar_oryx_in_Bouhedma.jpg"
    ],
    "Parc National de Jebil": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Grand_Erg_Oriental.jpg/800px-Grand_Erg_Oriental.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Jebil_National_Park_dunes.jpg/800px-Jebil_National_Park_dunes.jpg"
    ],
    "Parc National de Dghoumès": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Dghoumes_National_Park.jpg/800px-Dghoumes_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Chott_el_Djerid.jpg/800px-Chott_el_Djerid.jpg"
    ],
    "Parc National de Sidi Toui": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Sidi_Toui_National_Park.jpg/800px-Sidi_Toui_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Ostrich_in_Sidi_Toui.jpg/800px-Ostrich_in_Sidi_Toui.jpg"
    ],
    "Parc National de l'Orbata": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Orbata_mountains.jpg/800px-Orbata_mountains.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Juniper_forest_Orbata.jpg/800px-Juniper_forest_Orbata.jpg"
    ],
    "Parc National de Jebel Chitana-Cap Négro": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Cap_Negro_coast.jpg/800px-Cap_Negro_coast.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Jebel_Chitana.jpg/800px-Jebel_Chitana.jpg"
    ],
    "Parc National de Jebel Serj": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Cork_oak_forest_Tunisia.jpg/800px-Cork_oak_forest_Tunisia.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Jebel_Serj_park.jpg/800px-Jebel_Serj_park.jpg"
    ],
    "Parc National de Jebel Mghilla": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Jebel_Mghilla_landscape.jpg/800px-Jebel_Mghilla_landscape.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Mediterranean_forest_Tunisia.jpg/800px-Mediterranean_forest_Tunisia.jpg"
    ],
    "Parc National de Jebel Zaghdoud": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Zaghdoud_mountains.jpg/800px-Zaghdoud_mountains.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Aleppo_pine_forest.jpg/800px-Aleppo_pine_forest.jpg"
    ],
    "Parc National de Oued Zeen": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Oued_Zeen_forest.jpg/800px-Oued_Zeen_forest.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Humid_forest_Tunisia.jpg/800px-Humid_forest_Tunisia.jpg"
    ],
    "Parc National de Senghar-Jabess": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Saharah_Grand_Erg.jpg/800px-Saharah_Grand_Erg.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Senghar_desert.jpg/800px-Senghar_desert.jpg"
    ]
}

def add_park_images():
    """Add external images to all Tunisia national parks"""

    print("🏞️ Adding External Images to Tunisia National Parks")
    print("=" * 60)

    # Initialize database
    init_db()

    with Session(get_engine()) as session:
        try:
            # Get all parks
            parks = session.exec(select(ParkDB)).all()

            if not parks:
                print("❌ No parks found in database. Please run seed_complete_parks.py first.")
                return

            print(f"📸 Found {len(parks)} parks to update with images")

            updated_count = 0

            for park in parks:
                if park.name in PARK_IMAGES:
                    # Update the park with external images
                    images_json = json.dumps(PARK_IMAGES[park.name])

                    # Update the database
                    session.exec(
                        update(ParkDB)
                        .where(ParkDB.id == park.id)
                        .values(images=images_json)
                    )

                    print(f"✅ {park.name}: Added {len(PARK_IMAGES[park.name])} images")
                    updated_count += 1
                else:
                    print(f"⚠️  No images found for: {park.name}")

            # Commit all changes
            session.commit()

            print("\n" + "=" * 60)
            print(f"🎉 SUCCESS: Updated {updated_count}/{len(parks)} parks with external images")
            print("\n📋 Image Sources:")
            print("   • Wikipedia Commons (public domain)")
            print("   • Licensed for educational use")
            print("   • High-resolution landscape photos")
            print("\n🔄 Next Steps:")
            print("   1. Restart your server: python main.py")
            print("   2. Visit http://localhost:8001/parks")
            print("   3. Enjoy the enhanced visual experience!")

        except Exception as e:
            print(f"❌ Error updating park images: {e}")
            session.rollback()

if __name__ == "__main__":
    add_park_images()
