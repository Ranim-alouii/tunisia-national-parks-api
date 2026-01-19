"""
Parks management router
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from models import ParkDB
from database import get_engine
from utils import get_file_url
from schemas import Park, ParkCreate, ParkUpdate
from dependencies import get_current_user
from fastapi import Depends
from sqlmodel import select

# Create router
router = APIRouter()

# ---------- PARK ENDPOINTS ----------

@router.get("", response_model=List[Park])
def list_parks(
    skip: int = 0,
    limit: int = 100,
    governorate: str | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
):
    """List all parks with filtering and pagination."""
    with Session(get_engine()) as session:
        stmt = select(ParkDB)

        # Apply filters
        if governorate:
            stmt = stmt.where(ParkDB.governorate == governorate)
        if min_area is not None:
            stmt = stmt.where(ParkDB.area_km2 >= min_area)
        if max_area is not None and max_area > 0:
            stmt = stmt.where(ParkDB.area_km2 <= max_area)

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        parks_db = session.exec(stmt).all()

        import json
        result = []
        for p in parks_db:
            try:
                images_list = json.loads(p.images) if p.images else []
                processed_images = [get_file_url(img, "parks") for img in images_list]
                result.append(Park(
                    id=p.id,
                    name=p.name,
                    governorate=p.governorate,
                    description=p.description,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    area_km2=p.area_km2,
                    images=processed_images,
                ))
            except Exception as e:
                print(f"Error processing park {p.id}: {e}")
                # Fallback: return empty images list
                result.append(Park(
                    id=p.id,
                    name=p.name,
                    governorate=p.governorate,
                    description=p.description,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    area_km2=p.area_km2,
                    images=[],
                ))
        return result

@router.get("/{park_id}", response_model=Park)
def get_park(park_id: int):
    """Get a specific park by ID."""
    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        import json
        return Park(
            id=park.id,
            name=park.name,
            governorate=park.governorate,
            description=park.description,
            latitude=park.latitude,
            longitude=park.longitude,
            area_km2=park.area_km2,
            images=[get_file_url(img, "parks") for img in (json.loads(park.images) if park.images else [])],
        )

@router.post("", response_model=Park, status_code=201)
def create_park(park_in: ParkCreate, current_user=Depends(get_current_user)):
    """Create a new park."""
    with Session(get_engine()) as session:
        park_db = ParkDB(
            name=park_in.name,
            governorate=park_in.governorate,
            description=park_in.description,
            latitude=park_in.latitude,
            longitude=park_in.longitude,
            area_km2=park_in.area_km2,
            google_maps_url=park_in.google_maps_url,
        )
        session.add(park_db)
        session.commit()
        session.refresh(park_db)

        return Park(
            id=park_db.id,
            name=park_db.name,
            governorate=park_db.governorate,
            description=park_db.description,
            latitude=park_db.latitude,
            longitude=park_db.longitude,
            area_km2=park_db.area_km2,
            images=[],
        )

@router.get("/{park_id}/species")
def get_park_species(park_id: int):
    """Get all species for a specific park."""
    from models import SpeciesDB, ParkSpeciesLink
    from sqlmodel import select

    with Session(get_engine()) as session:
        # Verify park exists
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        # Get species linked to this park
        species_links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park_id)
        ).all()

        if not species_links:
            return []

        species_ids = [link.species_id for link in species_links]
        species_db = session.exec(
            select(SpeciesDB).where(SpeciesDB.species_id.in_(species_ids))
        ).all()

        return [
            {
                "id": s.species_id,
                "name": s.name,
                "type": s.type,
                "scientific_name": s.scientific_name,
                "description": s.description,
                "threats": s.threats,
                "protection_measures": s.protection_measures,
                "safety_guidelines": s.safety_guidelines,
                "medicinal_use": s.medicinal_use,
                "image_url": s.image_url,
                "park_ids": [park_id]  # Simplified for this park
            }
            for s in species_db
        ]

@router.get("/{park_id}/trails")
def get_park_trails(park_id: int):
    """Get all trails for a specific park."""
    from models import TrailDB
    from sqlmodel import select

    with Session(get_engine()) as session:
        # Verify park exists
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        trails_db = session.exec(
            select(TrailDB).where(TrailDB.park_id == park_id)
        ).all()

        from typing import List
        from pydantic import BaseModel

        class TrailResponse(BaseModel):
            id: int
            park_id: int
            name: str
            description: str
            difficulty: str
            length_km: float
            duration_hours: float
            elevation_gain: int | None = None
            trail_type: str
            surface: str | None = None
            highlights: List[str] | None = None

        return [
            {
                "trail_id": t.trail_id,
                "park_id": t.park_id,
                "name": t.name,
                "description": t.description,
                "difficulty": t.difficulty,
                "length_km": t.length_km,
                "duration_hours": t.duration_hours,
                "elevation_gain": t.elevation_gain,
                "trail_type": t.trail_type,
                "surface": t.surface,
                "highlights": t.highlights.split(",") if t.highlights else None,
            }
            for t in trails_db
        ]

@router.get("/{park_id}/reviews")
def get_park_reviews(park_id: int):
    """Get all reviews for a specific park."""
    from models import ReviewDB
    from sqlmodel import select

    with Session(get_engine()) as session:
        # Verify park exists
        park = session.get(ParkDB, park_id)
        if park is None:
            return []  # Return empty list instead of 404

        reviews_db = session.exec(
            select(ReviewDB).where(ReviewDB.park_id == park_id)
        ).all()

        return [
            {
                "review_id": r.review_id,
                "park_id": r.park_id,
                "author_name": r.author_name,
                "rating": r.rating,
                "title": r.title,
                "comment": r.comment,
                "visit_date": r.visit_date,
                "helpful_count": r.helpful_count,
                "created_at": r.created_at
            }
            for r in reviews_db
        ]

@router.post("/{park_id}/reviews")
def create_park_review(park_id: int, review_data: dict):
    """Create a new review for a park."""
    from models import ReviewDB

    with Session(get_engine()) as session:
        # Verify park exists
        park = session.get(ParkDB, park_id)
        if park is None:
            return []  # Return empty list instead of 404

        review = ReviewDB(
            park_id=park_id,
            author_name=review_data.get("author_name", "Anonymous"),
            rating=review_data.get("rating", 5),
            title=review_data.get("title", ""),
            comment=review_data.get("comment", ""),
            visit_date=review_data.get("visit_date")
        )
        session.add(review)
        session.commit()
        session.refresh(review)

        return {
            "review_id": review.review_id,
            "park_id": review.park_id,
            "author_name": review.author_name,
            "rating": review.rating,
            "title": review.title,
            "comment": review.comment,
            "visit_date": review.visit_date,
            "helpful_count": review.helpful_count,
            "created_at": review.created_at
        }

@router.get("/{park_id}/weather")
async def get_park_weather(park_id: int):
    """Get weather for a park."""
    from weather_service import get_weather_for_location

    with Session(get_engine()) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            return {
                "park_id": park_id,
                "park_name": "Unknown Park",
                "weather": {
                    "icon_url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=100",
                    "temperature": "N/A",
                    "description": "Weather data unavailable",
                    "temp_min": "N/A",
                    "temp_max": "N/A",
                    "humidity": "N/A",
                    "wind_speed": "N/A"
                }
            }  # Return dummy object instead of 404

        weather_data = await get_weather_for_location(park.latitude, park.longitude)
        if "error" in weather_data:
            return {
                "park_id": park.id,
                "park_name": park.name,
                "weather": {
                    "icon_url": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=100",
                    "temperature": "N/A",
                    "description": "Weather service temporarily unavailable",
                    "temp_min": "N/A",
                    "temp_max": "N/A",
                    "humidity": "N/A",
                    "wind_speed": "N/A"
                }
            }  # Return dummy object instead of 503

        return {
            "park_id": park.id,
            "park_name": park.name,
            "weather": weather_data,
        }

@router.get("/{park_id}/unsplash-images")
async def get_park_unsplash_images(park_id: int, count: int = 4):
    """Get Unsplash images for a park using park name as search keyword."""
    try:
        # Get park information
        with Session(get_engine()) as session:
            park = session.get(ParkDB, park_id)
            if not park:
                return []

            park_name = park.name

        # Create search query from park name - use the official Unsplash source format
        # Remove common words and extract key terms
        name_parts = park_name.lower().replace('parc national', '').replace('parc', '').replace('de', '').replace("d'", '').strip().split()

        # Create search query with park name and Tunisia/nature keywords
        search_terms = name_parts[:2] + ['tunisie', 'nature']  # Limit to first 2 name parts to avoid too long URLs
        search_query = ','.join(search_terms)

        # Use official Unsplash source.unsplash.com format (no API key needed)
        images = []
        for i in range(min(count, 4)):  # Limit to 4 images max
            # Create different variations for each image
            variations = ['', '?featured', '?sig=1', '?sig=2']
            variation = variations[i % len(variations)]

            image_url = f"https://source.unsplash.com/featured/?{search_query}{variation}"
            images.append({
                "url": image_url,
                "alt_description": f"Vue du {park_name} - Image {i+1}",
                "description": f"Paysage naturel du {park_name} en Tunisie",
                "photographer": "Unsplash Community",
                "unsplash_url": image_url  # Same URL since we can't get the original photo URL
            })

        return images

    except Exception as e:
        print(f"Error fetching Unsplash images for park {park_id}: {e}")
        # Fallback to empty array to prevent frontend errors
        return []


@router.get("/{park_id}/wikipedia")
async def get_park_wikipedia_info(park_id: int):
    """Get Wikipedia information for a park."""
    try:
        import httpx

        # Get park information
        with Session(get_engine()) as session:
            park = session.get(ParkDB, park_id)
            if not park:
                return {"wikipedia_info": {"title": park.name, "extract": "Informations non disponibles."}}

            park_name = park.name

        # Try different search names for Wikipedia
        search_names = [
            park_name,
            park_name.replace('Parc National', '').strip(),
            park_name.replace('Parc', '').strip(),
            f"{park_name} Tunisie"
        ]

        for search_name in search_names:
            try:
                # Format name for Wikipedia URL
                wiki_name = search_name.replace(' ', '_')

                # Try French Wikipedia first
                url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"

                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if 'extract' in data and data['extract']:
                            return {
                                "wikipedia_info": {
                                    "title": data.get('title', park_name),
                                    "extract": data['extract'][:500] + "..." if len(data['extract']) > 500 else data['extract'],
                                    "url": data.get('content_urls', {}).get('desktop', {}).get('page', f"https://fr.wikipedia.org/wiki/{wiki_name}")
                                }
                            }
            except Exception as e:
                print(f"Wikipedia search failed for {search_name}: {e}")
                continue

        # If no Wikipedia info found, return basic info
        return {
            "wikipedia_info": {
                "title": park_name,
                "extract": f"Informations détaillées sur {park_name} non disponibles dans Wikipedia.",
                "url": None
            }
        }

    except Exception as e:
        print(f"Error fetching Wikipedia info for park {park_id}: {e}")
        # Fallback to basic info
        return {"wikipedia_info": {"title": "Information non disponible", "extract": "Erreur lors de la récupération des informations."}}


@router.get("/{park_id}/nearby-places")
async def get_park_nearby_places(park_id: int, place_type: str = "restaurant", radius: int = 5000):
    """Get nearby places for a park."""
    try:
        # For demo purposes, return mock data since we don't have Google Places API key
        # In production, this would use Google Places API or similar service

        # Get park information
        with Session(get_engine()) as session:
            park = session.get(ParkDB, park_id)
            if not park:
                return {"places": []}

        # Mock nearby places based on place type
        mock_places = {
            "restaurant": [
                {"name": "Restaurant Traditionnel Tunisien", "address": f"Près de {park.name}", "rating": 4.2, "open_now": True},
                {"name": "Café Maure", "address": f"Centre de {park.governorate}", "rating": 4.5, "open_now": False},
                {"name": "Restaurant Italien", "address": f"Zone touristique, {park.governorate}", "rating": 4.1, "open_now": True}
            ],
            "hotel": [
                {"name": "Hôtel Nature", "address": f"Vue sur {park.name}", "rating": 4.3, "open_now": True},
                {"name": "Éco-Lodge Tunisien", "address": f"Près de l'entrée du parc", "rating": 4.6, "open_now": True}
            ],
            "cafe": [
                {"name": "Café des Voyageurs", "address": f"Entrée de {park.name}", "rating": 4.0, "open_now": True},
                {"name": "Café Traditionnel", "address": f"Centre-ville {park.governorate}", "rating": 3.8, "open_now": False}
            ],
            "gas_station": [
                {"name": "Station Service Principale", "address": f"Route de {park.governorate}", "rating": 3.9, "open_now": True},
                {"name": "Station Shell", "address": f"Périphérie de {park.governorate}", "rating": 4.1, "open_now": True}
            ],
            "hospital": [
                {"name": "Hôpital Régional", "address": f"Centre de {park.governorate}", "rating": 4.2, "open_now": True},
                {"name": "Clinique Privée", "address": f"Zone résidentielle, {park.governorate}", "rating": 4.4, "open_now": False}
            ]
        }

        places = mock_places.get(place_type, [])
        formatted_places = []

        for place in places:
            formatted_places.append({
                "name": place["name"],
                "address": place["address"],
                "rating": place["rating"],
                "open_now": place["open_now"],
                "location": {
                    "lat": park.latitude + (0.01 * (len(formatted_places) - 1)),  # Mock coordinates near park
                    "lng": park.longitude + (0.01 * (len(formatted_places) - 1))
                },
                "types": [place_type],
                "price_level": 2
            })

        return {"places": formatted_places}

    except Exception as e:
        print(f"Error fetching nearby places for park {park_id}: {e}")
        # Fallback to empty list
        return {"places": []}

@router.put("/{park_id}", response_model=Park)
def update_park(park_id: int, park_in: ParkUpdate, current_user = Depends(get_current_user)):
    """Update an existing park."""
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        data = park_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(park_db, field, value)

        session.add(park_db)
        session.commit()
        session.refresh(park_db)

        import json
        return Park(
            id=park_db.id,
            name=park_db.name,
            governorate=park_db.governorate,
            description=park_db.description,
            latitude=park_db.latitude,
            longitude=park_db.longitude,
            area_km2=park_db.area_km2,
            images=[get_file_url(img, "parks") for img in (json.loads(park_db.images) if park_db.images else [])],
        )

@router.delete("/{park_id}", status_code=204)
def delete_park(park_id: int, current_user = Depends(get_current_user)):
    """Delete a park."""
    with Session(get_engine()) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        session.delete(park_db)
        session.commit()
        return None
