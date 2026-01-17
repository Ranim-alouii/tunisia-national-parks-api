"""
Check if species have image URLs in database
"""

from sqlmodel import Session, select
from database import engine
from models import SpeciesDB

with Session(engine) as session:
    species = session.exec(select(SpeciesDB)).all()
    
    print(f"Total species: {len(species)}\n")
    
    with_images = [s for s in species if s.image_url]
    without_images = [s for s in species if not s.image_url]
    
    print(f"✅ With images: {len(with_images)}")
    print(f"❌ Without images: {len(without_images)}\n")
    
    if with_images:
        print("Sample species WITH images:")
        for s in with_images[:5]:
            print(f"  • {s.name}: {s.image_url[:60]}...")
    
    if without_images:
        print(f"\nSpecies WITHOUT images:")
        for s in without_images[:10]:
            print(f"  • {s.name} ({s.scientific_name})")
# ---------- END OF FILE ----------