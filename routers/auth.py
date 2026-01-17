"""
Authentication router
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from datetime import datetime, timezone
from models import UserDB, ParkDB
from database import engine
from config import settings
from utils import get_password_hash, verify_password, create_access_token, get_file_url

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ---------- AUTH MODELS ----------

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str | None = None

class UserLogin(BaseModel):
    username: str
    password: str

# ---------- AUTH FUNCTIONS ----------

def get_user(username: str) -> UserInDB | None:
    """Get user from database."""
    with Session(engine) as session:
        user_db = session.exec(
            select(UserDB).where(UserDB.username == username)
        ).first()

        if user_db:
            return UserInDB(
                username=user_db.username,
                full_name=user_db.full_name,
                disabled=not user_db.is_active,
                hashed_password=user_db.hashed_password,
            )
    return None

def authenticate_user(username: str, password: str) -> UserInDB | None:
    """Authenticate a user."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# ---------- DEPENDENCIES ----------

from fastapi import HTTPException, Depends
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None or user.disabled:
        raise credentials_exception
    return User(username=user.username, full_name=user.full_name, disabled=user.disabled)

# ---------- AUTH ENDPOINTS ----------

@router.post("/register", response_model=UserDB, status_code=201)
def register_user(user_in: UserCreate):
    """Register a new user account."""
    with Session(engine) as session:
        # Check if user already exists
        existing_user = session.exec(
            select(UserDB).where(UserDB.username == user_in.username)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        existing_email = session.exec(
            select(UserDB).where(UserDB.email == user_in.email)
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_in.password)
        user_db = UserDB(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            favorite_parks=[],
            badges_earned=[],
            total_visits=0,
            joined_date=datetime.now(timezone.utc).isoformat(),
            is_active=True,
            role="user",
            hashed_password=hashed_password
        )

        session.add(user_db)
        session.commit()
        session.refresh(user_db)

        # Return user data without password
        return UserDB(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            full_name=user_db.full_name,
            avatar_url=user_db.avatar_url,
            bio=user_db.bio,
            location=user_db.location,
            favorite_parks=user_db.favorite_parks,
            badges_earned=user_db.badges_earned,
            total_visits=user_db.total_visits,
            joined_date=user_db.joined_date,
            is_active=user_db.is_active,
            role=user_db.role
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login to get an access token using credentials.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserDB)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile information."""
    with Session(engine) as session:
        user_db = session.exec(
            select(UserDB).where(UserDB.username == current_user.username)
        ).first()

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        return UserDB(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            full_name=user_db.full_name,
            avatar_url=user_db.avatar_url,
            bio=user_db.bio,
            location=user_db.location,
            favorite_parks=user_db.favorite_parks,
            badges_earned=user_db.badges_earned,
            total_visits=user_db.total_visits,
            joined_date=user_db.joined_date,
            is_active=user_db.is_active,
            role=user_db.role
        )

@router.put("/me", response_model=UserDB)
def update_user_profile(user_update: dict, current_user: User = Depends(get_current_user)):
    """Update current user profile."""
    with Session(engine) as session:
        user_db = session.exec(
            select(UserDB).where(UserDB.username == current_user.username)
        ).first()

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        # Update allowed fields
        allowed_fields = ["full_name", "bio", "location", "avatar_url"]
        for field in allowed_fields:
            if field in user_update:
                setattr(user_db, field, user_update[field])

        session.add(user_db)
        session.commit()
        session.refresh(user_db)

        return UserDB(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            full_name=user_db.full_name,
            avatar_url=user_db.avatar_url,
            bio=user_db.bio,
            location=user_db.location,
            favorite_parks=user_db.favorite_parks,
            badges_earned=user_db.badges_earned,
            total_visits=user_db.total_visits,
            joined_date=user_db.joined_date,
            is_active=user_db.is_active,
            role=user_db.role
        )

@router.post("/favorites/{park_id}")
def add_park_to_favorites(park_id: int, current_user: User = Depends(get_current_user)):
    """Add a park to user's favorites."""
    with Session(engine) as session:
        user_db = session.exec(
            select(UserDB).where(UserDB.username == current_user.username)
        ).first()

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify park exists
        park = session.get(ParkDB, park_id)
        if not park:
            raise HTTPException(status_code=404, detail="Park not found")

        if park_id not in user_db.favorite_parks:
            user_db.favorite_parks.append(park_id)
            session.add(user_db)
            session.commit()

        return {"message": "Park added to favorites", "favorites": user_db.favorite_parks}

@router.delete("/favorites/{park_id}")
def remove_park_from_favorites(park_id: int, current_user: User = Depends(get_current_user)):
    """Remove a park from user's favorites."""
    with Session(engine) as session:
        user_db = session.exec(
            select(UserDB).where(UserDB.username == current_user.username)
        ).first()

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        if park_id in user_db.favorite_parks:
            user_db.favorite_parks.remove(park_id)
            session.add(user_db)
            session.commit()

        return {"message": "Park removed from favorites", "favorites": user_db.favorite_parks}

@router.get("/favorites")
def get_user_favorites(current_user: User = Depends(get_current_user)):
    """Get user's favorite parks with details."""
    with Session(engine) as session:
        user_db = session.exec(
            select(UserDB).where(UserDB.username == current_user.username)
        ).first()

        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")

        if not user_db.favorite_parks:
            return {"favorites": [], "total": 0}

        parks_db = session.exec(
            select(ParkDB).where(ParkDB.id.in_(user_db.favorite_parks))
        ).all()

        favorites = [
            {
                "id": p.id,
                "name": p.name,
                "governorate": p.governorate,
                "area_km2": p.area_km2,
                "average_rating": p.average_rating,
                "images": [get_file_url(img, "parks") for img in (p.images or [])],
            }
            for p in parks_db
        ]

        return {"favorites": favorites, "total": len(favorites)}

# ---------- DEPENDENCIES ----------

from fastapi import HTTPException, Depends
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None or user.disabled:
        raise credentials_exception
    return User(username=user.username, full_name=user.full_name, disabled=user.disabled)
