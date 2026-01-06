"""
YouTube Service - Upload videos to YouTube.
"""
from typing import List, Optional
from loguru import logger

from app.config import get_settings


class YouTubeService:
    """Service for uploading videos to YouTube."""
    
    def __init__(self):
        self.settings = get_settings()
        self._credentials = None
    
    def upload_video(
        self,
        video_url: str,
        title: str,
        description: str,
        tags: List[str] = None,
        privacy_status: str = "public",
        is_short: bool = True,
    ) -> dict:
        """
        Upload a video to YouTube.
        
        Returns dict with youtube_id and youtube_url.
        """
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials
        except ImportError:
            raise ImportError("Google API libraries not installed")
        
        # Get credentials from refresh token
        if not self.settings.youtube_refresh_token:
            raise ValueError("YouTube refresh token not configured")
        
        credentials = Credentials(
            token=None,
            refresh_token=self.settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.youtube_client_id,
            client_secret=self.settings.youtube_client_secret,
        )
        
        logger.info(f"Uploading to YouTube: {title}")
        
        youtube = build("youtube", "v3", credentials=credentials)
        
        # Add #Shorts if it's a short
        if is_short and "#Shorts" not in title:
            title = f"{title} #Shorts"
        
        body = {
            "snippet": {
                "title": title,
                "description": f"{description}\n\n🚀 {self.settings.brand_website}",
                "tags": tags or ["sales", "AI", "B2B", self.settings.brand_name],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }
        
        # Download video from URL and upload
        # TODO: Implement video download and upload
        # For now, return placeholder
        
        # In production:
        # 1. Download video from video_url to temp file
        # 2. Upload using MediaFileUpload
        # 3. Return result
        
        return {
            "youtube_id": "placeholder",
            "youtube_url": f"https://youtube.com/shorts/placeholder",
            "status": "uploaded"
        }
    
    def get_channel_videos(self, max_results: int = 20) -> List[dict]:
        """Get recent videos from the channel."""
        # TODO: Implement with YouTube API
        return []

