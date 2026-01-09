"""
LibreOffice-based Word to PDF conversion engine

PERFORMANCE OPTIMIZATIONS:
1. Headless mode - No GUI overhead
2. ProcessPoolExecutor - Parallel conversions without GIL
3. Optimized flags - Minimal LibreOffice startup time
4. Direct output path - No intermediate files
5. Subprocess with timeout - Prevents hanging processes
"""
import asyncio
import subprocess
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Optional, Callable
import time

from app.config import LIBREOFFICE_PATH, LIBREOFFICE_FLAGS, OUTPUT_DIR


# Process pool for CPU-bound conversion tasks
_process_pool: Optional[ProcessPoolExecutor] = None
_thread_pool: Optional[ThreadPoolExecutor] = None


def get_process_pool() -> ProcessPoolExecutor:
    """Get or create the process pool for conversions."""
    global _process_pool
    if _process_pool is None:
        # Use fewer workers to avoid LibreOffice conflicts
        _process_pool = ProcessPoolExecutor(max_workers=2)
    return _process_pool


def get_thread_pool() -> ThreadPoolExecutor:
    """Get or create the thread pool for I/O operations."""
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = ThreadPoolExecutor(max_workers=4)
    return _thread_pool


def _convert_sync(
    input_path: str,
    output_dir: str,
    timeout: int = 300
) -> dict:
    """
    Synchronous conversion function that runs in a separate process.
    
    This function is designed to be run in a ProcessPoolExecutor to avoid
    blocking the async event loop during CPU-intensive conversion.
    """
    start_time = time.time()
    input_file = Path(input_path)
    
    # Create a unique user profile directory for this conversion
    # This prevents LibreOffice conflicts when running multiple conversions
    import tempfile
    user_profile = tempfile.mkdtemp(prefix="libreoffice_")
    
    # Build LibreOffice command with user profile
    cmd = [
        LIBREOFFICE_PATH,
        *LIBREOFFICE_FLAGS,
        f"-env:UserInstallation=file:///{user_profile.replace(os.sep, '/')}",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        str(input_path)
    ]
    
    try:
        # Run LibreOffice with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        elapsed_time = time.time() - start_time
        
        # Check for output file
        expected_output = Path(output_dir) / f"{input_file.stem}.pdf"
        
        if expected_output.exists():
            # Cleanup temp profile directory
            try:
                import shutil
                shutil.rmtree(user_profile, ignore_errors=True)
            except:
                pass
            
            return {
                "success": True,
                "output_path": str(expected_output),
                "elapsed_time": elapsed_time,
                "message": "Conversion successful"
            }
        else:
            # Cleanup temp profile directory
            try:
                import shutil
                shutil.rmtree(user_profile, ignore_errors=True)
            except:
                pass
            
            error_details = f"stdout: {result.stdout}, stderr: {result.stderr}, returncode: {result.returncode}"
            return {
                "success": False,
                "output_path": None,
                "elapsed_time": elapsed_time,
                "message": f"Conversion failed: Output file not created. {error_details}"
            }
            
    except subprocess.TimeoutExpired:
        # Cleanup temp profile directory
        try:
            import shutil
            shutil.rmtree(user_profile, ignore_errors=True)
        except:
            pass
        
        return {
            "success": False,
            "output_path": None,
            "elapsed_time": timeout,
            "message": f"Conversion timed out after {timeout} seconds"
        }
    except FileNotFoundError:
        # Cleanup temp profile directory
        try:
            import shutil
            shutil.rmtree(user_profile, ignore_errors=True)
        except:
            pass
        
        return {
            "success": False,
            "output_path": None,
            "elapsed_time": 0,
            "message": f"LibreOffice not found at {LIBREOFFICE_PATH}. Please install LibreOffice."
        }
    except Exception as e:
        # Cleanup temp profile directory
        try:
            import shutil
            shutil.rmtree(user_profile, ignore_errors=True)
        except:
            pass
        
        return {
            "success": False,
            "output_path": None,
            "elapsed_time": time.time() - start_time,
            "message": f"Conversion error: {str(e)}"
        }


async def convert_docx_to_pdf(
    input_path: Path,
    progress_callback: Optional[Callable[[int], None]] = None
) -> dict:
    """
    Convert a Word document to PDF asynchronously.
    
    Uses ProcessPoolExecutor to run the CPU-bound conversion in a separate
    process, keeping the async event loop responsive.
    
    Args:
        input_path: Path to the input .docx file
        progress_callback: Optional callback for progress updates
        
    Returns:
        dict with keys: success, output_path, elapsed_time, message
    """
    if progress_callback:
        progress_callback(10)  # Started
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    if progress_callback:
        progress_callback(20)  # Preparing
    
    # Run conversion in thread pool (subprocess is I/O bound, not CPU bound)
    loop = asyncio.get_event_loop()
    
    if progress_callback:
        progress_callback(30)  # Converting
    
    # Use thread pool for subprocess (I/O bound operation)
    result = await loop.run_in_executor(
        get_thread_pool(),
        _convert_sync,
        str(input_path),
        str(OUTPUT_DIR),
        300  # 5 minute timeout
    )
    
    if progress_callback:
        if result["success"]:
            progress_callback(100)  # Complete
        else:
            progress_callback(-1)  # Error
    
    return result


async def batch_convert(
    input_paths: list[Path],
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> list[dict]:
    """
    Convert multiple Word documents to PDF in parallel.
    
    Args:
        input_paths: List of paths to input .docx files
        progress_callback: Optional callback(current, total) for progress
        
    Returns:
        List of result dicts
    """
    results = []
    total = len(input_paths)
    
    # Process in batches of 2 to avoid LibreOffice conflicts
    batch_size = 2
    
    for i in range(0, total, batch_size):
        batch = input_paths[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[convert_docx_to_pdf(path) for path in batch]
        )
        results.extend(batch_results)
        
        if progress_callback:
            progress_callback(min(i + batch_size, total), total)
    
    return results


def shutdown_pools():
    """Shutdown thread and process pools gracefully."""
    global _process_pool, _thread_pool
    
    if _process_pool:
        _process_pool.shutdown(wait=False)
        _process_pool = None
    
    if _thread_pool:
        _thread_pool.shutdown(wait=False)
        _thread_pool = None
