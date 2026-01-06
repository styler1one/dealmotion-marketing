"""
Topics Router - Generate and manage content topics.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.topic_service import TopicService, ContentType


router = APIRouter()


class TopicRequest(BaseModel):
    """Request for topic generation."""
    content_type: Optional[str] = None
    count: int = 5
    language: str = "nl"


class TopicResponse(BaseModel):
    """Response with generated topic."""
    id: str
    content_type: str
    title: str
    hook: str
    main_points: List[str]
    cta: str
    hashtags: List[str]
    estimated_duration_seconds: int


class TopicsListResponse(BaseModel):
    """Response with list of topics."""
    topics: List[TopicResponse]
    count: int


@router.post("/generate", response_model=TopicsListResponse)
async def generate_topics(request: TopicRequest):
    """
    Generate content topic ideas.
    
    Uses Claude to brainstorm engaging video topics based on
    the content type and target language.
    """
    try:
        service = TopicService()
        
        content_type = None
        if request.content_type:
            try:
                content_type = ContentType(request.content_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid content_type. Must be one of: {[t.value for t in ContentType]}"
                )
        
        topics = service.generate_topics(
            content_type=content_type,
            count=request.count,
            language=request.language
        )
        
        return TopicsListResponse(
            topics=[TopicResponse(**t) for t in topics],
            count=len(topics)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_content_types():
    """Get available content types."""
    return {
        "types": [
            {"id": t.value, "name": t.name.replace("_", " ").title()}
            for t in ContentType
        ]
    }

