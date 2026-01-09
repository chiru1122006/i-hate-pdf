"""
Utility functions for Word to PDF Converter
"""
import os
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import aiofiles
import aiofiles.os

from app.config import UPLOAD_DIR, OUTPUT_DIR, ALLOWED_EXTENSIONS, FILE_CLEANUP_TIMEOUT


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the original name."""
    name = Path(original_filename).stem
    unique_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}_{unique_id}"


def validate_file_extension(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def get_pdf_filename(docx_filename: str) -> str:
    """Convert .docx filename to .pdf filename."""
    return Path(docx_filename).stem + ".pdf"


async def save_upload_file(file_content: bytes, filename: str) -> Path:
    """Save uploaded file to disk asynchronously."""
    unique_name = generate_unique_filename(filename)
    ext = Path(filename).suffix.lower()
    file_path = UPLOAD_DIR / f"{unique_name}{ext}"
    
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    
    return file_path


async def cleanup_file(file_path: Path, delay: int = 0) -> None:
    """Delete a file after optional delay."""
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        if file_path.exists():
            await aiofiles.os.remove(file_path)
    except Exception:
        pass  # Ignore cleanup errors


async def schedule_cleanup(file_paths: list[Path]) -> None:
    """Schedule cleanup of multiple files after timeout."""
    await asyncio.sleep(FILE_CLEANUP_TIMEOUT)
    for file_path in file_paths:
        await cleanup_file(file_path)


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)


async def cleanup_old_files() -> None:
    """Clean up files older than the timeout period."""
    cutoff_time = datetime.now() - timedelta(seconds=FILE_CLEANUP_TIMEOUT)
    
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not directory.exists():
            continue
            
        for file_path in directory.iterdir():
            if file_path.is_file():
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        await aiofiles.os.remove(file_path)
                except Exception:
                    pass
