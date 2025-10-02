"""
File system utility functions for yt-mpv
"""

import hashlib
import logging
import re
import subprocess
from datetime import datetime
from shutil import which

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


def generate_archive_id(url: str, upload_date: str = None) -> str:
    """Generate a unique Archive.org identifier for a video URL.

    Args:
        url: The video URL
        upload_date: Original upload date in YYYYMMDD or YYYY_MM_DD format
    """
    # Format date as YYYY_MM_DD
    if upload_date:
        # Handle YYYYMMDD format
        if len(upload_date) == 8 and upload_date.isdigit():
            date_str = f"{upload_date[:4]}_{upload_date[4:6]}_{upload_date[6:8]}"
        else:
            # Already in YYYY_MM_DD or similar format
            date_str = upload_date.replace("-", "_")
    else:
        # Fallback to current date if no upload date available
        date_str = datetime.now().strftime("%Y_%m_%d")

    # Get 8 chars of MD5 hash for uniqueness
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # Convert URL to underscore-separated format
    url_clean = re.sub(r"^https?://", "", url)
    url_clean = re.sub(r"[^a-zA-Z0-9]+", "_", url_clean)
    url_clean = re.sub(r"_+", "_", url_clean).strip("_")

    # Build identifier and ensure max 80 chars total
    # Format: YYYY_MM_DD-url_with_underscores-hash
    base_len = len(date_str) + 1 + 1 + 8  # date + hyphen + hyphen + hash = 21
    max_url_len = 80 - base_len
    if len(url_clean) > max_url_len:
        url_clean = url_clean[:max_url_len]

    return f"{date_str}-{url_clean}-{url_hash}"


# Command availability cache
_command_cache = {}


def is_command_available(command: str) -> bool:
    """Check if a command is available in the PATH."""
    if command in _command_cache:
        return _command_cache[command]

    result = which(command) is not None
    _command_cache[command] = result
    return result
