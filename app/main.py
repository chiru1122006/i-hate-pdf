"""
FastAPI application for Word to PDF Converter

High-performance, production-ready document converter with:
- Async file handling
- Progress tracking via SSE
- Automatic file cleanup
- Modern responsive UI
"""
import asyncio
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    UPLOAD_DIR, OUTPUT_DIR, MAX_FILE_SIZE, 
    ALLOWED_EXTENSIONS, BASE_DIR, FILE_CLEANUP_TIMEOUT
)
from app.converter import convert_docx_to_pdf, shutdown_pools
from app.utils import (
    validate_file_extension, save_upload_file, 
    get_pdf_filename, cleanup_file, cleanup_old_files
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup: Clean old files
    await cleanup_old_files()
    print("✓ Word to PDF Converter started")
    print(f"✓ Upload directory: {UPLOAD_DIR}")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    
    yield
    
    # Shutdown: Clean up pools
    shutdown_pools()
    print("✓ Converter shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Word to PDF Converter",
    description="Ultra-fast Word document to PDF conversion",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    index_path = BASE_DIR / "static" / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Word to PDF Converter</h1><p>Static files not found.</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "word-to-pdf-converter"}


@app.post("/upload")
async def upload_and_convert(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a Word document and convert it to PDF.
    
    Returns the download URL for the converted PDF.
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB"
        )
    
    # Save uploaded file
    try:
        input_path = await save_upload_file(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Convert to PDF
    try:
        result = await convert_docx_to_pdf(input_path)
    except Exception as e:
        # Clean up input file on error
        await cleanup_file(input_path)
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")
    
    if not result["success"]:
        # Clean up input file on failure
        await cleanup_file(input_path)
        raise HTTPException(status_code=500, detail=result["message"])
    
    # Get output path and generate download filename
    output_path = Path(result["output_path"])
    original_name = Path(file.filename).stem
    download_filename = f"{original_name}.pdf"
    
    # Schedule cleanup of both files
    background_tasks.add_task(
        schedule_file_cleanup,
        [input_path, output_path]
    )
    
    return JSONResponse({
        "success": True,
        "message": "Conversion successful",
        "download_url": f"/download/{output_path.name}",
        "filename": download_filename,
        "original_name": file.filename,
        "elapsed_time": round(result["elapsed_time"], 2)
    })


@app.get("/download/{filename}")
async def download_pdf(filename: str):
    """Download a converted PDF file."""
    # Sanitize filename to prevent path traversal
    safe_filename = Path(filename).name
    file_path = OUTPUT_DIR / safe_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found or expired")
    
    if not file_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_filename
    )


async def schedule_file_cleanup(file_paths: list[Path]):
    """Schedule cleanup of files after timeout."""
    await asyncio.sleep(FILE_CLEANUP_TIMEOUT)
    for file_path in file_paths:
        await cleanup_file(file_path)


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
