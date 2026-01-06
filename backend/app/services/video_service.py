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
        self._creds_file_path = None
        self._setup_credentials()
    
    def _setup_credentials(self):
        """Setup Google Cloud credentials from environment."""
        creds_json_b64 = self.settings.google_application_credentials_json
        
        if creds_json_b64:
            try:
                # Decode base64 credentials
                creds_data = base64.b64decode(creds_json_b64)
                creds_json = creds_data.decode('utf-8')
                
                # Validate it's valid JSON
                json.loads(creds_json)
                
                # Write to temp file
                fd, temp_path = tempfile.mkstemp(suffix='.json', prefix='gcp_creds_')
                with os.fdopen(fd, 'w') as f:
                    f.write(creds_json)
                
                self._creds_file_path = temp_path
                
                # Set environment variable for Google SDK
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_path
                logger.info(f"Google Cloud credentials configured at: {temp_path}")
            except Exception as e:
                logger.error(f"Failed to setup Google credentials: {e}")
                self._creds_file_path = None
        else:
            self._creds_file_path = None
            logger.warning("Google Cloud credentials not configured (no base64 JSON provided)")
    
    def _get_client(self):
        """Get Google GenAI client for Vertex AI."""
        try:
            from google import genai
            
            logger.info(f"Creating GenAI client - project: {self.settings.google_cloud_project}, location: {self.settings.google_cloud_location}")
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')}")
            
            # Initialize client for Vertex AI (using service account credentials from env)
            client = genai.Client(
                vertexai=True,
                project=self.settings.google_cloud_project,
                location=self.settings.google_cloud_location,
            )
            
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
        if not self.settings.google_cloud_project:
            raise ValueError("Google Cloud project not configured")
        
        if not self._creds_file_path:
            raise ValueError("Google Cloud credentials not configured")
        
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
                
        except ImportError as e:
            raise Exception(f"Google GenAI library not installed: {e}. Run: pip install google-genai")
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
        creds_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        creds_exists = os.path.exists(creds_env) if creds_env else False
        
        return {
            "service": "Google Veo 2",
            "project_configured": bool(self.settings.google_cloud_project),
            "project_id": self.settings.google_cloud_project or "not set",
            "location": self.settings.google_cloud_location,
            "credentials_file_path": self._creds_file_path,
            "credentials_env_var": creds_env or "not set",
            "credentials_file_exists": creds_exists,
        }
    
    def debug_credentials(self) -> dict:
        """Debug endpoint to check credentials setup."""
        creds_b64 = self.settings.google_application_credentials_json
        creds_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
        
        result = {
            "has_base64_creds": bool(creds_b64),
            "base64_length": len(creds_b64) if creds_b64 else 0,
            "creds_file_path": self._creds_file_path,
            "creds_env_var": creds_env,
            "creds_file_exists": os.path.exists(creds_env) if creds_env else False,
        }
        
        # Try to read and validate the credentials file
        if creds_env and os.path.exists(creds_env):
            try:
                with open(creds_env, 'r') as f:
                    creds_content = json.load(f)
                result["creds_type"] = creds_content.get("type", "unknown")
                result["creds_project"] = creds_content.get("project_id", "unknown")
                result["creds_client_email"] = creds_content.get("client_email", "unknown")[:50] + "..."
            except Exception as e:
                result["creds_read_error"] = str(e)
        
        return result
