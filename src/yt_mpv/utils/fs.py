"""
File system utility functions for yt-mpv
"""

import hashlib
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import tuple

# Configure logging
logger = logging.getLogger("yt-mpv")


def run_command(
    cmd: list, desc: str = "", check: bool = True, env=None, timeout=None
) -> tuple[int, str, str]:
    """Run a command and return status, stdout, stderr."""
    try:
        if desc:
            logger.info(desc)

        proc = subprocess.run(
            cmd, check=check, text=True, capture_output=True, env=env, timeout=timeout
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {e}")
        return 124, "", f"Timeout after {timeout}s"
    except subprocess.SubprocessError as e:
        logger.error(f"Command failed: {e}")
        return 1, "", str(e)


def generate_archive_id(url: str, username: str = None) -> str:
    """Generate a unique Archive.org identifier for a video URL."""
    if username is None:
        username = os.getlogin()
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"yt-mpv-{username}-{url_hash}"


# Command availability cache
_command_cache = {}


def is_command_available(command: str) -> bool:
    """Check if a command is available in the PATH."""
    if command in _command_cache:
        return _command_cache[command]

    from shutil import which

    result = which(command) is not None
    _command_cache[command] = result
    return result


def cleanup_cache_files(video_file: Path, info_file: Path) -> bool:
    """Remove downloaded video and info files after successful upload."""
    files_to_remove = [video_file, info_file]
    success = True

    for file_path in files_to_remove:
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Removed cache file: {file_path}")
            except OSError as e:
                logger.error(f"Failed to remove file {file_path}: {e}")
                success = False

    return success


def purge_cache(cache_dir: Path = None, max_age_days: int = 7) -> tuple[int, int]:
    """Purge old files from the cache directory."""
    from yt_mpv.utils.config import DL_DIR

    if cache_dir is None:
        cache_dir = DL_DIR

    # Get file information
    files_deleted = 0
    bytes_freed = 0

    logger.info(f"Purging cache files older than {max_age_days} days from {cache_dir}")

    now = time.time()

    # Delete files older than max_age_days
    for file_path in cache_dir.iterdir():
        if file_path.is_file():
            file_age_days = (now - file_path.stat().st_mtime) / (24 * 60 * 60)
            if file_age_days > max_age_days:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    files_deleted += 1
                    bytes_freed += file_size
                    logger.debug(f"Deleted old cache file: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to delete cache file {file_path}: {e}")

    logger.info(
        f"Cache cleanup: removed {files_deleted} files ({bytes_freed / 1048576:.2f} MB)"
    )
    return files_deleted, bytes_freed
