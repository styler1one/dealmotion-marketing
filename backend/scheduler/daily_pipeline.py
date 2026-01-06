"""
Daily Pipeline - Automated content generation and publishing.

This scheduler runs daily to:
1. Generate new content topics
2. Create scripts
3. Generate videos
4. Upload to YouTube
5. Track results

Usage:
    python backend/scheduler/daily_pipeline.py          # Run once
    python backend/scheduler/daily_pipeline.py --daemon # Run as daemon
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, time
from typing import List

import click
import schedule
from rich.console import Console
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.config import get_settings
from backend.agents.topic_agent import TopicAgent, TopicIdea
from backend.agents.script_agent import ScriptAgent, VideoScript
from backend.services.tts_service import TTSService
from backend.services.nanobanana_service import get_nanobanana_service, VideoGenerationRequest, VideoStyle
from backend.services.youtube_service import get_youtube_service, VideoUploadRequest


console = Console()


class DailyPipeline:
    """
    Automated daily content generation pipeline.
    
    Generates and publishes shorts based on configured schedule.
    """
    
    def __init__(self, mock: bool = False):
        self.settings = get_settings()
        self.mock = mock
        self.topic_agent = TopicAgent()
        self.script_agent = ScriptAgent()
        
    async def run_pipeline(self) -> dict:
        """
        Run the full content generation pipeline.
        
        Returns:
            dict with pipeline results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "shorts_generated": 0,
            "shorts_uploaded": 0,
            "errors": []
        }
        
        logger.info("=== Starting Daily Pipeline ===")
        
        try:
            # Generate topics for today
            topics = await self._generate_topics()
            
            for topic in topics:
                try:
                    # Generate script
                    script = await self._generate_script(topic)
                    
                    # Generate audio
                    audio_path = await self._generate_audio(script)
                    
                    # Generate video
                    video_path = await self._generate_video(script, audio_path)
                    
                    results["shorts_generated"] += 1
                    
                    # Upload to YouTube
                    if await self._upload_video(script, video_path):
                        results["shorts_uploaded"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing topic '{topic.title}': {e}")
                    results["errors"].append(str(e))
                    
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["errors"].append(str(e))
        
        logger.info(f"=== Pipeline Complete: {results['shorts_generated']} generated, {results['shorts_uploaded']} uploaded ===")
        return results
    
    async def _generate_topics(self) -> List[TopicIdea]:
        """Generate topics for the day."""
        logger.info(f"Generating {self.settings.shorts_per_day} topics...")
        
        # Mix of content types for variety
        topics = self.topic_agent.generate_topics(
            content_type=None,  # Mixed
            count=self.settings.shorts_per_day,
            language=self.settings.default_language
        )
        
        logger.info(f"Generated {len(topics)} topics")
        return topics
    
    async def _generate_script(self, topic: TopicIdea) -> VideoScript:
        """Generate a script from a topic."""
        logger.info(f"Generating script for: {topic.title}")
        
        script = self.script_agent.generate_script(
            topic=topic,
            language=self.settings.default_language,
            target_duration=45
        )
        
        return script
    
    async def _generate_audio(self, script: VideoScript) -> Path:
        """Generate voice-over for a script."""
        logger.info("Generating voice-over...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = self.settings.output_dir / f"audio_{timestamp}.mp3"
        
        if self.mock:
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_text("MOCK_AUDIO")
        else:
            tts = TTSService()
            audio_path = await tts.generate_audio(
                text=script.to_full_text(),
                output_path=audio_path
            )
        
        return audio_path
    
    async def _generate_video(self, script: VideoScript, audio_path: Path) -> Path:
        """Generate video from script and audio."""
        logger.info("Generating video...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = self.settings.shorts_output_dir / f"short_{timestamp}.mp4"
        
        nanobanana = get_nanobanana_service(mock=self.mock)
        
        request = VideoGenerationRequest(
            script=script.to_full_text(),
            audio_path=audio_path,
            style=VideoStyle.PROFESSIONAL,
            duration_seconds=int(script.total_duration_seconds),
            include_captions=True
        )
        
        result = await nanobanana.generate_video(request, video_path)
        return result.video_path
    
    async def _upload_video(self, script: VideoScript, video_path: Path) -> bool:
        """Upload video to YouTube."""
        logger.info("Uploading to YouTube...")
        
        youtube = get_youtube_service(mock=self.mock)
        
        if not self.mock:
            if not youtube.authenticate():
                logger.error("YouTube authentication failed")
                return False
        
        request = VideoUploadRequest(
            video_path=video_path,
            title=script.title,
            description=f"{script.description}\n\n🚀 {self.settings.brand_website}",
            tags=script.topic.hashtags + ["sales", "AI", "B2B", self.settings.brand_name],
            is_short=True
        )
        
        result = youtube.upload_video(request)
        logger.info(f"Uploaded: {result.video_url}")
        
        return result.status in ["uploaded", "mock_uploaded"]


def run_pipeline_sync(mock: bool = False):
    """Synchronous wrapper for the pipeline."""
    pipeline = DailyPipeline(mock=mock)
    return asyncio.run(pipeline.run_pipeline())


def schedule_daily(publish_hour: int, mock: bool = False):
    """Schedule the pipeline to run daily."""
    logger.info(f"Scheduling daily pipeline at {publish_hour}:00")
    
    schedule.every().day.at(f"{publish_hour:02d}:00").do(
        run_pipeline_sync, mock=mock
    )
    
    logger.info("Scheduler started. Press Ctrl+C to stop.")
    
    while True:
        schedule.run_pending()
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(60))


@click.command()
@click.option("--mock", "-m", is_flag=True, help="Run in mock mode")
@click.option("--daemon", "-d", is_flag=True, help="Run as daemon (scheduled)")
def main(mock: bool, daemon: bool):
    """Run the daily content pipeline."""
    if daemon:
        settings = get_settings()
        schedule_daily(settings.publish_hour, mock)
    else:
        results = run_pipeline_sync(mock)
        console.print(results)


if __name__ == "__main__":
    main()

