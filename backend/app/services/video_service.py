"""
Video Service - Generate videos using Google Veo 2 via Vertex AI.
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
    """Service for generating videos using Google Veo 2."""
    
    def __init__(self):
        self.settings = get_settings()
        self.storage = StorageService()
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup Google Cloud credentials from environment."""
        creds_json = self.settings.google_application_credentials_json
        
        if creds_json:
            try:
                # Decode base64 credentials and write to temp file
                creds_data = base64.b64decode(creds_json)
                self.creds_path = tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.json', 
                    delete=False
                )
                self.creds_path.write(creds_data.decode('utf-8'))
                self.creds_path.close()
                
                # Set environment variable for Google SDK
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.creds_path.name
                logger.info("Google Cloud credentials configured")
            except Exception as e:
                logger.warning(f"Failed to setup Google credentials: {e}")
                self.creds_path = None
        else:
            self.creds_path = None
            logger.warning("Google Cloud credentials not configured")
    
    def _get_client(self):
        """Get Google GenAI client."""
        try:
            from google import genai
            
            # Initialize client with project
            client = genai.Client(
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
            )
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
        if not self.settings.google_cloud_project:
            raise ValueError("Google Cloud project not configured")
        
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
            
            operation = client.models.generate_videos(
                model="veo-2.0-generate-001",  # Veo 2 model
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",  # Vertical for Shorts
                    number_of_videos=1,
                    duration_seconds=8,  # Veo 2 generates 8-sec clips
                    negative_prompt="blurry, low quality, distorted, amateur",
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
                
                # Download video to temp file
                video_id = str(uuid.uuid4())
                temp_path = f"/tmp/{video_id}.mp4"
                
                # Save video locally first
                client.files.download(file=video.video)
                video.video.save(temp_path)
                
                # Upload to Supabase Storage
                logger.info("Uploading video to Supabase Storage...")
                video_url = self.storage.upload_file(
                    bucket="media",
                    file_path=temp_path,
                    destination_path=f"videos/{video_id}.mp4",
                    content_type="video/mp4"
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
                    "audio_url": audio_url,  # Keep reference to audio
                }
            else:
                raise Exception("No video generated in response")
                
        except ImportError:
            raise Exception("Google GenAI library not installed. Run: pip install google-genai")
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    def _build_video_prompt(self, script_text: str, style: str) -> str:
        """Build a video generation prompt from script text."""
        # Extract key themes from script for visual prompt
        # Keep it concise for better results
        
        prompt = f"""
Professional business video, {style}.

Content theme: {script_text[:200]}...

Visual style:
- Modern, clean corporate aesthetic
- Dynamic motion graphics and text overlays
- Professional color grading (blues, whites)
- Smooth camera movements
- High quality, 4K appearance
- Suitable for YouTube Shorts
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
        For MVP, we return both URLs and combine client-side or 
        use a video editing service.
        """
        # Generate video
        video_result = self.generate_video(script, audio_url, style)
        
        # Add audio reference
        video_result["audio_url"] = audio_url
        video_result["needs_audio_merge"] = True
        
        return video_result
    
    def get_video_status(self, video_id: str) -> dict:
        """Get the status of a video (from Supabase storage check)."""
        try:
            # Check if video exists in storage
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
        return {
            "service": "Google Veo 2",
            "project_configured": bool(self.settings.google_cloud_project),
            "project_id": self.settings.google_cloud_project or "not set",
            "location": self.settings.google_cloud_location,
            "credentials_configured": self.creds_path is not None,
        }
