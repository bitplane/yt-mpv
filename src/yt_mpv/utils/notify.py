"""
Notification utilities for yt-mpv
"""

import logging
import subprocess

# Configure logging
logger = logging.getLogger("yt-mpv")


def notify(message: str, title: str = "YouTube MPV") -> None:
    """Send desktop notification if possible."""
    try:
        subprocess.run(
            ["notify-send", title, message], check=False, capture_output=True
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        # If notification fails, just log it
        logger.debug(f"Could not send notification: {message}")
