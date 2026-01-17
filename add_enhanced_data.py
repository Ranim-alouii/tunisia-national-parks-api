#!/usr/bin/env python3
"""
Enhanced data seeding script for Tunisia Parks API
Adds badges, sample users, and gamification data
"""

from datetime import datetime, timezone, timedelta
import random
from models import *
from database import engine,, get_engine init_db
from sqlmodel import Session, select


def seed_badges():
    """Seed the database with achievement badges."""
    print("🌟 Seeding badges...")

    badges_data = [
        # Exploration Badges
        {
            "name": "Premier Parc",
            "description": "Visitez votre premier parc national",
            "icon": "🏞️",
            "category": "exploration",
            "requirement_type": "parks_visited",
            "requirement_value": 1,
            "points": 10,
            "rarity": "common"
        },
        {
            "name": "Explorateur",
            "description": "Visitez 5 parcs différents",
            "icon": "🗺️",
            "category": "exploration",
            "requirement_type": "parks_visited",
            "requirement_value": 5,
            "points": 25,
            "rarity": "uncommon"
        },
        {
            "name": "Voyageur Passionné",
            "description": "Visitez 10 parcs nationaux",
            "icon": "✈️",
            "category": "exploration",
            "requirement_type": "parks_visited",
            "requirement_value": 10,
            "points": 50,
            "rarity": "rare"
        },
        {
            "name": "Gardien de la Nature",
            "description": "Visitez tous les parcs de Tunisie",
            "icon": "🌍",
            "category": "exploration",
            "requirement_type": "parks_visited",
            "requirement_value": 17,
            "points": 100,
            "rarity": "epic"
        },

        # Conservation Badges
        {
            "name": "Observateur",
            "description": "Observez 5 espèces différentes",
            "icon": "👁️",
            "category": "conservation",
            "requirement_type": "species_seen",
            "requirement_value": 5,
            "points": 20,
            "rarity": "common"
        },
        {
            "name": "Naturaliste",
            "description": "Observez 25 espèces différentes",
            "icon": "🔬",
            "category": "conservation",
            "requirement_type": "species_seen",
            "requirement_value": 25,
            "points": 40,
            "rarity": "uncommon"
        },
        {
            "name": "Protecteur de la Biodiversité",
            "description": "Observez 50 espèces différentes",
            "icon": "🦋",
            "category": "conservation",
            "requirement_type": "species_seen",
            "requirement_value": 50,
            "points": 75,
            "rarity": "rare"
        },

        # Social Badges
        {
            "name": "Critique Constructif",
            "description": "Écrivez votre premier avis",
            "icon": "📝",
            "category": "social",
            "requirement_type": "reviews_written",
            "requirement_value": 1,
            "points": 15,
            "rarity": "common"
        },
        {
            "name": "Guide Local",
            "description": "Écrivez 10 avis sur les parcs",
            "icon": "⭐",
            "category": "social",
            "requirement_type": "reviews_written",
            "requirement_value": 10,
            "points": 35,
            "rarity": "uncommon"
        },

        # Expert Badges
        {
            "name": "Randonneur",
            "description": "Complétez votre premier sentier",
            "icon": "🥾",
            "category": "expert",
            "requirement_type": "trails_completed",
            "requirement_value": 1,
            "points": 20,
            "rarity": "common"
        },
        {
            "name": "Guide de Montagne",
            "description": "Complétez 10 sentiers",
            "icon": "🏔️",
            "category": "expert",
            "requirement_type": "trails_completed",
            "requirement_value": 10,
            "points": 45,
            "rarity": "rare"
        },

        # Special Badges
        {
            "name": "Observateur d'Oiseaux",
            "description": "Observez 20 espèces d'oiseaux",
            "icon": "🦅",
            "category": "conservation",
            "requirement_type": "species_seen",
            "requirement_value": 20,
            "points": 60,
            "rarity": "rare"
        },
        {
            "name": "Légende Vivante",
            "description": "Atteignez le niveau maximum d'exploration",
            "icon": "👑",
            "category": "exploration",
            "requirement_type": "parks_visited",
            "requirement_value": 17,
            "points": 200,
            "rarity": "legendary"
        }
    ]

    with Session(get_engine()) as session:
        for badge_data in badges_data:
            # Check if badge already exists
            existing = session.exec(
                select(BadgeDB).where(BadgeDB.name == badge_data["name"])
            ).first()

            if not existing:
                badge = BadgeDB(**badge_data)
                session.add(badge)

        session.commit()
        print(f"✅ Added {len(badges_data)} badges")


def seed_sample_users():
    """Create sample users with realistic data."""
    print("👥 Creating sample users...")

    users_data = [
        {
            "username": "nature_lover_tn",
            "email": "nature.lover@example.com",
            "full_name": "Ahmed Ben Ali",
            "bio": "Passionné par la nature tunisienne et sa biodiversité exceptionnelle.",
            "location": "Tunis, Tunisie",
            "parks_visited": 8,
            "species_seen": 15,
            "trails_completed": 12,
            "reviews_written": 6,
            "sightings_reported": 3,
            "total_points": 180,
            "current_level": 2,
            "experience_points": 180,
            "badges_earned": 5
        },
        {
            "username": "eco_guide_sfax",
            "email": "eco.guide@example.com",
            "full_name": "Fatma Trabelsi",
            "bio": "Guide écologique spécialisée dans les parcs du Sahel.",
            "location": "Sfax, Tunisie",
            "parks_visited": 12,
            "species_seen": 35,
            "trails_completed": 8,
            "reviews_written": 15,
            "sightings_reported": 7,
            "total_points": 320,
            "current_level": 4,
            "experience_points": 320,
            "badges_earned": 8
        },
        {
            "username": "bird_watcher_gabes",
            "email": "bird.watcher@example.com",
            "full_name": "Mohamed Zribi",
            "bio": "Ornithologue amateur passionné par les oiseaux migrateurs.",
            "location": "Gabès, Tunisie",
            "parks_visited": 6,
            "species_seen": 45,
            "trails_completed": 4,
            "reviews_written": 3,
            "sightings_reported": 12,
            "total_points": 250,
            "current_level": 3,
            "experience_points": 250,
            "badges_earned": 6
        }
    ]

    with Session(get_engine()) as session:
        for user_data in users_data:
            # Check if user already exists
            existing = session.exec(
                select(UserDB).where(UserDB.username == user_data["username"])
            ).first()

            if not existing:
                # Create user
                user = UserDB(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    bio=user_data["bio"],
                    location=user_data["location"],
                    favorite_parks=[],
                    badges_earned=[],
                    total_visits=0,
                    joined_date=(datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365))).isoformat(),
                    is_active=True,
                    role="user"
                )
                session.add(user)
                session.flush()  # Get user ID

                # Create user stats
                stats = UserStatsDB(
                    user_id=user.id,
                    parks_visited=user_data["parks_visited"],
                    species_seen=user_data["species_seen"],
                    trails_completed=user_data["trails_completed"],
                    reviews_written=user_data["reviews_written"],
                    sightings_reported=user_data["sightings_reported"],
                    total_points=user_data["total_points"],
                    current_level=user_data["current_level"],
                    experience_points=user_data["experience_points"],
                    badges_earned=user_data["badges_earned"],
                    consecutive_days_active=random.randint(1, 30),
                    last_activity_date=(datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))).isoformat(),
                    created_at=user.joined_date,
                    updated_at=datetime.now(timezone.utc).isoformat()
                )
                session.add(stats)

                # Assign some badges based on stats
                assign_sample_badges(session, user.id, user_data)

        session.commit()
        print(f"✅ Created {len(users_data)} sample users with stats and badges")


def assign_sample_badges(session, user_id, user_data):
    """Assign appropriate badges to sample users based on their stats."""
    badges = session.exec(select(BadgeDB)).all()

    awarded_badges = []

    for badge in badges:
        if badge.requirement_type == "parks_visited" and user_data["parks_visited"] >= badge.requirement_value:
            awarded_badges.append(badge)
        elif badge.requirement_type == "species_seen" and user_data["species_seen"] >= badge.requirement_value:
            awarded_badges.append(badge)
        elif badge.requirement_type == "trails_completed" and user_data["trails_completed"] >= badge.requirement_value:
            awarded_badges.append(badge)
        elif badge.requirement_type == "reviews_written" and user_data["reviews_written"] >= badge.requirement_value:
            awarded_badges.append(badge)
        elif badge.requirement_type == "sightings_reported" and user_data["sightings_reported"] >= badge.requirement_value:
            awarded_badges.append(badge)

    # Limit to reasonable number of badges
    awarded_badges = awarded_badges[:user_data["badges_earned"]]

    for badge in awarded_badges:
        user_badge = UserBadgeDB(
            user_id=user_id,
            badge_id=badge.badge_id,
            earned_at=(datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).isoformat(),
            progress=badge.requirement_value,
            completed=True
        )
        session.add(user_badge)


def seed_sample_sightings():
    """Add some realistic wildlife sightings."""
    print("🦌 Adding sample wildlife sightings...")

    sightings_data = [
        {
            "park_id": 1,  # Ichkeul
            "species_id": 1,  # Flamingo
            "reporter_name": "Ahmed Ben Ali",
            "sighting_date": "2024-03-15",
            "location_lat": 37.160,
            "location_lng": 9.680,
            "notes": "Large flock of flamingos in the main lake. Beautiful sunset lighting!",
            "verified": True
        },
        {
            "park_id": 2,  # Boukornine
            "species_id": 5,  # Barbary deer
            "reporter_name": "Fatma Trabelsi",
            "sighting_date": "2024-02-20",
            "location_lat": 36.850,
            "location_lng": 10.120,
            "notes": "Spotted two deer near the main trail. Very shy but healthy looking.",
            "verified": True
        },
        {
            "park_id": 3,  # Zaghouan
            "species_id": 8,  # Bonelli's eagle
            "reporter_name": "Mohamed Zribi",
            "sighting_date": "2024-01-28",
            "location_lat": 36.400,
            "location_lng": 10.150,
            "notes": "Magnificent eagle soaring above the mountains. Rare sighting!",
            "verified": False
        }
    ]

    with Session(get_engine()) as session:
        for sighting_data in sightings_data:
            # Check if sighting already exists (avoid duplicates)
            existing = session.exec(
                select(SightingDB).where(
                    (SightingDB.park_id == sighting_data["park_id"]) &
                    (SightingDB.species_id == sighting_data["species_id"]) &
                    (SightingDB.reporter_name == sighting_data["reporter_name"])
                )
            ).first()

            if not existing:
                sighting = SightingDB(**sighting_data)
                session.add(sighting)

        session.commit()
        print(f"✅ Added {len(sightings_data)} sample wildlife sightings")


def main():
    """Main seeding function."""
    print("🌱 Starting enhanced data seeding...")

    try:
        # Initialize database
        init_db()

        # Seed data
        seed_badges()
        seed_sample_users()
        seed_sample_sightings()

        print("\n🎉 Enhanced data seeding completed successfully!")
        print("\n📊 Summary:")
        print("   • Gamification badges system")
        print("   • Sample users with realistic stats")
        print("   • Wildlife sightings data")
        print("   • User achievement progress")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        raise


if __name__ == "__main__":
    main()
