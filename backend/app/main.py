"""
FastAPI main application for Agentic AI Project Management Assistant
Transformed from existing Flask BOTMEDICAL application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os

# Import core modules
from .core.config import settings
from .core.database import engine, Base
from .api import auth, projects, tasks, users, ai_agent, analytics

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Project Management Assistant",
    description="AI-powered project management with automation and analytics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(ai_agent.router, prefix="/api/ai", tags=["ai-agent"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("🚀 Agentic AI Project Management Assistant is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Agentic AI Project Management Assistant...")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Agentic AI Project Management Assistant",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "active"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agentic AI Project Management Assistant",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )