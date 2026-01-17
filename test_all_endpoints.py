#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Tests all Tunisia National Parks API endpoints systematically
"""

import requests
import json
import time
from typing import Dict, List, Tuple
import sys

BASE_URL = "http://localhost:8002"
TIMEOUT = 10

class EndpointTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []

    def log_result(self, endpoint: str, method: str, status_code: int, success: bool, error: str = None):
        """Log test result"""
        result = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'success': success,
            'error': error
        }
        self.results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print("15")

    def test_endpoint(self, endpoint: str, method: str = "GET", params: Dict = None,
                     data: Dict = None, json_data: Dict = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            kwargs = {'timeout': TIMEOUT}

            if params:
                kwargs['params'] = params
            if data:
                kwargs['data'] = data
            if json_data:
                kwargs['json'] = json_data

            response = self.session.request(method, url, **kwargs)

            success = response.status_code == expected_status
            error = None if success else f"Expected {expected_status}, got {response.status_code}"

            self.log_result(endpoint, method, response.status_code, success, error)
            return success

        except Exception as e:
            self.log_result(endpoint, method, 0, False, str(e))
            return False

    def test_all_endpoints(self):
        """Test all API endpoints systematically"""
        print("🚀 Starting Comprehensive API Endpoint Testing")
        print("=" * 70)

        # Health Check
        print("\n🏥 HEALTH CHECKS")
        self.test_endpoint("/health")
        self.test_endpoint("/api/health")

        # Parks Endpoints
        print("\n🏞️ PARKS ENDPOINTS")
        self.test_endpoint("/api/parks", params={'limit': 5})
        self.test_endpoint("/api/parks/1")
        self.test_endpoint("/api/parks/compare", params={'park_ids': '1,2'})

        # Species Endpoints
        print("\n🦌 SPECIES ENDPOINTS")
        self.test_endpoint("/api/species", params={'limit': 3})
        self.test_endpoint("/api/species/1")
        self.test_endpoint("/api/parks/1/species")

        # Search Endpoints
        print("\n🔍 SEARCH ENDPOINTS")
        self.test_endpoint("/api/search/parks", params={'query': 'nature'})
        self.test_endpoint("/api/search/species", params={'query': 'flamingo'})
        self.test_endpoint("/api/search/suggestions", params={'query': 'ichkeul'})

        # Maps & Navigation
        print("\n🗺️ MAPS & NAVIGATION")
        self.test_endpoint("/api/parks/1/map")
        self.test_endpoint("/api/maps/all-parks")

        # Weather Integration
        print("\n🌤️ WEATHER INTEGRATION")
        self.test_endpoint("/api/parks/1/weather")
        self.test_endpoint("/api/parks/1/forecast", params={'days': 3})

        # Media & Images
        print("\n📸 MEDIA & IMAGES")
        self.test_endpoint("/api/parks/1/unsplash-images", params={'count': 2})

        # Content & News
        print("\n📰 CONTENT & NEWS")
        self.test_endpoint("/api/news/parks", params={'count': 3})
        self.test_endpoint("/api/parks/1/nearby-places", params={'place_type': 'restaurant'})

        # Chat
        print("\n💬 CHAT ENDPOINT")
        self.test_endpoint("/api/chat", method="POST", json_data={'message': 'Hello'})

        # Analytics
        print("\n📊 ANALYTICS")
        self.test_endpoint("/api/analytics/overview")

        # Language Support
        print("\n🌐 INTERNATIONALIZATION")
        self.test_endpoint("/api/languages")

        # Media Config
        print("\n⚙️ MEDIA CONFIGURATION")
        self.test_endpoint("/api/media/config")

        # Frontend Pages (HTML responses - expect 200)
        print("\n🌐 FRONTEND PAGES")
        frontend_pages = ['/', '/parks', '/species', '/map', '/comparison', '/emergency', '/chat', '/upload']
        for page in frontend_pages:
            self.test_endpoint(page)

        # Documentation
        print("\n📚 DOCUMENTATION")
        self.test_endpoint("/docs")
        self.test_endpoint("/redoc")

        # Static Files
        print("\n📁 STATIC FILES")
        static_files = ['/static/css/main.css', '/static/js/app.js']
        for static_file in static_files:
            self.test_endpoint(static_file)

        return self.generate_report()

    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{'='*70}")
        print("📊 FINAL TEST REPORT")
        print(f"{'='*70}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(".1f")
        print(f"{'='*70}")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  {result['method']} {result['endpoint']} - {result['error']}")

        # Group results by category
        categories = {
            'Health': ['/health', '/api/health'],
            'Parks': ['/api/parks', '/api/parks/1', '/api/parks/compare'],
            'Species': ['/api/species', '/api/species/1', '/api/parks/1/species'],
            'Search': ['/api/search/parks', '/api/search/species', '/api/search/suggestions'],
            'Maps': ['/api/parks/1/map', '/api/maps/all-parks'],
            'Weather': ['/api/parks/1/weather', '/api/parks/1/forecast'],
            'Media': ['/api/parks/1/unsplash-images'],
            'Content': ['/api/news/parks', '/api/parks/1/nearby-places'],
            'Chat': ['/api/chat'],
            'Analytics': ['/api/analytics/overview'],
            'Languages': ['/api/languages'],
            'Media Config': ['/api/media/config'],
            'Frontend': ['/', '/parks', '/species', '/map', '/comparison', '/emergency', '/chat', '/upload'],
            'Docs': ['/docs', '/redoc'],
            'Static': ['/static/css/main.css', '/static/js/app.js']
        }

        print("\n📈 CATEGORY BREAKDOWN:")
        for category, endpoints in categories.items():
            cat_results = [r for r in self.results if any(ep in r['endpoint'] for ep in endpoints)]
            if cat_results:
                cat_passed = sum(1 for r in cat_results if r['success'])
                cat_total = len(cat_results)
                cat_rate = (cat_passed / cat_total * 100) if cat_total > 0 else 0
                status = "✅" if cat_rate == 100 else "⚠️" if cat_rate >= 80 else "❌"
                print("20")

        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'results': self.results
        }

def main():
    """Main test function"""
    tester = EndpointTester()
    report = tester.test_all_endpoints()

    # Exit with appropriate code
    if report['success_rate'] == 100.0:
        print("\n🎉 ALL TESTS PASSED! API is fully functional.")
        sys.exit(0)
    elif report['success_rate'] >= 90.0:
        print(f"\n⚠️ MOST TESTS PASSED ({report['success_rate']}%). Minor issues detected.")
        sys.exit(1)
    else:
        print(f"\n❌ SIGNIFICANT ISSUES DETECTED ({report['success_rate']}%). API needs attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()
