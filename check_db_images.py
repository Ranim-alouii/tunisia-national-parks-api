#!/usr/bin/env python3
"""
Check what's actually stored in the database for park images
"""

from sqlmodel import Session, select
from database import get_engine, init_db
from models import ParkDB
import json

def check_database_images():
    """Check what's stored in the database for park images"""
    print("🔍 Checking Database Images")
    print("=" * 50)

    init_db()

    with Session(get_engine()) as session:
        parks = session.exec(select(ParkDB)).all()

        for i, park in enumerate(parks[:5]):  # Check first 5 parks
            print(f"\n🏞️ Park {i+1}: {park.name}")
            print(f"   Raw images field: {repr(park.images)}")
            print(f"   Type: {type(park.images)}")

            if park.images:
                try:
                    # Try to parse as JSON
                    parsed = json.loads(park.images)
                    print(f"   Parsed as JSON: {parsed}")
                    print(f"   Parsed type: {type(parsed)}")

                    if isinstance(parsed, list) and len(parsed) > 0:
                        first_image = parsed[0]
                        print(f"   First image: {first_image[:100]}...")
                        if first_image.startswith('http'):
                            print("   ✅ External image detected")
                        else:
                            print("   ❌ Not external image")

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                except Exception as e:
                    print(f"   ❌ Other error: {e}")
            else:
                print("   ❌ No images field")

if __name__ == "__main__":
    check_database_images()
