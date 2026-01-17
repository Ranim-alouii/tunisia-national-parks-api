from typing import List, Literal
from datetime import datetime, timedelta, timezone

import logging
import time
import json

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Depends,
    status,
    File,
    UploadFile,
    Query,
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field
from sqlmodel import Session, select
from jose import JWTError, jwt
from passlib.context import CryptContext

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIASGIMiddleware

from database import init_db, engine
from models import (
    ParkDB,
    SpeciesDB,
    ParkSpeciesLink,
    TrailDB,
    ReviewDB,
    BadgeDB,
    SightingDB,
)
from config import settings
from utils import (
    save_upload_file,
    delete_file,
    get_file_url,
    PARKS_DIR,
    SPECIES_DIR,
)
from weather_service import get_weather_for_location, get_weather_forecast


# ---------- APP & GLOBAL MIDDLEWARE ----------

app = FastAPI(
    title="Tunisia National Parks API - Enhanced Edition",
    description="""
    Complete API for Tunisia's national parks with biodiversity, trails, reviews, and gamification.

    ## 🌟 New Features
    * **Trails**: Hiking trails with difficulty levels and GPX data
    * **Reviews & Ratings**: User reviews and park ratings
    * **Wildlife Sightings**: Report and view species sightings
    * **Badges & Gamification**: Achievement system for park explorers
    * **Enhanced Species**: Audio, conservation status, best viewing times
    * **Park Details**: Difficulty levels, activities, best visiting months
    * **Comparison Tool**: Compare multiple parks side-by-side

    ## 🎯 Existing Features
    * **Authentication**: Secure JWT-based authentication
    * **Parks Management**: CRUD operations for national parks
    * **Species Management**: Comprehensive fauna & flora database
    * **Image Upload**: Upload and manage images
    * **Weather**: Real-time weather data and forecasts
    * **Maps & Navigation**: Google Maps integration with directions
    * **Emergency**: Report emergencies with location data
    """,
    version="3.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIASGIMiddleware)

# Logging
logger = logging.getLogger("tunisia_parks")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Static files and templates
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_ms = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} "
        f"({process_ms:.2f} ms)"
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": 422,
                "message": "Validation failed",
                "details": exc.errors(),
            }
        },
    )


# ---------- SECURITY CONFIG ----------

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


fake_admin_user_db: dict[str, UserInDB] = {
    settings.ADMIN_USERNAME: UserInDB(
        username=settings.ADMIN_USERNAME,
        full_name=settings.ADMIN_FULL_NAME,
        disabled=False,
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
    )
}


def get_user(username: str) -> UserInDB | None:
    return fake_admin_user_db.get(username)


def authenticate_user(username: str, password: str) -> UserInDB | None:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None or user.disabled:
        raise credentials_exception
    return user


# ---------- STARTUP & HEALTH ----------

@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "3.0.0"}


@app.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login to get an access token using credentials in .env.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# ---------- PARK MODELS ----------

class Park(BaseModel):
    id: int
    name: str
    governorate: str
    description: str
    latitude: float
    longitude: float
    area_km2: float
    images: List[str]


class ParkCreate(BaseModel):
    name: str
    governorate: str
    description: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    area_km2: float = Field(gt=0)


class ParkUpdate(BaseModel):
    name: str | None = None
    governorate: str | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    area_km2: float | None = Field(default=None, gt=0)


# ---------- SPECIES MODELS ----------

class Species(BaseModel):
    id: int
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    safety_guidelines: str
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int]


class SpeciesCreate(BaseModel):
    name: str
    type: Literal["animal", "plant"]
    scientific_name: str
    description: str
    threats: str
    protection_measures: str
    safety_guidelines: str = ""
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int] = []


class SpeciesUpdate(BaseModel):
    name: str | None = None
    type: Literal["animal", "plant"] | None = None
    scientific_name: str | None = None
    description: str | None = None
    threats: str | None = None
    protection_measures: str | None = None
    safety_guidelines: str | None = None
    medicinal_use: str | None = None
    image_url: str | None = None
    park_ids: List[int] | None = None


# ---------- ENHANCED FEATURE MODELS ----------

class Trail(BaseModel):
    trail_id: int
    park_id: int
    name: str
    description: str
    difficulty: str
    length_km: float
    duration_hours: float
    elevation_gain: int | None
    trail_type: str
    highlights: List[str]


class Review(BaseModel):
    review_id: int
    park_id: int
    author_name: str
    rating: int
    title: str
    comment: str
    visit_date: str | None
    helpful_count: int
    created_at: str


class ReviewCreate(BaseModel):
    author_name: str
    rating: int = Field(ge=1, le=5)
    title: str
    comment: str
    visit_date: str | None = None


class Sighting(BaseModel):
    sighting_id: int
    park_id: int
    species_id: int
    reporter_name: str
    sighting_date: str
    location_lat: float
    location_lng: float
    photo_url: str | None
    notes: str | None
    verified: bool
    created_at: str


class SightingCreate(BaseModel):
    park_id: int
    species_id: int
    reporter_name: str
    sighting_date: str
    location_lat: float
    location_lng: float
    photo_url: str | None = None
    notes: str | None = None


class Badge(BaseModel):
    badge_id: int
    name: str
    description: str
    icon: str
    requirement: str
    points: int


class ParkComparison(BaseModel):
    park_id: int
    park_name: str
    governorate: str
    difficulty_level: str | None
    area_hectares: int | None
    species_count: int
    trails_count: int
    average_rating: float | None
    activities: List[str]
    best_months: List[str]


# ---------- WEATHER & MAP MODELS ----------

class WeatherResponse(BaseModel):
    temperature: int
    feels_like: int
    temp_min: int
    temp_max: int
    humidity: int
    pressure: int
    description: str
    icon: str
    icon_url: str
    wind_speed: float
    wind_direction: int
    clouds: int
    visibility: float
    sunrise: int
    sunset: int
    timezone: int
    city_name: str


class MapData(BaseModel):
    park_id: int
    park_name: str
    latitude: float
    longitude: float
    governorate: str
    google_maps_url: str
    directions_url: str


class DirectionsRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_park_id: int


# ---------- FILTER & SEARCH MODELS ----------

class SearchResult(BaseModel):
    total_results: int
    parks: List[Park]


class MultiParkRoute(BaseModel):
    park_ids: List[int]


class RoutePoint(BaseModel):
    order: int
    park_id: int
    park_name: str
    latitude: float
    longitude: float
    governorate: str
    google_maps_url: str


class MultiParkRouteResponse(BaseModel):
    total_parks: int
    total_distance_km: float
    estimated_time_hours: float
    route_points: List[RoutePoint]
    google_maps_url: str


# ---------- PARK ENDPOINTS ----------

@app.get("/api/parks", response_model=List[Park], tags=["Parks"])
def list_parks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    with Session(engine) as session:
        statement = select(ParkDB).offset(skip).limit(limit)
        parks_db = session.exec(statement).all()
        return [
            Park(
                id=p.id,
                name=p.name,
                governorate=p.governorate,
                description=p.description,
                latitude=p.latitude,
                longitude=p.longitude,
                area_km2=p.area_km2,
                images=[get_file_url(img, "parks") for img in (p.images or [])],
            )
            for p in parks_db
        ]


@app.get("/api/parks/{park_id}", response_model=Park, tags=["Parks"])
def get_park(park_id: int):
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        return Park(
            id=park.id,
            name=park.name,
            governorate=park.governorate,
            description=park.description,
            latitude=park.latitude,
            longitude=park.longitude,
            area_km2=park.area_km2,
            images=[get_file_url(img, "parks") for img in (park.images or [])],
        )


@app.post("/api/parks", response_model=Park, status_code=201, tags=["Parks"])
def create_park(
    park_in: ParkCreate,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        park_db = ParkDB(
            name=park_in.name,
            governorate=park_in.governorate,
            description=park_in.description,
            latitude=park_in.latitude,
            longitude=park_in.longitude,
            area_km2=park_in.area_km2,
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


@app.put("/api/parks/{park_id}", response_model=Park, tags=["Parks"])
def update_park(
    park_id: int,
    park_in: ParkUpdate,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        data = park_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(park_db, field, value)

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
            images=[get_file_url(img, "parks") for img in (park_db.images or [])],
        )


@app.delete("/api/parks/{park_id}", status_code=204, tags=["Parks"])
def delete_park(
    park_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        if park_db.images:
            for img_filename in park_db.images:
                delete_file(img_filename, PARKS_DIR)

        session.delete(park_db)
        session.commit()
        return None


# ---------- PARK IMAGE ENDPOINTS ----------

@app.post("/api/parks/{park_id}/images", status_code=201, tags=["Park Images"])
async def upload_park_image(
    park_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        filename = await save_upload_file(file, PARKS_DIR)

        if park_db.images is None:
            park_db.images = []
        park_db.images.append(filename)

        session.add(park_db)
        session.commit()
        session.refresh(park_db)

        return {
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": get_file_url(filename, "parks"),
            "total_images": len(park_db.images),
        }


@app.delete(
    "/api/parks/{park_id}/images/{filename}", status_code=204, tags=["Park Images"]
)
def delete_park_image(
    park_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        if not park_db.images or filename not in park_db.images:
            raise HTTPException(status_code=404, detail="Image not found")

        park_db.images.remove(filename)
        session.add(park_db)
        session.commit()

        delete_file(filename, PARKS_DIR)
        return None


# ---------- SPECIES ENDPOINTS (JOIN-BASED) ----------

@app.get("/api/species", response_model=List[Species], tags=["Species"])
def list_species(
    type: Literal["animal", "plant"] | None = None,
    park_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get a list of all species.

    Optional filters:
    - type: Filter by 'animal' or 'plant'
    - park_id: Filter species by park ID
    """
    with Session(engine) as session:
        stmt = select(SpeciesDB)

        if type is not None:
            stmt = stmt.where(SpeciesDB.type == type)

        if park_id is not None:
            stmt = (
                stmt.join(
                    ParkSpeciesLink,
                    ParkSpeciesLink.species_id == SpeciesDB.species_id,
                )
                .where(ParkSpeciesLink.park_id == park_id)
            )

        stmt = stmt.offset(skip).limit(limit)
        species_rows = session.exec(stmt).all()

        if species_rows:
            species_ids = [s.species_id for s in species_rows]
            links = session.exec(
                select(ParkSpeciesLink).where(
                    ParkSpeciesLink.species_id.in_(species_ids)
                )
            ).all()
            park_ids_map: dict[int, list[int]] = {}
            for link in links:
                park_ids_map.setdefault(link.species_id, []).append(link.park_id)
        else:
            park_ids_map = {}

        return [
            Species(
                id=s.species_id,
                name=s.name,
                type=s.type,
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats or "",
                protection_measures=s.protection_measures or "",
                safety_guidelines=s.safety_guidelines or "",
                medicinal_use=s.medicinal_use,
                image_url=get_file_url(s.image_url, "species") if s.image_url else None,
                park_ids=park_ids_map.get(s.species_id, []),
            )
            for s in species_rows
        ]


@app.get("/api/species/{species_id}", response_model=Species, tags=["Species"])
def get_species(species_id: int):
    with Session(engine) as session:
        s = session.get(SpeciesDB, species_id)
        if s is None:
            raise HTTPException(status_code=404, detail="Species not found")

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == s.species_id)
        ).all()
        park_ids = [l.park_id for l in links]

        return Species(
            id=s.species_id,
            name=s.name,
            type=s.type,
            scientific_name=s.scientific_name,
            description=s.description,
            threats=s.threats or "",
            protection_measures=s.protection_measures or "",
            safety_guidelines=s.safety_guidelines or "",
            medicinal_use=s.medicinal_use,
            image_url=get_file_url(s.image_url, "species") if s.image_url else None,
            park_ids=park_ids,
        )


@app.get("/api/parks/{park_id}/species", response_model=List[Species], tags=["Species"])
def list_species_for_park(park_id: int):
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.park_id == park_id)
        ).all()
        species_ids = [l.species_id for l in links]
        if not species_ids:
            return []

        species_rows = session.exec(
            select(SpeciesDB).where(SpeciesDB.species_id.in_(species_ids))
        ).all()

        links_all = session.exec(
            select(ParkSpeciesLink).where(
                ParkSpeciesLink.species_id.in_([s.species_id for s in species_rows])
            )
        ).all()
        park_ids_map: dict[int, list[int]] = {}
        for link in links_all:
            park_ids_map.setdefault(link.species_id, []).append(link.park_id)

        return [
            Species(
                id=s.species_id,
                name=s.name,
                type=s.type,
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats or "",
                protection_measures=s.protection_measures or "",
                safety_guidelines=s.safety_guidelines or "",
                medicinal_use=s.medicinal_use,
                image_url=get_file_url(s.image_url, "species") if s.image_url else None,
                park_ids=park_ids_map.get(s.species_id, []),
            )
            for s in species_rows
        ]


@app.post("/api/species", response_model=Species, status_code=201, tags=["Species"])
def create_species(
    species_in: SpeciesCreate,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        species_db = SpeciesDB(
            name=species_in.name,
            type=species_in.type,
            scientific_name=species_in.scientific_name,
            description=species_in.description,
            threats=species_in.threats,
            protection_measures=species_in.protection_measures,
            safety_guidelines=species_in.safety_guidelines,
            medicinal_use=species_in.medicinal_use,
            image_url=species_in.image_url,
        )
        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        for park_id in species_in.park_ids:
            park = session.get(ParkDB, park_id)
            if park:
                session.add(
                    ParkSpeciesLink(
                        park_id=park.id,
                        species_id=species_db.species_id,
                    )
                )
        session.commit()

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species_db.species_id)
        ).all()
        park_ids = [l.park_id for l in links]

        return Species(
            id=species_db.species_id,
            name=species_db.name,
            type=species_db.type,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats or "",
            protection_measures=species_db.protection_measures or "",
            safety_guidelines=species_db.safety_guidelines or "",
            medicinal_use=species_db.medicinal_use,
            image_url=get_file_url(species_db.image_url, "species") if species_db.image_url else None,
            park_ids=park_ids,
        )


@app.put("/api/species/{species_id}", response_model=Species, tags=["Species"])
def update_species(
    species_id: int,
    species_in: SpeciesUpdate,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        data = species_in.model_dump(exclude_unset=True)

        simple_fields = {
            "name",
            "type",
            "scientific_name",
            "description",
            "threats",
            "protection_measures",
            "safety_guidelines",
            "medicinal_use",
            "image_url",
        }
        for field in simple_fields:
            if field in data:
                setattr(species_db, field, data[field])

        if "park_ids" in data:
            new_ids = set(data["park_ids"] or [])

            existing_links = session.exec(
                select(ParkSpeciesLink).where(
                    ParkSpeciesLink.species_id == species_db.species_id
                )
            ).all()
            existing_ids = {l.park_id for l in existing_links}

            for link in existing_links:
                if link.park_id not in new_ids:
                    session.delete(link)

            for park_id in new_ids - existing_ids:
                park = session.get(ParkDB, park_id)
                if park:
                    session.add(
                        ParkSpeciesLink(
                            park_id=park.id,
                            species_id=species_db.species_id,
                        )
                    )

        session.add(species_db)
        session.commit()

        links = session.exec(
            select(ParkSpeciesLink).where(ParkSpeciesLink.species_id == species_db.species_id)
        ).all()
        park_ids = [l.park_id for l in links]

        return Species(
            id=species_db.species_id,
            name=species_db.name,
            type=species_db.type,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats or "",
            protection_measures=species_db.protection_measures or "",
            safety_guidelines=species_db.safety_guidelines or "",
            medicinal_use=species_db.medicinal_use,
            image_url=get_file_url(species_db.image_url, "species") if species_db.image_url else None,
            park_ids=park_ids,
        )


@app.delete("/api/species/{species_id}", status_code=204, tags=["Species"])
def delete_species(
    species_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        if species_db.image_url:
            delete_file(species_db.image_url, SPECIES_DIR)

        session.exec(
            select(ParkSpeciesLink)
            .where(ParkSpeciesLink.species_id == species_db.species_id)
        )
        session.query(ParkSpeciesLink).filter(
            ParkSpeciesLink.species_id == species_db.species_id
        ).delete(synchronize_session=False)

        session.delete(species_db)
        session.commit()
        return None


# ---------- SPECIES IMAGE ENDPOINTS ----------

@app.post(
    "/api/species/{species_id}/image", status_code=201, tags=["Species Images"]
)
async def upload_species_image(
    species_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        if species_db.image_url:
            delete_file(species_db.image_url, SPECIES_DIR)

        filename = await save_upload_file(file, SPECIES_DIR)
        species_db.image_url = filename

        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        return {
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": get_file_url(filename, "species"),
        }


@app.delete("/api/species/{species_id}/image", status_code=204, tags=["Species Images"])
def delete_species_image(
    species_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        if not species_db.image_url:
            raise HTTPException(status_code=404, detail="No image to delete")

        delete_file(species_db.image_url, SPECIES_DIR)

        species_db.image_url = None
        session.add(species_db)
        session.commit()
        return None


# ---------- WEATHER ENDPOINTS ----------

@app.get("/api/weather/current", tags=["Weather"])
async def get_current_weather(
    latitude: float,
    longitude: float,
):
    weather_data = await get_weather_for_location(latitude, longitude)
    if "error" in weather_data:
        raise HTTPException(status_code=503, detail=weather_data)
    return weather_data


@app.get("/api/parks/{park_id}/weather", tags=["Weather"])
async def get_park_weather(park_id: int):
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        weather_data = await get_weather_for_location(park.latitude, park.longitude)
        if "error" in weather_data:
            raise HTTPException(status_code=503, detail=weather_data)

        return {
            "park_id": park.id,
            "park_name": park.name,
            "weather": weather_data,
        }


@app.get("/api/parks/{park_id}/forecast", tags=["Weather"])
async def get_park_forecast(park_id: int, days: int = 5):
    if days < 1 or days > 5:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 5")

    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        forecast_data = await get_weather_forecast(park.latitude, park.longitude, days)
        if "error" in forecast_data:
            raise HTTPException(status_code=503, detail=forecast_data)

        return {
            "park_id": park.id,
            "park_name": park.name,
            "forecast": forecast_data,
        }


# ---------- MAP & DIRECTIONS ENDPOINTS ----------

@app.get("/map", response_class=HTMLResponse, tags=["Maps & Navigation"])
async def view_interactive_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})


@app.get("/api/parks/{park_id}/map", response_model=MapData, tags=["Maps & Navigation"])
def get_park_map_data(park_id: int):
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
        directions_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&destination={park.latitude},{park.longitude}"
        )

        return MapData(
            park_id=park.id,
            park_name=park.name,
            latitude=park.latitude,
            longitude=park.longitude,
            governorate=park.governorate,
            google_maps_url=google_maps_url,
            directions_url=directions_url,
        )


@app.get("/api/maps/all-parks", tags=["Maps & Navigation"])
def get_all_parks_map_data():
    with Session(engine) as session:
        parks = session.exec(select(ParkDB)).all()

        parks_data = []
        for park in parks:
            google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
            directions_url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&destination={park.latitude},{park.longitude}"
            )

            parks_data.append(
                {
                    "park_id": park.id,
                    "park_name": park.name,
                    "latitude": park.latitude,
                    "longitude": park.longitude,
                    "governorate": park.governorate,
                    "google_maps_url": google_maps_url,
                    "directions_url": directions_url,
                    "description": (
                        park.description[:100] + "..."
                        if len(park.description) > 100
                        else park.description
                    ),
                }
            )

        return {
            "total_parks": len(parks_data),
            "parks": parks_data,
        }


@app.post("/api/maps/directions", tags=["Maps & Navigation"])
def get_directions_to_park(directions: DirectionsRequest):
    with Session(engine) as session:
        park = session.get(ParkDB, directions.destination_park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        directions_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={directions.origin_lat},{directions.origin_lng}"
            f"&destination={park.latitude},{park.longitude}"
            f"&travelmode=driving"
        )

        return {
            "park_id": park.id,
            "park_name": park.name,
            "origin": {
                "latitude": directions.origin_lat,
                "longitude": directions.origin_lng,
            },
            "destination": {
                "latitude": park.latitude,
                "longitude": park.longitude,
            },
            "directions_url": directions_url,
            "google_maps_url": f"https://www.google.com/maps?q={park.latitude},{park.longitude}",
        }
 