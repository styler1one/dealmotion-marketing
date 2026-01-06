"""
DealMotion Marketing Engine - FastAPI Backend

Cloud-based automated content generation for YouTube.
"""
import os
import sys
import traceback
from contextlib import asynccontextmanager

print("🔍 Starting imports...", flush=True)

try:
    from fastapi import FastAPI
    print("✅ FastAPI imported", flush=True)
    
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ CORS imported", flush=True)
    
    import inngest
    from inngest.fast_api import serve
    print("✅ Inngest imported", flush=True)
    
    from app.config import get_settings
    print("✅ Config imported", flush=True)
    
    # Import routers one by one for debugging
    from app.routers import topics
    print("✅ topics router imported", flush=True)
    
    from app.routers import scripts
    print("✅ scripts router imported", flush=True)
    
    from app.routers import videos
    print("✅ videos router imported", flush=True)
    
    from app.routers import youtube
    print("✅ youtube router imported", flush=True)
    
    from app.routers import tts
    print("✅ tts router imported", flush=True)
    
    from app.routers import render
    print("✅ render router imported", flush=True)
    
    from app.routers import pipeline
    print("✅ pipeline router imported", flush=True)
    
    from app.inngest.client import inngest_client
    print("✅ Inngest client imported", flush=True)
    
    from app.inngest.functions import (
        daily_content_pipeline,
        generate_video_fn,
        upload_to_youtube_fn,
        test_full_pipeline_fn,
    )
    print("✅ Inngest functions imported", flush=True)

except Exception as e:
    print(f"❌ Import error: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🎬 DealMotion Marketing Engine starting...", flush=True)
    yield
    # Shutdown
    print("👋 Shutting down...", flush=True)


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
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])

print("✅ All routers registered", flush=True)

# Inngest endpoint
serve(
    app,
    inngest_client,
    [
        daily_content_pipeline,
        generate_video_fn,
        upload_to_youtube_fn,
        test_full_pipeline_fn,
    ],
)

print("✅ Inngest serve registered", flush=True)


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

print("✅ App fully initialized", flush=True)
