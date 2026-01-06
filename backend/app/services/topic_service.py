"""
Topic Service - Generate content topics using Claude.
Optimized for viral YouTube Shorts (15-30 sec).
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
        current_date = datetime.now().strftime("%d %B %Y")
        current_year = datetime.now().year
        
        return f"""Je bent een viral YouTube Shorts strateeg voor B2B sales content.

VANDAAG: {current_date}
JAAR: {current_year} (altijd actuele referenties!)

BRAND: {self.settings.brand_name}
WEBSITE: {self.settings.brand_website}
TAGLINE: {self.settings.brand_tagline}
DOELGROEP: B2B sales professionals

⚡ VIRAL SHORTS FORMULES:
1. CONTROVERSY: "X is dood" / "Stop met Y"
2. CURIOSITY GAP: "Dit wist je niet over..."
3. QUICK WIN: "Doe dit NU en..."
4. MYTH BUST: "Iedereen denkt X, maar..."
5. SECRET: "Niemand vertelt je dit..."

CONTENT TYPES:
1. SALES_TIP - Één praktische tip (niet meerdere!)
2. AI_NEWS - Één AI tool of trend ({current_year})
3. HOT_TAKE - Controversiële mening
4. PRODUCT_SHOWCASE - Één DealMotion feature

REQUIREMENTS:
- Shorts zijn 15-25 seconden (KORT!)
- Hook: scroll-stopper in 1-2 sec
- ÉÉN boodschap per video
- Content {lang_instruction}
- Zachte CTA (geen harde sell)

OUTPUT: JSON array met:
- content_type: een van [sales_tip, ai_news, hot_take, product_showcase]
- title: YouTube titel (pakkend, max 50 chars)
- hook: scroll-stopper (max 10 woorden!)
- main_points: array van PRECIES 1 key point
- cta: subtiele call to action
- hashtags: 3 relevante hashtags
- estimated_duration_seconds: 15-25"""

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

