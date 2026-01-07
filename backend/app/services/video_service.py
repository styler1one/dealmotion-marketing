"""
Video Service - Generate abstract thought leadership videos using Google Veo 2.

Visual Philosophy: Symbolic, abstract, quiet, slightly alienating.
NOT lifestyle stock. NOT obvious sales scenes.
The video should feel like a thought, not an ad.
"""
import os
import time
import uuid
import random
from loguru import logger

from app.config import get_settings
from app.services.storage_service import StorageService


class VideoService:
    """Service for generating abstract videos using Google Veo 2 via Gemini API."""
    
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
        style: str = "abstract thought leadership",
    ) -> dict:
        """
        Generate an abstract video from a script using Google Veo 2.
        
        Args:
            script: Script dict with title, full_text, segments
            audio_url: URL to the audio file
            style: Visual style description
            
        Returns:
            dict with video_id, video_url, status
        """
        if not self.settings.google_gemini_api_key:
            raise ValueError("Google Gemini API key not configured")
        
        title = script.get('title', 'Unknown')
        logger.info(f"🎬 Generating video: {title}")
        
        # Build abstract video prompt
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
                    negative_prompt="celebrations, smiles, high energy, pointing, typing, selling, lifestyle, productivity, stock photo, obvious success, warm colors, upbeat, corporate happiness",
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
    
    def _build_video_prompt(self, script_text: str, style: str) -> str:
        """
        Build an abstract, symbolic video prompt.
        
        Visual philosophy:
        - Symbolic, not illustrative
        - Abstract, not lifestyle
        - Quiet, not energetic
        - Slightly alienating
        - Thought, not ad
        """
        
        # Abstract visual scenes - no obvious sales/success imagery
        abstract_scenes = [
            # Empty spaces / architecture
            "Empty modern glass corridor, slow tracking shot, person walking away in distance, muted cool tones, minimal, quiet tension",
            "Vast empty office floor after hours, single figure standing by window, city lights beyond, contemplative stillness, blue hour",
            "Long hotel hallway, symmetrical perspective, figure pausing mid-walk, ambient light, sense of waiting",
            "Glass elevator ascending slowly, lone figure inside, city below, reflection and reality merging, quiet isolation",
            
            # Movement without purpose
            "Person walking through empty parking garage, footsteps echoing, concrete brutalism, directionless movement",
            "Figure standing in crosswalk as others pass, time slowed, urban anonymity, slight disconnection",
            "Silhouette on escalator moving upward, no destination visible, liminal space, quiet ascent",
            "Person sitting alone in empty waiting room, fluorescent light, patient stillness, uncertain anticipation",
            
            # Reflections and glass
            "Office window at dusk, figure reflected but facing away, city becoming abstract lights, introspective moment",
            "Glass conference room, empty chairs, one person standing, reflection duplicating solitude",
            "Rain on window, blurred cityscape beyond, figure barely visible inside, contemplation",
            "Revolving door in slow motion, figure passing through, threshold between spaces",
            
            # System metaphors
            "Hands hovering over phone on desk, not touching, decision suspended, quiet paralysis",
            "Empty boardroom table, chairs pushed back, evidence of recent departure, aftermath",
            "Laptop closed on desk, person looking out window instead, rejection of busywork",
            "Figure walking past rows of empty desks, systematic solitude, post-work liminal",
            
            # Urban observation
            "Person on rooftop edge, city sprawling below, observer not participant, removed perspective",
            "Train platform, figure standing still as train passes, blur of movement, stillness within chaos",
            "Coffee cup untouched on table, person gazing at nothing, thoughts elsewhere",
            "Stairwell between floors, figure paused mid-step, between states, uncertain direction",
        ]
        
        # Pick random scene
        scene = random.choice(abstract_scenes)
        
        prompt = f"""Abstract cinematic vertical video (9:16).

Visual metaphor for B2B decision-making and stalled progress.

SCENE: {scene}

STYLE:
- Minimalist
- Quiet
- Observational
- Slightly tense
- No obvious success or failure

VISUAL ELEMENTS:
- Empty or semi-empty modern spaces
- Slow human movement without interaction
- Waiting, walking, pausing, observing
- Reflections, glass, corridors, elevators, lobbies
- City or office architecture as system metaphors

CAMERA:
- Slow tracking shots
- Static frames with subtle movement
- Natural imperfections
- Shallow depth of field

COLOR:
- Muted tones
- Cool or neutral grading
- No warm "success" colors
- Slight desaturation

STRICTLY AVOID:
- Celebrations
- Smiles
- High energy
- Pointing, typing, selling
- Obvious sales scenes
- Lifestyle productivity shots
- Stock photo aesthetics
- Warm golden hour lighting
- Victory moments

NO text overlays.
NO watermarks.

TEMPORAL ALIGNMENT (CRUCIAL):
The visual should lag behind the spoken text.
Never illustrate the sentence being spoken.
The image should feel like the thought after the thought.

The video should feel like a thought, not an ad.
Visual representation of stalled progress and quiet realization."""
        
        logger.info(f"Generated abstract Veo prompt")
        return prompt.strip()
    
    def generate_video_with_audio(
        self,
        script: dict,
        audio_url: str,
        style: str = "abstract thought leadership",
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
    
    def debug_credentials(self) -> dict:
        """Debug endpoint to check credentials setup."""
        api_key = self.settings.google_gemini_api_key
        return {
            "gemini_api_key_configured": bool(api_key),
            "gemini_api_key_length": len(api_key) if api_key else 0,
            "gemini_api_key_prefix": api_key[:10] + "..." if api_key else "not set",
        }
