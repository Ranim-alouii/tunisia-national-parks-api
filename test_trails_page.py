#!/usr/bin/env python3
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_trails_page():
    print("🧪 Testing Trails Page Display...")

    # Set up headless browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)

        # Load the trails page
        print("Loading trails page...")
        driver.get("http://localhost:8001/trails")

        # Wait for JavaScript to load
        time.sleep(5)

        # Check for JavaScript errors
        logs = driver.get_log('browser')
        if logs:
            print("❌ JavaScript errors found:")
            for log in logs:
                print(f"  {log['level']}: {log['message']}")
        else:
            print("✅ No JavaScript errors detected")

        # Check if trails are displayed
        trails_grid = driver.find_element_by_id("trailsGrid")
        if trails_grid:
            trail_cards = driver.find_elements_by_class_name("card")
            print(f"✅ Found {len(trail_cards)} trail cards displayed")

            if len(trail_cards) > 0:
                # Check first trail card
                first_card = trail_cards[0]
                card_text = first_card.text
                print(f"Sample trail card content: {card_text[:200]}...")
            else:
                print("❌ No trail cards found in grid")

                # Check what's actually in the grid
                grid_content = trails_grid.text
                print(f"Grid content: '{grid_content[:300]}...'")

        else:
            print("❌ Trails grid not found")

        driver.quit()
        return len(trail_cards) > 0 if 'trail_cards' in locals() else False

    except Exception as e:
        print(f"❌ Error testing page: {e}")
        return False

if __name__ == "__main__":
    success = test_trails_page()
    print("\n" + "=" * 50)
    if success:
        print("✅ Trails page is working correctly")
    else:
        print("❌ Trails page has issues - check JavaScript errors")
