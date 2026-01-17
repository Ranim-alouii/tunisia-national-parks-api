# Tunisia Protected Areas & Parks API

This project provides a WDPA-inspired REST API for Tunisia's protected areas, plus a simple frontend map and a conservation pressure advisor.

Tech stack: Python (FastAPI), PostgreSQL + PostGIS, SQLAlchemy, GeoAlchemy2, HTML/CSS/JS (Leaflet), Docker Compose.

Quick start (with Docker):

```powershell
# From project root
docker-compose up --build

# API at http://localhost:8000
# Open the frontend at http://localhost:8000/frontend/index.html (served by mounting frontend directory)
```

Seeding example data
--------------------

After the API and DB are running you can seed demo data (creates one demo park, biodiversity feature and recent visitor stats) using the seed script inside the `api` service:

```powershell
docker-compose exec api python app/scripts/seed_data.py
```

This will insert a demo park named `Ichkeul National Park Demo` and 7 days of visitor counts used by the pressure advisor. You can then try:

```powershell
curl http://localhost:8000/api/v1/parks
curl http://localhost:8000/api/v1/parks/<id>
curl http://localhost:8000/api/v1/parks/<id>/pressure
```

Serving the frontend
--------------------

The backend mounts the `frontend/` folder and serves the UI at `/frontend/index.html` by default. The compose file also includes an optional `frontend` nginx service exposing the static site on port `8080`.

- UI via API static mount: http://localhost:8000/
- UI via nginx (optional): http://localhost:8080/

OpenAPI YAML
------------
An `openapi.yaml` file with core endpoints is included in `backend/openapi.yaml`. You can also generate a fresh OpenAPI file from the running app:

```powershell
docker-compose exec api python app/scripts/export_openapi.py
```

Docker troubleshooting
----------------------
If `docker-compose` fails, ensure Docker Desktop / Docker Engine is running on your machine. On Windows you may need to start Docker Desktop and enable WSL2 integration or configure the Docker daemon.

Common checks:
- Start Docker Desktop (Windows) and confirm the whale icon is running.
- Run `docker version` and `docker-compose version` to verify the CLI can reach the daemon.
- If you get pipe errors like "dockerDesktopLinuxEngine" failing to connect, restart Docker Desktop.



Alembic migrations
------------------

Alembic is configured under `backend/alembic`. To create and run migrations from inside the running `api` container:

```powershell
docker-compose exec api alembic revision --autogenerate -m "create models"
docker-compose exec api alembic upgrade head
```

The alembic `env.py` reads the `DATABASE_URL` from the app settings so migrations will run against the configured DB.

API examples
------------

List parks (no geometry by default):

```powershell
curl http://localhost:8000/api/v1/parks
```

Get park details (includes GeoJSON geometry and subresources):

```powershell
curl http://localhost:8000/api/v1/parks/<id>
```

Get computed conservation pressure for a park (today):

```powershell
curl http://localhost:8000/api/v1/parks/<id>/pressure
```

Search parks for hiking with low pressure:

```powershell
curl "http://localhost:8000/api/v1/search/parks?activity=hiking&pressure=low"
```

Write endpoints (create/update) require an API key header `x-api-key` matching `API_SECRET_KEY`.

Authentication (JWT)
--------------------
This project supports JWT-based admin tokens. Use the seeded admin user (`admin` / `adminpass`) created by the seed script, or create your own user via the DB.

Get a token:

```powershell
curl -X POST http://localhost:8000/api/v1/auth/token -H "Content-Type: application/json" -d '{"username":"admin","password":"adminpass"}'
```

Then include the token in requests:

```powershell
curl -X POST http://localhost:8000/api/v1/parks -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"name_en":"New Park"}'
```


Conservation pressure algorithm (summary)
--------------------------------------
- Base score from recent visitors: 7-day average scaled to a base 0–60 value (assumes nominal capacity of 500 visitors).
- Biodiversity sensitivity: +20 if the park has high-sensitivity features during configured critical months (e.g., March–April for migratory birds).
- Seasonal modifiers: +10 during summer (Jun–Aug) and −10 during low season (Nov–Feb).
- Final numeric score is clamped to 0–100 and mapped to levels: 0–40 `low`, 41–70 `medium`, 71–100 `high`.

See `backend/app/services/pressure.py` for the documented implementation.




Important files:
- `backend/` - FastAPI app and models
- `frontend/` - static frontend (index.html, app.js, map.js)
- `init_db/init_postgis.sql` - enables PostGIS on DB init
- `docker-compose.yml` - orchestrates services

Conservation pressure logic:
- Uses recent visitor statistics (7-day average) to compute a base score
- Adds modifiers for biodiversity sensitivity and seasonal patterns
- Maps numeric score to `low`/`medium`/`high` and returns a recommendation string

See `backend/app/services/pressure.py` for the exact algorithm and comments.
