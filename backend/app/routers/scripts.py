"""
Scripts Router - Generate video scripts from topics.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class ScriptSegment(BaseModel):
    """A segment of the video script."""
    type: str
    text: str
    duration_seconds: float
    visual_cue: str


class ScriptRequest(BaseModel):
    """Request for script generation."""
    topic_id: Optional[str] = None
    title: str
    hook: str
    main_points: List[str]
    cta: str
    language: str = "nl"
    target_duration: int = 45


class ScriptResponse(BaseModel):
    """Response with generated script."""
    id: str
    title: str
    description: str
    segments: List[ScriptSegment]
    full_text: str
    total_duration_seconds: float


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(request: ScriptRequest):
    """
    Generate a video script from a topic.
    
    Creates an engaging script with hook, content, and CTA segments.
    """
    from app.services.script_service import ScriptService
    
    try:
        service = ScriptService()
        
        topic_data = {
            "title": request.title,
            "hook": request.hook,
            "main_points": request.main_points,
            "cta": request.cta
        }
        
        script = service.generate_script(
            topic=topic_data,
            language=request.language,
            target_duration=request.target_duration
        )
        
        return ScriptResponse(**script)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

