import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Custom icons for map markers
const createCustomIcon = (color) => new Icon({
  iconUrl: `data:image/svg+xml;base64,${btoa(`
    <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
      <path d="M12.5 0C5.596 0 0 5.596 0 12.5c0 2.5 0.75 4.83 2.02 6.81L12.5 41l10.48-21.69C22.25 17.33 23 14.99 23 12.5 23 5.596 17.404 0 10.5 0z" fill="${color}"/>
      <circle cx="12.5" cy="12.5" r="5" fill="white"/>
    </svg>
  `)}`,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [0, -41]
});

const ParkComparisonDashboard = ({ userHealthProfile, userLocation }) => {
  const [parks, setParks] = useState([]);
  const [selectedParks, setSelectedParks] = useState([]);
  const [comparisonData, setComparisonData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('suitability');
  const [filterCriteria, setFilterCriteria] = useState({
    maxDistance: 100,
    difficulty: 'all',
    hasEmergency: false
  });

  // Status color mapping
  const statusColors = {
    recommended: '#10b981',
    caution: '#f59e0b',
    not_recommended: '#ef4444'
  };

  // Status labels
  const statusLabels = {
    recommended: 'Recommandé',
    caution: 'Avec précaution',
    not_recommended: 'Non recommandé'
  };

  useEffect(() => {
    loadParksWithSuitability();
  }, [userHealthProfile, userLocation]);

  const loadParksWithSuitability = async () => {
    try {
      setLoading(true);

      // Fetch parks
      const parksResponse = await fetch('/api/parks');
      const parksData = await parksResponse.json();

      // Get current weather (you would integrate with actual weather API)
      const weatherResponse = await fetch('/api/weather/current');
      const weatherData = await weatherResponse.json();

      // Calculate suitability for each park
      const parksWithSuitability = parksData.map(park => {
        const suitability = calculateVisitSuitability(weatherData, userHealthProfile, park, userLocation);
        return {
          ...park,
          suitability
        };
      });

      setParks(parksWithSuitability);
    } catch (error) {
      console.error('Error loading parks:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateVisitSuitability = (weather, health, park, userLoc) => {
    // This would call your backend recommendation engine
    // For demo purposes, we'll simulate the calculation
    return {
      can_visit: Math.random() > 0.3,
      suitability_score: Math.floor(Math.random() * 100),
      status: Math.random() > 0.6 ? 'recommended' : Math.random() > 0.3 ? 'caution' : 'not_recommended',
      risk_reasons: ['High temperature', 'Distance from location'],
      safety_tips: ['Stay hydrated', 'Wear sunscreen'],
      alternative_times: ['Early morning', 'Evening']
    };
  };

  const handleParkSelection = (park) => {
    if (selectedParks.find(p => p.id === park.id)) {
      setSelectedParks(selectedParks.filter(p => p.id !== park.id));
    } else if (selectedParks.length < 4) {
      setSelectedParks([...selectedParks, park]);
    }
  };

  const generateComparisonData = () => {
    if (selectedParks.length < 2) return [];

    return selectedParks.map(park => ({
      id: park.id,
      name: park.name,
      governorate: park.governorate,
      area_km2: park.area_km2,
      difficulty_level: park.difficulty_level,
      suitability_score: park.suitability.suitability_score,
      status: park.suitability.status,
      distance: calculateDistance(userLocation, [park.latitude, park.longitude]),
      species_count: park.species_count || 0,
      trails_count: park.trails_count || 0,
      average_rating: park.average_rating || 0
    }));
  };

  const calculateDistance = (loc1, loc2) => {
    // Haversine formula for distance calculation
    const R = 6371; // Earth's radius in km
    const dLat = (loc2[0] - loc1[0]) * Math.PI / 180;
    const dLon = (loc2[1] - loc1[1]) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(loc1[0] * Math.PI / 180) * Math.cos(loc2[0] * Math.PI / 180) *
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return (R * c).toFixed(1);
  };

  const sortComparisonData = (data) => {
    return [...data].sort((a, b) => {
      switch (sortBy) {
        case 'suitability':
          return b.suitability_score - a.suitability_score;
        case 'distance':
          return parseFloat(a.distance) - parseFloat(b.distance);
        case 'rating':
          return b.average_rating - a.average_rating;
        case 'area':
          return b.area_km2 - a.area_km2;
        default:
          return 0;
      }
    });
  };

  const filteredParks = parks.filter(park => {
    const distance = calculateDistance(userLocation, [park.latitude, park.longitude]);
    const meetsDistance = parseFloat(distance) <= filterCriteria.maxDistance;
    const meetsDifficulty = filterCriteria.difficulty === 'all' || park.difficulty_level === filterCriteria.difficulty;
    const meetsEmergency = !filterCriteria.hasEmergency || park.has_emergency_services;

    return meetsDistance && meetsDifficulty && meetsEmergency;
  });

  const comparisonDataSorted = sortComparisonData(generateComparisonData());

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Comparaison des Parcs</h1>
              <p className="text-gray-600 mt-1">Comparez jusqu'à 4 parcs selon vos critères de santé et préférences</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                {filteredParks.length} parcs trouvés
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Filtres</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Distance maximale (km)
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="200"
                    value={filterCriteria.maxDistance}
                    onChange={(e) => setFilterCriteria({...filterCriteria, maxDistance: e.target.value})}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="text-sm text-gray-500 mt-1">{filterCriteria.maxDistance} km</div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Difficulté
                  </label>
                  <select
                    value={filterCriteria.difficulty}
                    onChange={(e) => setFilterCriteria({...filterCriteria, difficulty: e.target.value})}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Toutes</option>
                    <option value="facile">Facile</option>
                    <option value="modéré">Modéré</option>
                    <option value="difficile">Difficile</option>
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="emergency"
                    checked={filterCriteria.hasEmergency}
                    onChange={(e) => setFilterCriteria({...filterCriteria, hasEmergency: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="emergency" className="ml-2 text-sm text-gray-700">
                    Services d'urgence uniquement
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">

            {/* Park Selection */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Sélectionnez des parcs à comparer ({selectedParks.length}/4)
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
                {filteredParks.slice(0, 20).map(park => (
                  <div
                    key={park.id}
                    onClick={() => handleParkSelection(park)}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedParks.find(p => p.id === park.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{park.name}</h4>
                        <p className="text-sm text-gray-600">{park.governorate}</p>
                        <div className="flex items-center mt-2">
                          <div
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: statusColors[park.suitability.status] }}
                          ></div>
                          <span className="text-sm text-gray-600">
                            {statusLabels[park.suitability.status]}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {park.suitability.suitability_score}/100
                        </div>
                        <div className="text-xs text-gray-500">
                          {calculateDistance(userLocation, [park.latitude, park.longitude])} km
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Comparison Results */}
            {selectedParks.length >= 2 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Résultats de comparaison
                  </h3>

                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="suitability">Trier par adéquation</option>
                    <option value="distance">Trier par distance</option>
                    <option value="rating">Trier par note</option>
                    <option value="area">Trier par superficie</option>
                  </select>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Parc
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Statut
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Score
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Distance
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Espèces
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Sentiers
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {comparisonDataSorted.map((park, index) => (
                        <tr key={park.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{park.name}</div>
                              <div className="text-sm text-gray-500">{park.governorate}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              style={{
                                backgroundColor: `${statusColors[park.status]}20`,
                                color: statusColors[park.status]
                              }}
                            >
                              {statusLabels[park.status]}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {park.suitability_score}/100
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {park.distance} km
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {park.species_count}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {park.trails_count}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Map View */}
                <div className="mt-8">
                  <h4 className="text-md font-medium text-gray-900 mb-4">Carte des parcs sélectionnés</h4>
                  <div className="h-96 rounded-lg overflow-hidden border">
                    <MapContainer
                      center={userLocation}
                      zoom={8}
                      style={{ height: '100%', width: '100%' }}
                    >
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      />

                      {/* User location */}
                      <Marker position={userLocation} icon={createCustomIcon('#2563eb')}>
                        <Popup>Votre position</Popup>
                      </Marker>

                      {/* Park markers */}
                      {selectedParks.map(park => (
                        <Marker
                          key={park.id}
                          position={[park.latitude, park.longitude]}
                          icon={createCustomIcon(statusColors[park.suitability.status])}
                        >
                          <Popup>
                            <div>
                              <h3 className="font-semibold">{park.name}</h3>
                              <p className="text-sm text-gray-600">{park.governorate}</p>
                              <div className="mt-2">
                                <span
                                  className="inline-block px-2 py-1 text-xs rounded"
                                  style={{
                                    backgroundColor: `${statusColors[park.suitability.status]}20`,
                                    color: statusColors[park.suitability.status]
                                  }}
                                >
                                  {statusLabels[park.suitability.status]}
                                </span>
                              </div>
                              <p className="text-xs mt-1">
                                Score: {park.suitability.suitability_score}/100
                              </p>
                            </div>
                          </Popup>
                        </Marker>
                      ))}

                      {/* Route lines */}
                      {selectedParks.length > 1 && (
                        <Polyline
                          positions={[
                            userLocation,
                            ...selectedParks.map(park => [park.latitude, park.longitude])
                          ]}
                          color="#2563eb"
                          weight={3}
                          opacity={0.7}
                        />
                      )}
                    </MapContainer>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParkComparisonDashboard;
