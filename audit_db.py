#!/usr/bin/env python3
"""
Database Audit Script for Tunisia National Parks
Counts Parks, Animals, and Plants in the database.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_engine
from sqlmodel import Session, select
from models import ParkDB, SpeciesDB

def audit_database():
    """Audit the database and print counts."""
    try:
        print("🔍 Auditing Tunisia National Parks Database...\n")

        with Session(get_engine()) as session:
            # Count total parks
            total_parks = len(session.exec(select(ParkDB)).all())

            # Count species by type
            all_species = session.exec(select(SpeciesDB)).all()
            total_species = len(all_species)

            # Count animals and plants
            animals = [s for s in all_species if s.type == 'animal']
            plants = [s for s in all_species if s.type == 'plant']

            total_animals = len(animals)
            total_plants = len(plants)

            print("📊 Database Audit Results:")
            print("=" * 40)
            print(f"🏞️  Total Parks:     {total_parks}")
            print(f"🦋 Total Species:   {total_species}")
            print(f"🐾 Animals:         {total_animals}")
            print(f"🌿 Plants:          {total_plants}")
            print("=" * 40)

            if total_parks > 0:
                avg_species_per_park = total_species / total_parks
                print(".1f")
                print(".1f")
            else:
                print("⚠️  No parks found in database!")

            if total_animals == 0:
                print("⚠️  No animals found!")
            if total_plants == 0:
                print("⚠️  No plants found!")

            print("\n✅ Audit completed successfully!")

            return {
                'parks': total_parks,
                'species': total_species,
                'animals': total_animals,
                'plants': total_plants
            }

    except Exception as e:
        print(f"❌ Audit failed: {e}")
        return None

if __name__ == "__main__":
    # Run the audit
    results = audit_database()

    # Exit with error code if audit failed
    if results is None:
        sys.exit(1)

    # Check for expected minimum counts
    if results['parks'] < 17:
        print(f"⚠️  Expected at least 17 parks, found {results['parks']}")
        sys.exit(1)

    if results['animals'] < 6:
        print(f"⚠️  Expected at least 6 animals, found {results['animals']}")
        sys.exit(1)

    if results['plants'] < 10:
        print(f"⚠️  Expected at least 10 plants, found {results['plants']}")
        sys.exit(1)

    print("🎉 All checks passed!")
    sys.exit(0)
