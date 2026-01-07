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

VOORBEELDEN (PIJN → CONTRAST structuur):

**Research Hell:**
Segment 1: "Je googlet weer. Twintig tabs."
Segment 2: "Twintig minuten later: nog steeds niks."
Segment 3: "Of: je typt de bedrijfsnaam."
Segment 4: "Dertig seconden later heb je alles."
(25 woorden)

**Ignored Outreach:**
Segment 1: "Hey voornaam, ik zag dat jullie..."
Segment 2: "Copy. Paste. Geen reactie."
Segment 3: "Of: een bericht dat echt persoonlijk is."
Segment 4: "Gebaseerd op wat je al weet."
(26 woorden)

**Unprepared:**
Segment 1: "De call begint over twee minuten."
Segment 2: "Je opent snel LinkedIn. Scrolt."
Segment 3: "Of: je opent je voorbereiding."
Segment 4: "Alles staat er al. Namen, context, vragen."
(27 woorden)

**Note-taking:**
Segment 1: "Je typt mee tijdens de call."
Segment 2: "De klant zegt iets. Je mist het."
Segment 3: "Of: je luistert gewoon."
Segment 4: "Alles wordt voor je vastgelegd."
(25 woorden)

**Slow follow-up:**
Segment 1: "Goede meeting gehad."
Segment 2: "Volgende week stuur je pas je follow-up."
Segment 3: "Of: dezelfde dag nog."
Segment 4: "Klaar om te versturen. Zonder moeite."
(24 woorden)

**No feedback:**
Segment 1: "Honderd calls dit jaar."
Segment 2: "Dezelfde fouten. Niemand die het zegt."
Segment 3: "Of: na elke call feedback."
Segment 4: "Concreet. Wat ging goed. Wat beter kan."
(26 woorden)

---

REGELS:

- 25-30 woorden (8 seconden = ~28 woorden bij normaal tempo)
- Korte zinnen (max 6 woorden)
- Herhaling mag ("Je typt. Je mist. Je typt.")
- Spreektaal, geen schrijftaal
- Eindig met de steek, niet met hoop
- SPLIT in 4 segmenten voor ondertiteling

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
  "title": "Korte titel",
  "full_text": "Alle 4 segmenten achter elkaar",
  "segments": [
    {"text": "Segment 1 - Hook (0-2 sec)"},
    {"text": "Segment 2 - Beeld (2-4 sec)"},
    {"text": "Segment 3 - Verdieping (4-6 sec)"},
    {"text": "Segment 4 - Steek (6-8 sec)"}
  ],
  "total_word_count": 25,
  "total_duration_seconds": 8
}

BELANGRIJK: Precies 4 segmenten! Elk segment = 2 seconden ondertitel."""

    def _build_user_prompt(self, topic: dict, target_duration: int) -> str:
        return f"""Schrijf een 8-seconden script met PRECIES 4 segmenten:

PIJN TYPE: {topic.get('pain_type', topic.get('content_type', 'research_hell'))}

TITEL: {topic.get('title', '')}

HOOK: {topic.get('hook', '')}

SCENE: {topic.get('scene', topic.get('core_observation', ''))}

STEEK: {topic.get('sting', topic.get('cta', ''))}

---

Schrijf 4 segmenten van elk ~6 woorden.
Totaal: 25-30 woorden = 8 seconden audio.

Elk segment = 2 seconden ondertitel.

STRUCTUUR: PIJN → CONTRAST (before/after zonder product te noemen)

Segment 1 = HOOK - De herkenbare pijn (pakt aandacht)
Segment 2 = BEELD - Meer detail van de pijn
Segment 3 = SWITCH - "Of:" / "Maar stel:" / "Er zijn ook mensen die:"
Segment 4 = VISIE - Hoe het er WEL uitziet (zonder tool te noemen)

DE KIJKER MOET BEIDE WERELDEN ZIEN:
- Wereld A: Hun huidige realiteit (herkenbaar, pijnlijk)
- Wereld B: Hoe het kan zijn (aantrekkelijk, moeiteloos)

VOORBEELD UNPREPARED MEETINGS:
Segment 1: "De call begint over twee minuten."
Segment 2: "Je opent snel LinkedIn. Scrolt door hun profiel."
Segment 3: "Of: je opent je voorbereiding."
Segment 4: "Alles staat er al. Namen, context, gesprekspunten."

VOORBEELD RESEARCH HELL:
Segment 1: "Je googlet weer. Twintig tabs open."
Segment 2: "Twintig minuten later: nog steeds niks."
Segment 3: "Of: je typt de bedrijfsnaam."
Segment 4: "Dertig seconden later heb je alles."

VOORBEELD NOTE-TAKING:
Segment 1: "Je typt mee tijdens de call."
Segment 2: "De klant zegt iets. Je mist het."
Segment 3: "Of: je luistert gewoon."
Segment 4: "Alles wordt voor je vastgelegd."

DE SWITCH-WOORDEN:
- "Of:"
- "Maar stel je voor:"
- "Er zijn ook mensen die:"
- "Het kan ook zo:"

VERBODEN:
- Productnamen, tools, of apps noemen
- "Met [product] kun je..."
- CTA's of links
- Uitleggen HOE het werkt (alleen LATEN ZIEN dat het bestaat)

JSON output. Geen uitleg."""

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
