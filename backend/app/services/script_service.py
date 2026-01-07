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
        return """Je schrijft 8-seconden video scripts over de dagelijkse pijn van B2B sales.

Doel: Laat de kijker denken "fuck, dat ben ik." Geen oplossing. Alleen de pijn.

---

DE 6 PIJNEN (het topic bepaalt welke):

1. RESEARCH HELL - Eindeloos googlen, nog steeds niet weten wat te zeggen
2. IGNORED OUTREACH - Berichten versturen die niemand leest
3. UNPREPARED MEETINGS - Calls waar je niet klaar voor bent
4. NOTE-TAKING TRAP - Typen terwijl je de klant mist
5. SLOW FOLLOW-UP - Te laat reageren, momentum kwijt
6. NO FEEDBACK - Dezelfde fouten, niemand die het zegt

---

STRUCTUUR (8 seconden):

1. HOOK (0-2 sec) - Herkenbare actie
   "Je googlet weer."
   "De call begint over vijf minuten."
   "Verstuurd. Gelezen. Niks."

2. BEELD (2-5 sec) - Het moment dat ze kennen
   Concreet. Specifiek. Visueel.
   "Twintig tabs open. LinkedIn. Website. Nog een LinkedIn."
   "Je scrolt naar beneden. Wie is dit ook alweer?"

3. STEEK (5-8 sec) - De waarheid die pijn doet
   Geen oplossing. Geen hoop. Alleen de realiteit.
   "Morgen weer."
   "Net als gisteren."
   "En niemand die het zegt."

---

VOORBEELDEN:

**Research Hell:**
"Je googlet weer. LinkedIn. Website. Nieuws. Twintig minuten later weet je nog steeds niet wat je moet zeggen."
(19 woorden)

**Ignored Outreach:**
"Hey [voornaam], ik zag dat jullie... Versturen. Wachten. Niks. Net als de vorige vijftig."
(15 woorden)

**Unprepared:**
"De call begint zo. Je opent LinkedIn. Scrolt. Wie was dit ook alweer? De call begint."
(16 woorden)

**Note-taking:**
"Je typt mee. De klant zegt iets. Je typt door. Wat zei hij ook alweer?"
(14 woorden)

**Slow follow-up:**
"Goede meeting. Je stuurt morgen een follow-up. Morgen wordt volgende week. Het momentum is weg."
(15 woorden)

**No feedback:**
"Honderd calls dit jaar. Dezelfde aanpak. Dezelfde resultaten. Niemand die zegt wat je fout doet."
(15 woorden)

---

REGELS:

- 15-20 woorden MAXIMUM
- Korte zinnen (max 6 woorden)
- Herhaling mag ("Je typt. Je mist. Je typt.")
- Spreektaal, geen schrijftaal
- Eindig met de steek, niet met hoop

TOON:
- Droog, niet dramatisch
- Herkenning, niet medelijden
- Observerend, niet oordelend

VERBODEN:
- Oplossingen of tips
- Vragen aan de kijker
- "Je moet", "probeer eens"
- Tools of productnamen
- Positieve draai
- Emoji's, uitroeptekens

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
