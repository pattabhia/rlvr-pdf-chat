"""
Ground Truth Service - Main Application

Generic, domain-agnostic ground truth management service.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database.connection import engine, Base
from .api import domains, entries, health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Ground Truth Service...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Ground Truth Service...")


# Create FastAPI app
app = FastAPI(
    title="Ground Truth Service",
    description="Generic, domain-agnostic ground truth management for RLVR Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(domains.router, prefix="/domains", tags=["Domains"])
app.include_router(entries.router, prefix="/ground-truth", tags=["Ground Truth Entries"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Ground Truth Service",
        "version": "1.0.0",
        "description": "Generic ground truth management for RLVR Platform",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

