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
        Get varied scene prompts - REAL B2B sales moments.
        Each 2-second clip shows authentic sales work life.
        """
        scenes = [
            # Scene 1: Early morning / laptop glow
            """Cinematic vertical video (9:16), 2 seconds.
            
            Dark room, early morning. Laptop screen illuminating person's face.
            Checking emails, slight frown of concentration. Coffee mug nearby.
            The quiet intensity of starting the day before others wake up.
            
            Style: Moody, intimate, real. Blue screen light on face.
            Camera: Close-up on face, slight handheld movement.""",
            
            # Scene 2: CRM / Pipeline view
            """Cinematic vertical video (9:16), 2 seconds.
            
            Close-up of hands scrolling through CRM or spreadsheet.
            Many tasks, deals, numbers visible. Slight sigh or pause.
            The reality of managing a pipeline.
            
            Style: Documentary, authentic. Screen glow, office lighting.
            Camera: Over-shoulder or hands close-up.""",
            
            # Scene 3: Waiting for reply
            """Cinematic vertical video (9:16), 2 seconds.
            
            Person glancing at phone on desk. Waiting. Checking again.
            The anticipation of a reply that doesn't come.
            Slight frustration, then acceptance.
            
            Style: Intimate, relatable. Natural office light.
            Camera: Medium shot, subtle focus shift.""",
            
            # Scene 4: Before the call
            """Cinematic vertical video (9:16), 2 seconds.
            
            Person adjusting headset, checking camera angle.
            Quick glance at notes. Deep breath before clicking join.
            The moment of preparation before a big meeting.
            
            Style: Tense, focused. Ring light or window light.
            Camera: Close on face and hands, slight movement.""",
            
            # Scene 5: End of day
            """Cinematic vertical video (9:16), 2 seconds.
            
            Empty office, one person still at desk. Laptop glow.
            Rubbing eyes, leaning back. The solitude of sales work.
            Looking at tomorrow's calendar, then shutting laptop.
            
            Style: Quiet, reflective. Evening office lighting.
            Camera: Wide then close, slow movement.""",
            
            # Scene 6: Small win moment
            """Cinematic vertical video (9:16), 2 seconds.
            
            Reading an email, subtle smile forming.
            Quick satisfied nod or small fist pump, alone at desk.
            The private celebration of progress.
            
            Style: Warm, hopeful. Natural light.
            Camera: Close on face, reaction shot.""",
            
            # Scene 7: Research mode
            """Cinematic vertical video (9:16), 2 seconds.
            
            Multiple browser tabs open. LinkedIn, company website.
            Taking notes while reading. Finding something useful.
            The detective work of sales preparation.
            
            Style: Focused, intent. Screen light on face.
            Camera: Over-shoulder, slight zoom on screen.""",
            
            # Scene 8: Coffee and thinking
            """Cinematic vertical video (9:16), 2 seconds.
            
            Person holding coffee, staring into distance.
            Not at screen. Just thinking. Processing a conversation.
            The mental work that happens between calls.
            
            Style: Contemplative, honest. Warm café or office light.
            Camera: Profile shot, shallow depth of field.""",
        ]
        
        # Shuffle to get variety each time
        import random
        random.shuffle(scenes)
        return scenes
    
    def _build_video_prompt(self, script_text: str, style: str) -> str:
        """
        Build a dynamic multi-shot video prompt for Shorts.
        
        Key for Shorts:
        - MULTIPLE quick shots within 8 seconds (like cuts in a music video)
        - Each shot ~2 seconds
        - Visual variety and pacing
        - B2B professional but cinematic
        """
        
        # Define shot sequences - REAL B2B sales moments that sellers recognize
        shot_sequences = [
            # Sequence 1: Early morning grind
            [
                "Quick shot: Dark room, laptop screen illuminating face, early morning, checking emails",
                "Quick shot: Hand scrolling through CRM dashboard, many overdue tasks visible",
                "Quick shot: Coffee mug being picked up, steam rising, tired but determined expression",
                "Quick shot: Deep breath, hands on keyboard, ready to start the day"
            ],
            # Sequence 2: The waiting game
            [
                "Quick shot: Phone on desk, person glancing at it, waiting for reply",
                "Quick shot: Refreshing inbox, slight frustration, no new messages",
                "Quick shot: Looking at LinkedIn, scrolling through prospect's profile",
                "Quick shot: Leaning back in chair, thinking, hand on chin"
            ],
            # Sequence 3: Before the big call
            [
                "Quick shot: Notes spread on desk, reviewing key points",
                "Quick shot: Adjusting headset, checking camera angle",
                "Quick shot: Quick glance at mirror/screen, fixing hair",
                "Quick shot: Deep breath, slight nod, clicking to join meeting"
            ],
            # Sequence 4: End of day reality
            [
                "Quick shot: Empty office, one person still at desk, laptop glow",
                "Quick shot: Closing tabs, many browser windows",
                "Quick shot: Looking at calendar, tomorrow packed with meetings",
                "Quick shot: Rubbing eyes, slight smile, shutting laptop"
            ],
            # Sequence 5: The small wins
            [
                "Quick shot: Email notification pops up, eyes widen slightly",
                "Quick shot: Reading screen, subtle smile forming",
                "Quick shot: Quick fist pump or satisfied nod, alone at desk",
                "Quick shot: Immediately typing response, energized"
            ],
            # Sequence 6: Pipeline pressure
            [
                "Quick shot: Spreadsheet with numbers, scrolling through deals",
                "Quick shot: Hand moving sticky notes on kanban board",
                "Quick shot: Checking watch, then back to screen",
                "Quick shot: Standing up, stretching, then sitting back down focused"
            ],
            # Sequence 7: Research mode
            [
                "Quick shot: Multiple browser tabs open, researching company",
                "Quick shot: Taking notes by hand while reading screen",
                "Quick shot: Switching between LinkedIn and company website",
                "Quick shot: Nodding while reading, found something useful"
            ],
        ]
        
        # Pick a random sequence
        sequence = random.choice(shot_sequences)
        shots_description = "\n".join([f"  {i+1}. {shot}" for i, shot in enumerate(sequence)])
        
        prompt = f"""Create a CINEMATIC 8-second vertical video (9:16) showing REAL B2B SALES WORK LIFE.

This should feel AUTHENTIC and RELATABLE to sales professionals - moments they recognize from their daily work.

SHOT SEQUENCE (each ~2 seconds):
{shots_description}

TONE:
- Real, not staged
- The quiet intensity of sales work
- Relatable moments, not corporate propaganda
- Honest portrayal of the grind

VISUAL STYLE:
- Documentary feel, not commercial
- Natural lighting (office lights, screen glow, window light)
- Muted, realistic colors
- Shallow depth of field for intimacy
- Subtle camera movement, feels observational

SETTING:
- Real home office or modern workspace
- Laptop, phone, coffee - the tools of the trade
- Could be early morning or late evening
- Slightly messy desk is more authentic than perfectly staged

SUBJECT:
- 30-45 year old professional
- Casual or business casual (not suit and tie)
- Focused, determined, sometimes tired
- Real expressions, not corporate smiles
- NEVER looks at camera

THE FEELING:
- "This is my life"
- The solitude of sales work
- Small moments of focus and determination
- Authentic, not aspirational

MUST AVOID:
- Corporate stock footage clichés
- Fake enthusiasm or smiles
- Staged handshakes or meetings
- Perfect lighting setups
- Looking directly at camera
- Anything that feels like an ad

Duration: 8 seconds, documentary style with subtle cuts."""
        
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
