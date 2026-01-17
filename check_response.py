#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8001"

def check_response(url):
    print(f"Checking: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")

        # Check first 200 characters
        content = response.text[:200]
        print(f"First 200 chars: {repr(content)}")

        # Check if it's HTML
        if "<!DOCTYPE html>" in content:
            print("✅ Contains HTML DOCTYPE")
        else:
            print("❌ No HTML DOCTYPE found")

        if "<html" in content:
            print("✅ Contains HTML tag")
        else:
            print("❌ No HTML tag found")

        if "<body" in content:
            print("✅ Contains BODY tag")
        else:
            print("❌ No BODY tag found")

        return response.status_code == 200 and "<!DOCTYPE html>" in content

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking response content")
    print("=" * 50)

    result = check_response(BASE_URL + "/parks")
    print(f"\nResult: {'✅ Working' if result else '❌ Not working'}")
