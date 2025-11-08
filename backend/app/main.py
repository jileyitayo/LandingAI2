"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health, auth, users, templates, generation, projects, deployment
from app.middleware.auth_middleware import AuthenticationMiddleware
from app.services.vite_preview_service import vite_preview_service

import logging
import os
import asyncio

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
    # Suppress uvicorn access logs (HTTP request logs)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    # Suppress httpx INFO logs (only show WARNING and above)
    logging.getLogger("httpx").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up...")
    print(f"📝 API Documentation: http://localhost:8000/docs")
    setup_logging()
    
    # Ensure shared template is initialized
    vite_preview_service._ensure_shared_template()
    
    # Start background cleanup task
    async def cleanup_task():
        while True:
            await asyncio.sleep(1800)  # Run every 30 minutes
            try:
                vite_preview_service.cleanup_old_previews(max_age_hours=1)
            except Exception as e:
                logging.error(f"Preview cleanup failed: {e}")
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    cleanup_task_handle.cancel()
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
    expose_headers=["*"]
)

# Configure Authentication Middleware
app.add_middleware(AuthenticationMiddleware)

# Mount static files for previews
previews_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "previews")
if os.path.exists(previews_path):
    app.mount("/previews", StaticFiles(directory=previews_path, html=True, check_dir=True), name="previews")
    # app.mount("/previews/builds", StaticFiles(directory=previews_path + "/builds"), name="previews")
else:
    print(f"Warning: Previews directory not found at {previews_path}")

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
app.include_router(deployment.router, prefix="/api/v1", tags=["Deployment"])

