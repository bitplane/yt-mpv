"""
Common utility functions and constants for yt-mpv
"""

import hashlib
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Configure logging
logger = logging.getLogger("yt-mpv")

# Common constants
HOME = Path.home()
DL_DIR = HOME / ".cache/yt-mpv"
VENV_DIR = Path(os.environ.get("YT_MPV_VENV", HOME / ".local/share/yt-mpv/.venv"))
VENV_BIN = VENV_DIR / "bin"


def notify(message: str) -> None:
    """Send desktop notification if possible.

    Args:
        message: Message to display in the notification
    """
    try:
        subprocess.run(
            ["notify-send", "YouTube MPV", message], check=False, capture_output=True
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        # If notification fails, just log it
        logger.debug(f"Could not send notification: {message}")


def generate_archive_id(url: str, username: Optional[str] = None) -> str:
    """Generate a unique Archive.org identifier for a video URL.

    Args:
        url: The URL to generate an ID for
        username: Optional username, defaults to current user

    Returns:
        str: The archive identifier
    """
    if username is None:
        username = os.getlogin()
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"yt-mpv-{username}-{url_hash}"


def get_real_url(raw_url: str) -> str:
    """Convert custom scheme to regular http/https URL.

    Args:
        raw_url: URL possibly using custom x-yt-mpv scheme

    Returns:
        str: URL with standard http/https scheme
    """
    # Remove any query parameters first
    url_part = raw_url.split("?", 1)[0]

    if url_part.startswith("x-yt-mpvs:"):
        return url_part.replace("x-yt-mpvs:", "https:", 1)
    elif url_part.startswith("x-yt-mpv:"):
        return url_part.replace("x-yt-mpv:", "http:", 1)
    return url_part


def extract_video_id(url: str) -> Tuple[str, str]:
    """Extract video ID and extractor name from URL.

    Args:
        url: URL to extract ID from

    Returns:
        Tuple[str, str]: Video ID and extractor name
    """
    # YouTube format
    youtube_pattern = (
        r"(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|"
        r"(?:v|e(?:mbed)?)\/|"
        r"\S*?[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    )
    youtube_match = re.search(youtube_pattern, url)

    if youtube_match:
        return youtube_match.group(1), "youtube"

    # For other URLs, use a hash of the URL as fallback
    # This is simplified and would ideally be improved with more extractors
    url_hash = hashlib.md5(url.encode()).hexdigest()[:11]
    return url_hash, "generic"


def run_command(cmd: list, desc: str = "", check: bool = True) -> Tuple[int, str, str]:
    """Run a command and return status, stdout, stderr.

    Args:
        cmd: Command to run as a list of arguments
        desc: Description of the command for logging
        check: Whether to raise an exception if command fails

    Returns:
        Tuple[int, str, str]: return code, stdout, stderr
    """
    try:
        if desc:
            logger.info(desc)

        proc = subprocess.run(cmd, check=check, text=True, capture_output=True)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.SubprocessError as e:
        logger.error(f"Command failed: {e}")
        return 1, "", str(e)
