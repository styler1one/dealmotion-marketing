"""
Video Service - Generate videos using Google Veo 2 via Gemini API.
"""
import os
import json
import base64
import time
import uuid
import tempfile
from pathlib import Path
from loguru import logger

from app.config import get_settings
from app.services.storage_service import StorageService


class VideoService:
    """Service for generating videos using Google Veo 2 via Gemini API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.storage = StorageService()
    
    def _get_client(self):
        """Get Google GenAI client using Gemini API key."""
        try:
            from google import genai
            
            api_key = self.settings.google_gemini_api_key
            
            if not api_key:
                raise ValueError("GOOGLE_GEMINI_API_KEY not configured")
            
            logger.info("Creating GenAI client with Gemini API key...")
            
            # Initialize client with API key (Gemini Developer API)
            client = genai.Client(api_key=api_key)
            
            logger.info("GenAI client created successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to create GenAI client: {e}")
            raise
    
    def generate_video(
        self,
        script: dict,
        audio_url: str = None,
        style: str = "professional B2B content",
    ) -> dict:
        """
        Generate a video from a script using Google Veo 2.
        
        Args:
            script: Script dict with title, full_text, segments
            audio_url: URL to the audio file (from ElevenLabs/Supabase)
            style: Visual style description
            
        Returns:
            dict with video_id, video_url, status
        """
        if not self.settings.google_gemini_api_key:
            raise ValueError("Google Gemini API key not configured")
        
        title = script.get('title', 'Unknown')
        logger.info(f"🎬 Generating video: {title}")
        
        # Build the video prompt from script
        full_text = script.get('full_text', '')
        prompt = self._build_video_prompt(full_text, style)
        
        try:
            from google import genai
            from google.genai import types
            
            client = self._get_client()
            
            # Start video generation with Veo 2
            logger.info("Starting Veo 2 video generation...")
            logger.info(f"Prompt: {prompt[:200]}...")
            
            operation = client.models.generate_videos(
                model="veo-2.0-generate-001",  # Veo 2 model
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",  # Vertical for Shorts
                    number_of_videos=1,
                    duration_seconds=8,  # Veo 2 generates 8-sec clips
                    negative_prompt="blurry, low quality, distorted, amateur, cartoon",
                ),
            )
            
            # Wait for generation to complete (with timeout)
            max_wait = 300  # 5 minutes
            waited = 0
            poll_interval = 10
            
            while not operation.done and waited < max_wait:
                logger.info(f"Video generation in progress... ({waited}s)")
                time.sleep(poll_interval)
                waited += poll_interval
                operation = client.operations.get(operation)
            
            if not operation.done:
                raise Exception("Video generation timed out after 5 minutes")
            
            # Get the generated video
            if operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0]
                
                # Download video
                video_id = str(uuid.uuid4())
                
                logger.info("Downloading generated video...")
                client.files.download(file=video.video)
                
                # Save to temp file first
                temp_path = f"/tmp/{video_id}.mp4"
                video.video.save(temp_path)
                
                # Read video bytes
                with open(temp_path, 'rb') as f:
                    video_bytes = f.read()
                
                # Upload to Supabase Storage
                logger.info(f"Uploading video to Supabase Storage ({len(video_bytes)} bytes)...")
                video_url = self.storage.upload_video(
                    video_bytes=video_bytes,
                    filename=f"videos/{video_id}.mp4"
                )
                
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                logger.info(f"✅ Video generated successfully: {video_url}")
                
                return {
                    "id": video_id,
                    "video_url": video_url,
                    "status": "completed",
                    "duration_seconds": 8,
                    "audio_url": audio_url,
                }
            else:
                raise Exception("No video generated in response")
                
        except ImportError as e:
            raise Exception(f"Google GenAI library not installed: {e}. Run: pip install google-genai")
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    def _build_video_prompt(self, script_text: str, style: str) -> str:
        """Build a video generation prompt from script text."""
        prompt = f"""
Professional business video, {style}.

Content theme: {script_text[:200]}

Visual style:
- Modern, clean corporate aesthetic
- Dynamic motion graphics
- Professional color grading (blues, whites)
- Smooth camera movements
- High quality, cinematic appearance
- Suitable for YouTube Shorts (vertical 9:16)
"""
        return prompt.strip()
    
    def generate_video_with_audio(
        self,
        script: dict,
        audio_url: str,
        style: str = "professional B2B content",
    ) -> dict:
        """
        Generate video and combine with audio.
        
        Note: Veo 2 generates video without audio, so we need to 
        combine the video with ElevenLabs audio in post-processing.
        """
        video_result = self.generate_video(script, audio_url, style)
        video_result["audio_url"] = audio_url
        video_result["needs_audio_merge"] = True
        return video_result
    
    def get_video_status(self, video_id: str) -> dict:
        """Get the status of a video (from Supabase storage check)."""
        try:
            video_url = f"{self.settings.supabase_url}/storage/v1/object/public/media/videos/{video_id}.mp4"
            return {
                "id": video_id,
                "status": "completed",
                "video_url": video_url
            }
        except Exception as e:
            logger.error(f"Failed to get video status: {e}")
            return {
                "id": video_id,
                "status": "unknown",
                "error": str(e)
            }
    
    def health_check(self) -> dict:
        """Check if video service is properly configured."""
        api_key = self.settings.google_gemini_api_key
        return {
            "service": "Google Veo 2 (Gemini API)",
            "api_key_configured": bool(api_key),
            "api_key_prefix": api_key[:10] + "..." if api_key else "not set",
        }
    
    def debug_credentials(self) -> dict:
        """Debug endpoint to check credentials setup."""
        api_key = self.settings.google_gemini_api_key
        return {
            "gemini_api_key_configured": bool(api_key),
            "gemini_api_key_length": len(api_key) if api_key else 0,
            "gemini_api_key_prefix": api_key[:10] + "..." if api_key else "not set",
        }
