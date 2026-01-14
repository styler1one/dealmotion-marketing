"""
Inngest functions for automated content generation.

COMPLETE PIPELINE:
1. Topic Generation (Claude)
2. Script Generation (Claude)
3. Voice-over (ElevenLabs)
4. Background Video (Google Veo 2)
5. Final Render with Captions (Creatomate)
6. YouTube Upload
7. Save to Database

NOTE: Using Inngest SDK v0.5+ signature where step is accessed via ctx.step
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
from app.services.database_service import DatabaseService


# =============================================================================
# Daily Content Pipeline - PAUSED (uncomment trigger to enable)
# =============================================================================
# @inngest_client.create_function(
#     fn_id="daily-content-pipeline",
#     trigger=inngest.TriggerCron(cron="0 10 * * *"),  # 10:00 AM daily
#     retries=2,
# )
async def daily_content_pipeline_PAUSED(ctx: inngest.Context) -> dict:
    """
    Daily automated content generation pipeline.
    
    Generates and publishes configured number of shorts per day.
    """
    step = ctx.step
    settings = get_settings()
    db = DatabaseService()
    
    # Create pipeline run record
    pipeline_run = await step.run(
        "create-pipeline-run",
        lambda: db.create_pipeline_run()
    )
    run_id = pipeline_run.get("id")
    
    results = {
        "date": datetime.now().isoformat(),
        "run_id": run_id,
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
        
        # Save topics to database
        saved_topics = []
        for topic in topics:
            saved_topic = await step.run(
                f"save-topic-{topic.get('id', 'unknown')}",
                lambda t=topic: db.create_topic(t)
            )
            saved_topics.append(saved_topic)
        
        # Update pipeline run
        await step.run(
            "update-run-topics",
            lambda: db.update_pipeline_run(run_id, topics_generated=len(topics))
        )
        
        # Step 2: Process each topic
        for i, topic in enumerate(saved_topics):
            topic_id = topic.get("id", f"topic_{i}")
            
            try:
                # Generate script
                script = await step.run(
                    f"generate-script-{topic_id}",
                    lambda t=topic: ScriptService().generate_script(t)
                )
                logger.info(f"📜 Script generated for: {topic.get('title')}")
                
                # Save script to database
                saved_script = await step.run(
                    f"save-script-{topic_id}",
                    lambda s=script, tid=topic_id: db.create_script(s, tid)
                )
                
                # Update pipeline run
                await step.run(
                    f"update-run-scripts-{topic_id}",
                    lambda: db.update_pipeline_run(run_id, scripts_generated=i+1)
                )
                
                # Trigger video generation workflow
                await step.send_event(
                    "trigger-video-generation",
                    inngest.Event(
                        name="marketing/video.generate",
                        data={
                            "topic": topic,
                            "script": script,
                            "topic_id": topic_id,
                            "script_id": saved_script.get("id"),
                            "run_id": run_id,
                            "upload_after": True
                        }
                    )
                )
                
            except Exception as e:
                logger.error(f"❌ Error processing topic {topic_id}: {e}")
                results["errors"].append(f"Topic {topic_id}: {str(e)}")
        
        # Mark pipeline as completed
        await step.run(
            "complete-pipeline-run",
            lambda: db.update_pipeline_run(run_id, status="completed")
        )
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        results["errors"].append(str(e))
        await step.run(
            "fail-pipeline-run",
            lambda: db.update_pipeline_run(run_id, status="failed", errors=[str(e)])
        )
    
    logger.info(f"✅ === Pipeline Complete: {results} ===")
    return results


# =============================================================================
# Generate Video - PAUSED (uncomment to enable)
# =============================================================================
# @inngest_client.create_function(
#     fn_id="generate-video",
#     trigger=inngest.TriggerEvent(event="marketing/video.generate"),
#     retries=2,
# )
async def generate_video_fn_PAUSED(ctx: inngest.Context) -> dict:
    """
    Complete video generation pipeline:
    
    1. Generate voice-over (ElevenLabs)
    2. Generate background video (Google Veo 2)
    3. Render final video with captions (Creatomate)
    4. Save to database
    5. Upload to YouTube
    """
    step = ctx.step
    data = ctx.event.data
    script = data.get("script")
    topic = data.get("topic")
    topic_id = data.get("topic_id")
    script_id = data.get("script_id")
    run_id = data.get("run_id")
    upload_after = data.get("upload_after", True)
    
    db = DatabaseService()
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
    # Note: Inngest step results may not support Python slicing, so convert to list first
    segments = list(script.get("segments", []) or [])
    texts = [seg.get("text", "") if isinstance(seg, dict) else str(seg) for seg in segments[:4]]
    
    # If no segments, split full_text into 4 parts
    if not texts or all(t == "" for t in texts):
        full_text = script.get("full_text", "") or ""
        words = full_text.split()
        chunk_size = max(1, len(words) // 4)
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
    
    # Step 4: Save video to database
    video_record = await step.run(
        "save-video-to-db",
        lambda: db.create_video(
            title=title,
            script_id=script_id,
            video_url=final_video_url,
            audio_url=audio_url,
            duration_seconds=script.get("total_duration_seconds", 25)
        )
    )
    video_db_id = video_record.get("id")
    logger.info(f"💾 Video saved to database: {video_db_id}")
    
    # Update pipeline run if we have run_id
    if run_id:
        await step.run(
            "update-run-videos",
            lambda: db.update_pipeline_run(run_id, videos_created=1)
        )
    
    # Step 5: Upload to YouTube
    if upload_after:
        logger.info("📺 Step 5: Uploading to YouTube...")
        await step.send_event(
            "trigger-youtube-upload",
            inngest.Event(
                name="marketing/youtube.upload",
                data={
                    "video_url": final_video_url,
                    "video_db_id": video_db_id,
                    "run_id": run_id,
                    "title": script.get("title", title),
                    "description": script.get("description", f"Sales tips van {get_settings().brand_name}"),
                    "tags": topic.get("hashtags", ["sales", "AI", "B2B"])
                }
            )
        )
    
    return {
        "status": "completed",
        "video_db_id": video_db_id,
        "audio_url": audio_url,
        "background_video_url": background_video_url,
        "final_video_url": final_video_url,
        "upload_triggered": upload_after
    }


# =============================================================================
# Upload to YouTube - PAUSED (uncomment to enable)
# =============================================================================
# @inngest_client.create_function(
#     fn_id="upload-youtube",
#     trigger=inngest.TriggerEvent(event="marketing/youtube.upload"),
#     retries=2,
# )
async def upload_to_youtube_fn_PAUSED(ctx: inngest.Context) -> dict:
    """Upload a video to YouTube and save to database."""
    step = ctx.step
    data = ctx.event.data
    db = DatabaseService()
    
    video_db_id = data.get("video_db_id")
    run_id = data.get("run_id")
    
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
    
    youtube_id = result.get("youtube_id")
    youtube_url = result.get("youtube_url")
    logger.info(f"✅ Uploaded: {youtube_url}")
    
    # Save YouTube upload to database
    if video_db_id:
        await step.run(
            "save-youtube-upload",
            lambda: db.create_youtube_upload(
                video_id=video_db_id,
                youtube_id=youtube_id,
                youtube_url=youtube_url,
                title=data.get("title"),
                description=data.get("description"),
                tags=data.get("tags", [])
            )
        )
        logger.info(f"💾 YouTube upload saved to database")
    
    # Update pipeline run if we have run_id
    if run_id:
        await step.run(
            "update-run-uploads",
            lambda: db.update_pipeline_run(run_id, videos_uploaded=1)
        )
    
    return {
        "youtube_id": youtube_id,
        "youtube_url": youtube_url,
        "status": "uploaded"
    }


# =============================================================================
# Manual Full Pipeline Test - PAUSED (uncomment to enable)
# =============================================================================
# @inngest_client.create_function(
#     fn_id="test-full-pipeline",
#     trigger=inngest.TriggerEvent(event="marketing/test.full-pipeline"),
#     retries=0,
# )
async def test_full_pipeline_fn_PAUSED(ctx: inngest.Context) -> dict:
    """
    Test the complete pipeline with a sample topic.
    Saves all results to database for dashboard visibility.
    
    Trigger via Inngest dashboard or API:
    POST /api/inngest with event: marketing/test.full-pipeline
    """
    step = ctx.step
    db = DatabaseService()
    logger.info("🧪 === Starting Full Pipeline Test ===")
    
    settings = get_settings()
    
    # Create pipeline run record
    pipeline_run = await step.run(
        "test-create-pipeline-run",
        lambda: db.create_pipeline_run()
    )
    run_id = pipeline_run.get("id")
    logger.info(f"📊 Pipeline run created: {run_id}")
    
    # Step 1: Generate 1 topic
    topics = await step.run(
        "test-generate-topic",
        lambda: TopicService().generate_topics(count=1, language="nl")
    )
    topic = topics[0] if topics else {
        "id": "test-topic",
        "title": "Cold Calling is Dood",
        "hook": "Cold calling werkt niet meer. Dit wel.",
        "main_points": ["Moderne buyers doen research"],
        "cta": "Start gratis met DealMotion",
        "hashtags": ["sales", "coldcalling", "AI", "B2B"],
        "content_type": "hot_take"
    }
    logger.info(f"📝 Topic: {topic.get('title')}")
    
    # Save topic to database
    saved_topic = await step.run(
        "test-save-topic",
        lambda: db.create_topic(topic)
    )
    topic_id = saved_topic.get("id")
    
    # Update pipeline run
    await step.run(
        "test-update-run-topics",
        lambda: db.update_pipeline_run(run_id, topics_generated=1)
    )
    
    # Step 2: Generate script
    script = await step.run(
        "test-generate-script",
        lambda: ScriptService().generate_script(topic)
    )
    logger.info(f"📜 Script generated ({len(script.get('full_text', ''))} chars)")
    
    # Save script to database
    saved_script = await step.run(
        "test-save-script",
        lambda: db.create_script(script, topic_id)
    )
    script_id = saved_script.get("id")
    
    # Update pipeline run
    await step.run(
        "test-update-run-scripts",
        lambda: db.update_pipeline_run(run_id, scripts_generated=1)
    )
    
    # Step 3: Generate audio
    audio_result = await step.run(
        "test-generate-audio",
        lambda: TTSService().generate_audio(script.get("full_text"))
    )
    audio_url = audio_result.get("audio_url") if isinstance(audio_result, dict) else audio_result
    logger.info(f"🎤 Audio: {audio_url}")
    
    # Step 4: Generate 4 background video clips for variety
    logger.info("🎥 Generating 4 video clips (this takes ~10-15 min)...")
    video_clips = await step.run(
        "test-generate-video-clips",
        lambda: VideoService().generate_multiple_clips(script=script, num_clips=4, audio_url=audio_url)
    )
    
    # Extract URLs from clips
    background_urls = [clip.get("video_url") for clip in video_clips if clip.get("video_url")]
    logger.info(f"🎥 Generated {len(background_urls)} clips: {background_urls}")
    
    # Step 5: Render final video
    # Note: Inngest step results may not support Python slicing, so extract list first
    segments = list(script.get("segments", []) or [])
    texts = [seg.get("text", "") if isinstance(seg, dict) else str(seg) for seg in segments[:4]]
    if not texts or all(t == "" for t in texts):
        full_text = script.get("full_text", "") or ""
        words = full_text.split()
        chunk_size = max(1, len(words) // 4)
        texts = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)][:4]
    while len(texts) < 4:
        texts.append("")
    
    render_result = await step.run(
        "test-render-video",
        lambda: RenderService().render_short(
            script_segments=[{"text": t} for t in texts],
            audio_url=audio_url,
            background_video_urls=background_urls,  # 4 different clips!
        )
    )
    final_url = render_result.get("video_url")
    logger.info(f"✨ Final video: {final_url}")
    
    # Save video to database
    title = script.get("title", topic.get("title"))
    video_record = await step.run(
        "test-save-video",
        lambda: db.create_video(
            title=title,
            script_id=script_id,
            video_url=final_url,
            audio_url=audio_url,
            duration_seconds=script.get("total_duration_seconds", 25)
        )
    )
    video_db_id = video_record.get("id")
    
    # Update pipeline run
    await step.run(
        "test-update-run-videos",
        lambda: db.update_pipeline_run(run_id, videos_created=1)
    )
    
    # Step 6: Upload to YouTube (unlisted for testing)
    youtube_result = await step.run(
        "test-upload-youtube",
        lambda: YouTubeService().upload_video(
            video_url=final_url,
            title=title,
            description=script.get("description", "Test video"),
            tags=topic.get("hashtags", []),
            privacy_status="unlisted"  # Unlisted for testing
        )
    )
    youtube_id = youtube_result.get("youtube_id")
    youtube_url = youtube_result.get("youtube_url")
    logger.info(f"📺 YouTube: {youtube_url}")
    
    # Save YouTube upload to database
    await step.run(
        "test-save-youtube-upload",
        lambda: db.create_youtube_upload(
            video_id=video_db_id,
            youtube_id=youtube_id,
            youtube_url=youtube_url,
            title=title,
            description=script.get("description", ""),
            tags=topic.get("hashtags", [])
        )
    )
    
    # Update pipeline run - completed
    await step.run(
        "test-complete-pipeline-run",
        lambda: db.update_pipeline_run(run_id, status="completed", videos_uploaded=1)
    )
    
    logger.info("🎉 === Full Pipeline Test Complete! ===")
    
    return {
        "status": "success",
        "run_id": run_id,
        "topic": topic.get("title"),
        "audio_url": audio_url,
        "background_video_url": background_url,
        "final_video_url": final_url,
        "youtube_url": youtube_url,
        "youtube_id": youtube_id,
    }
