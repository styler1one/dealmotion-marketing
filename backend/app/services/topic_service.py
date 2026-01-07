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
        
        return f"""You are a senior B2B sales strategist.

Your role is NOT to generate viral content.
Your role is to surface uncomfortable truths about how B2B deals actually work.

Brand: {self.settings.brand_name}
Positioning: Operating system for serious B2B sellers
Audience: Experienced B2B sellers, founders, sales leaders

CORE CONTENT PHILOSOPHY
- Observation beats advice
- Framing beats tactics
- Clarity beats hype

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
- core_observation: 1 sentence, declarative
- false_belief: what most sellers think
- reframing: what's actually true
- title: calm, confident, max 45 chars, no emojis
- opening_line: first sentence of the video, no hook language
- closing_line: open loop, no CTA
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
