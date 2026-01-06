#!/usr/bin/env python3
"""
Generate a single YouTube Short.

This script demonstrates the full pipeline:
1. Generate a topic idea
2. Write a script
3. Generate voice-over (TTS)
4. Create video (NanoBanana)
5. (Optional) Upload to YouTube

Usage:
    python scripts/generate_short.py
    python scripts/generate_short.py --topic "sales_tip" --upload
    python scripts/generate_short.py --mock  # Test without API calls
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings
from backend.agents.topic_agent import TopicAgent, ContentType
from backend.agents.script_agent import ScriptAgent
from backend.services.tts_service import TTSService
from backend.services.nanobanana_service import get_nanobanana_service, VideoGenerationRequest, VideoStyle
from backend.services.youtube_service import get_youtube_service, VideoUploadRequest


console = Console()


async def generate_short(
    content_type: str | None = None,
    mock: bool = False,
    upload: bool = False,
    language: str = "nl"
):
    """Generate a complete YouTube Short."""
    settings = get_settings()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    console.print(Panel.fit(
        "[bold blue]🎬 DealMotion Short Generator[/bold blue]\n"
        f"Mode: {'MOCK' if mock else 'LIVE'} | Language: {language.upper()}"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # =====================================================================
        # Step 1: Generate Topic
        # =====================================================================
        task = progress.add_task("Generating topic idea...", total=None)
        
        topic_agent = TopicAgent()
        
        ct = ContentType(content_type) if content_type else None
        topics = topic_agent.generate_topics(content_type=ct, count=1, language=language)
        
        if not topics:
            console.print("[red]❌ Failed to generate topic[/red]")
            return
        
        topic = topics[0]
        progress.update(task, description=f"✅ Topic: {topic.title}")
        
        console.print(f"\n[green]Topic:[/green] {topic.title}")
        console.print(f"[dim]Hook:[/dim] {topic.hook}")
        console.print(f"[dim]Points:[/dim] {', '.join(topic.main_points)}")
        
        # =====================================================================
        # Step 2: Generate Script
        # =====================================================================
        task = progress.add_task("Writing script...", total=None)
        
        script_agent = ScriptAgent()
        script = script_agent.generate_script(topic, language=language)
        
        progress.update(task, description=f"✅ Script: {script.total_duration_seconds}s")
        
        console.print(f"\n[green]Script ({script.total_duration_seconds}s):[/green]")
        for seg in script.segments:
            console.print(f"  [{seg.type}] {seg.text[:80]}...")
        
        # =====================================================================
        # Step 3: Generate Voice-Over (TTS)
        # =====================================================================
        task = progress.add_task("Generating voice-over...", total=None)
        
        audio_path = settings.output_dir / f"audio_{timestamp}.mp3"
        
        if mock:
            # Create mock audio file
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_text("MOCK_AUDIO")
            progress.update(task, description="✅ Voice-over (mock)")
        else:
            tts = TTSService()
            audio_path = await tts.generate_audio(
                text=script.to_full_text(),
                output_path=audio_path
            )
            progress.update(task, description=f"✅ Voice-over: {audio_path.name}")
        
        # =====================================================================
        # Step 4: Generate Video
        # =====================================================================
        task = progress.add_task("Creating video...", total=None)
        
        video_path = settings.shorts_output_dir / f"short_{timestamp}.mp4"
        
        nanobanana = get_nanobanana_service(mock=mock)
        video_request = VideoGenerationRequest(
            script=script.to_full_text(),
            audio_path=audio_path,
            style=VideoStyle.PROFESSIONAL,
            duration_seconds=int(script.total_duration_seconds),
            include_captions=True
        )
        
        video_result = await nanobanana.generate_video(video_request, video_path)
        progress.update(task, description=f"✅ Video: {video_result.video_path.name}")
        
        # =====================================================================
        # Step 5: Upload to YouTube (optional)
        # =====================================================================
        if upload:
            task = progress.add_task("Uploading to YouTube...", total=None)
            
            youtube = get_youtube_service(mock=mock)
            
            if not mock:
                youtube.authenticate()
            
            upload_request = VideoUploadRequest(
                video_path=video_result.video_path,
                title=script.title,
                description=f"{script.description}\n\n🚀 {settings.brand_website}",
                tags=topic.hashtags + ["sales", "AI", "B2B", settings.brand_name],
                is_short=True
            )
            
            upload_result = youtube.upload_video(upload_request)
            progress.update(task, description=f"✅ Uploaded: {upload_result.video_url}")
            
            console.print(f"\n[green]🎉 Video live at:[/green] {upload_result.video_url}")
        
    # =========================================================================
    # Summary
    # =========================================================================
    console.print(Panel.fit(
        f"[bold green]✅ Short Generated![/bold green]\n\n"
        f"📝 Title: {script.title}\n"
        f"⏱️ Duration: {script.total_duration_seconds}s\n"
        f"🎬 Video: {video_result.video_path}\n"
        f"🎙️ Audio: {audio_path}"
    ))


@click.command()
@click.option("--topic", "-t", type=click.Choice(["sales_tip", "ai_news", "hot_take", "product_showcase"]), 
              help="Content type to generate")
@click.option("--mock", "-m", is_flag=True, help="Run in mock mode (no API calls)")
@click.option("--upload", "-u", is_flag=True, help="Upload to YouTube after generation")
@click.option("--language", "-l", default="nl", type=click.Choice(["nl", "en"]), help="Content language")
def main(topic: str | None, mock: bool, upload: bool, language: str):
    """Generate a YouTube Short for DealMotion."""
    asyncio.run(generate_short(topic, mock, upload, language))


if __name__ == "__main__":
    main()

