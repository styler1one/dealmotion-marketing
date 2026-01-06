"""
Render Service - Create final videos with Creatomate (audio + video + captions).
"""
import time
import httpx
from typing import List, Optional
from loguru import logger

from app.config import get_settings
from app.services.storage_service import StorageService


class RenderService:
    """Service for rendering final videos with Creatomate."""
    
    BASE_URL = "https://api.creatomate.com/v1"
    
    def __init__(self):
        self.settings = get_settings()
        self.storage = StorageService()
    
    def health_check(self) -> dict:
        """Check if Creatomate is configured."""
        return {
            "service": "Creatomate",
            "api_key_configured": bool(self.settings.creatomate_api_key),
            "template_id": self.settings.creatomate_template_id or "not set",
        }
    
    def render_short(
        self,
        script_segments: List[dict],
        audio_url: str,
        background_video_url: Optional[str] = None,
        music_url: Optional[str] = None,
    ) -> dict:
        """
        Render a YouTube Short with animated captions.
        
        Args:
            script_segments: List of text segments with timing
            audio_url: URL to the voice-over audio
            background_video_url: URL to background video (from Veo)
            music_url: Optional background music URL
            
        Returns:
            dict with render_id and video_url
        """
        if not self.settings.creatomate_api_key:
            raise ValueError("CREATOMATE_API_KEY not configured")
        
        if not self.settings.creatomate_template_id:
            raise ValueError("CREATOMATE_TEMPLATE_ID not configured")
        
        logger.info(f"🎬 Starting Creatomate render with {len(script_segments)} segments")
        
        # Build modifications for the template
        modifications = self._build_modifications(
            script_segments=script_segments,
            audio_url=audio_url,
            background_video_url=background_video_url,
            music_url=music_url,
        )
        
        # Start render
        render_response = self._start_render(modifications)
        render_id = render_response.get("id")
        
        logger.info(f"Render started: {render_id}")
        
        # Poll for completion
        result = self._wait_for_render(render_id)
        
        if result.get("status") == "succeeded":
            video_url = result.get("url")
            logger.info(f"✅ Render completed: {video_url}")
            
            return {
                "render_id": render_id,
                "video_url": video_url,
                "status": "completed",
            }
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"Render failed: {error}")
            raise Exception(f"Render failed: {error}")
    
    def _build_modifications(
        self,
        script_segments: List[dict],
        audio_url: str,
        background_video_url: Optional[str],
        music_url: Optional[str],
    ) -> dict:
        """Build Creatomate modifications from script segments."""
        modifications = {}
        
        # Add audio (voice-over)
        if audio_url:
            modifications["Audio.source"] = audio_url
        
        # Add background video if provided
        if background_video_url:
            # Apply same background to all scenes
            for i in range(1, 5):
                modifications[f"Background-{i}.source"] = background_video_url
        
        # Add music if provided
        if music_url:
            modifications["Music.source"] = music_url
            modifications["Music.volume"] = "30%"  # Lower volume for voice-over
        
        # Add text segments
        for i, segment in enumerate(script_segments[:4], start=1):
            text = segment.get("text", "")
            modifications[f"Text-{i}.text"] = text
        
        return modifications
    
    def _start_render(self, modifications: dict) -> dict:
        """Start a Creatomate render job."""
        headers = {
            "Authorization": f"Bearer {self.settings.creatomate_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "template_id": self.settings.creatomate_template_id,
            "modifications": modifications,
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.BASE_URL}/renders",
                headers=headers,
                json=payload,
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Creatomate API error: {response.status_code} - {response.text}")
            
            # Response is a list with one render
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
    
    def _wait_for_render(self, render_id: str, max_wait: int = 300) -> dict:
        """Poll for render completion."""
        headers = {
            "Authorization": f"Bearer {self.settings.creatomate_api_key}",
        }
        
        waited = 0
        poll_interval = 5
        
        with httpx.Client(timeout=30.0) as client:
            while waited < max_wait:
                response = client.get(
                    f"{self.BASE_URL}/renders/{render_id}",
                    headers=headers,
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get render status: {response.text}")
                
                result = response.json()
                status = result.get("status")
                
                logger.info(f"Render status: {status} ({waited}s)")
                
                if status == "succeeded":
                    return result
                elif status == "failed":
                    return result
                
                time.sleep(poll_interval)
                waited += poll_interval
        
        raise Exception("Render timed out")
    
    def render_simple_short(
        self,
        texts: List[str],
        audio_url: str,
        background_video_url: Optional[str] = None,
    ) -> dict:
        """
        Simplified render for a short with just text segments.
        
        Args:
            texts: List of 4 text strings for each scene
            audio_url: Voice-over audio URL
            background_video_url: Background video URL
        """
        # Convert texts to segments
        segments = [{"text": text} for text in texts]
        
        return self.render_short(
            script_segments=segments,
            audio_url=audio_url,
            background_video_url=background_video_url,
        )

