#!/usr/bin/env python3
"""
Simple test script to verify frontend routes work and show debug output.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

def test_frontend_routes():
    client = TestClient(app)

    print("Testing frontend routes with debug output...")

    # Test parks page
    print("\n=== Testing /parks ===")
    response = client.get("/parks")
    print(f"Status: {response.status_code}")
    print("Response contains 'DEBUG' messages from server logs above")

    # Test species page
    print("\n=== Testing /species ===")
    response = client.get("/species")
    print(f"Status: {response.status_code}")
    print("Response contains 'DEBUG' messages from server logs above")

    # Test trails page
    print("\n=== Testing /trails ===")
    response = client.get("/trails")
    print(f"Status: {response.status_code}")
    print("Response contains 'DEBUG' messages from server logs above")

    # Test docs page
    print("\n=== Testing /docs ===")
    response = client.get("/docs")
    print(f"Status: {response.status_code}")
    print("Response contains 'DEBUG' messages from server logs above")

if __name__ == "__main__":
    test_frontend_routes()
