from typing import List, Literal
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Request, Depends, status, File, UploadFile
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

import logging
import time

from database import init_db, engine
from models import ParkDB, SpeciesDB, ParkSpeciesLink
from config import settings
from utils import (
    save_upload_file, 
    delete_file, 
    get_file_url,
    PARKS_DIR,
    SPECIES_DIR,
)
from weather_service import get_weather_for_location, get_weather_forecast

app = FastAPI(
    title="Tunisia National Parks API",
    description="""
    API for managing Tunisia's national parks, species, routes, and emergency information.
    
    ## Features
    * **Authentication**: Secure JWT-based authentication
    * **Parks Management**: CRUD operations for national parks
    * **Species Management**: Manage endangered species and their conservation
    * **Image Upload**: Upload and manage images for parks and species
    * **Weather**: Real-time weather data and forecasts for parks
    * **Maps & Navigation**: Google Maps integration with directions
    * **Route Information**: Get travel directions and safety tips
    * **Emergency**: Report emergencies with location data
    * **Biodiversity**: Complete fauna and flora with safety guidelines and medicinal information
    """,
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger = logging.getLogger("tunisia_parks")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Mount uploads directory for serving static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Templates for interactive map
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


# Single in-memory admin user
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
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
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


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health", tags=["Health"])
def health_check():
    """Check if the API is running"""
    return {"status": "ok", "version": "2.0.0"}


@app.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login to get an access token.
    
    Use the following credentials:
    - **username**: admin
    - **password**: admin123
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
def list_parks():
    """Get a list of all national parks"""
    with Session(engine) as session:
        parks_db = session.exec(select(ParkDB)).all()
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
    """Get details of a specific park by ID"""
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
    """
    Create a new park (requires authentication).
    
    Click the 🔒 lock icon to authorize with your token.
    """
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
    """Update an existing park (requires authentication)"""
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
    """Delete a park and all its images (requires authentication)"""
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        # Delete all associated images
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
    """
    Upload an image for a park (requires authentication).
    
    Accepted formats: JPG, JPEG, PNG, WEBP
    Max size: 5MB
    """
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")
        
        # Save the file
        filename = await save_upload_file(file, PARKS_DIR)
        
        # Add filename to park's images list
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
            "total_images": len(park_db.images)
        }


@app.delete("/api/parks/{park_id}/images/{filename}", status_code=204, tags=["Park Images"])
def delete_park_image(
    park_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a specific image from a park (requires authentication)"""
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")
        
        if not park_db.images or filename not in park_db.images:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Remove from database
        park_db.images.remove(filename)
        session.add(park_db)
        session.commit()
        
        # Delete file
        delete_file(filename, PARKS_DIR)
        
        return None


# ---------- SPECIES ENDPOINTS ----------

@app.get("/api/species", response_model=List[Species], tags=["Species"])
def list_species(
    type: Literal["animal", "plant"] | None = None,
    park_id: int | None = None,
):
    """
    Get a list of all species.
    
    Optional filters:
    - **type**: Filter by 'animal' or 'plant'
    - **park_id**: Filter species by park ID
    """
    with Session(engine) as session:
        statement = select(SpeciesDB)

        if type is not None:
            statement = statement.where(SpeciesDB.type == type)

        species_db = session.exec(statement).all()

        if park_id is not None:
            species_db = [
                s for s in species_db
                if any(p.id == park_id for p in s.parks)
            ]

        return [
            Species(
                id=s.id,
                name=s.name,
                type=s.type.value,
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats,
                protection_measures=s.protection_measures,
                safety_guidelines=s.safety_guidelines,
                medicinal_use=s.medicinal_use,
                image_url=get_file_url(s.image_url, "species") if s.image_url else None,
                park_ids=[p.id for p in s.parks],
            )
            for s in species_db
        ]


@app.get("/api/species/{species_id}", response_model=Species, tags=["Species"])
def get_species(species_id: int):
    """Get details of a specific species by ID"""
    with Session(engine) as session:
        s = session.get(SpeciesDB, species_id)
        if s is None:
            raise HTTPException(status_code=404, detail="Species not found")

        return Species(
            id=s.id,
            name=s.name,
            type=s.type.value,
            scientific_name=s.scientific_name,
            description=s.description,
            threats=s.threats,
            protection_measures=s.protection_measures,
            safety_guidelines=s.safety_guidelines,
            medicinal_use=s.medicinal_use,
            image_url=get_file_url(s.image_url, "species") if s.image_url else None,
            park_ids=[p.id for p in s.parks],
        )


@app.get("/api/parks/{park_id}/species", response_model=List[Species], tags=["Species"])
def list_species_for_park(park_id: int):
    """Get all species found in a specific park"""
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")

        return [
            Species(
                id=s.id,
                name=s.name,
                type=s.type.value,
                scientific_name=s.scientific_name,
                description=s.description,
                threats=s.threats,
                protection_measures=s.protection_measures,
                safety_guidelines=s.safety_guidelines,
                medicinal_use=s.medicinal_use,
                image_url=get_file_url(s.image_url, "species") if s.image_url else None,
                park_ids=[p.id for p in s.parks],
            )
            for s in park.species
        ]


@app.post("/api/species", response_model=Species, status_code=201, tags=["Species"])
def create_species(
    species_in: SpeciesCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new species (requires authentication)"""
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

        if species_in.park_ids:
            for park_id in species_in.park_ids:
                park = session.get(ParkDB, park_id)
                if park:
                    link = ParkSpeciesLink(park_id=park.id, species_id=species_db.id)
                    session.add(link)
            session.commit()
            session.refresh(species_db)

        return Species(
            id=species_db.id,
            name=species_db.name,
            type=species_db.type.value,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats,
            protection_measures=species_db.protection_measures,
            safety_guidelines=species_db.safety_guidelines,
            medicinal_use=species_db.medicinal_use,
            image_url=get_file_url(species_db.image_url, "species") if species_db.image_url else None,
            park_ids=[p.id for p in species_db.parks],
        )


@app.put("/api/species/{species_id}", response_model=Species, tags=["Species"])
def update_species(
    species_id: int, 
    species_in: SpeciesUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update an existing species (requires authentication)"""
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
            current_ids = {p.id for p in species_db.parks}

            for park in list(species_db.parks):
                if park.id not in new_ids:
                    species_db.parks.remove(park)

            for park_id in new_ids - current_ids:
                park = session.get(ParkDB, park_id)
                if park:
                    species_db.parks.append(park)

        session.add(species_db)
        session.commit()
        session.refresh(species_db)

        return Species(
            id=species_db.id,
            name=species_db.name,
            type=species_db.type.value,
            scientific_name=species_db.scientific_name,
            description=species_db.description,
            threats=species_db.threats,
            protection_measures=species_db.protection_measures,
            safety_guidelines=species_db.safety_guidelines,
            medicinal_use=species_db.medicinal_use,
            image_url=get_file_url(species_db.image_url, "species") if species_db.image_url else None,
            park_ids=[p.id for p in species_db.parks],
        )


@app.delete("/api/species/{species_id}", status_code=204, tags=["Species"])
def delete_species(
    species_id: int,
    current_user: User = Depends(get_current_user),
):
    """Delete a species and its image (requires authentication)"""
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")

        # Delete image if exists
        if species_db.image_url:
            delete_file(species_db.image_url, SPECIES_DIR)

        session.delete(species_db)
        session.commit()
        return None


# ---------- SPECIES IMAGE ENDPOINTS ----------

@app.post("/api/species/{species_id}/image", status_code=201, tags=["Species Images"])
async def upload_species_image(
    species_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload an image for a species (requires authentication).
    
    Replaces existing image if one exists.
    Accepted formats: JPG, JPEG, PNG, WEBP
    Max size: 5MB
    """
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")
        
        # Delete old image if exists
        if species_db.image_url:
            delete_file(species_db.image_url, SPECIES_DIR)
        
        # Save new image
        filename = await save_upload_file(file, SPECIES_DIR)
        species_db.image_url = filename
        
        session.add(species_db)
        session.commit()
        session.refresh(species_db)
        
        return {
            "message": "Image uploaded successfully",
            "filename": filename,
            "url": get_file_url(filename, "species")
        }


@app.delete("/api/species/{species_id}/image", status_code=204, tags=["Species Images"])
def delete_species_image(
    species_id: int,
    current_user: User = Depends(get_current_user),
):
    """Delete the image from a species (requires authentication)"""
    with Session(engine) as session:
        species_db = session.get(SpeciesDB, species_id)
        if species_db is None:
            raise HTTPException(status_code=404, detail="Species not found")
        
        if not species_db.image_url:
            raise HTTPException(status_code=404, detail="No image to delete")
        
        # Delete file
        delete_file(species_db.image_url, SPECIES_DIR)
        
        # Update database
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
    """
    Get current weather for any location by coordinates.
    
    Example: Get weather for Tunis
    - latitude: 36.8065
    - longitude: 10.1815
    """
    weather_data = await get_weather_for_location(latitude, longitude)
    
    if "error" in weather_data:
        raise HTTPException(status_code=503, detail=weather_data)
    
    return weather_data


@app.get("/api/parks/{park_id}/weather", tags=["Weather"])
async def get_park_weather(park_id: int):
    """
    Get current weather for a specific park.
    
    Returns real-time weather data including temperature, conditions, and forecast.
    """
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
            "weather": weather_data
        }


@app.get("/api/parks/{park_id}/forecast", tags=["Weather"])
async def get_park_forecast(park_id: int, days: int = 5):
    """
    Get weather forecast for a specific park (up to 5 days).
    """
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
            "forecast": forecast_data
        }


# ---------- MAP & DIRECTIONS ENDPOINTS ----------

@app.get("/map", response_class=HTMLResponse, tags=["Maps & Navigation"])
async def view_interactive_map(request: Request):
    """
    View an interactive map with all national parks.
    
    Features:
    - 🗺️ Interactive map with all parks marked
    - 📍 Click markers to see park details
    - 🌤️ Real-time weather for each park
    - 🧭 Get directions from your current location
    - 📱 Mobile-friendly and responsive
    
    This uses OpenStreetMap (free, no API key needed).
    """
    return templates.TemplateResponse("map.html", {"request": request})


@app.get("/api/parks/{park_id}/map", response_model=MapData, tags=["Maps & Navigation"])
def get_park_map_data(park_id: int):
    """
    Get map data for a specific park.
    
    Returns coordinates and links to Google Maps for viewing and directions.
    """
    with Session(engine) as session:
        park = session.get(ParkDB, park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")
        
        # Generate Google Maps URLs
        google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
        directions_url = f"https://www.google.com/maps/dir/?api=1&destination={park.latitude},{park.longitude}"
        
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
    """
    Get map data for all parks.
    
    Useful for displaying all parks on a single map.
    """
    with Session(engine) as session:
        parks = session.exec(select(ParkDB)).all()
        
        parks_data = []
        for park in parks:
            google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
            directions_url = f"https://www.google.com/maps/dir/?api=1&destination={park.latitude},{park.longitude}"
            
            parks_data.append({
                "park_id": park.id,
                "park_name": park.name,
                "latitude": park.latitude,
                "longitude": park.longitude,
                "governorate": park.governorate,
                "google_maps_url": google_maps_url,
                "directions_url": directions_url,
                "description": park.description[:100] + "..." if len(park.description) > 100 else park.description,
            })
        
        return {
            "total_parks": len(parks_data),
            "parks": parks_data
        }


@app.post("/api/maps/directions", tags=["Maps & Navigation"])
def get_directions_to_park(directions: DirectionsRequest):
    """
    Get directions from a specific location to a park.
    
    Provide your current location coordinates and the park ID.
    Returns a Google Maps directions URL.
    """
    with Session(engine) as session:
        park = session.get(ParkDB, directions.destination_park_id)
        if park is None:
            raise HTTPException(status_code=404, detail="Park not found")
        
        # Generate directions URL with origin and destination
        directions_url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={directions.origin_lat},{directions.origin_lng}"
            f"&destination={park.latitude},{park.longitude}"
            f"&travelmode=driving"
        )
        
        return {
            "park_id": park.id,
            "park_name": park.name,
            "origin": {
                "latitude": directions.origin_lat,
                "longitude": directions.origin_lng
            },
            "destination": {
                "latitude": park.latitude,
                "longitude": park.longitude
            },
            "directions_url": directions_url,
            "google_maps_url": f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
        }


# ---------- FILTER & SEARCH ENDPOINTS ----------

@app.get("/api/parks/filter", response_model=List[Park], tags=["Maps & Navigation"])
def filter_parks(
    governorate: str | None = None,
    min_area_km2: float | None = None,
    max_area_km2: float | None = None,
):
    """
    Filter parks by various criteria.
    
    Filters:
    - **governorate**: Filter by governorate name (e.g., "Bizerte", "Kasserine")
    - **min_area_km2**: Minimum park area in square kilometers
    - **max_area_km2**: Maximum park area in square kilometers
    """
    with Session(engine) as session:
        statement = select(ParkDB)
        
        if governorate:
            statement = statement.where(ParkDB.governorate.ilike(f"%{governorate}%"))
        
        if min_area_km2 is not None:
            statement = statement.where(ParkDB.area_km2 >= min_area_km2)
        
        if max_area_km2 is not None:
            statement = statement.where(ParkDB.area_km2 <= max_area_km2)
        
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


@app.get("/api/parks/search", response_model=SearchResult, tags=["Maps & Navigation"])
def search_parks(q: str):
    """
    Search parks by name, description, or governorate.
    
    Example searches:
    - "Ichkeul" - Find Ichkeul park
    - "Bizerte" - Find parks in Bizerte
    - "cerf" - Find parks with deer (cerf)
    - "desert" - Find desert parks
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    with Session(engine) as session:
        search_term = f"%{q}%"
        statement = select(ParkDB).where(
            (ParkDB.name.ilike(search_term)) |
            (ParkDB.description.ilike(search_term)) |
            (ParkDB.governorate.ilike(search_term))
        )
        
        parks_db = session.exec(statement).all()
        
        parks = [
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
        
        return SearchResult(
            total_results=len(parks),
            parks=parks
        )


@app.get("/api/governorates", tags=["Maps & Navigation"])
def list_governorates():
    """
    Get list of all governorates that have national parks.
    
    Useful for filtering parks by region.
    """
    with Session(engine) as session:
        parks = session.exec(select(ParkDB)).all()
        governorates = sorted(set(p.governorate for p in parks))
        
        # Count parks per governorate
        gov_counts = {}
        for park in parks:
            gov_counts[park.governorate] = gov_counts.get(park.governorate, 0) + 1
        
        return {
            "total_governorates": len(governorates),
            "governorates": [
                {
                    "name": gov,
                    "park_count": gov_counts[gov]
                }
                for gov in governorates
            ]
        }


@app.post("/api/maps/multi-park-route", response_model=MultiParkRouteResponse, tags=["Maps & Navigation"])
def plan_multi_park_route(route_request: MultiParkRoute):
    """
    Plan a route visiting multiple parks in order.
    
    Provide a list of park IDs in the order you want to visit them.
    Returns a route with distance estimates and Google Maps link.
    
    Example: Visit Ichkeul, then Boukornine, then Zaghouan
    """
    if not route_request.park_ids or len(route_request.park_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least 2 park IDs for route planning"
        )
    
    with Session(engine) as session:
        route_points = []
        total_distance = 0.0
        
        for i, park_id in enumerate(route_request.park_ids):
            park = session.get(ParkDB, park_id)
            if not park:
                raise HTTPException(
                    status_code=404,
                    detail=f"Park with ID {park_id} not found"
                )
            
            google_maps_url = f"https://www.google.com/maps?q={park.latitude},{park.longitude}"
            
            route_points.append(
                RoutePoint(
                    order=i + 1,
                    park_id=park.id,
                    park_name=park.name,
                    latitude=park.latitude,
                    longitude=park.longitude,
                    governorate=park.governorate,
                    google_maps_url=google_maps_url,
                )
            )
            
            # Calculate distance to next park (simple Euclidean distance)
            if i > 0:
                prev_park = session.get(ParkDB, route_request.park_ids[i - 1])
                if prev_park:
                    # Rough distance calculation (1 degree ≈ 111 km)
                    lat_diff = park.latitude - prev_park.latitude
                    lng_diff = park.longitude - prev_park.longitude
                    distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111
                    total_distance += distance
        
        # Estimate driving time (average 60 km/h)
        estimated_hours = total_distance / 60.0
        
        # Build Google Maps multi-stop route URL
        waypoints = []
        for point in route_points[1:-1]:  # Middle points as waypoints
            waypoints.append(f"{point.latitude},{point.longitude}")
        
        origin = route_points[0]
        destination = route_points[-1]
        
        maps_url = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin.latitude},{origin.longitude}"
            f"&destination={destination.latitude},{destination.longitude}"
        )
        
        if waypoints:
            maps_url += f"&waypoints={"|".join(waypoints)}"
        
        maps_url += "&travelmode=driving"
        
        return MultiParkRouteResponse(
            total_parks=len(route_points),
            total_distance_km=round(total_distance, 2),
            estimated_time_hours=round(estimated_hours, 2),
            route_points=route_points,
            google_maps_url=maps_url,
        )


# ---------- ROUTE & EMERGENCY ----------

class RouteInfo(BaseModel):
    park_id: int
    park_name: str
    governorate: str
    latitude: float
    longitude: float
    nearest_city: str
    travel_advice: str
    safety_tips: List[str]


def build_route_info(park: ParkDB) -> RouteInfo:
    if "Ichkeul" in park.name:
        nearest_city = "Bizerte"
        travel_advice = (
            "From Tunis, drive north towards Bizerte (A4), then follow signs to "
            "Ichkeul National Park. Plan 1.5–2 hours by car."
        )
    elif "Chaambi" in park.name:
        nearest_city = "Kasserine"
        travel_advice = (
            "From Kasserine, follow the main road south-west towards Chaambi National Park. "
            "Check current security advice before travelling in this region."
        )
    else:
        nearest_city = park.governorate
        travel_advice = (
            "Use a navigation app or local directions to reach the park from the nearest town."
        )

    safety_tips = [
        "Check current security and access rules for the park before your trip.",
        "Tell someone your route and expected return time.",
        "Take enough water, sun protection, and a fully charged phone.",
        "Stay on marked trails and respect park rules about waste and wildlife.",
        "Avoid hiking alone late in the day; plan to leave before dark where parks have closing hours.",
    ]

    return RouteInfo(
        park_id=park.id,
        park_name=park.name,
        governorate=park.governorate,
        latitude=park.latitude,
        longitude=park.longitude,
        nearest_city=nearest_city,
        travel_advice=travel_advice,
        safety_tips=safety_tips,
    )


@app.get("/api/parks/{park_id}/route", response_model=RouteInfo, tags=["Routes & Emergency"])
def get_route_for_park(park_id: int):
    """
    Get travel directions and safety tips for a specific park.
    
    Provides nearest city, travel advice, and safety recommendations.
    """
    with Session(engine) as session:
        park_db = session.get(ParkDB, park_id)
        if park_db is None:
            raise HTTPException(status_code=404, detail="Park not found")

        return build_route_info(park_db)


class EmergencyRequest(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    park_id: int | None = None
    situation: str


class EmergencyResponse(BaseModel):
    message: str
    recommended_actions: List[str]
    emergency_numbers: dict
    park_info: dict | None = None


@app.post("/api/emergency", response_model=EmergencyResponse, tags=["Routes & Emergency"])
def handle_emergency(payload: EmergencyRequest):
    """
    Report an emergency situation.
    
    Provides emergency contact numbers and recommended actions.
    Include GPS coordinates and/or park_id for better assistance.
    """
    emergency_numbers = {
        "international": 112,
        "ambulance_samu": 190,
        "police": 197,
        "fire": 198,
    }

    park_info = None
    message_prefix = "Emergency reported."

    with Session(engine) as session:
        if payload.park_id is not None:
            park = session.get(ParkDB, payload.park_id)
            if park:
                park_info = {
                    "park_id": park.id,
                    "park_name": park.name,
                    "governorate": park.governorate,
                    "latitude": park.latitude,
                    "longitude": park.longitude,
                }
                message_prefix = f"Emergency near {park.name}."

    recommended_actions = [
        "If you or someone with you is in immediate danger or has a serious injury, call the appropriate emergency number now (190 ambulance, 197 police, 198 fire, or 112).",
        "Describe your location as clearly as possible: nearest town or road, park name, and any visible landmarks.",
        "If you have a GPS location on your phone or app, read the coordinates slowly to the operator.",
        "Unless you are in immediate danger (rockfall, fire, flooding), stay where you are after calling so rescuers can find you more easily.",
        "Conserve phone battery: close non-essential apps, lower screen brightness, and keep the phone for emergency calls and navigation only.",
        "Keep warm, hydrated, and sheltered while you wait for help; use extra clothes or a space blanket if you have one.",
    ]

    if payload.latitude is not None and payload.longitude is not None:
        recommended_actions.append(
            "Write down or screenshot your GPS coordinates so you can repeat them to emergency services if the call drops."
        )

    if park_info:
        recommended_actions.append(
            "Tell the operator you are in or near this park, and mention any official trail names or access roads you used."
        )

    message = f"{message_prefix} Stay calm and contact local emergency services."

    return EmergencyResponse(
        message=message,
        recommended_actions=recommended_actions,
        emergency_numbers=emergency_numbers,
        park_info=park_info,
    )
