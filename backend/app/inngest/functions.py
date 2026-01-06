"""
Inngest functions for automated content generation.

COMPLETE PIPELINE:
1. Topic Generation (Claude)
2. Script Generation (Claude)
3. Voice-over (ElevenLabs)
4. Background Video (Google Veo 2)
5. Final Render with Captions (Creatomate)
6. YouTube Upload
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
from app.services.render_service import RenderService
from app.services.youtube_service import YouTubeService


# =============================================================================
# Daily Content Pipeline - Runs every day at 10:00 AM
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
    
    Generates and publishes configured number of shorts per day.
    """
    settings = get_settings()
    results = {
        "date": datetime.now().isoformat(),
        "topics_generated": 0,
        "videos_created": 0,
        "videos_uploaded": 0,
        "errors": []
    }
    
    logger.info("🚀 === Starting Daily Content Pipeline ===")
    
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
        logger.info(f"📝 Generated {len(topics)} topics")
        
        # Step 2: Process each topic
        for i, topic in enumerate(topics):
            topic_id = topic.get("id", f"topic_{i}")
            
            try:
                # Generate script
                script = await step.run(
                    f"generate-script-{topic_id}",
                    lambda t=topic: ScriptService().generate_script(t)
                )
                logger.info(f"📜 Script generated for: {topic.get('title')}")
                
                # Trigger video generation workflow
                await step.send_event(
                    "trigger-video-generation",
                    inngest.Event(
                        name="marketing/video.generate",
                        data={
                            "topic": topic,
                            "script": script,
                            "upload_after": True
                        }
                    )
                )
                
            except Exception as e:
                logger.error(f"❌ Error processing topic {topic_id}: {e}")
                results["errors"].append(f"Topic {topic_id}: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        results["errors"].append(str(e))
    
    logger.info(f"✅ === Pipeline Complete: {results} ===")
    return results


# =============================================================================
# Generate Video - Full video creation workflow
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
    Complete video generation pipeline:
    
    1. Generate voice-over (ElevenLabs)
    2. Generate background video (Google Veo 2)
    3. Render final video with captions (Creatomate)
    4. Upload to YouTube
    """
    data = ctx.event.data
    script = data.get("script")
    topic = data.get("topic")
    upload_after = data.get("upload_after", True)
    
    title = topic.get('title', script.get('title', 'Unknown'))
    logger.info(f"🎬 Starting video generation: {title}")
    
    # Step 1: Generate voice-over
    logger.info("🎤 Step 1: Generating voice-over...")
    audio_result = await step.run(
        "generate-tts",
        lambda: TTSService().generate_audio(script.get("full_text"))
    )
    audio_url = audio_result.get("audio_url") if isinstance(audio_result, dict) else audio_result
    logger.info(f"✅ Audio generated: {audio_url}")
    
    # Step 2: Generate background video with Veo 2
    logger.info("🎥 Step 2: Generating background video with Veo 2...")
    video_result = await step.run(
        "generate-background-video",
        lambda: VideoService().generate_video(
            script=script,
            audio_url=audio_url
        )
    )
    background_video_url = video_result.get("video_url")
    logger.info(f"✅ Background video generated: {background_video_url}")
    
    # Step 3: Render final video with Creatomate
    logger.info("✨ Step 3: Rendering final video with captions...")
    
    # Extract text segments for Creatomate (4 scenes max)
    segments = script.get("segments", [])
    texts = [seg.get("text", "") for seg in segments[:4]]
    
    # If no segments, split full_text into 4 parts
    if not texts or all(t == "" for t in texts):
        full_text = script.get("full_text", "")
        words = full_text.split()
        chunk_size = len(words) // 4 + 1
        texts = [
            " ".join(words[i:i+chunk_size]) 
            for i in range(0, len(words), chunk_size)
        ][:4]
    
    # Pad to 4 texts
    while len(texts) < 4:
        texts.append("")
    
    render_result = await step.run(
        "render-final-video",
        lambda: RenderService().render_simple_short(
            texts=texts,
            audio_url=audio_url,
            background_video_url=background_video_url,
        )
    )
    final_video_url = render_result.get("video_url")
    logger.info(f"✅ Final video rendered: {final_video_url}")
    
    # Step 4: Upload to YouTube
    if upload_after:
        logger.info("📺 Step 4: Uploading to YouTube...")
        await step.send_event(
            "trigger-youtube-upload",
            inngest.Event(
                name="marketing/youtube.upload",
                data={
                    "video_url": final_video_url,
                    "title": script.get("title", title),
                    "description": script.get("description", f"Sales tips van {get_settings().brand_name}"),
                    "tags": topic.get("hashtags", ["sales", "AI", "B2B"])
                }
            )
        )
    
    return {
        "status": "completed",
        "audio_url": audio_url,
        "background_video_url": background_video_url,
        "final_video_url": final_video_url,
        "upload_triggered": upload_after
    }


# =============================================================================
# Upload to YouTube
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
    """Upload a video to YouTube."""
    data = ctx.event.data
    
    logger.info(f"📺 Uploading to YouTube: {data.get('title')}")
    
    result = await step.run(
        "upload-video",
        lambda: YouTubeService().upload_video(
            video_url=data.get("video_url"),
            title=data.get("title"),
            description=data.get("description"),
            tags=data.get("tags", [])
        )
    )
    
    logger.info(f"✅ Uploaded: {result.get('youtube_url')}")
    
    return {
        "youtube_id": result.get("youtube_id"),
        "youtube_url": result.get("youtube_url"),
        "status": "uploaded"
    }


# =============================================================================
# Manual Full Pipeline Test - For testing the complete flow
# =============================================================================
@inngest_client.create_function(
    fn_id="test-full-pipeline",
    trigger=inngest.TriggerEvent(event="marketing/test.full-pipeline"),
    retries=0,
)
async def test_full_pipeline_fn(ctx: inngest.Context, step: inngest.Step) -> dict:
    """
    Test the complete pipeline with a sample topic.
    
    Trigger via Inngest dashboard or API:
    POST /api/inngest with event: marketing/test.full-pipeline
    """
    logger.info("🧪 === Starting Full Pipeline Test ===")
    
    settings = get_settings()
    
    # Step 1: Generate 1 topic
    topics = await step.run(
        "test-generate-topic",
        lambda: TopicService().generate_topics(count=1, language="nl")
    )
    topic = topics[0] if topics else {
        "id": "test-topic",
        "title": "Cold Calling is Dood",
        "hook": "Cold calling werkt niet meer. Dit wel.",
        "main_points": ["Moderne buyers doen research", "AI helpt je de juiste timing te vinden", "Focus op waarde, niet pushen"],
        "cta": "Start gratis met DealMotion",
        "hashtags": ["sales", "coldcalling", "AI", "B2B"]
    }
    logger.info(f"📝 Topic: {topic.get('title')}")
    
    # Step 2: Generate script
    script = await step.run(
        "test-generate-script",
        lambda: ScriptService().generate_script(topic)
    )
    logger.info(f"📜 Script generated ({len(script.get('full_text', ''))} chars)")
    
    # Step 3: Generate audio
    audio_result = await step.run(
        "test-generate-audio",
        lambda: TTSService().generate_audio(script.get("full_text"))
    )
    audio_url = audio_result.get("audio_url") if isinstance(audio_result, dict) else audio_result
    logger.info(f"🎤 Audio: {audio_url}")
    
    # Step 4: Generate background video
    video_result = await step.run(
        "test-generate-video",
        lambda: VideoService().generate_video(script=script, audio_url=audio_url)
    )
    background_url = video_result.get("video_url")
    logger.info(f"🎥 Background: {background_url}")
    
    # Step 5: Render final video
    texts = [seg.get("text", "") for seg in script.get("segments", [])[:4]]
    if not texts:
        full_text = script.get("full_text", "")
        words = full_text.split()
        chunk_size = max(1, len(words) // 4)
        texts = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)][:4]
    while len(texts) < 4:
        texts.append("")
    
    render_result = await step.run(
        "test-render-video",
        lambda: RenderService().render_simple_short(
            texts=texts,
            audio_url=audio_url,
            background_video_url=background_url,
        )
    )
    final_url = render_result.get("video_url")
    logger.info(f"✨ Final video: {final_url}")
    
    # Step 6: Upload to YouTube (unlisted for testing)
    youtube_result = await step.run(
        "test-upload-youtube",
        lambda: YouTubeService().upload_video(
            video_url=final_url,
            title=script.get("title", topic.get("title")),
            description=script.get("description", "Test video"),
            tags=topic.get("hashtags", []),
            privacy_status="unlisted"  # Unlisted for testing
        )
    )
    logger.info(f"📺 YouTube: {youtube_result.get('youtube_url')}")
    
    logger.info("🎉 === Full Pipeline Test Complete! ===")
    
    return {
        "status": "success",
        "topic": topic.get("title"),
        "audio_url": audio_url,
        "background_video_url": background_url,
        "final_video_url": final_url,
        "youtube_url": youtube_result.get("youtube_url"),
        "youtube_id": youtube_result.get("youtube_id"),
    }
