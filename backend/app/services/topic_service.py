"""
Topic Service - Generate thought leadership topics using Claude.

Philosophy: Observation beats advice. Framing beats tactics. Clarity beats hype.
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum

import anthropic
from loguru import logger

from app.config import get_settings


class ContentType(str, Enum):
    """Types of thought leadership content."""
    SALES_ILLUSION = "sales_illusion"      # Something sellers believe that is quietly false
    EXECUTION_FAILURE = "execution_failure" # Why deals stall despite "good activity"
    SIGNAL_MISS = "signal_miss"            # A buying signal most sellers misinterpret
    SYSTEM_FLAW = "system_flaw"            # Where CRM/process creates false confidence
    DECISION_DYNAMICS = "decision_dynamics" # How buyers actually decide vs what sellers assume


class TopicService:
    """Service for generating thought leadership topics using Claude."""
    
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
        """Generate thought leadership topic ideas."""
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
        lang_instruction = "in het Nederlands" if language == "nl" else "in English"
        
        # Native Dutch language rules - only added when language is Dutch
        native_dutch_section = """

=== NATIVE DUTCH LANGUAGE (CRITICAL) ===

You write in native Dutch, NOT translated English.
Write like a Dutch sales director thinks and speaks, not like a translated LinkedIn post.

The difference:
❌ TRANSLATED: "Activiteit in deals maskeert vaak het gebrek aan echte progressie"
✅ NATIVE: "In veel deals is het druk, maar komt er niets dichterbij"

❌ TRANSLATED: "De vraag is niet hoeveel er gebeurt, maar wat er daadwerkelijk verandert"
✅ NATIVE: "Er gebeurt genoeg. Alleen niet wat nodig is"

❌ TRANSLATED: "Beweging zonder richting is gewoon dure stilstand"
✅ NATIVE: "Als niemand een stap zet, blijf je gewoon staan"

FORBIDDEN Dutch patterns (too abstract, too English):
- "maskeert het gebrek aan"
- "daadwerkelijk verandert"
- "richting een beslissing"
- "de vraag is niet X, maar Y"
- "essentieel voor succes"
- "leidt tot" (abstract constructions)
- Abstract noun + verb + abstract noun patterns
- Symmetrical sentences
- "Round" complete sentences

REQUIRED Dutch patterns:
- Prefer verbs over abstract nouns
- Short sentences (max 12 words)
- Spoken thought, not written theory
- Understatement (onderkoeld)
- Sentences that feel slightly unfinished
- "Dan" not "In dat geval"
- "Je" not "men"
- One thought per sentence

EXAMPLES of native Dutch phrasing:
- "Je kunt druk zijn zonder ergens te komen"
- "Daar zit het probleem meestal niet"
- "Dat klinkt logisch, maar klopt niet"
- "Niemand zegt het, maar iedereen weet het"
- "Dan ben je bezig. Maar niet verder"

QUALITY TEST:
Would a Dutch sales director say this in a 1:1 conversation?
If it sounds like a LinkedIn post → rewrite it.

=== END NATIVE DUTCH ===""" if language == "nl" else ""
        
        return f"""You are a senior B2B sales strategist who thinks and writes in native Dutch.

Your role is NOT to generate viral content.
Your role is to surface uncomfortable truths about how B2B deals actually work.

Brand: {self.settings.brand_name}
Positioning: Operating system for serious B2B sellers
Audience: Experienced Dutch B2B sellers, founders, sales leaders

CORE CONTENT PHILOSOPHY
- Observation beats advice
- Framing beats tactics
- Clarity beats hype

EDITORIAL SPINE (MANDATORY)
Every topic must lean into ONE of these tensions:
1. Activity vs Progress → favor Progress
2. Visibility vs Control → favor Control
3. Confidence vs Clarity → favor Clarity
4. Process vs Reality → favor Reality
5. Motion vs Movement → favor Movement

The content must clearly favor one side.
Neutrality is not allowed.

EVERY TOPIC MUST:
- Be based on a real-world sales pattern or failure mode
- Contain one clear point of view
- Challenge a commonly accepted belief in sales

POSITIONING (NON-NEGOTIABLE):
DealMotion content is:
- Observational
- Contrarian
- Calm
- Precise
- Unemotional

NOT:
- Hype-driven
- Coachy
- Salesy
- Energetic
- Creator-like

THOUGHT LEADERSHIP RULES:
Every video must:
- Introduce or correct ONE mental model
- Unmask ONE illusion
- Force ONE framing shift

If it cannot do this → reject the topic.
{native_dutch_section}

LANGUAGE RULES (HARD):
FORBIDDEN words/phrases:
- "game changer"
- "in 2026" or any year reference
- "AI is changing..."
- "je moet" / "you should"
- "snelle tip" / "quick tip"
- emojis
- exclamation marks

ALLOWED:
- Short declarative sentences
- Calm
- Silence
- Implicit authority

AVOID:
- Tips, hacks, checklists
- Motivational language
- Tool-first thinking
- "AI news" unless it changes behavior, not capability

TOPIC TYPES (choose exactly one):
1. SALES_ILLUSION – something sellers believe that is quietly false
2. EXECUTION_FAILURE – why deals stall despite "good activity"
3. SIGNAL_MISS – a buying signal most sellers misinterpret
4. SYSTEM_FLAW – where CRM/process creates false confidence
5. DECISION_DYNAMICS – how buyers actually decide vs what sellers assume

OUTPUT FORMAT (JSON only):
- content_type: one of [sales_illusion, execution_failure, signal_miss, system_flaw, decision_dynamics]
- editorial_tension: which tension this leans into (activity_progress, visibility_control, confidence_clarity, process_reality, motion_movement)
- core_observation: 1 sentence, native Dutch, spoken language
- false_belief: what most sellers think (simple, almost naive phrasing)
- reframing: one sharp sentence, no metaphor stacking
- title: calm, confident, max 45 chars, no emojis, Dutch
- opening_line: observational, calm, no drama, sounds like spoken thought
- closing_line: undercooled, slightly confrontational, unfinished feeling
- estimated_duration_seconds: 20-40

Write {lang_instruction}."""

    def _build_user_prompt(self, content_type: Optional[ContentType], count: int, language: str) -> str:
        type_instruction = f"Focus on {content_type.value}" if content_type else "Mix of types"
        return f"Generate {count} topic(s). {type_instruction}. JSON output only. No explanations."

    def _parse_topics(self, content: str) -> List[dict]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        try:
            data = json.loads(content)
            # Handle single topic vs array
            if isinstance(data, dict):
                data = [data]
            for item in data:
                item["id"] = str(uuid.uuid4())
                # Map to old format for compatibility
                item["hook"] = item.get("opening_line", "")
                item["main_points"] = [item.get("core_observation", "")]
                item["cta"] = item.get("closing_line", "")
                item["hashtags"] = []  # No hashtags for thought leadership
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics: {e}")
            return []
