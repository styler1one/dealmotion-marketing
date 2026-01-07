"""
Topic Service - Generate B2B sales content using Claude.

Philosophy: Observation beats advice. Framing beats tactics. Clarity beats hype.
"""
import json
import uuid
from typing import List, Optional
from enum import Enum

import anthropic
from loguru import logger

from app.config import get_settings


class ContentType(str, Enum):
    """Types of B2B sales content."""
    SALES_ILLUSION = "sales_illusion"
    EXECUTION_FAILURE = "execution_failure"
    SIGNAL_MISS = "signal_miss"
    SYSTEM_FLAW = "system_flaw"
    DECISION_DYNAMICS = "decision_dynamics"


class TopicService:
    """Service for generating B2B sales topics using Claude."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_topics(
        self,
        content_type: Optional[ContentType] = None,
        count: int = 1,
        language: str = "nl"
    ) -> List[dict]:
        """Generate B2B sales topic ideas."""
        logger.info(f"Generating {count} topics (type={content_type}, lang={language})")
        
        system_prompt = self._build_system_prompt(language)
        user_prompt = self._build_user_prompt(content_type, count, language)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            content = response.content[0].text
            topics = self._parse_topics(content)
            
            logger.info(f"Generated {len(topics)} topics")
            return topics
            
        except Exception as e:
            logger.error(f"Failed to generate topics: {e}")
            raise
    
    def _build_system_prompt(self, language: str) -> str:
        return f"""Je maakt topics voor 8-seconden B2B sales video's.

Doel: Raak de dagelijkse pijn van B2B verkopers. Laat ze voelen: "dit is mijn leven."
Geen verkoop. Geen oplossing. Alleen de pijn - scherp en herkenbaar.

---

DE 6 PIJNPUNTEN (kies er één per topic):

1. RESEARCH HELL
   De pijn: 30+ minuten googlen per prospect. LinkedIn stalken. Nog steeds niet weten wat je moet zeggen.
   Hook: "Je googlet weer. Twintig tabs open. En je weet nog steeds niks."
   
2. IGNORED OUTREACH  
   De pijn: Dezelfde LinkedIn boodschap. Copy-paste. Geen reactie. Weer niet.
   Hook: "Verstuurd. Gelezen. Geen reactie. Net als de vorige 47."
   
3. UNPREPARED MEETINGS
   De pijn: De meeting begint over 5 minuten. Wie zit er aan tafel? Geen idee.
   Hook: "Over vijf minuten begint je call. Je weet niet eens wie er belt."
   
4. NOTE-TAKING TRAP
   De pijn: Je typt mee. Je mist de helft. De klant zegt iets belangrijks. Je was aan het typen.
   Hook: "Je typt. Je mist wat hij zegt. Je typt door."
   
5. SLOW FOLLOW-UP
   De pijn: Een week later stuur je je follow-up. Het momentum is weg. De klant is verder.
   Hook: "Je follow-up komt een week later. Te laat. Altijd te laat."
   
6. NO FEEDBACK LOOP
   De pijn: Je doet hetzelfde. Elke call. Niemand zegt wat je fout doet. Je wordt niet beter.
   Hook: "Honderd calls. Dezelfde fouten. Niemand die het zegt."

---

STRUCTUUR (8 seconden totaal):

1. HOOK (0-2 sec) - Herkenbare pijn, direct
2. BEELD (2-5 sec) - Concreet moment dat ze kennen
3. STEEK (5-8 sec) - De ongemakkelijke waarheid

---

VOORBEELDEN:

**Research Hell:**
"Je googlet alweer. Twintig minuten later heb je drie LinkedIn posts gelezen en nog steeds geen idee wat je moet zeggen. Morgen weer."

**Ignored Outreach:**
"Hey [voornaam], ik zag dat jullie... Delete. Net als de rest."

**Unprepared:**
"De call begint. Je opent snel LinkedIn. Wie is dit ook alweer?"

---

TOON:
- Droog, niet dramatisch
- Herkenbaar, niet overdreven
- Collega die het hardop zegt
- Geen oordeel, alleen observatie

NATIVE DUTCH:
- Spreektaal, geen schrijftaal
- Korte zinnen (max 8 woorden)
- Geen "het feit dat" of "in staat stellen"

VERBODEN:
- Oplossingen of tips
- Vragen aan de kijker
- "Game changer", "je moet"
- Emoji's, uitroeptekens
- Productnamen of tools

---

OUTPUT (JSON):

{{
  "pain_type": "research_hell|ignored_outreach|unprepared_meetings|note_taking_trap|slow_followup|no_feedback",
  "title": "Korte titel, max 40 tekens",
  "hook": "Opening die pakt (max 10 woorden)",
  "scene": "Concreet moment (wat ze zien/voelen)",
  "sting": "De ongemakkelijke waarheid",
  "full_script": "Volledige tekst (max 25 woorden)",
  "estimated_duration_seconds": 8
}}"""

    def _build_user_prompt(self, content_type: Optional[ContentType], count: int, language: str) -> str:
        # Map old content types to new pain types
        pain_hints = {
            ContentType.SALES_ILLUSION: "Focus op RESEARCH HELL - het eindeloze googlen zonder resultaat.",
            ContentType.EXECUTION_FAILURE: "Focus op SLOW FOLLOW-UP - momentum verliezen door trage opvolging.",
            ContentType.SIGNAL_MISS: "Focus op IGNORED OUTREACH - berichten die niemand leest.",
            ContentType.SYSTEM_FLAW: "Focus op NOTE-TAKING TRAP - typen terwijl je de klant mist.",
            ContentType.DECISION_DYNAMICS: "Focus op UNPREPARED MEETINGS - calls waar je niet klaar voor bent."
        }
        
        type_hint = pain_hints.get(content_type, "") if content_type else ""
        
        # If no specific type, pick a random pain
        if not type_hint:
            type_hint = "Kies één van de 6 pijnen. Maak het zo specifiek en herkenbaar mogelijk."
        
        return f"""Genereer {count} topic(s).

{type_hint}

Denk aan een heel concreet moment. Niet abstract.
Iets waar een verkoper bij denkt: "fuck, dat is precies wat ik doe."

JSON output. Geen uitleg."""

    def _parse_topics(self, content: str) -> List[dict]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                item["id"] = str(uuid.uuid4())
                # Map new format to expected fields
                item["title"] = item.get("title", "Untitled")
                item["hook"] = item.get("hook", "")
                item["full_text"] = item.get("full_script", "")
                item["content_type"] = item.get("pain_type", "research_hell")
                # Backward compatibility
                item["main_points"] = [item.get("scene", "")]
                item["cta"] = item.get("sting", "")
                item["hashtags"] = ["b2bsales", "sales"]
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics: {e}")
            return []
