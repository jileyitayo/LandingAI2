"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up...")
    print(f"📝 API Documentation: http://localhost:8000/docs")
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

