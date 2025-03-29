"""
System utility functions for yt-mpv
"""

import hashlib
import logging
import os
import subprocess
from typing import Optional, Tuple

# Configure logging
logger = logging.getLogger("yt-mpv")


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
