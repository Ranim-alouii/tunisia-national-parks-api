
# 🌿 Tunisia National Parks API - Enhanced Edition

A comprehensive RESTful API for Tunisia's 18 national parks, built with **FastAPI**, **SQLModel**, and **SQLite**. Features complete biodiversity database with 29 species (16 animals, 13 plants), hiking trails, user reviews, wildlife sightings, gamification, weather integration, and interactive maps.

## ✨ Features

### 🏞️ Core Functionality
- **Complete Park Database**: 18 Tunisia national parks with detailed information
- **Biodiversity Management**: 29 species (16 animals, 13 plants) with conservation data, safety guidelines, and medicinal uses
- **Image Upload**: Park and species photos with automatic optimization

### 🥾 Enhanced Features
- **Hiking Trails**: Detailed trails with difficulty, length, elevation, and GPX support
- **User Reviews**: Star ratings, comments, and park recommendations
- **Wildlife Sightings**: User-reported animal sightings with verification
- **Gamification System**: Achievement badges, points, levels, and user progression
- **Park Comparison**: Side-by-side comparison of multiple parks with interactive dashboard

### 🌤️ Advanced Integration
- **Real-time Weather**: Current conditions and 5-day forecasts for all parks
- **Interactive Maps**: OpenStreetMap integration with directions and routes
- **Multi-park Routes**: Optimized itineraries visiting multiple parks
- **Emergency System**: Location-based emergency reporting

### 🔒 Security & Performance
- **OAuth2 JWT Authentication**: Secure API access with bearer tokens
- **Request Logging**: Comprehensive middleware logging
- **CORS Support**: Cross-origin requests enabled
- **Validation**: Pydantic models with strict data validation
- **Error Handling**: Consistent JSON error responses

### 📊 Monitoring & Observability
- **Prometheus Metrics**: Comprehensive API monitoring and alerting
- **Grafana Dashboards**: Real-time visualization of system performance
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions

### 🎨 Frontend Components
- **Park Comparison Dashboard**: Interactive React component for comparing parks
- **Health Onboarding Form**: User health and preference collection for personalized recommendations

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Git**
- **Virtual Environment** (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <YOUR-REPO-URL>
   cd tunisia-national-parks-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python seed_complete_parks.py
   ```

6. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at: `http://127.0.0.1:8000`

### Interactive Documentation
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **Interactive Map**: `http://127.0.0.1:8000/map`

## 🔐 Authentication

Protected endpoints require OAuth2 JWT tokens.

### Default Admin Account
- **Username**: `admin`
- **Password**: `admin123`

### Obtaining a Token

**Via Swagger UI:**
1. Open `http://127.0.0.1:8000/docs`
2. Click **Authorize** (top right)
3. Enter admin credentials
4. Click **Authorize**

**Via API Call:**
```bash
curl -X POST "http://127.0.0.1:8000/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
```

## 📚 API Endpoints

### Parks Management
- `GET /api/parks` - List all parks
- `GET /api/parks/{id}` - Get park details
- `POST /api/parks` - Create new park (auth required)
- `PUT /api/parks/{id}` - Update park (auth required)
- `DELETE /api/parks/{id}` - Delete park (auth required)

### Species & Biodiversity
- `GET /api/species` - List all species
- `GET /api/species/{id}` - Get species details
- `GET /api/parks/{id}/species` - Species in specific park
- `POST /api/species` - Add new species (auth required)

### Enhanced Features
- `GET /api/parks/{id}/trails` - Hiking trails
- `GET /api/parks/{id}/reviews` - User reviews
- `POST /api/parks/{id}/reviews` - Add review
- `GET /api/parks/{id}/sightings` - Wildlife sightings
- `POST /api/sightings` - Report sighting

### Weather & Maps
- `GET /api/weather/current` - Weather by coordinates
- `GET /api/parks/{id}/weather` - Park weather
- `GET /api/parks/{id}/forecast` - 5-day forecast
- `GET /api/maps/all-parks` - All parks map data
- `POST /api/maps/directions` - Get directions

### Utilities
- `GET /api/health` - Health check
- `GET /map` - Interactive map view
- `GET /api/governorates` - List governorates

## 🗄️ Database Schema

The application uses **SQLModel** with **SQLite** for data persistence:

### Core Tables
- **parks**: Park information, location, images
- **species**: Fauna and flora data
- **park_species**: Many-to-many relationships

### Enhanced Tables
- **trails**: Hiking trail details
- **reviews**: User reviews and ratings
- **sightings**: Wildlife observations
- **badges**: Achievement system

## 🐳 Deployment

### Development
```bash
# Run locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
The project includes Docker and production configurations:

```bash
# Using Docker Compose
docker-compose up -d

# Or manual production setup
python main_production.py
```

### Environment Variables
Create `.env` file:
```
SECRET_KEY=your-secret-key
OPENWEATHER_API_KEY=your-weather-api-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

## 🎮 Gamification System

The platform includes a comprehensive gamification system to encourage user engagement and learning about Tunisia's natural heritage:

### Achievement Badges
- **Exploration Badges**: Visit parks, complete trails, explore different governorates
- **Conservation Badges**: Report sightings, learn about endangered species, participate in conservation
- **Social Badges**: Write reviews, share experiences, help other users
- **Expert Badges**: Master specific topics like birdwatching, medicinal plants, or local history

### Points & Levels System
- **Activity Points**: Earn points for various actions:
  - Visit a park: +25 points
  - Report a species sighting: +15 points
  - Complete a trail: +30 points
  - Write a review: +20 points
  - Report a sighting: +15 points
- **Level Progression**: Advance through levels every 100 experience points
- **Leaderboards**: Compete with other users (future feature)

### User Stats Tracking
- Parks visited, species seen, trails completed
- Reviews written, sightings reported
- Current level and experience points
- Achievement progress and badge collection

### Rewards & Incentives
- Unlock exclusive content at higher levels
- Special badges for consistent activity
- Recognition on leaderboards
- Access to expert features and tools

## 🧪 Testing

Run the seeding scripts to populate comprehensive test data:
```bash
python seed_complete_parks.py
python seed_more_species.py
python add_enhanced_data.py
```

### API Testing Examples

**Get all parks:**
```bash
curl -X GET "http://127.0.0.1:8000/api/parks" \
     -H "accept: application/json"
```

**Get park weather:**
```bash
curl -X GET "http://127.0.0.1:8000/api/parks/1/weather" \
     -H "accept: application/json"
```

**Search species:**
```bash
curl -X GET "http://127.0.0.1:8000/api/species?type=animal&limit=5" \
     -H "accept: application/json"
```

**Create a review (requires authentication):**
```bash
curl -X POST "http://127.0.0.1:8000/api/parks/1/reviews" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -d '{
       "author_name": "John Doe",
       "rating": 5,
       "title": "Amazing experience!",
       "comment": "Beautiful park with rich biodiversity"
     }'
```

### Troubleshooting

**Common Issues:**
- **Database connection errors**: Run `python migrate_database.py` to initialize the database
- **API key errors**: Check your `.env` file has valid API keys for external services
- **Upload errors**: Ensure the `uploads/` directory exists and is writable
- **CORS errors**: Add your frontend URL to `ALLOWED_ORIGINS` in `.env`

**Performance Tips:**
- Enable Redis caching for better performance with external APIs
- Use pagination for large result sets
- Compress images before uploading
- Monitor API rate limits for external services

## 📁 Project Structure

```
tunisia-national-parks-api/
├── main.py                    # FastAPI application
├── main_production.py         # Production server
├── models.py                  # SQLModel database models
├── database.py                # Database connection & init
├── config.py                  # Configuration settings
├── config_validation.py       # Configuration validation
├── utils.py                   # Utility functions
├── weather_service.py         # Weather API integration
├── recommendation_engine.py   # Recommendation system
├── routers/                   # API route handlers
│   ├── auth.py
│   ├── parks.py
│   └── species.py
├── tests/                     # Unit and integration tests
│   ├── conftest.py
│   ├── test_parks.py
│   └── test_species.py
├── templates/                 # Jinja2 HTML templates
├── static/                    # Static assets (CSS, JS)
├── uploads/                   # User uploaded files
├── frontend/                  # Frontend components
├── monitoring/                # Monitoring setup
│   ├── prometheus.yml
│   └── grafana/
├── .github/workflows/         # CI/CD pipelines
├── ParkComparisonDashboard.jsx # React park comparison component
├── HealthOnboardingForm.jsx   # React health onboarding form
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker setup
├── docker-compose.monitoring.yml # Monitoring stack
├── pytest.ini                 # Test configuration
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Weather data from [OpenWeatherMap](https://openweathermap.org/)
- Maps powered by [OpenStreetMap](https://www.openstreetmap.org/)
