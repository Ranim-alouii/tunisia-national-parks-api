"""
Minimal FastAPI application for Tunisia National Parks
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIASGIMiddleware

from prometheus_fastapi_instrumentator import Instrumentator

from database import init_db
from config import settings

# Import routers
from routers import parks, species, auth

# Create FastAPI app
app = FastAPI(
    title="Tunisia National Parks API",
    description="Complete API for Tunisia's national parks with biodiversity, trails, reviews, and gamification.",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIASGIMiddleware)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.unsplash.com;"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Logging
logger = logging.getLogger("tunisia_parks")
logging.basicConfig(level=logging.INFO)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(parks.router)
app.include_router(species.router)
app.include_router(auth.router)

# Fallback static file routes
@app.get("/static/{path:path}")
async def serve_static(path: str):
    from fastapi.responses import FileResponse
    import os
    file_path = os.path.join("static", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@app.get("/uploads/{path:path}")
async def serve_uploads(path: str):
    from fastapi.responses import FileResponse
    import os
    file_path = os.path.join("uploads", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# Request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_ms = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({process_ms:.2f}ms)")
    return response

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": "Validation failed", "details": exc.errors()}},
    )

# Frontend routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/parks", response_class=HTMLResponse)
async def view_parks(request: Request):
    return templates.TemplateResponse("parks.html", {"request": request})

@app.get("/species", response_class=HTMLResponse)
async def view_species(request: Request):
    return templates.TemplateResponse("species.html", {"request": request})

@app.get("/map", response_class=HTMLResponse)
async def view_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})

# Health check
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "3.0.0"}

# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from pathlib import Path
    for folder in ["parks", "species", "users", "documents"]:
        Path(f"uploads/{folder}").mkdir(parents=True, exist_ok=True)
    yield

app.router.lifespan_context = lifespan

# Initialize monitoring
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False, should_gzip=True)

# Run server
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
