"""
Script Service - Generate video scripts using Claude.

Structure: Observatie → Frictie → Reframe
Tone: Rustig, constaterend, geen advies.
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
        target_duration: int = 8  # Video is 8 seconds
    ) -> dict:
        """Generate a video script from a topic."""
        logger.info(f"Generating script for: {topic.get('title', 'Unknown')}")
        
        system_prompt = self._build_system_prompt(language)
        user_prompt = self._build_user_prompt(topic, target_duration)
        
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
        return """Je schrijft scripts voor 8-seconden video's over B2B sales.

Doel: Stop scrolling. Laat denken. Geen verkoop.

---

STRUCTUUR (3 fasen in 8 seconden):

1. HOOK (0-2 sec) - Pak de aandacht
   → Directe, prikkelende opening
   → Iets wat ze nog niet eerder zo hoorden
   → Geen vraag. Een statement.

2. HERKENNING (2-5 sec) - "Dat ken ik"
   → Beschrijf hun realiteit
   → Concreet, specifiek
   → Ze voelen zich begrepen

3. SHIFT (5-8 sec) - Nieuwe kijk
   → Draai het perspectief
   → Laat ze anders denken
   → Geen conclusie. Open einde.

---

VOORBEELD 1: "Drukke deals"

"Een deal met veel meetings voelt productief.
Tot je beseft: de drukste deals lopen vaak het hardst dood.
Beweging is geen voortgang."

(23 woorden, hook + herkenning + shift)

---

VOORBEELD 2: "Follow-up"

"Je stuurt drie follow-ups.
Geen reactie.
De meeste sales denken: doorgaan.
De beste denken: waarom zou ik?"

(18 woorden, hook + herkenning + shift)

---

VOORBEELD 3: "Enthousiasme"

"Ze waren super enthousiast na de demo.
En toen... stilte.
Enthousiasme is makkelijk.
Commitment is zeldzaam."

(15 woorden, hook + herkenning + shift)

---

REGELS:

- 15-25 woorden MAXIMUM (8 seconden!)
- Eerste zin = haak (pakt aandacht)
- Korte zinnen (max 7 woorden)
- Spreektaal, geen schrijftaal
- Eindig OPEN - geen "dus" of "daarom"

TOON:
- Rustig, niet opgewonden
- Constaterend, niet predikend
- Collega in een café, niet spreker op een podium

VERBODEN:
- Vragen aan de kijker
- "Je moet..." of tips
- Emoji's of uitroeptekens
- "game changer", "snelle tip", jaarcijfers
- Conclusies of samenvattingen

---

OUTPUT (JSON):

{
  "title": "Titel van de video",
  "full_text": "Het complete script",
  "segments": [
    {"part": "observation", "text": "..."},
    {"part": "friction", "text": "..."},
    {"part": "reframe", "text": "..."}
  ],
  "total_word_count": 70,
  "total_duration_seconds": 28
}"""

    def _build_user_prompt(self, topic: dict, target_duration: int) -> str:
        # Video is 8 seconds, so script must be ~20 words max
        word_count = min(25, int(target_duration * 2.5))
        
        return f"""Schrijf een ZEER KORT script voor deze video:

TITEL: {topic.get('title', '')}

OBSERVATIE: {topic.get('core_observation', topic.get('hook', ''))}

WAT VERKOPERS DENKEN: {topic.get('false_belief', '')}

REFRAME: {topic.get('reframing', '')}

KRITIEK: Maximum {word_count} woorden! De video is maar 8 seconden.
Dat is 3-4 korte zinnen, niet meer.

JSON output."""

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
                segments = data.get("segments", [])
                if segments:
                    data["full_text"] = " ".join(
                        seg.get("text", "") for seg in segments
                    )
                else:
                    data["full_text"] = topic.get("opening_line", topic.get("hook", ""))
            
            # Calculate word count
            if "total_word_count" not in data:
                data["total_word_count"] = len(data["full_text"].split())
            
            # Add description
            data["description"] = topic.get("core_observation", "")
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script: {e}")
            return {
                "id": str(uuid.uuid4()),
                "title": topic.get("title", ""),
                "description": "",
                "segments": [],
                "full_text": topic.get("opening_line", topic.get("hook", "")),
                "total_word_count": 0,
                "total_duration_seconds": 30
            }
