"""
YouTube Router - Manage YouTube uploads and channel.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()


class YouTubeUploadRequest(BaseModel):
    """Request for YouTube upload."""
    video_url: str
    title: str
    description: str
    tags: List[str] = []
    privacy_status: str = "public"
    is_short: bool = True


class YouTubeUploadResponse(BaseModel):
    """Response for YouTube upload."""
    youtube_id: str
    youtube_url: str
    status: str


class YouTubeVideoResponse(BaseModel):
    """Response for a YouTube video."""
    youtube_id: str
    title: str
    published_at: str
    views: int
    likes: int
    comments: int
    thumbnail_url: Optional[str] = None


@router.post("/upload", response_model=YouTubeUploadResponse)
async def upload_video(request: YouTubeUploadRequest):
    """
    Upload a video to YouTube.
    
    Requires YouTube API credentials to be configured.
    """
    from app.services.youtube_service import YouTubeService
    
    try:
        service = YouTubeService()
        
        result = service.upload_video(
            video_url=request.video_url,
            title=request.title,
            description=request.description,
            tags=request.tags,
            privacy_status=request.privacy_status,
            is_short=request.is_short
        )
        
        return YouTubeUploadResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos")
async def list_youtube_videos(limit: int = 20):
    """
    List videos from the connected YouTube channel.
    """
    from app.services.youtube_service import YouTubeService
    
    try:
        service = YouTubeService()
        videos = service.get_channel_videos(max_results=limit)
        
        return {
            "videos": videos,
            "count": len(videos)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channel")
async def get_channel_info():
    """
    Get connected YouTube channel info.
    """
    from app.services.youtube_service import YouTubeService
    
    try:
        service = YouTubeService()
        return service.test_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def youtube_health():
    """
    Check if YouTube service is configured.
    """
    from app.services.youtube_service import YouTubeService
    
    service = YouTubeService()
    return service.health_check()


@router.post("/connect")
async def connect_youtube():
    """
    Start YouTube OAuth flow.
    """
    # TODO: Implement OAuth flow
    return {
        "auth_url": "https://accounts.google.com/...",
        "message": "Redirect user to auth_url to connect YouTube"
    }

