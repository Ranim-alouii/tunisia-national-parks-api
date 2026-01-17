"""
Eco-Tourism Recommendation Engine for Tunisia National Parks
Advanced suitability scoring and park comparison algorithms
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from models import (
    SuitabilityScore, ParkComparison, WeatherData,
    HealthProfileDB, ParkDB, UserDB
)


@dataclass
class VisitRecommendation:
    """Complete visit recommendation with detailed analysis"""
    park_id: int
    park_name: str
    suitability_score: SuitabilityScore
    weather_data: Optional[WeatherData] = None
    distance_km: float = 0.0
    travel_time_minutes: int = 0
    recommended_activities: List[str] = None
    safety_notes: List[str] = None
    alternative_parks: List[dict] = None

    def __post_init__(self):
        if self.recommended_activities is None:
            self.recommended_activities = []
        if self.safety_notes is None:
            self.safety_notes = []
        if self.alternative_parks is None:
            self.alternative_parks = []


class EcoTourismRecommendationEngine:
    """
    Advanced recommendation engine for eco-tourism suitability scoring
    Considers weather, health, terrain, distance, and biodiversity factors
    """

    def __init__(self):
        self.weather_weights = {
            'temperature': 0.25,
            'humidity': 0.20,
            'wind_speed': 0.15,
            'visibility': 0.15,
            'uv_index': 0.15,
            'air_quality': 0.10
        }

        self.health_weights = {
            'asthma': 0.30,
            'allergies': 0.25,
            'heart_condition': 0.20,
            'mobility': 0.15,
            'stamina': 0.10
        }

        self.terrain_weights = {
            'difficulty': 0.40,
            'elevation': 0.30,
            'accessibility': 0.20,
            'trail_length': 0.10
        }

    def calculate_visit_suitability(
        self,
        park: ParkDB,
        user_health: HealthProfileDB,
        weather_data: Optional[WeatherData] = None,
        user_location: Optional[Tuple[float, float]] = None
    ) -> VisitRecommendation:
        """
        Main algorithm for calculating park visit suitability

        Algorithm considers:
        1. Weather conditions (25% weight)
        2. User health profile (30% weight)
        3. Terrain difficulty (20% weight)
        4. Distance from user (15% weight)
        5. Biodiversity/activity match (10% weight)
        """

        # Calculate individual component scores
        weather_score, weather_reasons = self._calculate_weather_score(weather_data, user_health)
        health_score, health_reasons = self._calculate_health_score(user_health, park, weather_data)
        terrain_score, terrain_reasons = self._calculate_terrain_score(park, user_health)
        distance_score, distance_km, travel_time = self._calculate_distance_score(park, user_location)
        activity_score, activity_reasons = self._calculate_activity_score(park, user_health)

        # Weighted overall score
        overall_score = (
            weather_score * 0.25 +
            health_score * 0.30 +
            terrain_score * 0.20 +
            distance_score * 0.15 +
            activity_score * 0.10
        )

        # Determine status based on score
        if overall_score >= 75:
            status = "recommended"
        elif overall_score >= 50:
            status = "caution"
        else:
            status = "not_recommended"

        # Compile all reasons
        all_reasons = []
        all_reasons.extend(weather_reasons)
        all_reasons.extend(health_reasons)
        all_reasons.extend(terrain_reasons)

        if distance_km > 0:
            all_reasons.append(f"Distance: {distance_km:.1f} km away")

        all_reasons.extend(activity_reasons)

        # Create suitability score object
        suitability = SuitabilityScore(
            score=round(overall_score, 1),
            status=status,
            reasons=all_reasons,
            weather_score=weather_score,
            health_score=health_score,
            distance_score=distance_score,
            terrain_score=terrain_score
        )

        # Generate recommendations and safety notes
        recommended_activities = self._generate_activity_recommendations(park, user_health, weather_data)
        safety_notes = self._generate_safety_notes(park, user_health, weather_data)

        return VisitRecommendation(
            park_id=park.id,
            park_name=park.name,
            suitability_score=suitability,
            weather_data=weather_data,
            distance_km=distance_km,
            travel_time_minutes=travel_time,
            recommended_activities=recommended_activities,
            safety_notes=safety_notes
        )

    def _calculate_weather_score(
        self,
        weather: Optional[WeatherData],
        health: HealthProfileDB
    ) -> Tuple[float, List[str]]:
        """Calculate weather suitability score (0-100)"""
        if not weather:
            return 70.0, ["Weather data not available - moderate conditions assumed"]

        reasons = []
        score = 100.0

        # Temperature analysis
        temp_score = self._score_temperature(weather.temperature, health.asthma or health.heart_condition)
        score = min(score, temp_score)
        if temp_score < 80:
            reasons.append(f"Temperature {weather.temperature}°C may be challenging")

        # Humidity analysis
        humidity_score = self._score_humidity(weather.humidity, health.asthma or health.allergies)
        score = min(score, humidity_score)
        if humidity_score < 80:
            reasons.append(f"Humidity {weather.humidity}% may affect comfort")

        # Wind speed analysis
        wind_score = self._score_wind(weather.wind_speed, health.asthma)
        score = min(score, wind_score)
        if wind_score < 80:
            reasons.append(f"Wind speed {weather.wind_speed} m/s may be uncomfortable")

        # Visibility analysis
        visibility_score = self._score_visibility(weather.visibility)
        score = min(score, visibility_score)
        if visibility_score < 80:
            reasons.append(f"Visibility {weather.visibility} km may limit enjoyment")

        # UV Index analysis
        if weather.uv_index and weather.uv_index > 7:
            score -= 15
            reasons.append(f"High UV index ({weather.uv_index}) - use sun protection")

        # Air Quality analysis
        if weather.air_quality_index and weather.air_quality_index > 100:
            score -= 20
            reasons.append(f"Poor air quality (AQI: {weather.air_quality_index})")

        return round(score, 1), reasons

    def _calculate_health_score(
        self,
        health: HealthProfileDB,
        park: ParkDB,
        weather: Optional[WeatherData]
    ) -> Tuple[float, List[str]]:
        """Calculate health compatibility score (0-100)"""
        reasons = []
        score = 100.0

        # Asthma considerations
        if health.asthma:
            score -= 20
            reasons.append("Asthma condition requires caution")

            if weather and weather.humidity > 70:
                score -= 15
                reasons.append("High humidity may trigger asthma symptoms")

            if weather and weather.air_quality_index and weather.air_quality_index > 100:
                score -= 20
                reasons.append("Poor air quality may affect breathing")

        # Allergy considerations
        if health.pollen_allergy or health.allergies:
            score -= 15
            reasons.append("Allergy considerations - check pollen forecasts")

            # Check if park has high pollen seasons
            if park.best_months:
                try:
                    best_months = json.loads(park.best_months)
                    current_month = datetime.now().month
                    if current_month in best_months:
                        score -= 10
                        reasons.append("Current season may have high pollen counts")
                except:
                    pass

        # Heart condition considerations
        if health.heart_condition:
            score -= 25
            reasons.append("Heart condition requires medical clearance")

            if park.elevation_max and park.elevation_max > 2000:
                score -= 15
                reasons.append("High elevation may affect heart condition")

        # Mobility considerations
        if health.mobility_issues:
            score -= 30
            reasons.append("Mobility issues - check accessibility")

            if park.difficulty_level in ['difficile']:
                score -= 20
                reasons.append("Park terrain may be challenging for mobility")

        # Physical stamina considerations
        if health.physical_stamina == 'low':
            score -= 15
            reasons.append("Low stamina - consider shorter activities")

            if park.area_km2 and park.area_km2 > 50:
                score -= 10
                reasons.append("Large park area may require significant walking")

        # Walking distance limit
        if health.walking_distance_limit:
            max_distance = health.walking_distance_limit / 1000  # Convert to km
            if park.area_km2 and park.area_km2 > max_distance:
                score -= 20
                reasons.append(f"Park size exceeds recommended walking limit")

        return max(0, round(score, 1)), reasons

    def _calculate_terrain_score(
        self,
        park: ParkDB,
        health: HealthProfileDB
    ) -> Tuple[float, List[str]]:
        """Calculate terrain suitability score (0-100)"""
        reasons = []
        score = 100.0

        # Difficulty level analysis
        if park.difficulty_level == 'difficile':
            score -= 30
            reasons.append("Difficult terrain - advanced preparation required")
        elif park.difficulty_level == 'modéré':
            score -= 15
            reasons.append("Moderate terrain - good fitness recommended")
        else:
            reasons.append("Easy terrain - suitable for most visitors")

        # Elevation analysis
        if park.elevation_max:
            if park.elevation_max > 3000:
                score -= 25
                reasons.append("Very high elevation - altitude sickness risk")
            elif park.elevation_max > 2000:
                score -= 15
                reasons.append("High elevation - acclimatization recommended")
            elif park.elevation_max > 1000:
                score -= 5
                reasons.append("Moderate elevation")

        # Terrain preference analysis
        if health.preferred_terrain:
            if health.preferred_terrain == 'flat' and park.difficulty_level == 'difficile':
                score -= 20
                reasons.append("Terrain may not match your preferences")
            elif health.preferred_terrain == 'mountainous' and park.difficulty_level == 'facile':
                score -= 5
                reasons.append("Terrain may be less challenging than preferred")

        # Accessibility considerations
        if health.mobility_issues and not park.accessibility:
            score -= 25
            reasons.append("Limited accessibility information available")

        return max(0, round(score, 1)), reasons

    def _calculate_distance_score(
        self,
        park: ParkDB,
        user_location: Optional[Tuple[float, float]]
    ) -> Tuple[float, float, int]:
        """Calculate distance-based score and travel time"""
        if not user_location:
            return 70.0, 0.0, 0  # Neutral score when location unknown

        user_lat, user_lng = user_location
        park_lat, park_lng = park.latitude, park.longitude

        # Calculate distance using Haversine formula
        distance_km = self._calculate_distance(user_lat, user_lng, park_lat, park_lng)

        # Estimate travel time (rough approximation: 50 km/h average speed)
        travel_time_minutes = int((distance_km / 50) * 60)

        # Score based on distance (closer is better)
        if distance_km <= 10:
            score = 100.0
        elif distance_km <= 50:
            score = 90.0
        elif distance_km <= 100:
            score = 75.0
        elif distance_km <= 200:
            score = 60.0
        elif distance_km <= 500:
            score = 40.0
        else:
            score = 20.0

        return round(score, 1), distance_km, travel_time_minutes

    def _calculate_activity_score(
        self,
        park: ParkDB,
        health: HealthProfileDB
    ) -> Tuple[float, List[str]]:
        """Calculate activity/biodiversity match score"""
        reasons = []
        score = 70.0  # Base score

        # Check if park has activities suitable for user's health
        if park.activities:
            try:
                activities = json.loads(park.activities)

                # Count suitable activities
                suitable_count = 0
                total_activities = len(activities)

                for activity in activities:
                    activity_lower = activity.lower()

                    # Check health compatibility
                    if health.mobility_issues and any(word in activity_lower for word in ['hiking', 'climbing', 'trekking']):
                        continue  # Skip strenuous activities

                    if health.asthma and 'swimming' in activity_lower:
                        suitable_count += 1  # Swimming might be good for asthma
                    elif health.physical_stamina == 'low' and any(word in activity_lower for word in ['bird watching', 'photography', 'picnic']):
                        suitable_count += 1  # Low-impact activities
                    elif health.physical_stamina == 'high' and any(word in activity_lower for word in ['hiking', 'climbing']):
                        suitable_count += 1  # High-impact activities
                    else:
                        suitable_count += 0.5  # Partially suitable

                if total_activities > 0:
                    activity_ratio = suitable_count / total_activities
                    score = 50 + (activity_ratio * 50)  # 50-100 range

                    if activity_ratio > 0.7:
                        reasons.append("Excellent activity match for your profile")
                    elif activity_ratio > 0.4:
                        reasons.append("Good variety of suitable activities")
                    else:
                        reasons.append("Limited activities match your preferences")

            except json.JSONDecodeError:
                reasons.append("Activity information available")

        return round(score, 1), reasons

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _score_temperature(self, temp: float, has_respiratory_condition: bool) -> float:
        """Score temperature suitability"""
        if has_respiratory_condition:
            # More restrictive for respiratory conditions
            if 18 <= temp <= 24:
                return 100.0
            elif 15 <= temp <= 27:
                return 80.0
            elif 10 <= temp <= 30:
                return 60.0
            else:
                return 30.0
        else:
            # Normal range
            if 15 <= temp <= 28:
                return 100.0
            elif 10 <= temp <= 32:
                return 80.0
            elif 5 <= temp <= 35:
                return 60.0
            else:
                return 30.0

    def _score_humidity(self, humidity: int, has_asthma: bool) -> float:
        """Score humidity suitability"""
        if has_asthma:
            if humidity <= 50:
                return 100.0
            elif humidity <= 65:
                return 70.0
            elif humidity <= 80:
                return 40.0
            else:
                return 20.0
        else:
            if humidity <= 70:
                return 100.0
            elif humidity <= 80:
                return 80.0
            elif humidity <= 90:
                return 60.0
            else:
                return 40.0

    def _score_wind(self, wind_speed: float, has_asthma: bool) -> float:
        """Score wind speed suitability"""
        if has_asthma:
            if wind_speed <= 10:
                return 100.0
            elif wind_speed <= 15:
                return 70.0
            elif wind_speed <= 20:
                return 40.0
            else:
                return 20.0
        else:
            if wind_speed <= 15:
                return 100.0
            elif wind_speed <= 25:
                return 80.0
            elif wind_speed <= 35:
                return 60.0
            else:
                return 40.0

    def _score_visibility(self, visibility: float) -> float:
        """Score visibility suitability"""
        if visibility >= 10:
            return 100.0
        elif visibility >= 5:
            return 80.0
        elif visibility >= 2:
            return 60.0
        else:
            return 30.0

    def _generate_activity_recommendations(
        self,
        park: ParkDB,
        health: HealthProfileDB,
        weather: Optional[WeatherData]
    ) -> List[str]:
        """Generate personalized activity recommendations"""
        recommendations = []

        if not park.activities:
            return ["Explore at your own pace", "Enjoy nature photography"]

        try:
            activities = json.loads(park.activities)

            # Filter activities based on health and weather
            for activity in activities:
                activity_lower = activity.lower()

                # Skip unsuitable activities for health conditions
                if health.mobility_issues and any(word in activity_lower for word in ['hiking', 'climbing', 'trekking']):
                    continue

                if health.asthma and weather and weather.humidity > 80:
                    if 'swimming' not in activity_lower:  # Swimming might help with humidity
                        continue

                if health.heart_condition and any(word in activity_lower for word in ['climbing', 'high altitude']):
                    continue

                # Add suitable activities
                if health.physical_stamina == 'low':
                    if any(word in activity_lower for word in ['bird watching', 'photography', 'picnic', 'relaxation']):
                        recommendations.append(activity)
                elif health.physical_stamina == 'high':
                    if any(word in activity_lower for word in ['hiking', 'climbing', 'trekking']):
                        recommendations.append(activity)
                else:
                    recommendations.append(activity)

        except json.JSONDecodeError:
            recommendations = ["Nature exploration", "Photography", "Relaxation"]

        return recommendations[:5]  # Limit to 5 recommendations

    def _generate_safety_notes(
        self,
        park: ParkDB,
        health: HealthProfileDB,
        weather: Optional[WeatherData]
    ) -> List[str]:
        """Generate personalized safety notes"""
        notes = []

        # Weather-based notes
        if weather:
            if weather.temperature > 30:
                notes.append("High temperature - stay hydrated and avoid prolonged sun exposure")
            elif weather.temperature < 10:
                notes.append("Cold weather - dress warmly and be prepared for temperature changes")

            if weather.humidity > 80:
                notes.append("High humidity - take breaks in shaded areas")

            if weather.uv_index and weather.uv_index > 6:
                notes.append("High UV index - use sunscreen and protective clothing")

        # Health-based notes
        if health.asthma:
            notes.append("Carry inhaler and avoid triggers like dust or strong odors")

        if health.allergies or health.pollen_allergy:
            notes.append("Check pollen forecasts and carry antihistamines if needed")

        if health.heart_condition:
            notes.append("Consult physician before strenuous activities")

        if health.mobility_issues:
            notes.append("Use accessible paths and take regular breaks")

        if health.diabetes:
            notes.append("Monitor blood sugar levels and carry snacks/medication")

        # Park-specific notes
        if park.elevation_max and park.elevation_max > 2000:
            notes.append("High altitude - watch for altitude sickness symptoms")

        if park.difficulty_level == 'difficile':
            notes.append("Challenging terrain - experienced guides recommended")

        # Emergency contact reminder
        notes.append("Save local emergency numbers: Call 190 for medical emergencies")

        return notes

    def compare_parks(
        self,
        parks: List[ParkDB],
        user_health: HealthProfileDB,
        weather_data: Optional[Dict[int, WeatherData]] = None,
        user_location: Optional[Tuple[float, float]] = None,
        sort_by: str = "suitability"
    ) -> List[ParkComparison]:
        """
        Compare multiple parks and rank them by suitability

        Args:
            parks: List of parks to compare
            user_health: User's health profile
            weather_data: Optional dict mapping park_id to weather data
            user_location: User's current location (lat, lng)
            sort_by: "suitability", "distance", "rating"

        Returns:
            Ranked list of park comparisons
        """

        comparisons = []

        for park in parks:
            weather = weather_data.get(park.id) if weather_data else None
            recommendation = self.calculate_visit_suitability(park, user_health, weather, user_location)

            comparison = ParkComparison(
                park_id=park.id,
                park_name=park.name,
                governorate=park.governorate,
                distance_km=recommendation.distance_km,
                suitability_score=recommendation.suitability_score.score,
                status=recommendation.suitability_score.status,
                weather_conditions=weather.description if weather else "Unknown",
                terrain_difficulty=park.difficulty_level or "modéré",
                estimated_travel_time=f"{recommendation.travel_time_minutes} min" if recommendation.travel_time_minutes > 0 else "Unknown"
            )

            comparisons.append(comparison)

        # Sort by requested criteria
        if sort_by == "suitability":
            comparisons.sort(key=lambda x: x.suitability_score, reverse=True)
        elif sort_by == "distance":
            comparisons.sort(key=lambda x: x.distance_km)
        elif sort_by == "rating":
            # This would need park rating data
            comparisons.sort(key=lambda x: x.suitability_score, reverse=True)

        # Assign ranks
        for i, comp in enumerate(comparisons, 1):
            comp.rank = i

        return comparisons

    def get_personalized_recommendations(
        self,
        user: UserDB,
        all_parks: List[ParkDB],
        user_health: Optional[HealthProfileDB] = None,
        user_location: Optional[Tuple[float, float]] = None,
        limit: int = 5
    ) -> List[VisitRecommendation]:
        """
        Get personalized park recommendations for a user

        Considers:
        - User's health profile
        - User's visit history and preferences
        - Current location and weather
        - User's activity patterns
        """

        if not user_health:
            # Return general recommendations if no health data
            recommendations = []
            for park in all_parks[:limit]:
                basic_score = SuitabilityScore(
                    score=70.0,
                    status="caution",
                    reasons=["Complete health profile for personalized recommendations"]
                )
                recommendation = VisitRecommendation(
                    park_id=park.id,
                    park_name=park.name,
                    suitability_score=basic_score
                )
                recommendations.append(recommendation)
            return recommendations

        # Calculate suitability for all parks
        recommendations = []
        for park in all_parks:
            recommendation = self.calculate_visit_suitability(park, user_health, None, user_location)
            recommendations.append(recommendation)

        # Sort by suitability score
        recommendations.sort(key=lambda x: x.suitability_score.score, reverse=True)

        return recommendations[:limit]


# Global instance for easy access
recommendation_engine = EcoTourismRecommendationEngine()


def calculate_visit_suitability_score(
    park: ParkDB,
    user_health: HealthProfileDB,
    weather_data: Optional[WeatherData] = None,
    user_location: Optional[Tuple[float, float]] = None
) -> VisitRecommendation:
    """
    Convenience function for calculating visit suitability

    Returns a comprehensive recommendation with:
    - Overall suitability score (0-100)
    - Status (recommended/caution/not_recommended)
    - Detailed reasons for the score
    - Personalized activity recommendations
    - Safety notes
    - Weather considerations
    - Distance and travel time estimates
    """
    return recommendation_engine.calculate_visit_suitability(
        park, user_health, weather_data, user_location
    )


def compare_parks_for_user(
    parks: List[ParkDB],
    user_health: HealthProfileDB,
    weather_data: Optional[Dict[int, WeatherData]] = None,
    user_location: Optional[Tuple[float, float]] = None
) -> List[ParkComparison]:
    """
    Compare multiple parks for a specific user

    Returns ranked comparison with suitability scores,
    distances, travel times, and recommendations
    """
    return recommendation_engine.compare_parks(
        parks, user_health, weather_data, user_location
    )


def get_can_i_visit_recommendation(
    park: ParkDB,
    user_health: HealthProfileDB,
    weather_data: Optional[WeatherData] = None
) -> Dict[str, any]:
    """
    Simple "Can I Visit?" recommendation function

    Returns:
    {
        "can_visit": bool,
        "status": "recommended|caution|not_recommended",
        "score": float,
        "reason": str,
        "safety_notes": [str],
        "recommended_activities": [str]
    }
    """

    recommendation = recommendation_engine.calculate_visit_suitability(
        park, user_health, weather_data
    )

    return {
        "can_visit": recommendation.suitability_score.status in ["recommended", "caution"],
        "status": recommendation.suitability_score.status,
        "score": recommendation.suitability_score.score,
        "reason": "; ".join(recommendation.suitability_score.reasons[:3]),  # Top 3 reasons
        "safety_notes": recommendation.safety_notes,
        "recommended_activities": recommendation.recommended_activities
    }


# Export the main functions
__all__ = [
    'calculate_visit_suitability_score',
    'compare_parks_for_user',
    'get_can_i_visit_recommendation',
    'EcoTourismRecommendationEngine',
    'VisitRecommendation'
]
