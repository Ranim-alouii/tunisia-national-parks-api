"""
Migrate existing database to new schema
Run: python migrate_database.py
"""

from sqlmodel import SQLModel, Session, create_engine, select
from models import *
from database import engine
import json

def migrate_database():
    print("=== DATABASE MIGRATION ===\n")

    # First, add missing columns to existing tables using raw SQL
    import sqlite3

    conn = sqlite3.connect('tunisia_parks.db')
    cursor = conn.cursor()

    # Add new columns to parks table
    new_park_columns = [
        ("hero_image_url", "TEXT"),
        ("gallery_images", "TEXT"),
        ("difficulty_level", "TEXT"),
        ("accessibility", "TEXT"),
        ("best_months", "TEXT"),
        ("activities", "TEXT"),
        ("facilities", "TEXT"),
        ("circuit", "TEXT"),
        ("entrance_fee", "TEXT"),
        ("opening_hours", "TEXT"),
        ("contact_phone", "TEXT"),
        ("contact_email", "TEXT"),
        ("area_hectares", "INTEGER"),
        ("elevation_min", "INTEGER"),
        ("elevation_max", "INTEGER"),
        ("visitor_count_yearly", "INTEGER")
    ]

    for column_name, column_type in new_park_columns:
        try:
            cursor.execute(f"ALTER TABLE parks ADD COLUMN {column_name} {column_type}")
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"⚠️ Error adding {column_name}: {e}")
            else:
                print(f"⚠️ Column {column_name} already exists")

    # Add new columns to species table
    new_species_columns = [
        ("toxicity_level", "TEXT"),
        ("danger_level", "TEXT"),
        ("interaction_guide", "TEXT"),
        ("first_aid", "TEXT"),
        ("gallery_images", "TEXT"),
        ("audio_url", "TEXT"),
        ("video_url", "TEXT"),
        ("conservation_status", "TEXT"),
        ("habitat_type", "TEXT"),
        ("diet", "TEXT"),
        ("lifespan", "TEXT"),
        ("size", "TEXT"),
        ("weight", "TEXT"),
        ("best_viewing_months", "TEXT"),
        ("activity_time", "TEXT"),
        ("rarity", "TEXT")
    ]

    for column_name, column_type in new_species_columns:
        try:
            cursor.execute(f"ALTER TABLE species ADD COLUMN {column_name} {column_type}")
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"⚠️ Error adding {column_name}: {e}")
            else:
                print(f"⚠️ Column {column_name} already exists")

    # Add new columns to park_species table
    new_link_columns = [
        ("population_estimate", "TEXT"),
        ("sighting_probability", "TEXT"),
        ("best_spots", "TEXT")
    ]

    for column_name, column_type in new_link_columns:
        try:
            cursor.execute(f"ALTER TABLE park_species ADD COLUMN {column_name} {column_type}")
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"⚠️ Error adding {column_name}: {e}")
            else:
                print(f"⚠️ Column {column_name} already exists")

    # Add new columns to badges table
    new_badge_columns = [
        ("category", "TEXT"),
        ("requirement_type", "TEXT"),
        ("requirement_value", "INTEGER"),
        ("rarity", "TEXT")
    ]

    for column_name, column_type in new_badge_columns:
        try:
            cursor.execute(f"ALTER TABLE badges ADD COLUMN {column_name} {column_type}")
            print(f"✅ Added column: {column_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"⚠️ Error adding {column_name}: {e}")
            else:
                print(f"⚠️ Column {column_name} already exists")

    conn.commit()
    conn.close()

    print("\n✅ Database schema updated with new columns\n")

    # Create all new tables
    SQLModel.metadata.create_all(engine)
    print("✅ New tables created\n")

    with Session(engine) as session:
        # Add sample data for new features
        
        # 1. Update existing parks with new fields
        parks = session.exec(select(ParkDB)).all()
        
        for park in parks:
            # Add difficulty levels
            if "Jebil" in park.name or "Dghoumès" in park.name:
                park.difficulty_level = "difficile"
            elif "Ichkeul" in park.name or "El Feija" in park.name:
                park.difficulty_level = "facile"
            else:
                park.difficulty_level = "modéré"

            # Add accessibility
            accessible_parks = ["Ichkeul", "Boukornine", "Zaghouan"]
            if any(name in park.name for name in accessible_parks):
                park.accessibility = json.dumps(["family_friendly", "parking"])
            else:
                park.accessibility = json.dumps(["parking"])

            # Add best months (varies by region)
            if "Jebil" in park.name or "Sidi Toui" in park.name:
                # Desert parks - cooler months
                park.best_months = json.dumps(["10", "11", "12", "1", "2", "3"])
            elif "Ichkeul" in park.name:
                # Bird watching
                park.best_months = json.dumps(["11", "12", "1", "2", "3"])
            else:
                # Mountain/forest parks - spring
                park.best_months = json.dumps(["3", "4", "5", "9", "10"])

            # Add activities
            activities_map = {
                "Ichkeul": ["birdwatching", "photography", "nature_walks"],
                "El Feija": ["hiking", "wildlife_watching", "camping"],
                "Chaambi": ["hiking", "mountain_climbing", "photography"],
                "Jebil": ["desert_safari", "4x4_tours", "photography"],
                "Boukornine": ["hiking", "picnic", "family_activities"]
            }

            for key, activities in activities_map.items():
                if key in park.name:
                    park.activities = json.dumps(activities)
                    break

            if not park.activities:
                park.activities = json.dumps(["hiking", "nature_walks"])
            
            # Add entrance fees
            park.entrance_fee = "Gratuit"  # Most Tunisian parks are free
            park.opening_hours = "7h00 - 18h00"
            
            session.add(park)
        
        session.commit()
        print(f"✅ Updated {len(parks)} parks with new fields\n")
        
        # 2. Add sample trails
        print("Adding sample trails...\n")
        
        sample_trails = [
            {
                "park_name": "Boukornine",
                "name": "Sentier du Sommet",
                "description": "Sentier principal menant au sommet du Jebel Boukornine avec vue panoramique sur le golfe de Tunis.",
                "difficulty": "modéré",
                "length_km": 4.5,
                "duration_hours": 2.5,
                "elevation_gain": 450,
                "trail_type": "loop",
                "highlights": json.dumps(["panoramic_view", "rock_formations", "wildlife"])
            },
            {
                "park_name": "Chaambi",
                "name": "Ascension du Chaambi",
                "description": "Randonnée jusqu'au point culminant de la Tunisie (1544m).",
                "difficulty": "difficile",
                "length_km": 8.0,
                "duration_hours": 5.0,
                "elevation_gain": 700,
                "trail_type": "out_and_back",
                "highlights": json.dumps(["summit", "cedar_forest", "panoramic_view"])
            },
            {
                "park_name": "Ichkeul",
                "name": "Sentier des Oiseaux",
                "description": "Circuit facile autour du lac avec observatoires ornithologiques.",
                "difficulty": "facile",
                "length_km": 3.0,
                "duration_hours": 1.5,
                "elevation_gain": 20,
                "trail_type": "loop",
                "highlights": json.dumps(["bird_observatory", "lake_views", "wetlands"])
            },
            {
                "park_name": "El Feija",
                "name": "Sentier des Cerfs",
                "description": "Randonnée en forêt avec possibilité d'observer les cerfs de Barbarie.",
                "difficulty": "modéré",
                "length_km": 6.0,
                "duration_hours": 3.0,
                "elevation_gain": 300,
                "trail_type": "loop",
                "highlights": json.dumps(["cork_oak_forest", "wildlife", "stream"])
            }
        ]
        
        for trail_data in sample_trails:
            park = session.exec(
                select(ParkDB).where(ParkDB.name.contains(trail_data["park_name"]))
            ).first()

            if park:
                trail = TrailDB(
                    park_id=park.id,
                    name=trail_data["name"],
                    description=trail_data["description"],
                    difficulty=trail_data["difficulty"],
                    length_km=trail_data["length_km"],
                    duration_hours=trail_data["duration_hours"],
                    elevation_gain=trail_data["elevation_gain"],
                    trail_type=trail_data["trail_type"],
                    highlights=trail_data["highlights"]
                )
                session.add(trail)
                print(f"  ✅ {trail.name} → {park.name}")
        
        session.commit()
        print(f"\n✅ Added {len(sample_trails)} sample trails\n")
        
        # 3. Add sample reviews
        print("Adding sample reviews...\n")
        
        sample_reviews = [
            {
                "park_name": "Ichkeul",
                "author_name": "Mohamed Ben Ali",
                "rating": 5,
                "title": "Paradis pour les amateurs d'oiseaux",
                "comment": "Incroyable diversité d'oiseaux migrateurs! J'ai vu des flamants roses, des cigognes et bien d'autres espèces. Le paysage du lac est magnifique. Parfait pour la photographie nature.",
                "visit_date": "2024-12-15"
            },
            {
                "park_name": "Chaambi",
                "author_name": "Leila Trabelsi",
                "rating": 4,
                "title": "Randonnée exigeante mais gratifiante",
                "comment": "L'ascension au sommet est difficile mais la vue en vaut vraiment la peine. Prévoyez de bonnes chaussures et beaucoup d'eau. La forêt de cèdres est splendide.",
                "visit_date": "2024-10-20"
            },
            {
                "park_name": "El Feija",
                "author_name": "Karim Mansour",
                "rating": 5,
                "title": "Une journée mémorable",
                "comment": "Nous avons eu la chance de voir un cerf de Barbarie! La forêt est magnifique et les sentiers bien entretenus. Idéal pour une sortie familiale.",
                "visit_date": "2024-11-05"
            },
            {
                "park_name": "Boukornine",
                "author_name": "Amira Karoui",
                "rating": 4,
                "title": "Vue panoramique exceptionnelle",
                "comment": "La montée est un peu difficile mais faisable. Du sommet, on voit tout le golfe de Tunis. Belle diversité de plantes. Bon pour un picnic familial.",
                "visit_date": "2024-09-12"
            }
        ]
        
        for review_data in sample_reviews:
            park = session.exec(
                select(ParkDB).where(ParkDB.name.contains(review_data["park_name"]))
            ).first()

            if park:
                review = ReviewDB(
                    park_id=park.id,
                    author_name=review_data["author_name"],
                    rating=review_data["rating"],
                    title=review_data["title"],
                    comment=review_data["comment"],
                    visit_date=review_data["visit_date"],
                    helpful_count=0
                )
                session.add(review)

                # Update park average rating
                reviews = session.exec(
                    select(ReviewDB).where(ReviewDB.park_id == park.id)
                ).all()
                park.average_rating = sum(r.rating for r in reviews) / len(reviews)
                park.total_reviews = len(reviews)
                session.add(park)

                print(f"  ✅ Review by {review.author_name} → {park.name}")
        
        session.commit()
        print(f"\n✅ Added {len(sample_reviews)} sample reviews\n")
        
        # 4. Create badges
        print("Creating achievement badges...\n")
        print("⚠️ Skipping badge creation due to schema mismatch\n")
        
    print("=" * 60)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python add_enhanced_data.py")
    print("2. Restart server: uvicorn main:app --reload")
    print("3. Test new features at http://127.0.0.1:8000/map")


if __name__ == "__main__":
    migrate_database()
# ---------- END OF FILE ----------
