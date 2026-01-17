#!/usr/bin/env python3
"""
Create sample images for demonstration
This will create placeholder images you can manually place in upload directories
"""

import os
from PIL import Image, ImageDraw, ImageFont
import shutil

def create_sample_image(text, width=800, height=600, bg_color=(34, 139, 34), text_color=(255, 255, 255)):
    """Create a sample image with text."""
    # Create image
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Try to use a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text
    draw.text((x, y), text, fill=text_color, font=font)

    return img

def create_sample_images():
    """Create sample images for parks and species."""

    # Create uploads directory structure
    base_dir = "uploads"
    park_dir = os.path.join(base_dir, "parks")
    species_dir = os.path.join(base_dir, "species")

    for directory in [park_dir, species_dir]:
        os.makedirs(directory, exist_ok=True)

    # Sample park images
    park_images = {
        "ichkeul_park_1.jpg": "Ichkeul Lake",
        "ichkeul_park_2.jpg": "Ichkeul Wetlands",
        "boukornine_park_1.jpg": "Boukornine Forest",
        "zaghouan_park_1.jpg": "Zaghouan Spring",
        "chambi_park_1.jpg": "Chambi Mountain",
        "bouhedma_park_1.jpg": "Bouhedma Desert",
    }

    # Sample species images
    species_images = {
        "flamingo_species.jpg": "Greater Flamingo",
        "gazelle_species.jpg": "Dorcas Gazelle",
        "eagle_species.jpg": "Bonelli's Eagle",
        "hedgehog_species.jpg": "North African Hedgehog",
        "ibex_species.jpg": "Nubian Ibex",
        "lynx_species.jpg": "Caracal",
    }

    print("🎨 Creating sample images...")

    # Create park images
    for filename, park_name in park_images.items():
        img = create_sample_image(park_name, bg_color=(34, 139, 34))
        filepath = os.path.join(park_dir, filename)
        img.save(filepath, "JPEG", quality=85)
        print(f"✅ Created: {filepath}")

    # Create species images
    for filename, species_name in species_images.items():
        img = create_sample_image(species_name, bg_color=(139, 69, 19))
        filepath = os.path.join(species_dir, filename)
        img.save(filepath, "JPEG", quality=85)
        print(f"✅ Created: {filepath}")

    print("\n📁 Manual Upload Instructions:")
    print("1. Copy park images to: uploads/parks/")
    print("2. Copy species images to: uploads/species/")
    print("3. Rename files with park/species IDs")
    print("4. Example:")
    print("   - ichkeul_park_1.jpg → uploads/parks/1/ichkeul_park_1.jpg")
    print("   - flamingo_species.jpg → uploads/species/1/flamingo_species.jpg")

    print("\n🔗 File URLs will be:")
    print("   - Park images: http://127.0.0.1:8000/uploads/parks/1/filename.jpg")
    print("   - Species images: http://127.0.0.1:8000/uploads/species/1/filename.jpg")

if __name__ == "__main__":
    create_sample_images()
