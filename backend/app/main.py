"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import health, auth, users, templates, generation, projects
from app.middleware.auth_middleware import AuthenticationMiddleware

import logging
import os

def setup_logging():
    """Configure logging based on environment."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Console output
        ]
    )
    
    # Set specific logger levels if needed
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up...")
    print(f"📝 API Documentation: http://localhost:8000/docs")
    setup_logging()
    yield
    # Shutdown
    print(f"👋 {settings.app_name} shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Website Builder API for African Entrepreneurs",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Authentication Middleware
app.add_middleware(AuthenticationMiddleware)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning API information."""
    return JSONResponse(
        content={
            "message": "Welcome to SiteSmith API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(generation.router, prefix="/api/v1", tags=["Generation"])

