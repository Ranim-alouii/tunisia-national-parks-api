#!/usr/bin/env python3
"""
Test script to verify that parks now have real external images
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_park_images():
    """Test that parks now have external images instead of placeholders"""
    print("🖼️ Testing Park Images - External vs Placeholder")
    print("=" * 60)

    try:
        # Get parks data from API
        response = requests.get(f"{BASE_URL}/api/parks", timeout=10)
        parks = response.json()

        if not parks:
            print("❌ No parks data received")
            return False

        print(f"📸 Testing {len(parks)} parks for image presence...")

        parks_with_images = 0
        parks_with_external_images = 0
        parks_with_placeholders = 0

        for park in parks:
            park_name = park.get('name', 'Unknown')
            images = park.get('images', [])

            if images and len(images) > 0:
                parks_with_images += 1

                # Check if images are external (not local paths)
                first_image = images[0] if isinstance(images, list) else images

                if isinstance(first_image, str):
                    if first_image.startswith('http') and 'wikipedia' in first_image:
                        parks_with_external_images += 1
                        print(f"✅ {park_name}: External Wikipedia image loaded")
                    elif first_image.startswith('https://via.placeholder.com'):
                        parks_with_placeholders += 1
                        print(f"⚠️  {park_name}: Still using placeholder")
                    elif first_image.startswith('http'):
                        parks_with_external_images += 1
                        print(f"✅ {park_name}: External image loaded")
                    else:
                        print(f"ℹ️  {park_name}: Local image: {first_image[:50]}...")
                else:
                    print(f"⚠️  {park_name}: Invalid image format")
            else:
                print(f"❌ {park_name}: No images")

        print("\n" + "=" * 60)
        print(f"📊 IMAGE ANALYSIS RESULTS:")
        print(f"   • Total Parks: {len(parks)}")
        print(f"   • Parks with Images: {parks_with_images}")
        print(f"   • Parks with External Images: {parks_with_external_images}")
        print(f"   • Parks with Placeholders: {parks_with_placeholders}")

        success_rate = parks_with_external_images / len(parks) * 100

        if success_rate >= 90:
            print(f"\n🎉 SUCCESS: {success_rate:.1f}% of parks now have external images!")
            print("\n🌐 Sample External Images Added:")
            for park in parks[:3]:  # Show first 3
                images = park.get('images', [])
                if images and len(images) > 0:
                    first_image = images[0] if isinstance(images, list) else images
                    if isinstance(first_image, str) and first_image.startswith('http'):
                        print(f"   • {park.get('name', 'Unknown')}: {first_image[:80]}...")

            return True
        else:
            print(f"\n⚠️  Only {success_rate:.1f}% of parks have external images")
            return False

    except Exception as e:
        print(f"❌ Error testing park images: {e}")
        return False

if __name__ == "__main__":
    test_park_images()
