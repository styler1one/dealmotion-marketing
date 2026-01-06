"""
Script Agent - Generates full video scripts from topics.
"""
import json
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

import anthropic
from loguru import logger

from backend.config import get_settings
from backend.agents.topic_agent import TopicIdea, ContentType


@dataclass
class ScriptSegment:
    """A segment of the video script."""
    type: str  # "hook", "content", "cta"
    text: str
    duration_seconds: float
    visual_cue: str  # Description of what should be on screen


@dataclass
class VideoScript:
    """Complete video script with all segments."""
    topic: TopicIdea
    segments: list[ScriptSegment] = field(default_factory=list)
    title: str = ""
    description: str = ""
    total_duration_seconds: float = 0
    
    def to_full_text(self) -> str:
        """Get the full script text for TTS."""
        return " ".join(segment.text for segment in self.segments)
    
    def to_tts_segments(self) -> list[dict]:
        """Get segments formatted for TTS processing."""
        return [
            {
                "text": segment.text,
                "duration": segment.duration_seconds,
                "type": segment.type
            }
            for segment in self.segments
        ]


class ScriptAgent:
    """
    AI agent that generates full video scripts from topic ideas.
    Creates engaging, well-paced scripts optimized for YouTube Shorts.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def generate_script(
        self,
        topic: TopicIdea,
        language: str = "nl",
        target_duration: int = 45
    ) -> VideoScript:
        """
        Generate a complete video script from a topic idea.
        
        Args:
            topic: The topic idea to expand into a script
            language: Language for the script
            target_duration: Target duration in seconds (30-60)
        """
        logger.info(f"Generating script for: {topic.title}")
        
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
            
            logger.info(f"Generated script: {script.total_duration_seconds}s")
            return script
            
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            raise
    
    def _build_system_prompt(self, language: str) -> str:
        """Build the system prompt for script generation."""
        lang_instruction = "in het Nederlands" if language == "nl" else "in English"
        
        return f"""Je bent een expert scriptwriter voor YouTube Shorts.
Je schrijft scripts die:
- Direct de aandacht pakken (eerste 1-2 seconden cruciaal)
- Snelle, punchy zinnen gebruiken
- Waarde leveren zonder fluff
- Een duidelijke CTA hebben

BRAND CONTEXT:
- Brand: {self.settings.brand_name}
- Product: AI-powered sales enablement platform
- Tagline: {self.settings.brand_tagline}
- Waarde: Bespaart sales professionals uren aan research en voorbereiding

SCRIPT STRUCTUUR:
1. HOOK (0-3 sec): Pak direct de aandacht
2. CONTENT (3-50 sec): Lever de beloofde waarde
3. CTA (50-60 sec): Stuur naar actie

SCHRIJFSTIJL:
- Conversationeel, niet corporate
- Kort en krachtig
- Gebruik cijfers en specifieke voorbeelden
- {lang_instruction}

OUTPUT FORMAT:
Geef je antwoord als JSON met deze structuur:
{{
  "title": "YouTube titel",
  "description": "YouTube beschrijving (2-3 zinnen)",
  "segments": [
    {{
      "type": "hook" | "content" | "cta",
      "text": "De gesproken tekst",
      "duration_seconds": 5,
      "visual_cue": "Beschrijving van visual"
    }}
  ],
  "total_duration_seconds": 45
}}"""

    def _build_user_prompt(
        self,
        topic: TopicIdea,
        target_duration: int,
        language: str
    ) -> str:
        """Build the user prompt for script generation."""
        return f"""Schrijf een compleet script voor deze YouTube Short:

TOPIC:
- Type: {topic.content_type.value}
- Titel: {topic.title}
- Hook: {topic.hook}
- Hoofdpunten: {', '.join(topic.main_points)}
- CTA: {topic.cta}

REQUIREMENTS:
- Target duur: {target_duration} seconden
- Taal: {"Nederlands" if language == "nl" else "English"}
- Maak het energiek en engaging
- Elke zin moet waarde toevoegen

VISUAL CUES:
Geef bij elk segment een visual_cue die beschrijft wat er op het scherm moet staan.
Denk aan:
- Tekst overlays met key points
- Stock footage suggesties
- Animatie suggesties

Antwoord ALLEEN met JSON, geen andere tekst."""

    def _parse_script(self, content: str, topic: TopicIdea) -> VideoScript:
        """Parse the Claude response into a VideoScript object."""
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        try:
            data = json.loads(content)
            
            segments = []
            for seg in data.get("segments", []):
                segment = ScriptSegment(
                    type=seg.get("type", "content"),
                    text=seg.get("text", ""),
                    duration_seconds=seg.get("duration_seconds", 5),
                    visual_cue=seg.get("visual_cue", "")
                )
                segments.append(segment)
            
            script = VideoScript(
                topic=topic,
                segments=segments,
                title=data.get("title", topic.title),
                description=data.get("description", ""),
                total_duration_seconds=data.get("total_duration_seconds", 45)
            )
            
            return script
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse script JSON: {e}")
            logger.debug(f"Raw content: {content}")
            
            # Return a basic script on parse failure
            return VideoScript(
                topic=topic,
                segments=[
                    ScriptSegment(
                        type="content",
                        text=topic.hook + " " + " ".join(topic.main_points),
                        duration_seconds=45,
                        visual_cue="Main content"
                    )
                ],
                title=topic.title,
                description="",
                total_duration_seconds=45
            )


# Convenience function
def generate_script(
    topic: TopicIdea,
    language: str = "nl",
    target_duration: int = 45
) -> VideoScript:
    """Generate a video script from a topic idea."""
    agent = ScriptAgent()
    return agent.generate_script(topic, language, target_duration)

