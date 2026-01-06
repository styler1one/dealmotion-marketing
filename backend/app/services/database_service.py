"""
Database Service - Supabase CRUD operations.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID

from supabase import create_client, Client
from loguru import logger

from app.config import get_settings


class DatabaseService:
    """Service for database operations via Supabase."""
    
    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Lazy-loaded Supabase client."""
        if self._client is None:
            self._client = create_client(
                self.settings.supabase_url,
                self.settings.supabase_service_key or self.settings.supabase_anon_key
            )
        return self._client
    
    # =========================================================================
    # TOPICS
    # =========================================================================
    
    def create_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Save a generated topic to database."""
        data = {
            "content_type": topic.get("content_type", "sales_tip"),
            "title": topic.get("title", ""),
            "hook": topic.get("hook", ""),
            "main_points": topic.get("main_points", []),
            "cta": topic.get("cta", ""),
            "hashtags": topic.get("hashtags", []),
            "estimated_duration_seconds": topic.get("estimated_duration_seconds", 25),
            "language": topic.get("language", "nl"),
            "status": "pending",
        }
        result = self.client.table("topics").insert(data).execute()
        logger.info(f"Created topic: {data['title']}")
        return result.data[0] if result.data else data
    
    def get_topics(self, limit: int = 10, status: Optional[str] = None) -> List[Dict]:
        """Get recent topics."""
        query = self.client.table("topics").select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return result.data or []
    
    def update_topic_status(self, topic_id: str, status: str) -> None:
        """Update topic status."""
        self.client.table("topics").update({"status": status}).eq("id", topic_id).execute()
    
    # =========================================================================
    # SCRIPTS
    # =========================================================================
    
    def create_script(self, script: Dict[str, Any], topic_id: Optional[str] = None) -> Dict[str, Any]:
        """Save a generated script to database."""
        data = {
            "topic_id": topic_id,
            "title": script.get("title", ""),
            "description": script.get("description", ""),
            "segments": script.get("segments", []),
            "full_text": script.get("full_text", ""),
            "total_duration_seconds": script.get("total_duration_seconds", 25),
            "language": script.get("language", "nl"),
            "status": "pending",
        }
        result = self.client.table("scripts").insert(data).execute()
        logger.info(f"Created script: {data['title']}")
        return result.data[0] if result.data else data
    
    def get_scripts(self, limit: int = 10) -> List[Dict]:
        """Get recent scripts."""
        result = self.client.table("scripts").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    
    # =========================================================================
    # VIDEOS
    # =========================================================================
    
    def create_video(
        self,
        title: str,
        script_id: Optional[str] = None,
        video_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Save a generated video to database."""
        data = {
            "script_id": script_id,
            "title": title,
            "video_url": video_url,
            "audio_url": audio_url,
            "duration_seconds": duration_seconds,
            "status": "ready" if video_url else "processing",
        }
        result = self.client.table("videos").insert(data).execute()
        logger.info(f"Created video: {title}")
        return result.data[0] if result.data else data
    
    def update_video(self, video_id: str, updates: Dict[str, Any]) -> None:
        """Update video record."""
        self.client.table("videos").update(updates).eq("id", video_id).execute()
    
    def get_videos(self, limit: int = 10, status: Optional[str] = None) -> List[Dict]:
        """Get recent videos."""
        query = self.client.table("videos").select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("status", status)
        result = query.execute()
        return result.data or []
    
    # =========================================================================
    # YOUTUBE UPLOADS
    # =========================================================================
    
    def create_youtube_upload(
        self,
        video_id: str,
        youtube_id: str,
        youtube_url: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Save YouTube upload record."""
        data = {
            "video_id": video_id,
            "youtube_id": youtube_id,
            "youtube_url": youtube_url,
            "title": title,
            "description": description or "",
            "tags": tags or [],
            "is_short": True,
            "published_at": datetime.utcnow().isoformat(),
        }
        result = self.client.table("youtube_uploads").insert(data).execute()
        logger.info(f"Created YouTube upload: {youtube_id}")
        return result.data[0] if result.data else data
    
    def get_youtube_uploads(self, limit: int = 10) -> List[Dict]:
        """Get recent YouTube uploads with video data."""
        result = self.client.table("youtube_uploads").select(
            "*, videos(title, video_url, thumbnail_url)"
        ).order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    
    def update_youtube_stats(self, youtube_id: str, views: int, likes: int, comments: int) -> None:
        """Update YouTube video stats."""
        self.client.table("youtube_uploads").update({
            "views": views,
            "likes": likes,
            "comments": comments,
        }).eq("youtube_id", youtube_id).execute()
    
    # =========================================================================
    # PIPELINE RUNS
    # =========================================================================
    
    def create_pipeline_run(self) -> Dict[str, Any]:
        """Create a new pipeline run record."""
        data = {
            "run_date": date.today().isoformat(),
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        result = self.client.table("pipeline_runs").insert(data).execute()
        logger.info(f"Created pipeline run for {data['run_date']}")
        return result.data[0] if result.data else data
    
    def update_pipeline_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        topics_generated: Optional[int] = None,
        scripts_generated: Optional[int] = None,
        videos_created: Optional[int] = None,
        videos_uploaded: Optional[int] = None,
        errors: Optional[List[str]] = None,
    ) -> None:
        """Update pipeline run with progress."""
        updates = {}
        if status:
            updates["status"] = status
        if topics_generated is not None:
            updates["topics_generated"] = topics_generated
        if scripts_generated is not None:
            updates["scripts_generated"] = scripts_generated
        if videos_created is not None:
            updates["videos_created"] = videos_created
        if videos_uploaded is not None:
            updates["videos_uploaded"] = videos_uploaded
        if errors is not None:
            updates["errors"] = errors
        if status == "completed" or status == "failed":
            updates["completed_at"] = datetime.utcnow().isoformat()
        
        if updates:
            self.client.table("pipeline_runs").update(updates).eq("id", run_id).execute()
    
    def get_pipeline_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent pipeline runs."""
        result = self.client.table("pipeline_runs").select("*").order("created_at", desc=True).limit(limit).execute()
        return result.data or []
    
    def get_latest_pipeline_run(self) -> Optional[Dict]:
        """Get the most recent pipeline run."""
        result = self.client.table("pipeline_runs").select("*").order("created_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    
    # =========================================================================
    # DASHBOARD STATS
    # =========================================================================
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get aggregated stats for dashboard."""
        # Total videos
        videos_result = self.client.table("videos").select("id", count="exact").execute()
        total_videos = videos_result.count or 0
        
        # Total views (sum from youtube_uploads)
        uploads_result = self.client.table("youtube_uploads").select("views").execute()
        total_views = sum(u.get("views", 0) for u in (uploads_result.data or []))
        
        # Videos this week
        week_ago = (datetime.utcnow().date().isoformat())
        week_videos = self.client.table("videos").select("id", count="exact").gte("created_at", week_ago).execute()
        videos_this_week = week_videos.count or 0
        
        # Content type distribution
        content_mix = self.client.table("topics").select("content_type").execute()
        mix = {"sales_tip": 0, "ai_news": 0, "hot_take": 0, "product_showcase": 0}
        for t in (content_mix.data or []):
            ct = t.get("content_type", "sales_tip")
            if ct in mix:
                mix[ct] += 1
        
        return {
            "total_videos": total_videos,
            "total_views": total_views,
            "videos_this_week": videos_this_week,
            "content_mix": mix,
        }
    
    # =========================================================================
    # CONTENT PIPELINE VIEW
    # =========================================================================
    
    def get_content_pipeline(self, limit: int = 20) -> List[Dict]:
        """Get full content pipeline overview."""
        result = self.client.rpc("get_content_pipeline", {"limit_count": limit}).execute()
        return result.data or []

