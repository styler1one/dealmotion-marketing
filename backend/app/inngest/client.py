"""
Inngest client for scheduled content generation.
"""
import inngest
from app.config import get_settings

settings = get_settings()

# Initialize Inngest client
inngest_client = inngest.Inngest(
    app_id="dealmotion-marketing",
    event_key=settings.inngest_event_key,
)

