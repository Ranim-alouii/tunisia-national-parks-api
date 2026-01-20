# 🌿 Tunisia National Parks Platform

**A comprehensive full-stack platform for Tunisia's national parks and protected areas, featuring biodiversity data, interactive maps, weather integration, and environmental monitoring.**

[![API Version](https://img.shields.io/badge/API-v3.0.0-blue.svg)](https://github.com/Ranim-alouii/tunisia-national-parks-api)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**🚀 Production Ready - Deployed on Port 8000**

## 🌟 Overview

This production-ready platform provides comprehensive access to Tunisia's national parks ecosystem, combining a REST API with a complete web frontend. Key features include:

- **🏞️ Complete Park Database**: Detailed information on 18+ national parks and protected areas
- **🦌 Biodiversity Management**: 250+ species of wildlife and plants with conservation status
- **🗺️ Interactive Mapping**: OpenStreetMap integration with location services
- **🌤️ Weather Integration**: Real-time weather data and forecasts for all park locations
- **📸 Media Management**: Nature photography from Unsplash API with upload capabilities
- **📰 Content Integration**: Environmental news and conservation updates
- **⭐ User Engagement**: Reviews, ratings, and community features
- **🎖️ Gamification**: Achievement system with badges and user statistics
- **🔍 Advanced Search**: Multi-criteria filtering and search functionality
- **🌐 Internationalization**: Multi-language support (French, English, Arabic)

## 🏗️ Architecture

```
tunisia-parks-api/
├── 🐍 main.py                 # FastAPI application & routes
├── 🗄️ models.py               # SQLAlchemy models
├── ⚙️ config.py               # Environment configuration
├── 🗺️ routers/                # API route handlers
│   ├── parks.py              # Park management
│   ├── species.py            # Species & biodiversity
│   └── auth.py               # Authentication
├── 🌐 templates/             # Jinja2 HTML templates
│   ├── base.html            # Base template
│   ├── index.html           # Homepage
│   ├── parks.html           # Parks listing
│   ├── park_detail.html     # Park detail page
│   ├── custom_docs.html     # Enhanced API docs
│   └── map.html             # Interactive map
├── 📊 static/               # Static assets (CSS/JS)
├── 🧪 tests/                # Test suite
├── 📋 requirements.txt      # Python dependencies
├── 🐳 Dockerfile            # Container configuration
├── 🐳 docker-compose.yml    # Multi-service setup
└── 📖 README.md             # This file
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Ranim-alouii/tunisia-national-parks-api.git
cd tunisia-national-parks-api

# For development
docker-compose up --build

# For production
./deploy.sh production

# Access the application
# 🌐 Frontend: http://localhost:8000 (dev) / https://yourdomain.com (prod)
# 📚 API Docs: http://localhost:8000/docs (dev) / https://yourdomain.com/docs (prod)
# 🔌 API Base: http://localhost:8000/api (dev) / https://yourdomain.com/api (prod)
```

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/Ranim-alouii/tunisia-national-parks-api.git
cd tunisia-national-parks-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from database import init_db; init_db()"

# Start development server
python main.py

# Access the application
# 🌐 Frontend: http://localhost:8000
# 📚 API Docs: http://localhost:8000/docs
# 🔌 API Base: http://localhost:8000/api
```

### Option 3: Production Deployment

```bash
# Automated deployment
./deploy.sh production

# Manual deployment
docker-compose -f docker-compose.prod.yml up --build -d

# Backup data
./backup.sh

# Monitor services
./monitor.sh
```

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite:///./tunisia_parks.db
# Or for PostgreSQL: postgresql://user:password@localhost/tunisia_parks

# Security Settings
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# API Keys (Optional - Mock data available)
OPENWEATHER_API_KEY=your_openweather_key
UNSPLASH_ACCESS_KEY=your_unsplash_key
GOOGLE_PLACES_API_KEY=your_google_key
NEWSAPI_API_KEY=your_newsapi_key

# Application Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## 📋 API Endpoints

### 🌿 Parks Management
- `GET /api/parks` - List all parks with filtering
- `GET /api/parks/{id}` - Get park details
- `POST /api/parks` - Create new park (admin)
- `PUT /api/parks/{id}` - Update park (admin)
- `DELETE /api/parks/{id}` - Delete park (admin)

### 🦌 Species & Biodiversity
- `GET /api/species` - List all species
- `GET /api/species/{id}` - Get species details
- `GET /api/parks/{id}/species` - Species in specific park

### 🗺️ Maps & Navigation
- `GET /api/parks/{id}/map` - Park location data
- `GET /api/maps/all-parks` - All parks map data
- `POST /api/maps/directions` - Get directions

### 🌤️ Weather Integration
- `GET /api/parks/{id}/weather` - Current weather
- `GET /api/parks/{id}/forecast` - Weather forecast

### 📸 Media & Images
- `GET /api/parks/{id}/unsplash-images` - Nature photos
- `POST /api/parks/{id}/images` - Upload park images
- `GET /api/parks/{id}/wikipedia` - Wikipedia information

### 📰 Content & News
- `GET /api/news/parks` - Environmental news
- `GET /api/parks/{id}/nearby-places` - Nearby amenities

### 👥 User Features
- `GET /api/parks/{id}/reviews` - Park reviews
- `POST /api/parks/{id}/reviews` - Add review
- `GET /api/user/{id}/badges` - User achievements
- `GET /api/user/{id}/stats` - User statistics

### 🔍 Search & Discovery
- `GET /api/search/parks` - Advanced park search
- `GET /api/search/species` - Species search
- `GET /api/search/suggestions` - Search suggestions

## 🔐 Authentication

The platform supports multiple authentication methods:

### Admin Login
Access the secret admin panel at `/admin/login` with credentials from `.env`:

```bash
# Admin credentials (configured in .env file)
Username: admin (configurable via ADMIN_USERNAME)
Password: admin123 (configurable via ADMIN_PASSWORD)
```

The admin login provides:
- Backend management access
- JWT token generation for API access
- Secure session management

### User Authentication (JWT)
Standard JWT-based authentication for registered users:

```bash
# Register new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"securepass"}'

# Get access token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=securepass"

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:8000/api/parks
```

### Guest Sessions
The platform automatically creates persistent guest sessions using localStorage:
- Unique visitor ID generation
- XP and badge persistence across browser sessions
- No registration required for gamification features

### Environment Configuration
Configure authentication in your `.env` file:

```env
# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# JWT Settings
SECRET_KEY=your-256-bit-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_parks.py

# Run API integration tests
python test_localhost_apis.py
```

## 📊 Sample API Usage

### Get All Parks
```bash
curl "http://localhost:8000/api/parks?limit=5&governorate=Bizerte"
```

### Search Parks
```bash
curl "http://localhost:8000/api/search/parks?query=nature&min_area=100"
```

### Get Park Weather
```bash
curl "http://localhost:8000/api/parks/1/weather"
```

### Get Nature Images
```bash
curl "http://localhost:8000/api/parks/1/unsplash-images?count=10"
```

## 🗄️ Database Schema

### Core Tables
- **parks**: National parks information
- **species**: Wildlife and plant species
- **park_species**: Many-to-many park-species relationships
- **trails**: Hiking trails within parks
- **reviews**: User reviews and ratings
- **users**: User accounts and profiles

### Gamification Tables
- **badges**: Achievement definitions
- **user_badges**: User earned badges
- **user_stats**: User activity statistics

### Content Tables
- **sightings**: Wildlife sightings reports
- **user_visit_history**: Park visit tracking

## 🐳 Docker Deployment

The project includes complete Docker infrastructure for both development and production environments.

### Development Setup
```bash
# Start development environment
docker-compose up --build

# Includes: App, Redis, Nginx (optional)
# Access at: http://localhost:8000
```

### Production Setup
```bash
# Automated deployment
./deploy.sh production

# Manual deployment
docker-compose -f docker-compose.prod.yml up --build -d

# Includes: App, Redis, Nginx, SSL certificates
# Access at: https://yourdomain.com
```

### Deployment Features

- **🔒 SSL/TLS**: Automatic HTTPS with Let's Encrypt
- **🔄 Load Balancing**: Nginx reverse proxy with rate limiting
- **💾 Persistent Storage**: Database and uploads volume management
- **📊 Monitoring**: Health checks and resource monitoring
- **🔄 Auto-restart**: Container recovery and service orchestration
- **📦 Backup**: Automated database and file backup scripts

### Environment Files

- **`.env`**: Development configuration
- **`.env.production`**: Production configuration (secure keys)
- **`docker-compose.yml`**: Development stack
- **`docker-compose.prod.yml`**: Production stack with SSL
- **`docker-compose.override.yml`**: Development overrides

### Deployment Scripts

- **`deploy.sh`**: Automated deployment with health checks
- **`backup.sh`**: Database and uploads backup
- **`monitor.sh`**: Real-time service monitoring

### Infrastructure Overview

```
Production Stack:
├── 🌐 Nginx (SSL termination, rate limiting)
├── 🐳 App Container (FastAPI application)
├── 🗄️ Redis (caching, sessions)
└── 🔒 SSL Certificates (Let's Encrypt)

Development Stack:
├── 🐳 App Container
└── 🗄️ Redis (optional)
```

## 🔧 Development Features

### Mock Data
The API includes comprehensive mock data for all external services:
- ✅ **Weather**: Realistic Tunisian weather patterns
- ✅ **Images**: Curated nature photography
- ✅ **News**: Environmental conservation articles
- ✅ **Places**: Nearby amenities and services

### Enhanced API Documentation
- Custom UI with Tunisia-themed design
- Interactive examples and testing
- Keyboard shortcuts (Ctrl+K for search)
- Quick navigation between endpoints

### Code Quality
- **Type Hints**: Full type annotations
- **Linting**: Black, isort, flake8
- **Testing**: Pytest with async support
- **Documentation**: Auto-generated OpenAPI specs

## 📈 Monitoring & Analytics

### Health Checks
```bash
# API health
GET /api/health

# Database connectivity
GET /health
```

### Metrics (Prometheus)
```bash
# Metrics endpoint
GET /metrics
```

### Logging
- Structured JSON logging
- Request/response tracking
- Error monitoring and alerts

## 🌍 Internationalization

Support for multiple languages:
- 🇫🇷 **French** (Primary)
- 🇺🇸 **English**
- 🇹🇳 **Arabic** (RTL support)

```bash
# Get available languages
GET /api/languages

# Get translations
GET /api/languages/fr
```

## 🔒 Security Features

- **JWT Authentication** with configurable expiration
- **CORS Protection** with configurable origins
- **Rate Limiting** (60 requests/minute default)
- **Input Validation** with Pydantic models
- **SQL Injection Prevention** with SQLAlchemy
- **XSS Protection** with Content Security Policy
- **HTTPS Enforcement** in production

## 📱 Frontend Integration

The API serves a complete frontend application:

### Pages
- **🏠 Homepage**: Featured parks and statistics
- **🏞️ Parks**: Browse all national parks
- **🦌 Species**: Explore biodiversity
- **🗺️ Map**: Interactive park locations
- **⭐ Reviews**: User experiences

### Technologies
- **HTML5/CSS3**: Responsive design
- **Vanilla JavaScript**: No frameworks required
- **Leaflet.js**: Interactive maps
- **Font Awesome**: Icons and UI elements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints
- Write clear commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Tunisia Ministry of Environment** for park data and conservation efforts
- **OpenStreetMap contributors** for mapping data
- **Unsplash** for nature photography
- **OpenWeatherMap** for weather data
- **FastAPI** community for excellent documentation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Ranim-alouii/tunisia-national-parks-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ranim-alouii/tunisia-national-parks-api/discussions)
- **Email**: Contact through GitHub

---

**🌿 Explore Tunisia's incredible natural heritage through our comprehensive parks API! 🇹🇳**
