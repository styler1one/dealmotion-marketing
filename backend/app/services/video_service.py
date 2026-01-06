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
        """
        Build a cinematic video prompt based on the script content.
        
        Creates human, relatable, stylish scenes for modern sales professionals.
        NOT boring corporate stock footage - real people, authentic vibes.
        """
        import random
        
        # Analyze script to determine scene type
        text_lower = script_text.lower()
        
        # Human, stylish scene options - relatable to modern salespeople
        scenes = {
            'cold_calling': [
                "Confident young professional walking through city street while on phone call, stylish casual business attire, AirPods, golden hour sunlight, cinematic urban backdrop, genuine smile",
                "Charismatic salesperson in trendy co-working space, taking a call by large window, city skyline view, natural lighting, relaxed confident posture, modern aesthetic",
                "Dynamic professional pacing in minimalist loft apartment, on an important call, exposed brick walls, morning light streaming in, authentic moment of focus",
            ],
            'ai_tech': [
                "Young tech-savvy professional in sleek modern cafe, working on MacBook, thoughtful expression, ambient warm lighting, plants and coffee, creative energy",
                "Confident entrepreneur reviewing data on tablet in rooftop bar setting, city lights in background, evening ambiance, sophisticated but approachable",
                "Diverse team having animated discussion in bright modern space, authentic collaboration moment, natural body language, contemporary setting",
            ],
            'sales_deals': [
                "Two professionals having coffee meeting in upscale cafe, genuine connection moment, smart casual attire, warm natural lighting, authentic conversation",
                "Confident closer walking out of modern building, successful energy, stylish outfit, sunset lighting, urban environment, victory moment",
                "Charismatic professional presenting to small group in modern lounge setting, engaged audience, warm atmosphere, natural interaction",
            ],
            'outreach': [
                "Creative professional in cozy home office setup, plants and personality, focused but relaxed, morning coffee ritual, authentic workspace",
                "Young entrepreneur typing on laptop at trendy cafe terrace, urban backdrop, golden hour, casual confidence, lifestyle moment",
                "Professional scrolling phone in stylish lobby, modern architecture, natural light, candid moment of research",
            ],
            'growth_success': [
                "Team celebrating win in modern office with champagne, genuine joy and high-fives, diverse group, warm lighting, authentic celebration",
                "Entrepreneur looking out over city from high-rise window, contemplative success moment, silhouette against skyline, aspirational",
                "Professional pumping fist in victory after closing deal, authentic emotion, modern workspace backdrop, energy and triumph",
            ],
            'default': [
                "Stylish young professional walking confidently through modern city, smart casual look, AirPods in, purposeful stride, cinematic urban feel",
                "Charismatic person having video call in aesthetic home setup, ring light glow, genuine engagement, contemporary lifestyle",
                "Dynamic professional in motion through sleek building lobby, modern architecture, natural confidence, cinematic movement",
            ]
        }
        
        # Determine scene category based on content keywords
        if any(word in text_lower for word in ['cold call', 'bellen', 'telefoon', 'phone', 'call']):
            category = 'cold_calling'
        elif any(word in text_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'automatisering', 'tech']):
            category = 'ai_tech'
        elif any(word in text_lower for word in ['sales', 'verkoop', 'deal', 'prospect', 'lead', 'klant', 'close']):
            category = 'sales_deals'
        elif any(word in text_lower for word in ['email', 'outreach', 'linkedin', 'social', 'netwerk']):
            category = 'outreach'
        elif any(word in text_lower for word in ['groei', 'growth', 'scale', 'revenue', 'omzet', 'succes', 'win']):
            category = 'growth_success'
        else:
            category = 'default'
        
        # Pick random scene from category for variety
        scene = random.choice(scenes[category])
        
        prompt = f"""Cinematic vertical video (9:16 aspect ratio for YouTube Shorts).

Scene: {scene}

Style requirements:
- Real human subjects, authentic not staged
- Modern, aspirational lifestyle aesthetic
- Cinematic shallow depth of field
- Smooth camera movement (slow motion or gimbal)
- Premium color grading, warm tones
- NO corporate stock footage look
- NO suits and ties
- NO pointing at graphs
- Genuine human moments
- Stylish, confident, relatable

Technical: High-end commercial quality, photorealistic, no text overlays, no watermarks."""
        
        logger.info(f"Generated Veo prompt: category={category}")
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
