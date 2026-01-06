"""
Script Service - Generate video scripts using Claude.
"""
import json
import uuid
from typing import Optional

import anthropic
from loguru import logger

from app.config import get_settings


class ScriptService:
    """Service for generating video scripts using Claude."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_script(
        self,
        topic: dict,
        language: str = "nl",
        target_duration: int = 45
    ) -> dict:
        """Generate a video script from a topic."""
        logger.info(f"Generating script for: {topic.get('title', 'Unknown')}")
        
        system_prompt = self._build_system_prompt(language)
        user_prompt = self._build_user_prompt(topic, target_duration, language)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            content = response.content[0].text
            script = self._parse_script(content, topic)
            
            return script
            
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            raise
    
    def _build_system_prompt(self, language: str) -> str:
        lang_instruction = "in het Nederlands" if language == "nl" else "in English"
        
        return f"""Je bent een expert scriptwriter voor YouTube Shorts.
Schrijf scripts die direct de aandacht pakken en waarde leveren.

BRAND: {self.settings.brand_name}
WEBSITE: {self.settings.brand_website}

SCRIPT STRUCTUUR:
1. HOOK (0-3 sec): Pak direct aandacht
2. CONTENT (3-50 sec): Lever waarde
3. CTA (50-60 sec): Stuur naar actie

OUTPUT: JSON met:
- title: YouTube titel
- description: YouTube beschrijving
- segments: array van {{type, text, duration_seconds, visual_cue}}
- full_text: volledige tekst voor TTS
- total_duration_seconds: totale duur

Schrijf {lang_instruction}."""

    def _build_user_prompt(self, topic: dict, target_duration: int, language: str) -> str:
        return f"""Schrijf script voor:
- Titel: {topic.get('title')}
- Hook: {topic.get('hook')}
- Punten: {', '.join(topic.get('main_points', []))}
- CTA: {topic.get('cta')}
- Duur: {target_duration}s
- Taal: {'Nederlands' if language == 'nl' else 'English'}

Alleen JSON output."""

    def _parse_script(self, content: str, topic: dict) -> dict:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        try:
            data = json.loads(content)
            data["id"] = str(uuid.uuid4())
            
            # Ensure full_text exists
            if "full_text" not in data:
                data["full_text"] = " ".join(
                    seg.get("text", "") for seg in data.get("segments", [])
                )
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script: {e}")
            return {
                "id": str(uuid.uuid4()),
                "title": topic.get("title", ""),
                "description": "",
                "segments": [],
                "full_text": topic.get("hook", "") + " " + " ".join(topic.get("main_points", [])),
                "total_duration_seconds": 45
            }

