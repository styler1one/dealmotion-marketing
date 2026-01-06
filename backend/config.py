"""
Configuration management for DealMotion Marketing Engine
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
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
    # Video Generation
    # ==========================================================================
    nanobanana_api_key: str = Field(default="", description="NanoBanana API key")
    
    # ==========================================================================
    # YouTube API
    # ==========================================================================
    youtube_client_id: str = Field(default="", description="Google OAuth Client ID")
    youtube_client_secret: str = Field(default="", description="Google OAuth Client Secret")
    youtube_channel_id: str = Field(default="", description="YouTube channel ID")
    
    # ==========================================================================
    # Database
    # ==========================================================================
    database_url: str = Field(default="sqlite:///./marketing.db", description="Database URL")
    
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
    
    # ==========================================================================
    # Paths
    # ==========================================================================
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    @property
    def assets_dir(self) -> Path:
        """Get assets directory."""
        return self.project_root / "assets"
    
    @property
    def output_dir(self) -> Path:
        """Get output directory."""
        return self.project_root / "output"
    
    @property
    def shorts_output_dir(self) -> Path:
        """Get shorts output directory."""
        return self.output_dir / "shorts"
    
    @property
    def videos_output_dir(self) -> Path:
        """Get videos output directory."""
        return self.output_dir / "videos"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings

