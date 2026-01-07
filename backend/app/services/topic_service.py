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

Doel: Stop scrolling. Laat denken. Geen verkoop.

---

DE HOOK IS ALLES

De eerste 2 seconden bepalen of iemand stopt met scrollen.
Je opening moet:
- Iets zeggen wat ze nog niet eerder hoorden
- Direct hun realiteit raken
- Prikkelend zijn, maar niet schreeuwerig

GOEDE HOOKS:
- "Een deal met veel meetings voelt productief."
- "Je stuurt drie follow-ups. Geen reactie."
- "Ze waren super enthousiast na de demo."

SLECHTE HOOKS:
- "Wist je dat..." (saai)
- "In deze video..." (obvious)
- "Sales is..." (te algemeen)

---

TOPIC STRUCTUUR:

1. HOOK - Pakkende opening (wat ze herkennen)
2. HERKENNING - Concreet beeld van hun realiteit
3. SHIFT - Andere kijk (geen oplossing, geen advies)

---

TOPIC TYPES:

1. SALES_ILLUSION - overtuiging die niet klopt
   Hook: "Een drukke pipeline voelt goed."
   Shift: "Drukte en voortgang zijn niet hetzelfde."
   
2. EXECUTION_FAILURE - activiteit zonder resultaat
   Hook: "Je doet alles goed. En toch loopt het vast."
   Shift: "Soms is minder doen meer bereiken."
   
3. SIGNAL_MISS - verkeerd gelezen signaal
   Hook: "Ze vroegen om een voorstel."
   Shift: "Een vraag om info is geen koopsignaal."
   
4. SYSTEM_FLAW - proces dat averechts werkt
   Hook: "Alles staat netjes in Salesforce."
   Shift: "Registreren is geen verkopen."
   
5. DECISION_DYNAMICS - hoe kopers echt beslissen
   Hook: "De beslisser zei ja."
   Shift: "Ja zeggen is makkelijker dan nee zeggen."

---

TOON:

- Rustig, niet opgewonden
- Collega in een café, niet guru op LinkedIn
- Constateren, niet preken

---

NATIVE DUTCH:

Schrijf zoals een Nederlandse sales director praat.

NIET: "Activiteit maskeert het gebrek aan progressie"
WEL: "Je bent druk. Maar er gebeurt niks."

NIET: "De vraag is niet X, maar Y"
WEL: "Het gaat niet om X. Het gaat om Y."

Korte zinnen. Max 8 woorden per zin.

---

VERBODEN:
- Vragen ("Wist je dat...?")
- "game changer", "je moet", "snelle tip"
- Emoji's en uitroeptekens

---

OUTPUT (JSON):

{{
  "content_type": "sales_illusion|execution_failure|signal_miss|system_flaw|decision_dynamics",
  "title": "Korte titel, max 40 tekens",
  "hook": "Opening zin die aandacht pakt (max 8 woorden)",
  "core_observation": "Wat je ziet - concreet, herkenbaar",
  "false_belief": "Wat ze denken (simpel)",
  "reframing": "Andere kijk (geen oplossing)",
  "opening_line": "Eerste zin van video = de hook",
  "closing_line": "Laatste zin - open, geen conclusie",
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
