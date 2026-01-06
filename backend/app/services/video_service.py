"""
Video Service - Generate videos using NanoBanana.
"""
import uuid
import httpx
from loguru import logger

from app.config import get_settings


class VideoService:
    """Service for generating videos using NanoBanana."""
    
    BASE_URL = "https://api.nanobananavideo.com/v1"  # Update with actual URL
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.nanobanana_api_key
    
    def generate_video(
        self,
        script: dict,
        audio_url: str = None,
        style: str = "professional",
        include_captions: bool = True,
    ) -> dict:
        """
        Generate a video from a script.
        
        Returns dict with video_id and video_url.
        """
        if not self.api_key:
            raise ValueError("NanoBanana API key not configured")
        
        logger.info(f"Generating video: {script.get('title', 'Unknown')}")
        
        payload = {
            "script": script.get("full_text", ""),
            "style": style,
            "aspect_ratio": "9:16",  # Vertical for Shorts
            "duration": script.get("total_duration_seconds", 45),
            "captions": {
                "enabled": include_captions,
                "style": "modern"
            },
            "background_music": {
                "enabled": True,
                "volume": 0.3
            }
        }
        
        if audio_url:
            payload["audio_url"] = audio_url
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=300.0) as client:
                # Start generation
                response = client.post(
                    f"{self.BASE_URL}/videos/generate",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    raise Exception(f"NanoBanana error: {response.status_code} - {response.text}")
                
                result = response.json()
                
                return {
                    "id": result.get("id", str(uuid.uuid4())),
                    "video_url": result.get("video_url"),
                    "status": result.get("status", "processing"),
                    "duration_seconds": script.get("total_duration_seconds", 45)
                }
                
        except httpx.TimeoutException:
            raise Exception("Video generation timed out")
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    def get_video_status(self, video_id: str) -> dict:
        """Get the status of a video generation job."""
        if not self.api_key:
            raise ValueError("NanoBanana API key not configured")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        with httpx.Client() as client:
            response = client.get(
                f"{self.BASE_URL}/videos/{video_id}/status",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get status: {response.text}")
            
            return response.json()

