"""
Video Service - Generate dynamic B2B videos using Google Veo 2.

For YouTube Shorts: multiple scenes, visual variety, movement.
"""
import os
import time
import uuid
import random
from typing import List
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
        style: str = "dynamic B2B",
    ) -> dict:
        """
        Generate a single background video clip.
        
        For Shorts, we generate this as one dynamic clip.
        Scene variety comes from Creatomate template.
        """
        if not self.settings.google_gemini_api_key:
            raise ValueError("Google Gemini API key not configured")
        
        title = script.get('title', 'Unknown')
        logger.info(f"🎬 Generating video: {title}")
        
        # Build dynamic video prompt
        full_text = script.get('full_text', '')
        prompt = self._build_video_prompt(full_text, style)
        
        try:
            from google import genai
            from google.genai import types
            
            client = self._get_client()
            
            logger.info("Starting Veo 2 video generation...")
            logger.info(f"Prompt: {prompt[:300]}...")
            
            operation = client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",
                    number_of_videos=1,
                    duration_seconds=8,
                    negative_prompt="text, watermarks, logos, blurry, low quality, amateur, cartoon, anime, stock photo watermark",
                ),
            )
            
            # Wait for generation
            max_wait = 300
            waited = 0
            poll_interval = 10
            
            while not operation.done and waited < max_wait:
                logger.info(f"Video generation in progress... ({waited}s)")
                time.sleep(poll_interval)
                waited += poll_interval
                operation = client.operations.get(operation)
            
            if not operation.done:
                raise Exception("Video generation timed out after 5 minutes")
            
            if operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0]
                video_id = str(uuid.uuid4())
                
                logger.info("Downloading generated video...")
                client.files.download(file=video.video)
                
                temp_path = f"/tmp/{video_id}.mp4"
                video.video.save(temp_path)
                
                with open(temp_path, 'rb') as f:
                    video_bytes = f.read()
                
                logger.info(f"Uploading video to Supabase Storage ({len(video_bytes)} bytes)...")
                video_url = self.storage.upload_video(
                    video_bytes=video_bytes,
                    filename=f"videos/{video_id}.mp4"
                )
                
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
            raise Exception(f"Google GenAI library not installed: {e}")
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            raise
    
    def generate_multiple_clips(
        self,
        script: dict,
        num_clips: int = 4,
        audio_url: str = None,
    ) -> List[dict]:
        """
        Generate multiple short video clips for scene variety.
        
        This creates different scenes that can be used in Creatomate template.
        Each clip is ~5 seconds.
        
        Note: This is slower but creates better visual variety.
        """
        if not self.settings.google_gemini_api_key:
            raise ValueError("Google Gemini API key not configured")
        
        title = script.get('title', 'Unknown')
        full_text = script.get('full_text', '')
        
        logger.info(f"🎬 Generating {num_clips} video clips for: {title}")
        
        clips = []
        scene_types = self._get_scene_variety()[:num_clips]
        
        for i, scene_prompt in enumerate(scene_types):
            logger.info(f"Generating clip {i+1}/{num_clips}...")
            
            try:
                clip = self._generate_single_clip(scene_prompt)
                clips.append(clip)
            except Exception as e:
                logger.error(f"Failed to generate clip {i+1}: {e}")
                # Continue with other clips
        
        return clips
    
    def _generate_single_clip(self, scene_prompt: str) -> dict:
        """Generate a single short clip with specific scene."""
        from google import genai
        from google.genai import types
        
        client = self._get_client()
        
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=scene_prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                number_of_videos=1,
                duration_seconds=5,  # Shorter clips for variety
                negative_prompt="text, watermarks, blurry, amateur",
            ),
        )
        
        # Wait for generation
        max_wait = 180
        waited = 0
        poll_interval = 10
        
        while not operation.done and waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            operation = client.operations.get(operation)
        
        if operation.result and operation.result.generated_videos:
            video = operation.result.generated_videos[0]
            video_id = str(uuid.uuid4())
            
            client.files.download(file=video.video)
            temp_path = f"/tmp/{video_id}.mp4"
            video.video.save(temp_path)
            
            with open(temp_path, 'rb') as f:
                video_bytes = f.read()
            
            video_url = self.storage.upload_video(
                video_bytes=video_bytes,
                filename=f"videos/{video_id}.mp4"
            )
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                "id": video_id,
                "video_url": video_url,
                "duration_seconds": 5,
            }
        
        raise Exception("No video generated")
    
    def _get_scene_variety(self) -> List[str]:
        """
        Get varied scene prompts for different clips.
        Each scene should be visually distinct but cohesive.
        """
        return [
            # Scene 1: Urban movement
            """Cinematic vertical video (9:16).
            
            Busy city street at golden hour, camera tracking alongside a person walking purposefully.
            Shallow depth of field, background blurred. Modern architecture visible.
            Professional, cinematic look. Natural movement, slight camera shake.
            
            Style: Modern, clean, professional. Warm but not oversaturated.
            Camera: Smooth tracking shot, following subject.""",
            
            # Scene 2: Office environment
            """Cinematic vertical video (9:16).
            
            Modern office interior, glass walls and clean lines.
            Person walking through, seen from behind, movement through space.
            Natural lighting from large windows. Minimal, professional aesthetic.
            
            Style: Contemporary, clean, tech-forward. Cool tones with warm highlights.
            Camera: Steadicam following shot, smooth motion.""",
            
            # Scene 3: Contemplative moment
            """Cinematic vertical video (9:16).
            
            Person standing at large window, city skyline visible.
            Slight movement - turning head, shifting weight. Thoughtful pose.
            Beautiful natural light, silhouette effect possible.
            
            Style: Dramatic, cinematic, introspective. Mixed cool and warm light.
            Camera: Slow push in or subtle dolly movement.""",
            
            # Scene 4: Coffee/meeting environment
            """Cinematic vertical video (9:16).
            
            Modern café or meeting space. Person at table, possibly with laptop.
            Natural movement - reaching for coffee, gesturing, typing.
            Warm ambient lighting, bokeh background with other people.
            
            Style: Intimate, professional, relatable. Warm tones.
            Camera: Medium shot, slight handheld movement for authenticity.""",
            
            # Scene 5: Walking with purpose
            """Cinematic vertical video (9:16).
            
            Low angle tracking shot of person walking, only legs and feet visible.
            Modern flooring - concrete, wood, or polished surface.
            Confident pace, professional shoes. Sense of purpose and movement.
            
            Style: Dynamic, modern, professional. Neutral tones.
            Camera: Low tracking shot, smooth motion.""",
            
            # Scene 6: Technology interaction
            """Cinematic vertical video (9:16).
            
            Close-up of hands working on laptop or phone. Screen glow on face.
            Modern device, clean desk setup. Subtle finger movements.
            Professional environment suggested through lighting and props.
            
            Style: Tech-forward, clean, professional. Blue/white light mix.
            Camera: Close-up, slight movement, shallow depth of field.""",
        ]
    
    def _build_video_prompt(self, script_text: str, style: str) -> str:
        """
        Build a dynamic video prompt suitable for Shorts.
        
        Key for Shorts:
        - Movement and energy
        - Professional but not sterile
        - Visually interesting
        - Matches B2B professional context
        """
        
        # Dynamic scenes with movement
        dynamic_scenes = [
            # Urban/walking scenes
            "Person walking confidently through modern city street, golden hour lighting, camera tracking alongside, shallow depth of field, professional attire",
            "Busy financial district, person walking through crowd, camera following from behind, dynamic movement, modern architecture",
            "Walking up steps of modern office building, camera low angle tracking upward, sense of purpose and momentum",
            
            # Office/work scenes
            "Modern open office space, person walking between desks, natural daylight through large windows, slight camera movement",
            "Glass meeting room, person standing at whiteboard gesturing, dynamic hand movements, professional environment",
            "Person at standing desk, slight movements while working, modern workspace with plants and natural light",
            
            # Thinking/transition scenes
            "Person at window looking out at city, slight turn of head, contemplative but energetic, natural lighting",
            "Walking through modern lobby, revolving door, camera following smoothly, sense of arrival or departure",
            "Coffee shop, person looking up from laptop, slight smile, warm ambient lighting, authentic moment",
            
            # Dynamic close-ups
            "Hands typing on laptop, close-up, slight camera movement, professional environment visible in blur",
            "Person checking phone while walking, natural movement, city background in motion blur",
            "Face in profile, listening intently, slight nods, professional meeting context suggested",
        ]
        
        # Pick one scene
        scene = random.choice(dynamic_scenes)
        
        prompt = f"""Cinematic vertical video for social media (9:16 aspect ratio).

SCENE: {scene}

ESSENTIAL QUALITIES:
- Professional and modern
- Natural movement (not static)
- Cinematic quality (not stock footage feel)
- B2B/business context
- Authentic, not staged-looking

CAMERA:
- Smooth movement (tracking, dolly, or subtle handheld)
- Modern cinematic look
- Shallow depth of field where appropriate
- Natural camera motion, not robotic

LIGHTING:
- Natural or natural-looking
- Can be golden hour, daylight, or modern office lighting
- Avoid harsh or flat lighting
- Professional color grade

TALENT/SUBJECT:
- Professional appearance
- Confident, purposeful movement
- Not cheesy or over-acted
- Could be any gender, 30-50 age range appropriate

AVOID:
- Static locked-off shots
- Cheap stock footage look
- Over-saturated colors
- Obvious green screen
- Overly posed or staged feeling
- Direct camera address

Duration: 8 seconds with movement throughout.
Quality: 4K cinematic look, suitable for YouTube Shorts."""
        
        logger.info(f"Generated dynamic Veo prompt for Shorts")
        return prompt.strip()
    
    def generate_video_with_audio(
        self,
        script: dict,
        audio_url: str,
        style: str = "dynamic B2B",
    ) -> dict:
        """Generate video and combine with audio."""
        video_result = self.generate_video(script, audio_url, style)
        video_result["audio_url"] = audio_url
        video_result["needs_audio_merge"] = True
        return video_result
    
    def get_video_status(self, video_id: str) -> dict:
        """Get the status of a video."""
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
