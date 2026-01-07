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
        target_duration: int = 30
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
        return """Je schrijft scripts voor korte video's over B2B sales.

Je praat rustig. Alsof je in een café zit met een collega.
Geen presentatie. Geen pitch. Gewoon een gedachte delen.

---

STRUCTUUR:

1. OBSERVATIE - Wat je ziet (herkenbaar, direct)
2. FRICTIE - Waarom dat gek is of niet klopt
3. REFRAME - Hoe je er anders naar kunt kijken

Je eindigt NOOIT met een conclusie of advies.
Je laat de gedachte hangen. De kijker denkt zelf verder.

---

VOORBEELD SCRIPT:

Titel: "Waarom de drukste deals vaak doodlopen"

"Ik zie het steeds weer.
Een deal met twintig meetings. Eindeloos heen en weer.
En dan... niks.

Terwijl andere deals. Drie gesprekken. Klaar.

We denken: veel activiteit is goed.
Maar kopers die twijfelen, maken ook veel lawaai.
Ze stellen vragen. Vragen meetings aan. Betrekken collega's.
Niet omdat ze willen kopen. Maar omdat ze niet durven te zeggen: nee.

Drukte voelt als voortgang.
Maar het is vaak precies het tegenovergestelde."

(72 woorden, ~30 seconden)

---

VOORBEELD SCRIPT 2:

Titel: "De klant zegt ja, maar doet niks"

"Alles lijkt goed.
De demo ging geweldig. Ze waren enthousiast.
'We gaan dit intern bespreken.'

En dan... stilte.

Ik heb lang gedacht: dat ben ik. Ik doe iets fout.
Maar dat is het niet.

Aardige mensen zeggen ja om van je af te zijn.
Ze willen je niet teleurstellen.
Dus doen ze alsof.

Enthousiasme is geen commitment.
Een positieve klant is niet hetzelfde als een kopende klant."

(65 woorden, ~27 seconden)

---

REGELS:

- Maximum 80 woorden
- Korte zinnen (max 10 woorden per zin)
- Spreektaal, geen schrijftaal
- Geen vragen aan de kijker
- Geen "je moet" of tips
- Geen opsommingen
- Eindig open, niet met een conclusie

VERBODEN:
- "game changer"
- jaarcijfers
- "snelle tip"
- emoji's
- uitroeptekens

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
        return f"""Schrijf een script voor deze video:

TITEL: {topic.get('title', '')}

OBSERVATIE: {topic.get('core_observation', topic.get('hook', ''))}

WAT VERKOPERS DENKEN: {topic.get('false_belief', '')}

REFRAME: {topic.get('reframing', '')}

OPENING: {topic.get('opening_line', topic.get('hook', ''))}

SLUITING: {topic.get('closing_line', '')}

Doel: {target_duration} seconden (~{int(target_duration * 2.5)} woorden)

Schrijf alsof je dit tegen één persoon zegt.
Rustig. Geen haast.

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
