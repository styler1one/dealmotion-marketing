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
            "model_id": "eleven_multilingual_v2"
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"ElevenLabs error {response.status_code}: {error_detail}")
                raise Exception(f"ElevenLabs error: {response.status_code} - {error_detail}")
            
            audio_bytes = response.content
            logger.info(f"Audio generated: {len(audio_bytes)} bytes")
            
            # Upload to Supabase Storage
            from app.services.storage_service import StorageService
            storage = StorageService()
            audio_url = storage.upload_audio(audio_bytes)
            
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

