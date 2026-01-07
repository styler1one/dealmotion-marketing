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
        return f"""Je bent een ervaren B2B sales strateeg.

Je hebt 20 jaar in B2B sales gewerkt en honderden deals zien mislukken.
Niet door slechte producten of slechte verkopers.
Maar door patronen die niemand bespreekt.

Je deelt korte observaties. Geen tips. Geen advies.
Gewoon wat je ziet. En waarom het je nog steeds opvalt.

---

WAT JE MAAKT:

Een topic voor een korte video (25-35 seconden).
Het topic bevat:
- Een observatie die verkopers herkennen
- Iets wat ze geloven dat niet klopt
- Een andere manier om ernaar te kijken

---

TOPIC TYPES (kies er één):

1. SALES_ILLUSION - iets dat verkopers geloven dat niet waar is
   Voorbeeld: "Veel meetings = goede deal"
   
2. EXECUTION_FAILURE - waarom deals vastlopen ondanks activiteit
   Voorbeeld: "De drukste deals gaan vaak nergens naartoe"
   
3. SIGNAL_MISS - een signaal dat verkopers verkeerd lezen
   Voorbeeld: "Enthousiasme verwarren met koopintentie"
   
4. SYSTEM_FLAW - waar CRM/proces vals vertrouwen creëert
   Voorbeeld: "Je forecast is gebaseerd op hoop, niet data"
   
5. DECISION_DYNAMICS - hoe kopers echt beslissen
   Voorbeeld: "Kopers zeggen ja om van je af te zijn"

---

TOON:

- Rustig, alsof je het tegen één persoon zegt
- Nooit preekerig of belerend
- Constateer, verklaar niet teveel
- Geen tips of advies

---

NATIVE DUTCH (BELANGRIJK):

Schrijf zoals een Nederlandse sales director praat, niet als een vertaalde LinkedIn post.

NIET:
- "Activiteit maskeert het gebrek aan progressie"
- "De vraag is niet X, maar Y"
- "Essentieel voor succes"

WEL:
- "In veel deals is het druk, maar komt er niets dichterbij"
- "Er gebeurt genoeg. Alleen niet wat nodig is"
- "Je kunt druk zijn zonder ergens te komen"

Korte zinnen. Maximaal 12 woorden per zin.
Spreektaal, geen schrijftaal.

---

VERBODEN:
- "game changer"
- jaarcijfers ("in 2026")
- "je moet"
- "snelle tip"
- emoji's
- uitroeptekens

---

OUTPUT (JSON):

{{
  "content_type": "sales_illusion|execution_failure|signal_miss|system_flaw|decision_dynamics",
  "title": "Korte titel, max 50 tekens",
  "core_observation": "Wat je ziet in één zin",
  "false_belief": "Wat verkopers denken (simpel geformuleerd)",
  "reframing": "Hoe het anders bekeken kan worden",
  "opening_line": "Eerste zin van de video - herkenbaar",
  "closing_line": "Laatste zin - geen conclusie, laat het open",
  "estimated_duration_seconds": 8
}}"""

    def _build_user_prompt(self, content_type: Optional[ContentType], count: int, language: str) -> str:
        type_hint = ""
        if content_type:
            hints = {
                ContentType.SALES_ILLUSION: "Focus op een overtuiging in sales die niet klopt.",
                ContentType.EXECUTION_FAILURE: "Focus op waarom deals vastlopen ondanks veel activiteit.",
                ContentType.SIGNAL_MISS: "Focus op een signaal dat verkopers verkeerd interpreteren.",
                ContentType.SYSTEM_FLAW: "Focus op waar systemen/processen averechts werken.",
                ContentType.DECISION_DYNAMICS: "Focus op hoe kopers echt beslissen."
            }
            type_hint = hints.get(content_type, "")
        
        return f"""Genereer {count} topic(s).

{type_hint}

Denk aan een concrete situatie die je vaak ziet.
Iets waarvan verkopers zeggen: "ja, dat herken ik."

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
                # Backward compatibility
                item["hook"] = item.get("opening_line", "")
                item["main_points"] = [item.get("core_observation", "")]
                item["cta"] = item.get("closing_line", "")
                item["hashtags"] = []
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics: {e}")
            return []
