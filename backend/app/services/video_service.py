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
        Build a dynamic multi-shot video prompt for Shorts.
        
        Key for Shorts:
        - MULTIPLE quick shots within 8 seconds (like cuts in a music video)
        - Each shot ~2 seconds
        - Visual variety and pacing
        - B2B professional but cinematic
        """
        
        # Define shot sequences - each sequence has 4 quick shots
        shot_sequences = [
            # Sequence 1: Urban arrival
            [
                "Quick shot: Feet walking on wet city pavement, reflections, confident stride",
                "Quick shot: Low angle looking up at glass skyscraper, camera tilts up",
                "Quick shot: Hand pushing through revolving door, motion blur",
                "Quick shot: Person in profile, walking through lobby, natural light streaming in"
            ],
            # Sequence 2: Office energy
            [
                "Quick shot: Hands typing on laptop keyboard, shallow depth of field",
                "Quick shot: Coffee cup being set down on desk, slight splash",
                "Quick shot: Person walking past glass wall, reflection visible",
                "Quick shot: Close-up face in thought, slight head turn, window light"
            ],
            # Sequence 3: Meeting dynamics
            [
                "Quick shot: Hand gesturing while talking, out of focus listener in background",
                "Quick shot: Pen writing on paper, decisive strokes",
                "Quick shot: Two people walking down corridor, shot from front",
                "Quick shot: Person standing at window, city view, turns slightly"
            ],
            # Sequence 4: Tech & movement
            [
                "Quick shot: Phone screen lighting up face in dim room",
                "Quick shot: Laptop closing, person standing up",
                "Quick shot: Walking through busy open office, camera tracking",
                "Quick shot: Elevator doors opening, person stepping in"
            ],
            # Sequence 5: Street & transition
            [
                "Quick shot: Crossing street at crosswalk, camera low",
                "Quick shot: Hailing taxi, arm raised",
                "Quick shot: Sitting in back of car, cityscape passing window",
                "Quick shot: Looking out window, contemplative, buildings reflected"
            ],
        ]
        
        # Pick a random sequence
        sequence = random.choice(shot_sequences)
        shots_description = "\n".join([f"  {i+1}. {shot}" for i, shot in enumerate(sequence)])
        
        prompt = f"""Create a DYNAMIC 8-second vertical video (9:16) with FAST CUTS like a music video or commercial.

This video should feel like 4 QUICK SHOTS edited together, not one continuous take.

SHOT SEQUENCE (each ~2 seconds):
{shots_description}

EDITING STYLE:
- Fast cuts between shots (every ~2 seconds)
- Each shot is distinct but cohesive in style
- Creates rhythm and energy
- Like a Nike commercial or movie trailer

VISUAL STYLE:
- Cinematic, modern, premium feel
- Shallow depth of field on key moments
- Mix of movement types: tracking, static, handheld
- Natural but stylized lighting
- Muted colors with occasional warm highlights

CAMERA MOVEMENT:
- Varies per shot: some tracking, some static, some handheld
- Creates visual interest through variety
- Professional, not chaotic

SUBJECT:
- Professional 30-45 year old
- Business casual or smart attire
- Confident, purposeful energy
- NOT posing or looking at camera

MUST AVOID:
- Single static shot for entire duration
- Cheesy stock footage feeling
- Over-saturated or unnatural colors
- Direct eye contact with camera
- Anything that feels staged or fake

This is for a professional B2B brand. Think Apple, Nike, or high-end tech company aesthetics.
Total duration: 8 seconds with visible cuts/transitions between shots."""
        
        logger.info(f"Generated multi-shot Veo prompt for Shorts")
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
