"""
NanoBanana Service - AI Video Generation.

NanoBanana is used for generating faceless video content.
Documentation: https://nanobananavideo.com
"""
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import httpx
from loguru import logger

from backend.config import get_settings


class VideoStyle(str, Enum):
    """Available video styles."""
    PROFESSIONAL = "professional"
    MODERN = "modern"
    MINIMAL = "minimal"
    DYNAMIC = "dynamic"


@dataclass
class VideoGenerationRequest:
    """Request for video generation."""
    script: str
    audio_path: Optional[Path] = None
    style: VideoStyle = VideoStyle.PROFESSIONAL
    aspect_ratio: str = "9:16"  # Vertical for Shorts
    duration_seconds: int = 45
    include_captions: bool = True
    caption_style: str = "modern"
    background_music: bool = True
    music_volume: float = 0.3


@dataclass  
class VideoGenerationResult:
    """Result from video generation."""
    video_path: Path
    duration_seconds: float
    file_size_bytes: int
    generation_id: str


class NanoBananaService:
    """
    Service for generating videos using NanoBanana AI.
    
    Creates faceless video content from scripts and audio.
    """
    
    BASE_URL = "https://api.nanobananavideo.com/v1"  # Example URL - update with actual
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.nanobanana_api_key
    
    async def generate_video(
        self,
        request: VideoGenerationRequest,
        output_path: Optional[Path] = None
    ) -> VideoGenerationResult:
        """
        Generate a video from a script.
        
        Args:
            request: The video generation request
            output_path: Where to save the video
        
        Returns:
            VideoGenerationResult with the generated video
        """
        if not self.api_key:
            raise ValueError("NanoBanana API key not configured")
        
        # Generate default output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.settings.shorts_output_dir / f"short_{timestamp}.mp4"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating video with NanoBanana: {request.style.value} style")
        
        # Build the API request
        # Note: This is a placeholder - update with actual NanoBanana API format
        payload = {
            "script": request.script,
            "style": request.style.value,
            "aspect_ratio": request.aspect_ratio,
            "duration": request.duration_seconds,
            "captions": {
                "enabled": request.include_captions,
                "style": request.caption_style
            },
            "background_music": {
                "enabled": request.background_music,
                "volume": request.music_volume
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # If we have audio, we need to upload it first
        if request.audio_path and request.audio_path.exists():
            audio_url = await self._upload_audio(request.audio_path)
            payload["audio_url"] = audio_url
        
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for video gen
            # Start generation
            response = await client.post(
                f"{self.BASE_URL}/videos/generate",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"NanoBanana API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            result = response.json()
            generation_id = result.get("generation_id")
            
            # Poll for completion
            video_url = await self._wait_for_completion(client, headers, generation_id)
            
            # Download the video
            await self._download_video(client, video_url, output_path)
        
        file_size = output_path.stat().st_size
        logger.info(f"Video generated: {output_path} ({file_size} bytes)")
        
        return VideoGenerationResult(
            video_path=output_path,
            duration_seconds=request.duration_seconds,
            file_size_bytes=file_size,
            generation_id=generation_id
        )
    
    async def _upload_audio(self, audio_path: Path) -> str:
        """Upload audio file and return URL."""
        # Placeholder - implement actual upload logic
        logger.info(f"Uploading audio: {audio_path}")
        
        async with httpx.AsyncClient() as client:
            with open(audio_path, "rb") as f:
                response = await client.post(
                    f"{self.BASE_URL}/uploads/audio",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files={"file": f}
                )
            
            if response.status_code != 200:
                raise Exception(f"Audio upload failed: {response.text}")
            
            return response.json().get("url")
    
    async def _wait_for_completion(
        self, 
        client: httpx.AsyncClient,
        headers: dict,
        generation_id: str,
        max_wait_seconds: int = 300
    ) -> str:
        """Wait for video generation to complete."""
        import asyncio
        
        start_time = datetime.now()
        
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > max_wait_seconds:
                raise TimeoutError(f"Video generation timed out after {max_wait_seconds}s")
            
            response = await client.get(
                f"{self.BASE_URL}/videos/{generation_id}/status",
                headers=headers
            )
            
            if response.status_code != 200:
                raise Exception(f"Status check failed: {response.text}")
            
            status = response.json()
            
            if status.get("status") == "completed":
                return status.get("video_url")
            
            if status.get("status") == "failed":
                raise Exception(f"Video generation failed: {status.get('error')}")
            
            logger.debug(f"Video generation in progress... ({elapsed:.0f}s)")
            await asyncio.sleep(5)  # Poll every 5 seconds
    
    async def _download_video(
        self,
        client: httpx.AsyncClient,
        video_url: str,
        output_path: Path
    ):
        """Download the generated video."""
        response = await client.get(video_url)
        
        if response.status_code != 200:
            raise Exception(f"Video download failed: {response.status_code}")
        
        with open(output_path, "wb") as f:
            f.write(response.content)


class MockNanoBananaService(NanoBananaService):
    """
    Mock service for testing without API calls.
    Creates a placeholder video file.
    """
    
    async def generate_video(
        self,
        request: VideoGenerationRequest,
        output_path: Optional[Path] = None
    ) -> VideoGenerationResult:
        """Generate a mock video for testing."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.settings.shorts_output_dir / f"short_{timestamp}.mp4"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[MOCK] Generating placeholder video: {output_path}")
        
        # Create a placeholder file
        with open(output_path, "wb") as f:
            f.write(b"MOCK_VIDEO_PLACEHOLDER")
        
        return VideoGenerationResult(
            video_path=output_path,
            duration_seconds=request.duration_seconds,
            file_size_bytes=output_path.stat().st_size,
            generation_id="mock_generation_123"
        )


# Factory function
def get_nanobanana_service(mock: bool = False) -> NanoBananaService:
    """Get NanoBanana service instance."""
    if mock:
        return MockNanoBananaService()
    return NanoBananaService()

