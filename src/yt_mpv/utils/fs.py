"""
File system utility functions for yt-mpv
"""

import hashlib
import logging
import os
import subprocess

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
