"""
Pipeline Router - Trigger and monitor content pipelines.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
import inngest

from app.inngest.client import inngest_client
from app.services.topic_service import TopicService
from app.services.script_service import ScriptService
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from app.services.render_service import RenderService
from app.services.youtube_service import YouTubeService
from app.services.database_service import DatabaseService


router = APIRouter()


class PipelineResponse(BaseModel):
    """Response for pipeline trigger."""
    status: str
    message: str
    event_id: str = None


@router.post("/trigger-test")
async def trigger_test_pipeline():
    """
    Trigger a full pipeline test.
    
    This will:
    1. Generate a topic (Claude)
    2. Generate a script (Claude)
    3. Generate voice-over (ElevenLabs)
    4. Generate background video (Google Veo 2)
    5. Render final video with captions (Creatomate)
    6. Upload to YouTube (unlisted)
    
    Monitor progress in Inngest dashboard.
    """
    try:
        # Send event to trigger the test pipeline
        result = await inngest_client.send(
            [inngest.Event(
                name="marketing/test.full-pipeline",
                data={"source": "api_trigger"}
            )]
        )
        
        return {
            "status": "triggered",
            "message": "Full pipeline test started. Monitor progress in Inngest dashboard.",
            "event_ids": result.ids if hasattr(result, 'ids') else [],
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/trigger-daily")
async def trigger_daily_pipeline():
    """
    Manually trigger the daily content pipeline.
    
    Same as the cron job that runs at 10:00 AM.
    """
    try:
        # The daily pipeline is triggered by cron, but we can also trigger it manually
        # by sending a direct function invocation
        return {
            "status": "info",
            "message": "Daily pipeline runs automatically at 10:00 AM via cron. Use /trigger-test for manual testing.",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_pipeline_status():
    """
    Get the current pipeline status.
    """
    from app.config import get_settings
    settings = get_settings()
    
    return {
        "daily_pipeline": {
            "schedule": "0 10 * * * (10:00 AM daily)",
            "status": "active"
        },
        "services": {
            "topic_generation": "Claude AI",
            "script_generation": "Claude AI", 
            "tts": "ElevenLabs",
            "video_generation": "Google Veo 2",
            "final_render": "Creatomate",
            "upload": "YouTube API"
        },
        "inngest": {
            "event_key_configured": bool(settings.inngest_event_key),
            "event_key_length": len(settings.inngest_event_key) if settings.inngest_event_key else 0,
            "signing_key_configured": bool(settings.inngest_signing_key),
        }
    }


@router.post("/runs/{run_id}/complete")
async def mark_run_completed(run_id: str):
    """
    Manually mark a stuck run as completed.
    Use this when a run succeeded but status wasn't updated due to network issues.
    """
    try:
        db = DatabaseService()
        db.update_pipeline_run(run_id, status="completed")
        return {"status": "success", "message": f"Run {run_id} marked as completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{run_id}/fail")
async def mark_run_failed(run_id: str):
    """
    Manually mark a stuck run as failed.
    """
    try:
        db = DatabaseService()
        db.update_pipeline_run(run_id, status="failed")
        return {"status": "success", "message": f"Run {run_id} marked as failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-stuck-runs")
async def cleanup_stuck_runs():
    """
    Clean up stuck runs that have been running for more than 10 minutes.
    Marks them as 'failed' with an appropriate error message.
    """
    try:
        db = DatabaseService()
        # Get all running runs
        runs = db.get_pipeline_runs(limit=50)
        
        stuck_count = 0
        for run in runs:
            if run.get("status") == "running":
                # Check if it's been running for more than 10 minutes
                started_at = run.get("started_at")
                if started_at:
                    # Parse ISO format timestamp
                    try:
                        if isinstance(started_at, str):
                            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                        else:
                            started = started_at
                        
                        now = datetime.now(started.tzinfo) if started.tzinfo else datetime.utcnow()
                        if (now - started) > timedelta(minutes=10):
                            db.update_pipeline_run(
                                run.get("id"), 
                                status="failed",
                                errors=["Run timed out or was interrupted"]
                            )
                            stuck_count += 1
                    except Exception as e:
                        logger.error(f"Error parsing timestamp for run {run.get('id')}: {e}")
        
        return {
            "status": "success", 
            "message": f"Cleaned up {stuck_count} stuck runs",
            "stuck_runs_fixed": stuck_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

