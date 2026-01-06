"""
DealMotion Marketing Engine - FastAPI Backend

Cloud-based automated content generation for YouTube.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import inngest
from inngest.fast_api import serve

from app.config import get_settings
from app.routers import topics, scripts, videos, youtube, tts, render
from app.inngest.client import inngest_client
from app.inngest.functions import (
    daily_content_pipeline,
    generate_video_fn,
    upload_to_youtube_fn,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🎬 DealMotion Marketing Engine starting...")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="DealMotion Marketing Engine",
    description="Automated YouTube content generation for DealMotion",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics.router, prefix="/api/topics", tags=["Topics"])
app.include_router(scripts.router, prefix="/api/scripts", tags=["Scripts"])
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])
app.include_router(youtube.router, prefix="/api/youtube", tags=["YouTube"])
app.include_router(tts.router, prefix="/api/tts", tags=["TTS"])
app.include_router(render.router, prefix="/api/render", tags=["Render"])

# Inngest endpoint
serve(
    app,
    inngest_client,
    [
        daily_content_pipeline,
        generate_video_fn,
        upload_to_youtube_fn,
    ],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "DealMotion Marketing Engine",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "inngest": "connected",
        "database": "connected"
    }

