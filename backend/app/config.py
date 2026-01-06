"""
Configuration management for DealMotion Marketing Engine.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==========================================================================
    # App Settings
    # ==========================================================================
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL")
    
    # ==========================================================================
    # Database (Supabase)
    # ==========================================================================
    supabase_url: str = Field(default="", description="Supabase URL")
    supabase_anon_key: str = Field(default="", description="Supabase anon key")
    supabase_service_key: str = Field(default="", description="Supabase service key")
    
    # ==========================================================================
    # AI / LLM
    # ==========================================================================
    anthropic_api_key: str = Field(default="", description="Claude API key")
    
    # ==========================================================================
    # Text-to-Speech
    # ==========================================================================
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API key")
    elevenlabs_voice_id: str = Field(default="", description="Dutch voice ID")
    
    # ==========================================================================
    # Video Generation (Google Veo via Gemini API)
    # ==========================================================================
    google_gemini_api_key: str = Field(default="", description="Gemini API key for Veo video generation")
    google_cloud_project: str = Field(default="", description="Google Cloud Project ID (optional)")
    google_cloud_location: str = Field(default="us-central1", description="Google Cloud region")
    google_application_credentials_json: str = Field(default="", description="Service account JSON (base64 encoded, optional)")
    
    # ==========================================================================
    # Video Rendering (Creatomate - Final video with captions)
    # ==========================================================================
    creatomate_api_key: str = Field(default="", description="Creatomate API key")
    creatomate_template_id: str = Field(default="", description="Creatomate template ID for Shorts")
    
    # ==========================================================================
    # YouTube API
    # ==========================================================================
    youtube_client_id: str = Field(default="", description="Google OAuth Client ID")
    youtube_client_secret: str = Field(default="", description="Google OAuth Client Secret")
    youtube_channel_id: str = Field(default="", description="YouTube channel ID")
    youtube_refresh_token: str = Field(default="", description="YouTube refresh token")
    
    # ==========================================================================
    # Inngest
    # ==========================================================================
    inngest_signing_key: str = Field(default="", description="Inngest signing key")
    inngest_event_key: str = Field(default="", description="Inngest event key")
    
    # ==========================================================================
    # Content Settings
    # ==========================================================================
    default_language: str = Field(default="nl", description="Default content language")
    brand_name: str = Field(default="DealMotion", description="Brand name")
    brand_website: str = Field(default="https://dealmotion.ai", description="Brand website")
    brand_tagline: str = Field(default="Put your deals in motion", description="Brand tagline")
    
    # ==========================================================================
    # Scheduling
    # ==========================================================================
    publish_hour: int = Field(default=10, description="Hour to publish (24h format)")
    shorts_per_day: int = Field(default=1, description="Number of shorts per day")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

