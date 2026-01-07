"""
Topic Service - Generate B2B sales insights using Claude.

Approach: Persona-based prompting with concrete examples.
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
    BUYER_BEHAVIOR = "buyer_behavior"       # How buyers actually make decisions
    SELLER_BLINDSPOT = "seller_blindspot"   # What sellers consistently miss
    DEAL_DYNAMICS = "deal_dynamics"         # Why deals stall or fail
    PROCESS_TRAP = "process_trap"           # Where process hurts instead of helps
    REALITY_CHECK = "reality_check"         # Uncomfortable truths about sales


class TopicService:
    """Service for generating B2B sales insights using Claude."""
    
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
        """Generate B2B sales insight topics."""
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
        return """Je bent Martijn, 47 jaar. Je hebt 20 jaar in B2B sales gewerkt. 
De laatste 8 jaar als VP Sales bij twee scale-ups.

Je hebt honderden deals gezien mislukken. Niet door slechte producten. 
Niet door slechte verkopers. Maar door patronen die niemand bespreekt.

Je deelt nu korte observaties op video. Geen tips. Geen advies. 
Gewoon wat je ziet. En waarom het je nog steeds verbaast.

Je toon is:
- Rustig, alsof je het tegen één persoon zegt
- Nooit preekerig of belerend
- Soms licht cynisch, maar niet bitter
- Je constateert, je verklaart niet

Je praat Nederlands. Niet zakelijk-formeel, niet plat. 
Zoals je zou praten met een collega die ook 15 jaar ervaring heeft.

---

VOORBEELDEN VAN GOEDE TOPICS:

Voorbeeld 1:
{
  "title": "Waarom de drukste deals vaak doodlopen",
  "insight": "Veel activiteit in een deal voelt als voortgang. Maar het is meestal ruis.",
  "tension": "Verkopers denken: als er veel gebeurt, gaan we de goede kant op. Maar kopers die twijfelen maken ook veel lawaai.",
  "hook": "Ik zie deals met twintig meetings die nergens komen. En deals met drie gesprekken die sluiten.",
  "closing": "Drukte is geen bewijs. Het is vaak afleiding."
}

Voorbeeld 2:
{
  "title": "De klant zegt ja, maar doet niks",
  "insight": "Een positieve klant is niet hetzelfde als een kopende klant.",
  "tension": "We verwarren enthousiasme met commitment. En dan snappen we niet waarom het stil wordt.",
  "hook": "Je kent het wel. Alles lijkt goed. En dan... stilte.",
  "closing": "Aardige mensen zijn niet altijd serieuze kopers."
}

Voorbeeld 3:
{
  "title": "Je CRM liegt tegen je",
  "insight": "De data in je CRM zegt iets over wat verkopers invullen. Niet over wat er echt gebeurt.",
  "tension": "We sturen op cijfers die gebaseerd zijn op inschattingen. En dan noemen we dat forecast.",
  "hook": "Ik heb nog nooit een CRM gezien die de werkelijkheid weergaf.",
  "closing": "Het systeem doet wat je vraagt. Niet wat je nodig hebt."
}

---

OUTPUT FORMAT (JSON):
{
  "content_type": "buyer_behavior|seller_blindspot|deal_dynamics|process_trap|reality_check",
  "title": "Korte, concrete titel (max 50 tekens)",
  "insight": "De kernobservatie in één zin",
  "tension": "Wat verkopers denken vs wat er echt speelt",
  "hook": "Eerste zin van de video - herkenbaar, direct",
  "closing": "Laatste zin - geen advies, geen CTA, laat het hangen",
  "estimated_duration_seconds": 25-35
}"""

    def _build_user_prompt(self, content_type: Optional[ContentType], count: int, language: str) -> str:
        type_hint = ""
        if content_type:
            hints = {
                ContentType.BUYER_BEHAVIOR: "Focus op hoe kopers écht beslissen, niet hoe wij denken dat ze beslissen.",
                ContentType.SELLER_BLINDSPOT: "Focus op wat verkopers consequent missen of verkeerd inschatten.",
                ContentType.DEAL_DYNAMICS: "Focus op waarom deals vastlopen of mislukken.",
                ContentType.PROCESS_TRAP: "Focus op waar salesprocessen averechts werken.",
                ContentType.REALITY_CHECK: "Focus op ongemakkelijke waarheden die niemand uitspreekt."
            }
            type_hint = hints.get(content_type, "")
        
        return f"""Genereer {count} topic(s) voor een korte video.

{type_hint}

Denk aan een specifieke situatie die je vaak ziet.
Geen algemene wijsheden. Geen tips. Een observatie.

Iets waarvan verkopers denken: "ja, dat herken ik."

JSON output alleen. Geen uitleg."""

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
                # Backward compatibility mapping
                item["opening_line"] = item.get("hook", "")
                item["closing_line"] = item.get("closing", "")
                item["core_observation"] = item.get("insight", "")
                item["false_belief"] = item.get("tension", "")
                item["reframing"] = item.get("insight", "")
                item["hashtags"] = []
                item["main_points"] = [item.get("insight", "")]
                item["cta"] = item.get("closing", "")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics: {e}")
            return []
