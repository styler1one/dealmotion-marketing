"""
Script Service - Generate video scripts using Claude.
Optimized for viral YouTube Shorts (15-30 sec).
"""
import json
import uuid
from datetime import datetime
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
        target_duration: int = 25  # Shorts sweet spot: 15-30 sec
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
        current_date = datetime.now().strftime("%d %B %Y")
        current_year = datetime.now().year
        
        return f"""Je bent een viral YouTube Shorts expert. Je schrijft KORTE, PAKKENDE scripts.

VANDAAG: {current_date}
JAAR: {current_year} (gebruik altijd actuele referenties!)

BRAND: {self.settings.brand_name}
WEBSITE: {self.settings.brand_website}

⚡ SHORTS GOUDEN REGELS:
1. MAX 25 SECONDEN (15-25 sec is sweet spot)
2. ÉÉN BOODSCHAP per video (niet 3 punten!)
3. HOOK in eerste 1-2 sec (scroll-stopper)
4. DIRECT to the point - geen intro, geen "Hey guys"
5. SNELLE zinnen - max 8-10 woorden per zin
6. CONVERSATIONAL toon - alsof je een vriend tipt
7. END met nieuwsgierigheid of CTA

SCRIPT STRUCTUUR (max 25 sec):
- HOOK (0-2 sec): Scroll-stopper. Provocerend/verrassend.
- PAYLOAD (2-20 sec): ÉÉN gouden nugget. Concreet.
- CLOSER (20-25 sec): Punch of zachte CTA.

OUTPUT: JSON met:
- title: YouTube titel (pakkend, max 50 chars)
- description: korte beschrijving
- segments: array van {{type, text, duration_seconds}}
- full_text: tekst voor TTS (MAX 60 woorden!)
- total_duration_seconds: MAX 25

Schrijf {lang_instruction}. Kort. Punchy. Viral."""

    def _build_user_prompt(self, topic: dict, target_duration: int, language: str) -> str:
        # Take only the FIRST main point - ONE message per Short!
        main_points = topic.get('main_points', [])
        key_message = main_points[0] if main_points else topic.get('hook', '')
        
        return f"""KORT SCRIPT (max {target_duration}s, max 60 woorden):

TOPIC: {topic.get('title')}
HOOK IDEE: {topic.get('hook')}
KEY MESSAGE: {key_message}
CLOSER: {topic.get('cta')}

REGELS:
- MAX 60 woorden totaal
- Korte zinnen (max 10 woorden)
- ÉÉN boodschap, niet meerdere tips
- Geen "Hey", geen intro
- Direct punch

Taal: {'Nederlands' if language == 'nl' else 'English'}
JSON output only."""

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

