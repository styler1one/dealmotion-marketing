"""
TTS Router - Generate voice-overs.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.tts_service import TTSService


router = APIRouter()


class TTSRequest(BaseModel):
    """Request for TTS generation."""
    text: str
    voice_id: str = None


class TTSResponse(BaseModel):
    """Response with generated audio."""
    audio_url: str
    text_length: int


class VoiceInfo(BaseModel):
    """Voice information."""
    voice_id: str
    name: str
    category: str


@router.post("/generate", response_model=TTSResponse)
async def generate_audio(request: TTSRequest):
    """
    Generate audio from text using ElevenLabs.
    """
    try:
        service = TTSService()
        audio_url = service.generate_audio(
            text=request.text,
            voice_id=request.voice_id
        )
        
        return TTSResponse(
            audio_url=audio_url,
            text_length=len(request.text)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices():
    """
    Get available ElevenLabs voices.
    """
    try:
        service = TTSService()
        voices = service.get_voices()
        
        return {
            "voices": [
                {
                    "voice_id": v.get("voice_id"),
                    "name": v.get("name"),
                    "category": v.get("category", "unknown")
                }
                for v in voices
            ],
            "count": len(voices)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_connection():
    """
    Test ElevenLabs connection.
    """
    try:
        service = TTSService()
        voices = service.get_voices()
        
        return {
            "status": "connected",
            "voices_available": len(voices)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

