"""
YouTube Service - Upload videos to YouTube.
"""
import os
import tempfile
from typing import List
import httpx
from loguru import logger

from app.config import get_settings


class YouTubeService:
    """Service for uploading videos to YouTube."""
    
    def __init__(self):
        self.settings = get_settings()
        self._youtube = None
    
    def _get_youtube_client(self):
        """Get authenticated YouTube API client."""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        if not self.settings.youtube_refresh_token:
            raise ValueError("YOUTUBE_REFRESH_TOKEN not configured")
        
        if not self.settings.youtube_client_id:
            raise ValueError("YOUTUBE_CLIENT_ID not configured")
        
        if not self.settings.youtube_client_secret:
            raise ValueError("YOUTUBE_CLIENT_SECRET not configured")
        
        credentials = Credentials(
            token=None,
            refresh_token=self.settings.youtube_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.youtube_client_id,
            client_secret=self.settings.youtube_client_secret,
        )
        
        return build("youtube", "v3", credentials=credentials)
    
    def health_check(self) -> dict:
        """Check if YouTube service is properly configured."""
        return {
            "service": "YouTube Data API v3",
            "client_id_configured": bool(self.settings.youtube_client_id),
            "client_secret_configured": bool(self.settings.youtube_client_secret),
            "refresh_token_configured": bool(self.settings.youtube_refresh_token),
            "channel_id": self.settings.youtube_channel_id or "not set",
        }
    
    def test_connection(self) -> dict:
        """Test the YouTube API connection."""
        try:
            youtube = self._get_youtube_client()
            
            # Try to get channel info
            request = youtube.channels().list(
                part="snippet,statistics",
                mine=True
            )
            response = request.execute()
            
            if response.get("items"):
                channel = response["items"][0]
                return {
                    "success": True,
                    "channel_id": channel["id"],
                    "channel_title": channel["snippet"]["title"],
                    "subscribers": channel["statistics"].get("subscriberCount", "hidden"),
                    "video_count": channel["statistics"].get("videoCount", 0),
                }
            else:
                return {
                    "success": False,
                    "error": "No channel found for this account"
                }
                
        except Exception as e:
            logger.error(f"YouTube connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
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
        
        Args:
            video_url: URL to the video file (from Supabase Storage)
            title: Video title
            description: Video description
            tags: List of tags
            privacy_status: public, private, or unlisted
            is_short: Whether this is a YouTube Short
            
        Returns:
            dict with youtube_id, youtube_url, status
        """
        from googleapiclient.http import MediaFileUpload
        
        logger.info(f"📺 Uploading to YouTube: {title}")
        
        # Download video from URL to temp file
        logger.info(f"Downloading video from: {video_url}")
        temp_path = self._download_video(video_url)
        
        try:
            youtube = self._get_youtube_client()
            
            # Add #Shorts if it's a short
            if is_short and "#Shorts" not in title:
                title = f"{title} #Shorts"
            
            # Prepare metadata
            body = {
                "snippet": {
                    "title": title[:100],  # Max 100 chars
                    "description": f"{description}\n\n🚀 {self.settings.brand_website}",
                    "tags": tags or ["sales", "AI", "B2B", self.settings.brand_name],
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                }
            }
            
            # Upload video
            media = MediaFileUpload(
                temp_path,
                mimetype="video/mp4",
                resumable=True
            )
            
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = request.execute()
            
            youtube_id = response["id"]
            youtube_url = f"https://youtube.com/shorts/{youtube_id}" if is_short else f"https://youtube.com/watch?v={youtube_id}"
            
            logger.info(f"✅ Video uploaded: {youtube_url}")
            
            return {
                "youtube_id": youtube_id,
                "youtube_url": youtube_url,
                "status": "uploaded"
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def _download_video(self, video_url: str) -> str:
        """Download video from URL to temp file."""
        with httpx.Client(timeout=120.0) as client:
            response = client.get(video_url)
            response.raise_for_status()
            
            # Save to temp file
            fd, temp_path = tempfile.mkstemp(suffix=".mp4")
            with os.fdopen(fd, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Video downloaded to: {temp_path} ({len(response.content)} bytes)")
            return temp_path
    
    def get_channel_videos(self, max_results: int = 20) -> List[dict]:
        """Get recent videos from the channel."""
        try:
            youtube = self._get_youtube_client()
            
            request = youtube.search().list(
                part="snippet",
                channelId=self.settings.youtube_channel_id,
                maxResults=max_results,
                order="date",
                type="video"
            )
            response = request.execute()
            
            videos = []
            for item in response.get("items", []):
                videos.append({
                    "youtube_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail_url": item["snippet"]["thumbnails"]["default"]["url"],
                })
            
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []
