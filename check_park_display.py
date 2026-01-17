#!/usr/bin/env python3
"""
Check if all parks are displaying images on the frontend
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8001"

def check_parks_display():
    """Check if all parks are displaying images on the /parks page"""
    print("🏞️ Checking Park Images Display on Frontend")
    print("=" * 60)

    try:
        # Get the parks page
        response = requests.get(f"{BASE_URL}/parks", timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to load parks page: {response.status_code}")
            return False

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all park cards
        park_cards = soup.find_all('div', class_='card')

        if not park_cards:
            print("❌ No park cards found on the page")
            return False

        print(f"📋 Found {len(park_cards)} park cards on the page")

        parks_with_images = 0
        parks_with_placeholders = 0
        parks_without_images = 0

        for i, card in enumerate(park_cards):
            # Find the park name
            title_elem = card.find('h3')
            park_name = title_elem.text.strip() if title_elem else f"Park {i+1}"

            # Find the image
            img_elem = card.find('img')

            if img_elem:
                img_src = img_elem.get('src', '')

                if img_src.startswith('https://via.placeholder.com'):
                    parks_with_placeholders += 1
                    print(f"⚠️  {park_name}: Using placeholder image")
                elif img_src.startswith('http'):
                    parks_with_images += 1
                    print(f"✅ {park_name}: Displaying external image")
                elif img_src.startswith('/uploads/'):
                    parks_with_images += 1
                    print(f"✅ {park_name}: Displaying local image")
                else:
                    parks_without_images += 1
                    print(f"❓ {park_name}: Unknown image source: {img_src[:50]}...")
            else:
                parks_without_images += 1
                print(f"❌ {park_name}: No image element found")

        print("\n" + "=" * 60)
        print("📊 PARK DISPLAY RESULTS:")
        print(f"   • Total Parks Displayed: {len(park_cards)}")
        print(f"   • Parks with Images: {parks_with_images}")
        print(f"   • Parks with Placeholders: {parks_with_placeholders}")
        print(f"   • Parks without Images: {parks_without_images}")

        success_rate = parks_with_images / len(park_cards) * 100

        if success_rate >= 90:
            print(f"\n🎉 SUCCESS: {success_rate:.1f}% of parks are displaying images!")
            return True
        else:
            print(f"\n⚠️  Only {success_rate:.1f}% of parks have images displayed")
            return False

    except Exception as e:
        print(f"❌ Error checking park display: {e}")
        return False

if __name__ == "__main__":
    check_parks_display()
