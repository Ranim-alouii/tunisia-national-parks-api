"""
Add hero images, gallery photos, and multimedia to parks and species
"""

from sqlmodel import Session, select
from database import engine
from models import ParkDB, SpeciesDB
import json

def add_enhanced_data():
    print("=== ADDING ENHANCED DATA ===\n")
    
    with Session(engine) as session:
        
        # 1. Add hero images to parks
        print("Adding park hero images...\n")
        
        park_images = {
            "Ichkeul": {
                "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Ichkeul_National_Park.jpg/1200px-Ichkeul_National_Park.jpg",
                "gallery": [
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Phoenicopterus_roseus_-_two_flamingos.jpg/800px-Phoenicopterus_roseus_-_two_flamingos.jpg",
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Ciconia_ciconia_%28aka%29.jpg/800px-Ciconia_ciconia_%28aka%29.jpg"
                ]
            },
            "Boukornine": {
                "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Jebel_Boukornine.jpg/1200px-Jebel_Boukornine.jpg",
                "gallery": []
            },
            "Chaambi": {
                "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Djebel_Chambi.jpg/1200px-Djebel_Chambi.jpg",
                "gallery": []
            },
            "El Feija": {
                "hero": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Cork_oak_trunk_section.jpg/1200px-Cork_oak_trunk_section.jpg",
                "gallery": []
            }
        }
        
        parks = session.exec(select(ParkDB)).all()
        for park in parks:
            for key, data in park_images.items():
                if key in park.park_name:
                    park.hero_image_url = data["hero"]
                    park.gallery_images = json.dumps(data["gallery"])
                    session.add(park)
                    print(f"  ✅ {park.park_name}")
                    break
        
        session.commit()
        
        # 2. Add audio to species
        print("\nAdding species audio/sounds...\n")
        
        species_audio = {
            "Chacal doré": "https://www.xeno-canto.org/sounds/uploaded/...",  # Placeholder
            "Hyène rayée": "https://www.xeno-canto.org/sounds/uploaded/...",
            "Flamant rose": "https://www.xeno-canto.org/sounds/uploaded/...",
            "Aigle royal": "https://www.xeno-canto.org/sounds/uploaded/...",
            "Cigale commune": "https://www.xeno-canto.org/sounds/uploaded/..."
        }
        
        species_list = session.exec(select(SpeciesDB)).all()
        for species in species_list:
            # Add conservation status
            endangered_species = ["Oryx algazelle", "Cerf de Barbarie", "Outarde houbara"]
            if species.name in endangered_species:
                species.conservation_status = "en_danger"
            elif species.type == "animal":
                species.conservation_status = "préoccupation_mineure"
            
            # Add habitat type
            if species.name in ["Oryx algazelle", "Gazelle dorcas", "Autruche à cou rouge"]:
                species.habitat_type = "désert"
            elif species.name in ["Cerf de Barbarie", "Sanglier"]:
                species.habitat_type = "forêt"
            elif species.name in ["Flamant rose", "Puffin cendré"]:
                species.habitat_type = "zones_humides"
            else:
                species.habitat_type = "montagne"
            
            # Add activity time
            if species.name in ["Hyène rayée", "Chacal doré", "Renard roux"]:
                species.activity_time = "nocturne"
            else:
                species.activity_time = "diurne"
            
            # Add rarity
            rare_species = ["Oryx algazelle", "Cerf de Barbarie", "Outarde houbara", "Hyène rayée"]
            if species.name in rare_species:
                species.rarity = "très_rare"
            elif species.type == "animal":
                species.rarity = "commun"
            
            # Add audio if available
            if species.name in species_audio:
                species.audio_url = species_audio[species.name]
                print(f"  🔊 {species.name}")
            
            session.add(species)
        
        session.commit()
        
        print("\n✅ Enhanced data added successfully!")
        print("\n" + "=" * 60)


if __name__ == "__main__":
    add_enhanced_data()
