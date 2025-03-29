"""
System utility functions for yt-mpv
"""

import hashlib
import logging
import os
import subprocess
from typing import Dict, Optional, Tuple

# Configure logging
logger = logging.getLogger("yt-mpv")


def notify(message: str, title: str = "YouTube MPV") -> None:
    """Send desktop notification if possible.

    Args:
        message: Message to display in the notification
        title: Title for the notification
    """
    try:
        subprocess.run(
            ["notify-send", title, message], check=False, capture_output=True
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        # If notification fails, just log it
        logger.debug(f"Could not send notification: {message}")


def run_command(
    cmd: list, desc: str = "", check: bool = True, env=None, timeout=None
) -> Tuple[int, str, str]:
    """Run a command and return status, stdout, stderr.

    Args:
        cmd: Command to run as a list of arguments
        desc: Description of the command for logging
        check: Whether to raise an exception if command fails
        env: Environment variables for the command
        timeout: Timeout in seconds for the command

    Returns:
        Tuple[int, str, str]: return code, stdout, stderr
    """
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


# Build a cache of command availability to avoid repeated lookups
_command_cache: Dict[str, bool] = {}


def is_command_available(command: str) -> bool:
    """Check if a command is available in the PATH.

    Args:
        command: Command to check

    Returns:
        bool: True if the command is available, False otherwise
    """
    if command in _command_cache:
        return _command_cache[command]

    from shutil import which

    result = which(command) is not None
    _command_cache[command] = result
    return result
