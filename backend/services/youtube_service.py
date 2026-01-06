"""
YouTube Service - Upload and manage YouTube videos.
"""
import os
import pickle
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from backend.config import get_settings


@dataclass
class VideoUploadRequest:
    """Request for video upload."""
    video_path: Path
    title: str
    description: str
    tags: List[str]
    category_id: str = "22"  # People & Blogs (good for business content)
    privacy_status: str = "public"  # "public", "private", "unlisted"
    is_short: bool = True
    scheduled_time: Optional[datetime] = None


@dataclass
class VideoUploadResult:
    """Result from video upload."""
    video_id: str
    video_url: str
    status: str
    upload_time: datetime


class YouTubeService:
    """
    Service for uploading videos to YouTube.
    
    Uses YouTube Data API v3 with OAuth2 authentication.
    """
    
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    
    def __init__(self):
        self.settings = get_settings()
        self._credentials = None
    
    def authenticate(self, token_path: Optional[Path] = None) -> bool:
        """
        Authenticate with YouTube API.
        
        First time requires browser authentication.
        Subsequently uses saved token.
        """
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
        except ImportError:
            logger.error("Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib")
            return False
        
        token_path = token_path or Path("token.pickle")
        credentials_path = Path("credentials.json")
        
        # Check for existing token
        if token_path.exists():
            with open(token_path, "rb") as token:
                self._credentials = pickle.load(token)
        
        # Refresh or get new credentials
        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                logger.info("Refreshing YouTube credentials...")
                self._credentials.refresh(Request())
            else:
                if not credentials_path.exists():
                    logger.error(f"credentials.json not found. Download from Google Cloud Console.")
                    return False
                
                logger.info("Starting YouTube OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), self.SCOPES
                )
                self._credentials = flow.run_local_server(port=0)
            
            # Save credentials for next time
            with open(token_path, "wb") as token:
                pickle.dump(self._credentials, token)
        
        logger.info("YouTube authentication successful")
        return True
    
    def upload_video(self, request: VideoUploadRequest) -> VideoUploadResult:
        """
        Upload a video to YouTube.
        
        Args:
            request: The upload request with video details
        
        Returns:
            VideoUploadResult with video ID and URL
        """
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError:
            raise ImportError("Google API libraries not installed")
        
        if not self._credentials:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        if not request.video_path.exists():
            raise FileNotFoundError(f"Video not found: {request.video_path}")
        
        logger.info(f"Uploading video: {request.title}")
        
        # Build YouTube API client
        youtube = build("youtube", "v3", credentials=self._credentials)
        
        # Prepare video metadata
        body = {
            "snippet": {
                "title": request.title,
                "description": request.description,
                "tags": request.tags,
                "categoryId": request.category_id,
            },
            "status": {
                "privacyStatus": request.privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }
        
        # Add #Shorts to title if it's a short
        if request.is_short and "#Shorts" not in request.title:
            body["snippet"]["title"] = f"{request.title} #Shorts"
        
        # Add scheduling if specified
        if request.scheduled_time and request.privacy_status == "private":
            body["status"]["publishAt"] = request.scheduled_time.isoformat()
        
        # Prepare media upload
        media = MediaFileUpload(
            str(request.video_path),
            mimetype="video/mp4",
            resumable=True
        )
        
        # Execute upload
        insert_request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = insert_request.next_chunk()
            if status:
                logger.debug(f"Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response["id"]
        video_url = f"https://youtube.com/watch?v={video_id}"
        
        logger.info(f"Video uploaded: {video_url}")
        
        return VideoUploadResult(
            video_id=video_id,
            video_url=video_url,
            status="uploaded",
            upload_time=datetime.now()
        )
    
    def get_channel_videos(self, max_results: int = 10) -> List[dict]:
        """Get recent videos from the authenticated channel."""
        try:
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError("Google API libraries not installed")
        
        if not self._credentials:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        youtube = build("youtube", "v3", credentials=self._credentials)
        
        # Get channel ID
        channels_response = youtube.channels().list(
            mine=True,
            part="contentDetails"
        ).execute()
        
        if not channels_response.get("items"):
            return []
        
        uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Get videos from uploads playlist
        videos_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=max_results
        ).execute()
        
        videos = []
        for item in videos_response.get("items", []):
            snippet = item["snippet"]
            videos.append({
                "video_id": snippet["resourceId"]["videoId"],
                "title": snippet["title"],
                "published_at": snippet["publishedAt"],
                "thumbnail": snippet["thumbnails"].get("default", {}).get("url")
            })
        
        return videos


class MockYouTubeService(YouTubeService):
    """Mock service for testing without actual uploads."""
    
    def authenticate(self, token_path: Optional[Path] = None) -> bool:
        """Mock authentication."""
        logger.info("[MOCK] YouTube authentication successful")
        self._credentials = True
        return True
    
    def upload_video(self, request: VideoUploadRequest) -> VideoUploadResult:
        """Mock video upload."""
        logger.info(f"[MOCK] Would upload: {request.title}")
        
        video_id = f"mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return VideoUploadResult(
            video_id=video_id,
            video_url=f"https://youtube.com/watch?v={video_id}",
            status="mock_uploaded",
            upload_time=datetime.now()
        )


# Factory function
def get_youtube_service(mock: bool = False) -> YouTubeService:
    """Get YouTube service instance."""
    if mock:
        return MockYouTubeService()
    return YouTubeService()

