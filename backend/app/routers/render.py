"""
Render Router - Create final videos with captions.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.render_service import RenderService


router = APIRouter()
render_service = RenderService()


class RenderRequest(BaseModel):
    """Request for video rendering."""
    texts: List[str]  # 4 text segments
    audio_url: str
    background_video_url: Optional[str] = None
    music_url: Optional[str] = None


class RenderResponse(BaseModel):
    """Response for video rendering."""
    render_id: str
    video_url: str
    status: str


@router.get("/health")
async def render_health():
    """Check if render service is configured."""
    return render_service.health_check()


@router.post("/create", response_model=RenderResponse)
async def create_render(request: RenderRequest):
    """
    Create a final video with animated captions.
    
    Requires:
    - texts: List of 4 text strings (one per scene)
    - audio_url: URL to voice-over audio
    - background_video_url: Optional URL to background video
    """
    try:
        if len(request.texts) < 1:
            raise HTTPException(status_code=400, detail="At least 1 text segment required")
        
        # Pad to 4 texts if needed
        texts = request.texts[:4]
        while len(texts) < 4:
            texts.append("")
        
        result = render_service.render_simple_short(
            texts=texts,
            audio_url=request.audio_url,
            background_video_url=request.background_video_url,
        )
        
        return RenderResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_render():
    """
    Test render with sample data.
    """
    try:
        # Sample texts for testing
        sample_texts = [
            "Cold calling is dood. 💀",
            "Moderne sales draait om waarde bieden, niet pushen.",
            "AI helpt je de juiste prospects te vinden. 🎯",
            "Start vandaag met slimmer verkopen! 🚀"
        ]
        
        # Use a sample audio (you can replace this)
        sample_audio = "https://pqegtotvadioslahcxti.supabase.co/storage/v1/object/public/media/audio/20250106_134942_7eab5677.mp3"
        
        result = render_service.render_simple_short(
            texts=sample_texts,
            audio_url=sample_audio,
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

