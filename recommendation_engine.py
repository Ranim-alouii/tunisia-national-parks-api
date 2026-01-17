#!/usr/bin/env python3
"""
Eco-Tourism & Safety Recommendation Engine
Calculates park visit suitability based on weather, health profile, and park characteristics.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import math

@dataclass
class WeatherData:
    """Weather data structure"""
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    uv_index: Optional[float] = None
    pollen_count: Optional[int] = None
    air_quality_index: Optional[int] = None

@dataclass
class HealthProfile:
    """User health profile"""
    allergies: List[str]
    pollen_allergy: bool
    insect_sting_allergy: bool
    asthma: bool
    heart_condition: bool
    high_blood_pressure: bool
    diabetes: bool
    mobility_issues: bool
    physical_stamina: str  # "low", "medium", "high"
    walking_distance_limit: Optional[int]  # meters
    preferred_terrain: Optional[str]  # "flat", "hilly", "mountainous"

@dataclass
class ParkData:
    """Park characteristics"""
    name: str
    difficulty_level: Optional[str]  # "facile", "modéré", "difficile"
    elevation_gain: Optional[int]  # meters
    average_trail_length: Optional[float]  # km
    has_water_sources: bool
    has_shade_areas: bool
    has_emergency_services: bool

@dataclass
class SuitabilityScore:
    """Visit suitability result"""
    can_visit: bool
    score: float  # 0-100
    status: str  # "recommended", "caution", "not_recommended"
    reasons: List[str]
    safety_tips: List[str]
    alternative_times: List[str]

class VisitSuitabilityEngine:
    """Engine for calculating park visit suitability"""

    # Weather thresholds
    HIGH_HEAT_THRESHOLD = 35.0  # Celsius
    LOW_HEAT_THRESHOLD = 5.0   # Celsius
    HIGH_HUMIDITY_THRESHOLD = 80  # %
    LOW_PRESSURE_THRESHOLD = 1000  # hPa
    HIGH_WIND_THRESHOLD = 15.0  # m/s
    HIGH_UV_THRESHOLD = 8
    HIGH_POLLEN_THRESHOLD = 100

    # Health risk factors
    def __init__(self):
        self.risk_factors = {
            "extreme_heat": {
                "asthma": 0.8,
                "heart_condition": 0.9,
                "high_blood_pressure": 0.7,
                "diabetes": 0.6
            },
            "high_humidity": {
                "asthma": 0.7,
                "diabetes": 0.5
            },
            "low_pressure": {
                "asthma": 0.6,
                "heart_condition": 0.8,
                "high_blood_pressure": 0.7
            },
            "high_wind": {
                "asthma": 0.5,
                "mobility_issues": 0.6
            },
            "extreme_cold": {
                "heart_condition": 0.8,
                "high_blood_pressure": 0.7
            },
            "high_uv": {
                "general": 0.3
            },
            "high_pollen": {
                "pollen_allergy": 0.9,
                "asthma": 0.6
            }
        }

    def calculate_suitability(
        self,
        weather: WeatherData,
        health_profile: HealthProfile,
        park: ParkData,
        user_location: Optional[Tuple[float, float]] = None,
        park_location: Optional[Tuple[float, float]] = None
    ) -> SuitabilityScore:
        """
        Calculate visit suitability score

        Args:
            weather: Current weather conditions
            health_profile: User's health profile
            park: Park characteristics
            user_location: (lat, lng) of user
            park_location: (lat, lng) of park

        Returns:
            SuitabilityScore with recommendations
        """

        reasons = []
        safety_tips = []
        alternative_times = []
        risk_score = 0.0

        # Weather-based assessments
        weather_risks = self._assess_weather_risks(weather, health_profile)
        risk_score += weather_risks["score"]
        reasons.extend(weather_risks["reasons"])
        safety_tips.extend(weather_risks["tips"])
        alternative_times.extend(weather_risks["alternatives"])

        # Physical capability assessment
        physical_risks = self._assess_physical_risks(park, health_profile)
        risk_score += physical_risks["score"]
        reasons.extend(physical_risks["reasons"])
        safety_tips.extend(physical_risks["tips"])

        # Distance assessment
        if user_location and park_location:
            distance_risks = self._assess_distance_risks(user_location, park_location, health_profile)
            risk_score += distance_risks["score"]
            reasons.extend(distance_risks["reasons"])

        # Calculate final score (0-100, higher is better)
        final_score = max(0, 100 - risk_score)

        # Determine status
        if final_score >= 80:
            status = "recommended"
            can_visit = True
        elif final_score >= 60:
            status = "caution"
            can_visit = True
        else:
            status = "not_recommended"
            can_visit = False

        # Add general safety tips
        safety_tips.extend([
            "Stay hydrated and drink water regularly",
            "Wear appropriate clothing and sun protection",
            "Carry a charged phone and emergency contacts",
            "Inform someone about your plans",
            "Know the location of emergency services"
        ])

        # Remove duplicates
        reasons = list(set(reasons))
        safety_tips = list(set(safety_tips))
        alternative_times = list(set(alternative_times))

        return SuitabilityScore(
            can_visit=can_visit,
            score=final_score,
            status=status,
            reasons=reasons,
            safety_tips=safety_tips,
            alternative_times=alternative_times
        )

    def _assess_weather_risks(self, weather: WeatherData, health: HealthProfile) -> Dict:
        """Assess weather-related health risks"""
        reasons = []
        tips = []
        alternatives = []
        score = 0

        # Temperature risks
        if weather.temperature > self.HIGH_HEAT_THRESHOLD:
            score += 30
            reasons.append("Extreme heat conditions detected")
            tips.extend([
                "Avoid outdoor activities during peak heat hours (10 AM - 4 PM)",
                "Wear light, breathable clothing",
                "Take frequent breaks in shaded areas"
            ])
            alternatives.extend(["Visit early morning or evening", "Choose indoor activities"])

            if health.asthma or health.heart_condition:
                score += 20
                reasons.append("High heat particularly dangerous for your health conditions")

        elif weather.temperature < self.LOW_HEAT_THRESHOLD:
            score += 20
            reasons.append("Cold weather conditions")
            tips.extend([
                "Dress in warm layers",
                "Protect extremities from frostbite"
            ])

        # Humidity risks
        if weather.humidity > self.HIGH_HUMIDITY_THRESHOLD:
            score += 15
            reasons.append("High humidity levels")
            if health.asthma:
                score += 15
                reasons.append("High humidity may trigger asthma symptoms")
                tips.append("Carry rescue inhaler and avoid strenuous activities")

        # Pressure risks (particularly important for blood pressure)
        if weather.pressure < self.LOW_PRESSURE_THRESHOLD:
            score += 25
            reasons.append("Low atmospheric pressure")
            if health.high_blood_pressure or health.heart_condition:
                score += 20
                reasons.append("Low pressure may affect cardiovascular health")
                tips.extend([
                    "Monitor blood pressure regularly",
                    "Avoid sudden position changes",
                    "Take medication as prescribed"
                ])

        # Wind risks
        if weather.wind_speed > self.HIGH_WIND_THRESHOLD:
            score += 10
            reasons.append("Strong wind conditions")
            tips.append("Be cautious of falling branches and reduced visibility")

        # UV risks
        if weather.uv_index and weather.uv_index > self.HIGH_UV_THRESHOLD:
            score += 15
            reasons.append("High UV radiation")
            tips.extend([
                "Apply high SPF sunscreen",
                "Wear protective clothing and sunglasses",
                "Stay in shaded areas during peak sun hours"
            ])

        # Pollen/Allergy risks
        if weather.pollen_count and weather.pollen_count > self.HIGH_POLLEN_THRESHOLD:
            if health.pollen_allergy:
                score += 40
                reasons.append("High pollen count - severe allergy risk")
                tips.extend([
                    "Take antihistamines before visiting",
                    "Wear protective mask if available",
                    "Consider rescheduling if symptoms are severe"
                ])
                alternatives.append("Visit during low pollen seasons")

        # Air quality
        if weather.air_quality_index and weather.air_quality_index > 100:
            score += 20
            reasons.append("Poor air quality")
            if health.asthma or health.heart_condition:
                score += 15
                tips.extend([
                    "Wear N95 mask if available",
                    "Limit outdoor time",
                    "Monitor respiratory symptoms"
                ])

        return {
            "score": score,
            "reasons": reasons,
            "tips": tips,
            "alternatives": alternatives
        }

    def _assess_physical_risks(self, park: ParkData, health: HealthProfile) -> Dict:
        """Assess physical capability risks"""
        reasons = []
        tips = []
        score = 0

        # Difficulty level assessment
        if park.difficulty_level == "difficile":
            score += 20
            reasons.append("Park has difficult terrain")
            if health.physical_stamina == "low" or health.mobility_issues:
                score += 25
                reasons.append("Terrain difficulty exceeds your physical capabilities")
                tips.extend([
                    "Consider easier park alternatives",
                    "Consult with physician before attempting",
                    "Bring appropriate mobility aids"
                ])

        elif park.difficulty_level == "modéré":
            score += 10
            if health.physical_stamina == "low":
                score += 15

        # Elevation assessment
        if park.elevation_gain and park.elevation_gain > 500:
            score += 15
            reasons.append("Significant elevation gain required")
            if health.heart_condition or health.high_blood_pressure:
                score += 20
                reasons.append("Elevation may affect cardiovascular health")
                tips.extend([
                    "Ascend slowly to avoid altitude sickness",
                    "Stop and rest frequently",
                    "Monitor heart rate and breathing"
                ])

        # Distance assessment
        if park.average_trail_length and health.walking_distance_limit:
            max_distance = health.walking_distance_limit / 1000  # Convert to km
            if park.average_trail_length > max_distance:
                score += 25
                reasons.append("Trail length exceeds your walking limit")
                tips.extend([
                    "Choose shorter trails or park sections",
                    "Plan for rest stops and return transportation",
                    "Consider park shuttle services if available"
                ])

        # Terrain preference
        if health.preferred_terrain and park.difficulty_level:
            if health.preferred_terrain == "flat" and park.difficulty_level in ["modéré", "difficile"]:
                score += 10
                reasons.append("Terrain type may not match your preferences")

        return {
            "score": score,
            "reasons": reasons,
            "tips": tips
        }

    def _assess_distance_risks(self, user_loc: Tuple[float, float],
                              park_loc: Tuple[float, float],
                              health: HealthProfile) -> Dict:
        """Assess travel distance risks"""
        reasons = []
        score = 0

        # Calculate distance (simplified Haversine formula)
        lat1, lon1 = user_loc
        lat2, lon2 = park_loc

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = 6371 * c  # Earth radius in km

        # Distance-based recommendations
        if distance_km > 100:
            score += 15
            reasons.append("Park is located far from your position")
        elif distance_km > 50:
            score += 10
            reasons.append("Moderate distance to park")

        # Travel time consideration for health conditions
        if distance_km > 50 and (health.heart_condition or health.mobility_issues):
            score += 10
            reasons.append("Long travel distance may be fatiguing")

        return {
            "score": score,
            "reasons": reasons
        }

    def get_weather_warnings(self, weather: WeatherData) -> List[str]:
        """Get specific weather warnings"""
        warnings = []

        if weather.temperature > self.HIGH_HEAT_THRESHOLD:
            warnings.append("Extreme heat warning: Stay hydrated and avoid peak sun hours")
        if weather.temperature < self.LOW_HEAT_THRESHOLD:
            warnings.append("Cold weather warning: Dress warmly and protect extremities")
        if weather.humidity > self.HIGH_HUMIDITY_THRESHOLD:
            warnings.append("High humidity warning: May cause discomfort and breathing difficulties")
        if weather.pressure < self.LOW_PRESSURE_THRESHOLD:
            warnings.append("Low pressure warning: May affect those with cardiovascular conditions")
        if weather.wind_speed > self.HIGH_WIND_THRESHOLD:
            warnings.append("High wind warning: Exercise caution with visibility and stability")
        if weather.uv_index and weather.uv_index > self.HIGH_UV_THRESHOLD:
            warnings.append("High UV warning: Use sun protection and limit sun exposure")
        if weather.pollen_count and weather.pollen_count > self.HIGH_POLLEN_THRESHOLD:
            warnings.append("High pollen warning: May trigger allergies and respiratory issues")

        return warnings

    def suggest_alternative_parks(self, current_park: ParkData,
                                all_parks: List[ParkData],
                                weather: WeatherData,
                                health: HealthProfile) -> List[ParkData]:
        """Suggest alternative parks based on conditions"""
        alternatives = []

        for park in all_parks:
            if park.name == current_park.name:
                continue

            # Calculate suitability for this park
            suitability = self.calculate_suitability(weather, health, park)

            # Include parks with higher suitability scores
            if suitability.score > 70:
                alternatives.append((park, suitability.score))

        # Sort by suitability score
        alternatives.sort(key=lambda x: x[1], reverse=True)

        return [park for park, score in alternatives[:3]]  # Top 3 alternatives


# Global instance for easy access
visit_engine = VisitSuitabilityEngine()


def calculate_visit_suitability(weather_data: dict, health_profile: dict,
                              park_data: dict) -> dict:
    """
    Main function to calculate visit suitability

    Args:
        weather_data: Dictionary with weather information
        health_profile: Dictionary with user health information
        park_data: Dictionary with park information

    Returns:
        Dictionary with suitability assessment
    """

    # Convert dictionaries to data classes
    weather = WeatherData(**weather_data)
    health = HealthProfile(**health_profile)
    park = ParkData(**park_data)

    # Calculate suitability
    result = visit_engine.calculate_suitability(weather, health, park)

    # Return as dictionary
    return {
        "can_visit": result.can_visit,
        "suitability_score": result.score,
        "status": result.status,
        "risk_reasons": result.reasons,
        "safety_tips": result.safety_tips,
        "alternative_times": result.alternative_times,
        "weather_warnings": visit_engine.get_weather_warnings(weather)
    }


if __name__ == "__main__":
    # Example usage
    weather = WeatherData(
        temperature=38.0,
        humidity=85,
        pressure=995,
        wind_speed=8.0,
        uv_index=9,
        pollen_count=150
    )

    health = HealthProfile(
        allergies=["peanuts", "dust"],
        pollen_allergy=True,
        insect_sting_allergy=False,
        asthma=True,
        heart_condition=False,
        high_blood_pressure=True,
        diabetes=False,
        mobility_issues=False,
        physical_stamina="medium",
        walking_distance_limit=5000,
        preferred_terrain="flat"
    )

    park = ParkData(
        name="Ichkeul National Park",
        difficulty_level="modéré",
        elevation_gain=300,
        average_trail_length=8.0,
        has_water_sources=True,
        has_shade_areas=True,
        has_emergency_services=True
    )

    result = visit_engine.calculate_suitability(weather, health, park)

    print(f"Can Visit: {result.can_visit}")
    print(f"Score: {result.score}")
    print(f"Status: {result.status}")
    print("Reasons:", result.reasons)
    print("Safety Tips:", result.safety_tips)
