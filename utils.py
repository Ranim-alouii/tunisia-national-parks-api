import uuid
import shutil
from pathlib import Path
from typing import List
from datetime import timedelta

from fastapi import UploadFile, HTTPException
from PIL import Image


# Upload directories
UPLOAD_DIR = Path("uploads")
PARKS_DIR = UPLOAD_DIR / "parks"
SPECIES_DIR = UPLOAD_DIR / "species"

# Create directories if they do not exist
UPLOAD_DIR.mkdir(exist_ok=True)
PARKS_DIR.mkdir(exist_ok=True)
SPECIES_DIR.mkdir(exist_ok=True)

# Allowed file extensions and max size
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file type and content type."""
    file_ext = _get_file_extension(file.filename or "")
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image",
        )


async def save_upload_file(file: UploadFile, destination: Path) -> str:
    """Save uploaded file to destination directory after validation and optimization."""
    validate_image(file)

    # Generate unique filename
    file_ext = _get_file_extension(file.filename or "file")
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = destination / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        optimize_image(file_path)
        return unique_filename
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    finally:
        file.file.close()


def optimize_image(file_path: Path, max_width: int = 1200) -> None:
    """Optimize image size and quality to reduce storage and bandwidth."""
    try:
        with Image.open(file_path) as img:
            # Normalize to RGB if needed
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background

            # Resize if wider than max_width
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            img.save(file_path, quality=85, optimize=True)
    except Exception as e:
        # Non-fatal: keep original image if optimization fails
        print(f"Warning: Could not optimize image {file_path}: {e}")


def delete_file(filename: str, directory: Path) -> None:
    """Delete a file from uploads directory."""
    file_path = directory / filename
    if file_path.exists():
        file_path.unlink()


def get_file_url(filename: str, file_type: str) -> str:
    """Generate URL for uploaded file."""
    if filename and filename.startswith("http"):
        return filename  # External URL
    return f"/uploads/{file_type}/{filename}"


# Password hashing utilities
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    from jose import jwt
    from config import settings
    from datetime import datetime, timezone, timedelta

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
