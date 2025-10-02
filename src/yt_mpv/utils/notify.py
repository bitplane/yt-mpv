"""
Notification utilities for yt-mpv
"""

import logging
import subprocess

# Configure logging
logger = logging.getLogger("yt-mpv")


def notify(message: str, title: str = "YouTube MPV", url: str = None) -> None:
    """Send desktop notification if possible."""
    try:
        cmd = ["notify-send", title, message]
        if url:
            cmd.extend(["--action", "default=Open", "--action", f"open={url}"])
        subprocess.run(cmd, check=False, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        # If notification fails, just log it
        logger.debug(f"Could not send notification: {message}")
