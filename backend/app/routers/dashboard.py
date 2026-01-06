"""
Dashboard Router - API endpoints for frontend dashboard.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from app.services.database_service import DatabaseService

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """Get aggregated statistics for the dashboard."""
    try:
        db = DatabaseService()
        stats = db.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos")
async def get_recent_videos(limit: int = 10):
    """Get recent videos with YouTube upload data."""
    try:
        db = DatabaseService()
        uploads = db.get_youtube_uploads(limit=limit)
        
        # Format for frontend
        videos = []
        for upload in uploads:
            video_data = upload.get("videos", {}) or {}
            videos.append({
                "id": upload.get("id"),
                "youtube_id": upload.get("youtube_id"),
                "youtube_url": upload.get("youtube_url"),
                "title": upload.get("title"),
                "thumbnail_url": video_data.get("thumbnail_url") or f"https://img.youtube.com/vi/{upload.get('youtube_id')}/maxresdefault.jpg",
                "views": upload.get("views", 0),
                "likes": upload.get("likes", 0),
                "comments": upload.get("comments", 0),
                "published_at": upload.get("published_at"),
                "is_short": upload.get("is_short", True),
            })
        
        return {"videos": videos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-runs")
async def get_pipeline_runs(limit: int = 10):
    """Get recent pipeline run history."""
    try:
        db = DatabaseService()
        runs = db.get_pipeline_runs(limit=limit)
        return {"runs": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-runs/latest")
async def get_latest_pipeline_run():
    """Get the most recent pipeline run."""
    try:
        db = DatabaseService()
        run = db.get_latest_pipeline_run()
        return {"run": run}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content-mix")
async def get_content_mix():
    """Get content type distribution."""
    try:
        db = DatabaseService()
        stats = db.get_dashboard_stats()
        return {"content_mix": stats.get("content_mix", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics")
async def get_recent_topics(limit: int = 10, status: Optional[str] = None):
    """Get recent topics."""
    try:
        db = DatabaseService()
        topics = db.get_topics(limit=limit, status=status)
        return {"topics": topics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scripts")
async def get_recent_scripts(limit: int = 10):
    """Get recent scripts."""
    try:
        db = DatabaseService()
        scripts = db.get_scripts(limit=limit)
        return {"scripts": scripts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

