import os
import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
from PIL import Image

# Create uploads directory structure
UPLOAD_DIR = Path("uploads")
PARKS_DIR = UPLOAD_DIR / "parks"
SPECIES_DIR = UPLOAD_DIR / "species"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
PARKS_DIR.mkdir(exist_ok=True)
SPECIES_DIR.mkdir(exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )


async def save_upload_file(file: UploadFile, destination: Path) -> str:
    """Save uploaded file to destination directory"""
    validate_image(file)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = destination / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Optimize image size
        optimize_image(file_path)
        
        return unique_filename
    except Exception as e:
        # Clean up if something goes wrong
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    finally:
        file.file.close()


def optimize_image(file_path: Path, max_width: int = 1200) -> None:
    """Optimize image size and quality"""
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            
            # Resize if too large
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized
            img.save(file_path, quality=85, optimize=True)
    except Exception as e:
        print(f"Warning: Could not optimize image {file_path}: {e}")


def delete_file(filename: str, directory: Path) -> None:
    """Delete a file from uploads directory"""
    file_path = directory / filename
    if file_path.exists():
        file_path.unlink()


def get_file_url(filename: str, file_type: str) -> str:
    """Generate URL for uploaded file"""
    return f"/uploads/{file_type}/{filename}"
