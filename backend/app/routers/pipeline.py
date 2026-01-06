"""
Pipeline Router - Trigger and monitor content pipelines.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import inngest

from app.inngest.client import inngest_client


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
        }
    }

