"""
Storage Service - Upload files to Supabase Storage.
"""
import uuid
from datetime import datetime
from loguru import logger
from supabase import create_client, Client

from app.config import get_settings


class StorageService:
    """Service for uploading files to Supabase Storage."""
    
    BUCKET_NAME = "media"
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_service_key
        )
    
    def upload_audio(self, audio_bytes: bytes, filename: str = None) -> str:
        """
        Upload audio file to Supabase Storage.
        
        Returns the public URL of the uploaded file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"audio/{timestamp}_{unique_id}.mp3"
        
        logger.info(f"Uploading audio: {filename} ({len(audio_bytes)} bytes)")
        
        try:
            # Upload to Supabase Storage
            result = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=filename,
                file=audio_bytes,
                file_options={"content-type": "audio/mpeg"}
            )
            
            # Get public URL
            public_url = self.client.storage.from_(self.BUCKET_NAME).get_public_url(filename)
            
            logger.info(f"Audio uploaded: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload audio: {e}")
            raise
    
    def upload_video(self, video_bytes: bytes, filename: str = None) -> str:
        """
        Upload video file to Supabase Storage.
        
        Returns the public URL of the uploaded file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"videos/{timestamp}_{unique_id}.mp4"
        
        logger.info(f"Uploading video: {filename} ({len(video_bytes)} bytes)")
        
        try:
            result = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=filename,
                file=video_bytes,
                file_options={"content-type": "video/mp4"}
            )
            
            public_url = self.client.storage.from_(self.BUCKET_NAME).get_public_url(filename)
            
            logger.info(f"Video uploaded: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            raise
    
    def upload_image(self, image_bytes: bytes, filename: str = None, content_type: str = "image/png") -> str:
        """
        Upload image file to Supabase Storage.
        
        Returns the public URL of the uploaded file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            ext = "png" if "png" in content_type else "jpg"
            filename = f"thumbnails/{timestamp}_{unique_id}.{ext}"
        
        logger.info(f"Uploading image: {filename} ({len(image_bytes)} bytes)")
        
        try:
            result = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=filename,
                file=image_bytes,
                file_options={"content-type": content_type}
            )
            
            public_url = self.client.storage.from_(self.BUCKET_NAME).get_public_url(filename)
            
            logger.info(f"Image uploaded: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image: {e}")
            raise

