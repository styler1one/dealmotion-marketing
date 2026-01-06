"""
TTS Service - Generate voice-overs using ElevenLabs.
"""
import httpx
from loguru import logger

from app.config import get_settings


class TTSService:
    """Service for generating voice-overs using ElevenLabs."""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.voice_id = self.settings.elevenlabs_voice_id
    
    def generate_audio(
        self,
        text: str,
        voice_id: str = None,
    ) -> str:
        """
        Generate audio from text.
        
        Returns the URL of the generated audio file (stored in Supabase storage).
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        voice = voice_id or self.voice_id
        
        logger.info(f"Generating TTS: {len(text)} chars")
        
        url = f"{self.BASE_URL}/text-to-speech/{voice}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"ElevenLabs error: {response.status_code}")
            
            # TODO: Upload to Supabase storage and return URL
            audio_bytes = response.content
            
            # For now, return a placeholder URL
            # In production, upload to storage and return actual URL
            audio_url = f"https://storage.example.com/audio/{hash(text)}.mp3"
            
            logger.info(f"Audio generated: {len(audio_bytes)} bytes")
            return audio_url
    
    def get_voices(self) -> list:
        """Get available voices."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")
        
        with httpx.Client() as client:
            response = client.get(
                f"{self.BASE_URL}/voices",
                headers={"xi-api-key": self.api_key}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get voices: {response.text}")
            
            return response.json().get("voices", [])

