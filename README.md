# Tunisia National Parks API

A RESTful API built with FastAPI and SQLite to manage national parks and species in Tunisia. It includes data validation, centralized error handling, OAuth2 authentication with JWT, and basic request logging.

## Features

- CRUD operations for parks and species stored in SQLite.
- Validation of coordinates (latitude, longitude) and park area using Pydantic models.
- Consistent JSON error responses for 4xx and 5xx errors.
- OAuth2 password flow with JWT bearer tokens for protected write operations.
- Request logging middleware (method, path, status code, response time).
- Interactive API documentation via Swagger UI and ReDoc.

## Getting started

### Prerequisites

- Python 3.11+ installed.
- Git installed.

### Setup


The API will run at: `http://127.0.0.1:8000`.

Open the interactive docs at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Replace `<YOUR-REPO-URL>` with your GitHub repository URL.

## Authentication

Write operations (create, update, delete) are protected using OAuth2 with password flow and JWT bearer tokens.

### Admin account

For development, there is a single in-memory admin user:

- **username**: `admin`
- **password**: `admin123`

### Getting a token

1. Start the server and open `http://127.0.0.1:8000/docs`.
2. Click **Authorize** (top right).
3. Enter the admin username and password.
4. Click **Authorize** and then **Close**.

Or call the token endpoint directly:

