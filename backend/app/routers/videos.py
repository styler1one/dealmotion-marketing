"""
Videos Router - Generate and manage videos.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.inngest.client import inngest_client
from app.services.video_service import VideoService


router = APIRouter()
video_service = VideoService()


class VideoGenerateRequest(BaseModel):
    """Request for video generation."""
    script_id: Optional[str] = None
    script_text: str
    title: str
    description: str
    style: str = "professional"
    include_captions: bool = True
    upload_after: bool = True


class VideoGenerateResponse(BaseModel):
    """Response for video generation."""
    job_id: str
    status: str
    message: str


class VideoStatusResponse(BaseModel):
    """Response for video status."""
    id: str
    status: str
    video_url: Optional[str] = None
    youtube_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """
    Trigger video generation.
    
    This starts an async workflow via Inngest that:
    1. Generates voice-over
    2. Creates video with NanoBanana
    3. Optionally uploads to YouTube
    """
    try:
        # Send event to Inngest
        await inngest_client.send(
            inngest.Event(
                name="marketing/video.generate",
                data={
                    "script": {
                        "id": request.script_id,
                        "full_text": request.script_text,
                        "title": request.title,
                        "description": request.description,
                    },
                    "topic": {
                        "title": request.title,
                        "hashtags": ["sales", "AI", "B2B", "DealMotion"]
                    },
                    "style": request.style,
                    "include_captions": request.include_captions,
                    "upload_after": request.upload_after,
                }
            )
        )
        
        return VideoGenerateResponse(
            job_id="pending",  # Would come from Inngest
            status="queued",
            message="Video generation started. Check status endpoint for updates."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: str):
    """
    Get the status of a video generation job.
    """
    # TODO: Implement with database lookup
    return VideoStatusResponse(
        id=video_id,
        status="pending",
        video_url=None,
        youtube_url=None
    )


@router.get("/")
async def list_videos(limit: int = 20, offset: int = 0):
    """
    List generated videos.
    """
    # TODO: Implement with database
    return {
        "videos": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/health")
async def video_health():
    """
    Check if video service (Google Veo) is configured.
    """
    return video_service.health_check()


@router.get("/debug")
async def video_debug():
    """
    Debug credentials setup.
    """
    return video_service.debug_credentials()


@router.get("/models")
async def list_video_models():
    """
    List available video generation models.
    """
    try:
        from google import genai
        from app.config import get_settings
        
        settings = get_settings()
        client = genai.Client(api_key=settings.google_gemini_api_key)
        
        # List all models
        all_models = []
        video_models = []
        
        for model in client.models.list():
            name = getattr(model, 'name', str(model))
            model_info = {"name": name}
            all_models.append(name)
            
            # Filter for video-related models
            if 'veo' in name.lower() or 'video' in name.lower() or 'imagen' in name.lower():
                video_models.append(model_info)
        
        return {
            "video_models": video_models,
            "all_models": all_models[:50],  # First 50 models
            "total_models": len(all_models)
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}


class VideoTestRequest(BaseModel):
    """Simple test request for video generation."""
    prompt: str = "A professional business meeting in a modern office, clean corporate style, dynamic camera movement"


@router.post("/test")
async def test_video_generation(request: VideoTestRequest):
    """
    Test video generation with Google Veo 2.
    
    This is a direct test endpoint - not for production use.
    """
    try:
        # Create a simple test script
        test_script = {
            "title": "Test Video",
            "full_text": request.prompt,
            "total_duration_seconds": 8,
        }
        
        result = video_service.generate_video(
            script=test_script,
            style="professional B2B content"
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

