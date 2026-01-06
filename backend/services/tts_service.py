"""
Text-to-Speech Service - Generates voice-overs using ElevenLabs.
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx
from loguru import logger

from backend.config import get_settings


class TTSService:
    """
    Service for generating voice-overs using ElevenLabs API.
    Optimized for Dutch language content.
    """
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    # Dutch voice options (update with actual voice IDs)
    DUTCH_VOICES = {
        "male_professional": "pNInz6obpgDQGcFmaJgB",  # Example - Adam
        "female_professional": "EXAVITQu4vr4xnSDxMaL",  # Example - Bella
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.voice_id = self.settings.elevenlabs_voice_id or self.DUTCH_VOICES["male_professional"]
    
    async def generate_audio(
        self,
        text: str,
        output_path: Optional[Path] = None,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.5
    ) -> Path:
        """
        Generate audio from text using ElevenLabs.
        
        Args:
            text: The text to convert to speech
            output_path: Where to save the audio file
            voice_id: Override the default voice
            stability: Voice stability (0-1)
            similarity_boost: Voice clarity (0-1)
            style: Style exaggeration (0-1)
        
        Returns:
            Path to the generated audio file
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        voice = voice_id or self.voice_id
        
        # Generate default output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.settings.output_dir / f"audio_{timestamp}.mp3"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating TTS audio: {len(text)} chars -> {output_path}")
        
        url = f"{self.BASE_URL}/text-to-speech/{voice}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Best for Dutch
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Write audio to file
            with open(output_path, "wb") as f:
                f.write(response.content)
        
        logger.info(f"Audio generated: {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
    
    async def get_voices(self) -> list[dict]:
        """Get available voices from ElevenLabs."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        url = f"{self.BASE_URL}/voices"
        headers = {"xi-api-key": self.api_key}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get voices: {response.text}")
            
            data = response.json()
            return data.get("voices", [])
    
    async def get_subscription_info(self) -> dict:
        """Get subscription info (for checking usage limits)."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        url = f"{self.BASE_URL}/user/subscription"
        headers = {"xi-api-key": self.api_key}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get subscription: {response.text}")
            
            return response.json()


# Convenience function for sync usage
def generate_audio_sync(
    text: str,
    output_path: Optional[Path] = None,
    voice_id: Optional[str] = None
) -> Path:
    """Synchronous wrapper for audio generation."""
    import asyncio
    
    service = TTSService()
    return asyncio.run(service.generate_audio(text, output_path, voice_id))

