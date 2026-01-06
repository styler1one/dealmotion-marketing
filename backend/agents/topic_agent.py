"""
Topic Agent - Generates content topics and ideas for YouTube shorts.
"""
import json
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

import anthropic
from loguru import logger

from backend.config import get_settings


class ContentType(str, Enum):
    """Types of content we can generate."""
    SALES_TIP = "sales_tip"
    AI_NEWS = "ai_news"
    HOT_TAKE = "hot_take"
    PRODUCT_SHOWCASE = "product_showcase"


@dataclass
class TopicIdea:
    """A generated topic idea."""
    content_type: ContentType
    title: str
    hook: str  # Opening hook to grab attention
    main_points: List[str]
    cta: str  # Call to action
    hashtags: List[str]
    estimated_duration_seconds: int = 45


class TopicAgent:
    """
    AI agent that generates content topics for YouTube shorts.
    Uses Claude to brainstorm engaging video ideas.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_topics(
        self, 
        content_type: Optional[ContentType] = None,
        count: int = 5,
        language: str = "nl"
    ) -> List[TopicIdea]:
        """
        Generate topic ideas for YouTube shorts.
        
        Args:
            content_type: Specific type of content, or None for mixed
            count: Number of topics to generate
            language: Language for content (nl or en)
        """
        logger.info(f"Generating {count} topic ideas (type={content_type}, lang={language})")
        
        system_prompt = self._build_system_prompt(language)
        user_prompt = self._build_user_prompt(content_type, count, language)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            # Parse the response
            content = response.content[0].text
            topics = self._parse_topics(content)
            
            logger.info(f"Generated {len(topics)} topic ideas")
            return topics
            
        except Exception as e:
            logger.error(f"Failed to generate topics: {e}")
            raise
    
    def _build_system_prompt(self, language: str) -> str:
        """Build the system prompt for topic generation."""
        lang_instruction = "in het Nederlands" if language == "nl" else "in English"
        
        return f"""Je bent een expert content strategist voor B2B sales content op YouTube.
Je taak is om virale, engaging topic ideas te genereren voor YouTube Shorts over sales en AI.

CONTEXT:
- Brand: {self.settings.brand_name}
- Website: {self.settings.brand_website}
- Tagline: {self.settings.brand_tagline}
- Target audience: B2B sales professionals (Account Executives, BDRs, Sales Managers)

CONTENT TYPES:
1. SALES_TIP - Praktische sales tips en technieken
2. AI_NEWS - Nieuws over AI tools voor sales
3. HOT_TAKE - Controversiële meningen over sales/AI
4. PRODUCT_SHOWCASE - DealMotion features uitlichten

REQUIREMENTS:
- Shorts zijn 30-60 seconden
- Hook moet binnen 1 seconde aandacht pakken
- Content moet {lang_instruction}
- Focus op waarde, niet op verkopen
- Eindig altijd met een CTA naar DealMotion

OUTPUT FORMAT:
Geef je antwoord als een JSON array met objecten die deze velden hebben:
- content_type: een van [sales_tip, ai_news, hot_take, product_showcase]
- title: YouTube titel (max 60 chars)
- hook: opening hook (1-2 zinnen, moet direct intrigeren)
- main_points: array van 2-3 key points
- cta: call to action (kort)
- hashtags: array van 5 relevante hashtags
- estimated_duration_seconds: geschatte duur (30-60)"""

    def _build_user_prompt(
        self, 
        content_type: Optional[ContentType],
        count: int,
        language: str
    ) -> str:
        """Build the user prompt for topic generation."""
        type_instruction = ""
        if content_type:
            type_instruction = f"Focus alleen op {content_type.value} content."
        else:
            type_instruction = "Maak een mix van verschillende content types."
        
        return f"""Genereer {count} unieke topic ideas voor YouTube Shorts.

{type_instruction}

Zorg dat elk topic:
- Een sterke hook heeft die nieuwsgierig maakt
- Concrete, actionable waarde biedt
- Past bij B2B sales professionals
- Niet te "salesy" overkomt

Antwoord ALLEEN met een JSON array, geen andere tekst."""

    def _parse_topics(self, content: str) -> List[TopicIdea]:
        """Parse the Claude response into TopicIdea objects."""
        # Clean up the response (remove markdown code blocks if present)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        try:
            data = json.loads(content)
            topics = []
            
            for item in data:
                topic = TopicIdea(
                    content_type=ContentType(item.get("content_type", "sales_tip")),
                    title=item.get("title", ""),
                    hook=item.get("hook", ""),
                    main_points=item.get("main_points", []),
                    cta=item.get("cta", ""),
                    hashtags=item.get("hashtags", []),
                    estimated_duration_seconds=item.get("estimated_duration_seconds", 45)
                )
                topics.append(topic)
            
            return topics
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics JSON: {e}")
            logger.debug(f"Raw content: {content}")
            return []


# Convenience function
def generate_topics(
    content_type: Optional[ContentType] = None,
    count: int = 5,
    language: str = "nl"
) -> List[TopicIdea]:
    """Generate topic ideas for YouTube shorts."""
    agent = TopicAgent()
    return agent.generate_topics(content_type, count, language)

