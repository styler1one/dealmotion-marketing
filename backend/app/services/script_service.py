"""
Script Service - Generate thought leadership scripts using Claude.

Structure: Observation → Friction → Reframe → Implication
Tone: Calm, precise, slightly contrarian, no hype, no coaching.
"""
import json
import uuid
from datetime import datetime
from typing import Optional

import anthropic
from loguru import logger

from app.config import get_settings


class ScriptService:
    """Service for generating thought leadership scripts using Claude."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_script(
        self,
        topic: dict,
        language: str = "nl",
        target_duration: int = 30  # Thought leadership: 20-40 sec
    ) -> dict:
        """Generate a thought leadership script from a topic."""
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
        
        # Native Dutch language rules - only added when language is Dutch
        native_dutch_section = """

=== NATIVE DUTCH LANGUAGE (CRITICAL) ===

You write in native Dutch, NOT translated English.
Write like a Dutch sales director thinks and speaks in a 1:1 conversation.

The difference:
❌ TRANSLATED: "Activiteit maskeert het gebrek aan echte progressie"
✅ NATIVE: "Je bent druk. Maar niet verder"

❌ TRANSLATED: "De vraag is niet hoeveel er gebeurt, maar wat er daadwerkelijk verandert"
✅ NATIVE: "Er gebeurt genoeg. Alleen niet wat nodig is"

❌ TRANSLATED: "Dit leidt tot een vals gevoel van controle"
✅ NATIVE: "Dat voelt als controle. Maar dat is het niet"

FORBIDDEN Dutch patterns:
- "maskeert het gebrek aan"
- "daadwerkelijk verandert"
- "richting een beslissing"
- "de vraag is niet X, maar Y"
- "essentieel voor succes"
- "leidt tot" (abstract constructions)
- Abstract noun stacking
- Symmetrical sentences

REQUIRED Dutch patterns:
- Short sentences (max 12 words)
- Spoken thought, not written theory
- Understatement (onderkoeld)
- "Dan" not "In dat geval"
- "Je" not "men"
- One thought per sentence
- Prefer verbs over abstract nouns

GOOD Dutch phrasing examples:
- "Je kunt druk zijn zonder ergens te komen"
- "Daar zit het probleem meestal niet"
- "Niemand zegt het, maar iedereen weet het"
- "Dan ben je bezig. Maar niet verder"
- "Dat klinkt logisch. Maar klopt niet"

=== END NATIVE DUTCH ===
""" if language == "nl" else ""
        
        return f"""You are a thought leadership editor who writes in native Dutch.

You write scripts that sound like someone who has seen hundreds of B2B deals fail for the same reasons.
You write like a Dutch founder or sales director would actually speak, not like translated English.

POSITIONING (NON-NEGOTIABLE):
The content is:
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

TONE:
- Calm
- Precise
- Slightly contrarian
- No hype
- No coaching
- Onderkoeld (undercooled, Dutch understatement)
{native_dutch_section}

STRUCTURE (MANDATORY):
1. OBSERVATION – what you keep seeing
2. FRICTION – why this is uncomfortable or ignored
3. REFRAME – how to look at it differently
4. IMPLICATION – what this makes UNCOMFORTABLE for the seller

IMPLICATION RULES (CRITICAL):
- Must introduce mild cognitive dissonance
- Should question identity or habit, not suggest a solution
- Must NOT resolve the tension
- If the implication feels comforting, reject and rewrite

EDITORIAL SILENCE (MANDATORY):
The script must include at least one sentence that feels incomplete on purpose.
A sentence that ends, but does not conclude.
Example: "Je verliest deals niet door slechte intenties. Maar door wat je nooit opmerkt."

RULES (HARD):
- Max 90 words
- Short sentences, but not punchy
- No rhetorical questions
- No calls to action
- No product mention
- No time references ("today", "now", "in 2026")
- No emojis
- No exclamation marks
- If the implication feels comforting, reject the script

FORBIDDEN words/phrases:
- "game changer"
- year references
- "AI is changing..."
- "je moet" / "you should"
- "snelle tip" / "quick tip"

The script should feel unfinished on purpose.
Leave space for thought.
The viewer should feel slightly unsettled, not reassured.

OUTPUT FORMAT (JSON only):
- title: calm, confident, max 45 chars, no emojis
- description: one sentence summary
- full_text: the complete script (max 90 words, native Dutch)
- segments: array with observation, friction, reframe, implication
- total_word_count: actual word count
- total_duration_seconds: estimated duration (20-40)

Write {lang_instruction}."""

    def _build_user_prompt(self, topic: dict, target_duration: int, language: str) -> str:
        return f"""Create a script based on:

CORE OBSERVATION: {topic.get('core_observation', topic.get('hook', ''))}
FALSE BELIEF: {topic.get('false_belief', '')}
REFRAMING: {topic.get('reframing', '')}
OPENING LINE: {topic.get('opening_line', topic.get('hook', ''))}
CLOSING LINE: {topic.get('closing_line', '')}
TITLE: {topic.get('title', '')}

Target duration: {target_duration} seconds
Language: {'Nederlands' if language == 'nl' else 'English'}

JSON output only. No explanations.
Structure: observation → friction → reframe → implication
Max 90 words. Leave space for thought."""

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
                    data["full_text"] = topic.get("opening_line", "") + " " + topic.get("closing_line", "")
            
            # Calculate word count if not present
            if "total_word_count" not in data:
                data["total_word_count"] = len(data["full_text"].split())
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script: {e}")
            return {
                "id": str(uuid.uuid4()),
                "title": topic.get("title", ""),
                "description": "",
                "segments": [],
                "full_text": topic.get("opening_line", "") + " " + topic.get("core_observation", ""),
                "total_word_count": 0,
                "total_duration_seconds": 30
            }
