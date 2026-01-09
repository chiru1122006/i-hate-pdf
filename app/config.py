"""
Configuration settings for Word to PDF Converter
"""
import os
import platform
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Upload and output directories
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# File settings
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {".docx", ".doc"}

# Auto-cleanup settings (in seconds)
FILE_CLEANUP_TIMEOUT = 300  # 5 minutes after conversion

# LibreOffice paths based on OS
def get_libreoffice_path() -> str:
    """Get LibreOffice executable path based on operating system."""
    system = platform.system()
    
    if system == "Windows":
        # Common Windows installation paths
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            os.path.expandvars(r"%PROGRAMFILES%\LibreOffice\program\soffice.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        # Fallback to PATH
        return "soffice"
    
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/usr/local/bin/soffice",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "soffice"
    
    else:  # Linux
        possible_paths = [
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/soffice",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return "soffice"

LIBREOFFICE_PATH = get_libreoffice_path()

# Conversion optimization flags
LIBREOFFICE_FLAGS = [
    "--headless",           # No GUI
    "--invisible",          # Completely invisible
    "--nologo",             # Skip logo
    "--nofirststartwizard", # Skip first start wizard
    "--norestore",          # Don't restore previous session
]

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
