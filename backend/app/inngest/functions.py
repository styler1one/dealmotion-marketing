"""
Inngest functions for automated content generation.
"""
import inngest
from datetime import datetime
from loguru import logger

from app.inngest.client import inngest_client
from app.config import get_settings
from app.services.topic_service import TopicService
from app.services.script_service import ScriptService
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from app.services.youtube_service import YouTubeService


# =============================================================================
# Daily Content Pipeline - Runs every day at configured hour
# =============================================================================
@inngest_client.create_function(
    fn_id="daily-content-pipeline",
    trigger=inngest.TriggerCron(cron="0 10 * * *"),  # 10:00 AM daily
    retries=2,
)
async def daily_content_pipeline(
    ctx: inngest.Context,
    step: inngest.Step,
) -> dict:
    """
    Daily automated content generation pipeline.
    
    1. Generate topic ideas
    2. Create scripts
    3. Generate videos
    4. Upload to YouTube
    """
    settings = get_settings()
    results = {
        "date": datetime.now().isoformat(),
        "topics_generated": 0,
        "videos_created": 0,
        "videos_uploaded": 0,
        "errors": []
    }
    
    logger.info("=== Starting Daily Content Pipeline ===")
    
    try:
        # Step 1: Generate topics
        topics = await step.run(
            "generate-topics",
            lambda: TopicService().generate_topics(
                count=settings.shorts_per_day,
                language=settings.default_language
            )
        )
        results["topics_generated"] = len(topics)
        
        # Step 2: Process each topic
        for i, topic in enumerate(topics):
            topic_id = topic.get("id", f"topic_{i}")
            
            try:
                # Generate script
                script = await step.run(
                    f"generate-script-{topic_id}",
                    lambda t=topic: ScriptService().generate_script(t)
                )
                
                # Trigger video generation (separate workflow)
                await step.send_event(
                    "generate-video",
                    data={
                        "topic": topic,
                        "script": script,
                        "upload_after": True
                    }
                )
                
            except Exception as e:
                logger.error(f"Error processing topic {topic_id}: {e}")
                results["errors"].append(f"Topic {topic_id}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        results["errors"].append(str(e))
    
    logger.info(f"=== Pipeline Complete: {results} ===")
    return results


# =============================================================================
# Generate Video - Triggered by pipeline or manually
# =============================================================================
@inngest_client.create_function(
    fn_id="generate-video",
    trigger=inngest.TriggerEvent(event="marketing/video.generate"),
    retries=2,
)
async def generate_video_fn(
    ctx: inngest.Context,
    step: inngest.Step,
) -> dict:
    """
    Generate a video from a script.
    
    1. Generate voice-over (TTS)
    2. Create video with NanoBanana
    3. Optionally trigger upload
    """
    data = ctx.event.data
    script = data.get("script")
    topic = data.get("topic")
    upload_after = data.get("upload_after", True)
    
    logger.info(f"Generating video for: {topic.get('title', 'Unknown')}")
    
    # Step 1: Generate voice-over
    audio_url = await step.run(
        "generate-tts",
        lambda: TTSService().generate_audio(script.get("full_text"))
    )
    
    # Step 2: Generate video
    video_result = await step.run(
        "generate-video",
        lambda: VideoService().generate_video(
            script=script,
            audio_url=audio_url
        )
    )
    
    # Step 3: Trigger upload if requested
    if upload_after:
        await step.send_event(
            "upload-youtube",
            data={
                "video_url": video_result.get("video_url"),
                "title": script.get("title"),
                "description": script.get("description"),
                "tags": topic.get("hashtags", [])
            }
        )
    
    return {
        "video_id": video_result.get("id"),
        "video_url": video_result.get("video_url"),
        "upload_triggered": upload_after
    }


# =============================================================================
# Upload to YouTube - Triggered after video generation
# =============================================================================
@inngest_client.create_function(
    fn_id="upload-youtube",
    trigger=inngest.TriggerEvent(event="marketing/youtube.upload"),
    retries=2,
)
async def upload_to_youtube_fn(
    ctx: inngest.Context,
    step: inngest.Step,
) -> dict:
    """
    Upload a video to YouTube.
    """
    data = ctx.event.data
    
    logger.info(f"Uploading to YouTube: {data.get('title')}")
    
    # Upload video
    result = await step.run(
        "upload-video",
        lambda: YouTubeService().upload_video(
            video_url=data.get("video_url"),
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", [])
        )
    )
    
    logger.info(f"Uploaded: {result.get('youtube_url')}")
    
    return {
        "youtube_id": result.get("youtube_id"),
        "youtube_url": result.get("youtube_url"),
        "status": "uploaded"
    }


# =============================================================================
# Manual trigger for testing
# =============================================================================
@inngest_client.create_function(
    fn_id="test-pipeline",
    trigger=inngest.TriggerEvent(event="marketing/test.pipeline"),
    retries=0,
)
async def test_pipeline_fn(
    ctx: inngest.Context,
    step: inngest.Step,
) -> dict:
    """Test function for pipeline debugging."""
    logger.info("Test pipeline triggered")
    
    return {
        "status": "ok",
        "message": "Test pipeline executed successfully",
        "timestamp": datetime.now().isoformat()
    }

