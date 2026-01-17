#!/usr/bin/env python3
"""
Enhanced species data seeding script for Tunisia Parks API
Adds comprehensive fauna and flora information with detailed biology and safety data
"""

from models import *
from database import engine, init_db
from sqlmodel import Session, select
import json


def seed_enhanced_species():
    """Add comprehensive species data with all new fields."""
    print("🦌 Adding enhanced species data...")

    enhanced_species_data = [
        # Enhanced Birds
        {
            "name": "Flamant Rose",
            "scientific_name": "Phoenicopterus roseus",
            "type": "animal",
            "description": "Le flamant rose est un oiseau migrateur majestueux reconnaissable à son plumage rose et son long cou. Il fréquente les lacs et marais d'eau douce et saumâtre.",
            "threats": "Perte d'habitat due à la pollution et à la modification des zones humides, dérangement humain, prédation.",
            "protection_measures": "Protection des zones humides, contrôle de la pollution, régulation de la chasse.",
            "safety_guidelines": "Observer à distance avec des jumelles. Éviter de s'approcher des nids pendant la saison de reproduction.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "none",
            "interaction_guide": "Les flamants sont des oiseaux sauvages sensibles au dérangement. Observez-les depuis les observatoires dédiés sans les approcher.",
            "first_aid": None,
            "conservation_status": "near_threatened",
            "habitat_type": "marais, lacs saumâtres",
            "diet": "algues, crustacés, mollusques",
            "lifespan": "40-50 ans",
            "size": "120-145 cm",
            "weight": "2-4 kg",
            "best_viewing_months": json.dumps(["11", "12", "1", "2", "3"]),
            "activity_time": "diurne",
            "rarity": "rare"
        },
        {
            "name": "Cigogne Blanche",
            "scientific_name": "Ciconia ciconia",
            "type": "animal",
            "description": "Grande cigogne blanche avec un long bec rouge et des pattes rouges. Oiseau migrateur qui hiverne en Afrique.",
            "threats": "Électrocution sur les lignes électriques, empoisonnement, perte d'habitat.",
            "protection_measures": "Protection des nids, modification des lignes électriques, programmes de conservation.",
            "safety_guidelines": "Ne pas s'approcher des nids. Respecter les distances de sécurité.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "low",
            "interaction_guide": "Les cigognes peuvent être agressives près de leurs nids. Observez à distance.",
            "first_aid": "En cas de becquetage, nettoyer la plaie et consulter un médecin si nécessaire.",
            "conservation_status": "least_concern",
            "habitat_type": "prairies, marais",
            "diet": "amphibiens, reptiles, petits mammifères",
            "lifespan": "20-25 ans",
            "size": "100-115 cm",
            "weight": "2.5-4 kg",
            "best_viewing_months": json.dumps(["3", "4", "5", "9", "10"]),
            "activity_time": "diurne",
            "rarity": "common"
        },
        {
            "name": "Aigle de Bonelli",
            "scientific_name": "Aquila fasciata",
            "type": "animal",
            "description": "Rapace diurne de taille moyenne avec un plumage sombre et une queue barrée. Chasseur redoutable.",
            "threats": "Perte d'habitat, empoisonnement, dérangement humain.",
            "protection_measures": "Protection des zones de nidification, lutte contre le braconnage.",
            "safety_guidelines": "Ne jamais s'approcher des nids. Observer avec des jumelles.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "low",
            "interaction_guide": "Les aigles sont territoriaux et peuvent attaquer s'ils se sentent menacés.",
            "first_aid": "En cas d'attaque, protéger les yeux et la tête. Désinfecter les plaies.",
            "conservation_status": "least_concern",
            "habitat_type": "montagnes, falaises",
            "diet": "mammifères, oiseaux, reptiles",
            "lifespan": "25-30 ans",
            "size": "65-75 cm",
            "weight": "1.5-2.5 kg",
            "best_viewing_months": json.dumps(["3", "4", "5", "6", "9", "10"]),
            "activity_time": "diurne",
            "rarity": "rare"
        },

        # Enhanced Mammals
        {
            "name": "Cerf de Barbarie",
            "scientific_name": "Cervus elaphus barbarus",
            "type": "animal",
            "description": "Le cerf de Barbarie est un cervidé endémique d'Afrique du Nord, reconnaissable à ses bois palmés.",
            "threats": "Braconnage, perte d'habitat, compétition avec le bétail.",
            "protection_measures": "Protection des zones de reproduction, lutte contre le braconnage, gestion des populations.",
            "safety_guidelines": "Observer à distance. Ne pas nourrir les animaux sauvages.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "low",
            "interaction_guide": "Les cerfs sont généralement craintifs mais peuvent charger s'ils se sentent acculés.",
            "first_aid": "En cas de charge, monter sur un point élevé ou se cacher derrière un arbre.",
            "conservation_status": "vulnerable",
            "habitat_type": "forêts de chênes, maquis",
            "diet": "herbivore - feuilles, herbes, glands",
            "lifespan": "15-20 ans",
            "size": "140-180 cm",
            "weight": "80-120 kg",
            "best_viewing_months": json.dumps(["10", "11", "12", "1", "2"]),
            "activity_time": "crépusculaire",
            "rarity": "very_rare"
        },
        {
            "name": "Gazelle Dorcas",
            "scientific_name": "Gazella dorcas",
            "type": "animal",
            "description": "Petite gazelle gracieuse avec une robe beige et des cornes en forme de lyre.",
            "threats": "Braconnage, désertification, compétition avec le bétail.",
            "protection_measures": "Protection des populations restantes, gestion des pâturages.",
            "safety_guidelines": "Observer avec des jumelles depuis un véhicule.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "none",
            "interaction_guide": "Les gazelles sont très craintives et fuient à la moindre alerte.",
            "first_aid": None,
            "conservation_status": "vulnerable",
            "habitat_type": "désert, steppes arides",
            "diet": "herbivore - plantes désertiques",
            "lifespan": "12-15 ans",
            "size": "90-110 cm",
            "weight": "15-25 kg",
            "best_viewing_months": json.dumps(["10", "11", "12", "1", "2", "3"]),
            "activity_time": "crépusculaire",
            "rarity": "rare"
        },
        {
            "name": "Hérisson Algérien",
            "scientific_name": "Atelerix algirus",
            "type": "animal",
            "description": "Petit mammifère couvert de piquants, actif la nuit. Il se roule en boule pour se défendre.",
            "threats": "Prédation par les chiens errants, destruction d'habitat.",
            "protection_measures": "Protection des habitats naturels, contrôle des populations de chiens.",
            "safety_guidelines": "Ne pas toucher les hérissons sauvages. Ils peuvent transmettre des maladies.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "none",
            "interaction_guide": "Les hérissons sont nocturnes. On les rencontre rarement en journée.",
            "first_aid": "Laver les mains après contact. Consulter un médecin si morsure.",
            "conservation_status": "least_concern",
            "habitat_type": "maquis, forêts, jardins",
            "diet": "insectivore - insectes, vers, escargots",
            "lifespan": "3-6 ans",
            "size": "20-30 cm",
            "weight": "0.5-1.5 kg",
            "best_viewing_months": json.dumps(["3", "4", "5", "6", "9", "10"]),
            "activity_time": "nocturne",
            "rarity": "common"
        },

        # Enhanced Plants
        {
            "name": "Chêne-liège",
            "scientific_name": "Quercus suber",
            "type": "plant",
            "description": "Arbre emblématique de la forêt méditerranéenne avec une écorce épaisse qui fournit le liège.",
            "threats": "Incendies de forêt, défrichement, changement climatique.",
            "protection_measures": "Gestion durable des forêts, prévention des incendies, reboisement.",
            "safety_guidelines": "Respecter les sentiers balisés. Risque d'incendie en été.",
            "medicinal_use": "Propriétés anti-inflammatoires et antioxydantes. Utilisé en phytothérapie.",
            "toxicity_level": "none",
            "danger_level": "none",
            "interaction_guide": "Arbre non toxique. Peut servir d'abri à la faune.",
            "first_aid": None,
            "conservation_status": "least_concern",
            "habitat_type": "forêts méditerranéennes",
            "diet": None,
            "lifespan": "150-250 ans",
            "size": "10-20 m",
            "weight": None,
            "best_viewing_months": json.dumps(["4", "5", "6", "9", "10"]),
            "activity_time": None,
            "rarity": "common"
        },
        {
            "name": "Ciste Cotonneux",
            "scientific_name": "Cistus albidus",
            "type": "plant",
            "description": "Arbuste méditerranéen aux fleurs roses, couvert de poils cotonneux.",
            "threats": "Urbanisation, incendies, compétition avec espèces invasives.",
            "protection_measures": "Protection des zones naturelles, gestion des incendies.",
            "safety_guidelines": "Plante non toxique mais attention aux épines.",
            "medicinal_use": "Propriétés antimicrobiennes et anti-inflammatoires.",
            "toxicity_level": "none",
            "danger_level": "none",
            "interaction_guide": "Attire les pollinisateurs. Résiste bien aux incendies.",
            "first_aid": None,
            "conservation_status": "least_concern",
            "habitat_type": "maquis, garrigues",
            "diet": None,
            "lifespan": "20-30 ans",
            "size": "1-2 m",
            "weight": None,
            "best_viewing_months": json.dumps(["3", "4", "5", "6"]),
            "activity_time": None,
            "rarity": "common"
        },
        {
            "name": "Arganier",
            "scientific_name": "Argania spinosa",
            "type": "plant",
            "description": "Arbre endémique du Maroc et Tunisie méridionale, produisant l'huile d'argan précieuse.",
            "threats": "Défrichement, surpâturage, changement climatique.",
            "protection_measures": "Protection des dernières populations, agroforesterie.",
            "safety_guidelines": "Respecter l'arbre sacré. Ne pas consommer les graines crues.",
            "medicinal_use": "Huile riche en antioxydants, utilisée pour la peau et les cheveux.",
            "toxicity_level": "low",
            "danger_level": "none",
            "interaction_guide": "Arbre protégé. Les graines sont toxiques si non traitées.",
            "first_aid": "En cas d'ingestion de graines, consulter un médecin immédiatement.",
            "conservation_status": "near_threatened",
            "habitat_type": "régions arides du sud",
            "diet": None,
            "lifespan": "150-200 ans",
            "size": "8-12 m",
            "weight": None,
            "best_viewing_months": json.dumps(["4", "5", "6", "9", "10"]),
            "activity_time": None,
            "rarity": "rare"
        },

        # More species...
        {
            "name": "Lynx Caracal",
            "scientific_name": "Caracal caracal",
            "type": "animal",
            "description": "Félin sauvage avec des oreilles touffues caractéristiques et des capacités de saut exceptionnelles.",
            "threats": "Braconnage, perte d'habitat, empoisonnement.",
            "protection_measures": "Protection des populations restantes, surveillance anti-braconnage.",
            "safety_guidelines": "Ne jamais approcher. Observer à distance uniquement.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "medium",
            "interaction_guide": "Prédateur redoutable. Éviter tout contact.",
            "first_aid": "En cas d'attaque, plaies profondes nécessitant soins médicaux immédiats.",
            "conservation_status": "least_concern",
            "habitat_type": "montagnes, steppes",
            "diet": "carnivore - petits mammifères, oiseaux",
            "lifespan": "12-17 ans",
            "size": "65-90 cm",
            "weight": "8-20 kg",
            "best_viewing_months": json.dumps(["10", "11", "12", "1", "2"]),
            "activity_time": "nocturne",
            "rarity": "very_rare"
        },
        {
            "name": "Ibex Nubien",
            "scientific_name": "Capra nubiana",
            "type": "animal",
            "description": "Caprin sauvage adapté aux milieux arides avec de longues cornes recourbées.",
            "threats": "Braconnage, compétition avec le bétail domestique.",
            "protection_measures": "Protection des populations sauvages, gestion des pâturages.",
            "safety_guidelines": "Observer depuis les points d'observation dédiés.",
            "medicinal_use": None,
            "toxicity_level": "none",
            "danger_level": "low",
            "interaction_guide": "Les ibex sont territoriaux mais fuient généralement l'homme.",
            "first_aid": "En cas de blessure par les cornes, désinfection et points de suture si nécessaire.",
            "conservation_status": "vulnerable",
            "habitat_type": "montagnes arides, canyons",
            "diet": "herbivore - plantes désertiques",
            "lifespan": "15-20 ans",
            "size": "80-100 cm",
            "weight": "25-50 kg",
            "best_viewing_months": json.dumps(["9", "10", "11", "12", "1"]),
            "activity_time": "diurne",
            "rarity": "rare"
        }
    ]

    with Session(engine) as session:
        for species_data in enhanced_species_data:
            # Check if species already exists
            existing = session.exec(
                select(SpeciesDB).where(SpeciesDB.scientific_name == species_data["scientific_name"])
            ).first()

            if not existing:
                species = SpeciesDB(**species_data)
                session.add(species)
                print(f"✅ Added: {species.name} ({species.scientific_name})")
            else:
                # Update existing species with new data
                for key, value in species_data.items():
                    if hasattr(existing, key) and getattr(existing, key) is None:
                        setattr(existing, key, value)
                session.add(existing)
                print(f"📝 Updated: {existing.name}")

        session.commit()
        print(f"\n✅ Enhanced {len(enhanced_species_data)} species with detailed information")


def update_park_species_links():
    """Update park-species links with enhanced data."""
    print("🔗 Updating park-species relationships...")

    # Sample park-species associations with enhanced data
    enhanced_links = [
        {
            "park_name": "Ichkeul",
            "species_names": ["Flamant Rose", "Cigogne Blanche"],
            "population_estimate": "5000-10000 individus",
            "sighting_probability": "high",
            "best_spots": json.dumps(["Observatoire principal", "Lac sud"])
        },
        {
            "park_name": "El Feija",
            "species_names": ["Cerf de Barbarie"],
            "population_estimate": "50-100 individus",
            "sighting_probability": "medium",
            "best_spots": json.dumps(["Vallée centrale", "Collines ouest"])
        },
        {
            "park_name": "Zaghouan",
            "species_names": ["Aigle de Bonelli"],
            "population_estimate": "5-10 couples",
            "sighting_probability": "low",
            "best_spots": json.dumps(["Falaises nord", "Sommet du Jebel Zaghouan"])
        },
        {
            "park_name": "Jebil",
            "species_names": ["Gazelle Dorcas", "Lynx Caracal", "Ibex Nubien"],
            "population_estimate": "200-500 individus",
            "sighting_probability": "medium",
            "best_spots": json.dumps(["Dunes centrales", "Oasis de montagne"])
        },
        {
            "park_name": "Boukornine",
            "species_names": ["Cerf de Barbarie", "Hérisson Algérien", "Chêne-liège"],
            "population_estimate": "100-200 individus",
            "sighting_probability": "high",
            "best_spots": json.dumps(["Sentier principal", "Sommet"])
        }
    ]

    with Session(engine) as session:
        for link_data in enhanced_links:
            # Get park
            park = session.exec(
                select(ParkDB).where(ParkDB.name.contains(link_data["park_name"]))
            ).first()

            if park:
                for species_name in link_data["species_names"]:
                    # Get species
                    species = session.exec(
                        select(SpeciesDB).where(SpeciesDB.name == species_name)
                    ).first()

                    if species:
                        # Update or create link
                        link = session.exec(
                            select(ParkSpeciesLink).where(
                                (ParkSpeciesLink.park_id == park.id) &
                                (ParkSpeciesLink.species_id == species.species_id)
                            )
                        ).first()

                        if not link:
                            link = ParkSpeciesLink(
                                park_id=park.id,
                                species_id=species.species_id
                            )

                        # Update with enhanced data
                        link.population_estimate = link_data["population_estimate"]
                        link.sighting_probability = link_data["sighting_probability"]
                        link.best_spots = link_data["best_spots"]

                        session.add(link)
                        print(f"🔗 Enhanced link: {park.name} ↔ {species.name}")

        session.commit()
        print("✅ Updated park-species relationships with enhanced data")


def add_more_parks():
    """Add more Tunisian national parks with comprehensive data."""
    print("🏞️ Adding more Tunisian national parks...")

    additional_parks = [
        {
            "name": "Parc National de Sidi Toui",
            "governorate": "Kébili",
            "description": "Situé dans le sud tunisien, ce parc protège une oasis exceptionnelle dans le désert du Sahara. Il abrite une biodiversité unique adaptée aux conditions extrêmes.",
            "latitude": 33.050,
            "longitude": 9.450,
            "area_km2": 63.0,
            "google_maps_url": "https://goo.gl/maps/sidi-toui",
            "difficulty_level": "difficile",
            "accessibility": json.dumps(["4x4_required", "desert_access"]),
            "best_months": json.dumps(["10", "11", "12", "1", "2", "3"]),
            "activities": json.dumps(["desert_safari", "wildlife_watching", "photography", "cultural_sites"]),
            "facilities": json.dumps(["parking", "information_center"]),
            "entrance_fee": "5 TND",
            "opening_hours": "8h00 - 17h00",
            "area_hectares": 6300,
            "elevation_min": 50,
            "elevation_max": 150,
            "visitor_count_yearly": 15000
        },
        {
            "name": "Parc National de l'Île de Zembra",
            "governorate": "Nabeul",
            "description": "Île inhabitée au large de Nabeul, réserve naturelle exceptionnelle avec des falaises spectaculaires et une faune marine riche.",
            "latitude": 36.783,
            "longitude": 10.917,
            "area_km2": 0.4,
            "google_maps_url": "https://goo.gl/maps/zembra-island",
            "difficulty_level": "modéré",
            "accessibility": json.dumps(["boat_access", "guided_visits"]),
            "best_months": json.dumps(["4", "5", "6", "9", "10"]),
            "activities": json.dumps(["birdwatching", "marine_life", "photography", "hiking"]),
            "facilities": json.dumps(["boat_dock", "basic_shelter"]),
            "entrance_fee": "15 TND",
            "opening_hours": "9h00 - 16h00",
            "area_hectares": 40,
            "elevation_min": 0,
            "elevation_max": 435,
            "visitor_count_yearly": 8000
        }
    ]

    with Session(engine) as session:
        for park_data in additional_parks:
            # Check if park already exists
            existing = session.exec(
                select(ParkDB).where(ParkDB.name == park_data["name"])
            ).first()

            if not existing:
                park = ParkDB(**park_data)
                session.add(park)
                print(f"🏞️ Added park: {park.name}")
            else:
                print(f"⚠️ Park already exists: {existing.name}")

        session.commit()
        print(f"✅ Added {len(additional_parks)} additional parks")


def main():
    """Main seeding function."""
    print("🌱 Starting comprehensive species and park data enhancement...")

    try:
        # Initialize database
        init_db()

        # Add enhanced data
        seed_enhanced_species()
        update_park_species_links()
        add_more_parks()

        print("\n🎉 Data enhancement completed successfully!")
        print("\n📊 Summary:")
        print("   • Enhanced species with detailed biology, safety, and conservation info")
        print("   • Updated park-species relationships with population data")
        print("   • Added more Tunisian national parks")
        print("   • Comprehensive information for all sections")

    except Exception as e:
        print(f"❌ Error during enhancement: {e}")
        raise


if __name__ == "__main__":
    main()
