"""
Topic Service - Generate content topics using Claude.
"""
import json
import uuid
from typing import List, Optional
from enum import Enum

import anthropic
from loguru import logger

from app.config import get_settings


class ContentType(str, Enum):
    """Types of content we can generate."""
    SALES_TIP = "sales_tip"
    AI_NEWS = "ai_news"
    HOT_TAKE = "hot_take"
    PRODUCT_SHOWCASE = "product_showcase"


class TopicService:
    """Service for generating content topics using Claude."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_topics(
        self,
        content_type: Optional[ContentType] = None,
        count: int = 5,
        language: str = "nl"
    ) -> List[dict]:
        """Generate topic ideas for YouTube shorts."""
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
        
        return f"""Je bent een expert content strategist voor B2B sales content op YouTube.
Je taak is om virale, engaging topic ideas te genereren voor YouTube Shorts over sales en AI.

CONTEXT:
- Brand: {self.settings.brand_name}
- Website: {self.settings.brand_website}
- Tagline: {self.settings.brand_tagline}
- Target audience: B2B sales professionals

CONTENT TYPES:
1. SALES_TIP - Praktische sales tips
2. AI_NEWS - AI tools voor sales
3. HOT_TAKE - Controversiële meningen
4. PRODUCT_SHOWCASE - DealMotion features

REQUIREMENTS:
- Shorts zijn 30-60 seconden
- Hook moet direct aandacht pakken
- Content {lang_instruction}
- Eindig met CTA naar DealMotion

OUTPUT: JSON array met objecten:
- content_type: een van [sales_tip, ai_news, hot_take, product_showcase]
- title: YouTube titel (max 60 chars)
- hook: opening hook (1-2 zinnen)
- main_points: array van 2-3 key points
- cta: call to action
- hashtags: array van 5 hashtags
- estimated_duration_seconds: 30-60"""

    def _build_user_prompt(self, content_type: Optional[ContentType], count: int, language: str) -> str:
        type_instruction = f"Focus op {content_type.value}" if content_type else "Mix van types"
        return f"Genereer {count} topics. {type_instruction}. Alleen JSON output."

    def _parse_topics(self, content: str) -> List[dict]:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        try:
            data = json.loads(content)
            for item in data:
                item["id"] = str(uuid.uuid4())
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse topics: {e}")
            return []

