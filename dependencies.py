"""
Shared dependencies for authentication
"""

from fastapi import HTTPException, Depends, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from models import UserDB
from database import get_engine
from config import settings
from schemas import User, UserInDB

# ---------- AUTH FUNCTIONS ----------

def get_user(username: str) -> UserInDB | None:
    """Get user from database."""
    with Session(get_engine()) as session:
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

# ---------- DEPENDENCIES ----------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from JWT token."""
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
