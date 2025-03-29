"""
Video playback functionality for yt-mpv
"""

import logging
import os
import shutil
from pathlib import Path

from yt_mpv.utils import notify, run_command

# Configure logging
logger = logging.getLogger("yt-mpv")


def check_mpv_installed() -> bool:
    """Check if mpv is installed.

    Returns:
        bool: True if mpv is installed, False otherwise
    """
    return shutil.which("mpv") is not None


def play_video(url: str, additional_mpv_args: list = None) -> bool:
    """Play a video with mpv.

    Args:
        url: URL to play
        additional_mpv_args: Additional arguments to pass to mpv

    Returns:
        bool: True if successful, False otherwise
    """
    if not check_mpv_installed():
        logger.error("mpv is not installed")
        notify("mpv not found. Please install it.")
        return False

    # Build mpv command
    cmd = ["mpv", "--ytdl=yes", f"--term-status-msg=Playing: {url}"]

    # Add additional args if provided
    if additional_mpv_args:
        cmd.extend(additional_mpv_args)

    # Add the URL
    cmd.append(url)

    # Run mpv
    status, _, stderr = run_command(
        cmd,
        desc=f"Playing {url} with mpv",
        check=False,
    )

    if status != 0:
        logger.error(f"Failed to play video: {stderr}")
        notify("Failed to play video")
        return False

    return True


def update_yt_dlp(venv_dir: Path, venv_bin: Path) -> bool:
    """Update yt-dlp using uv if available.

    Args:
        venv_dir: Path to virtual environment
        venv_bin: Path to virtual environment bin directory

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare environment with venv
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(venv_dir)
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"

        # First try to use uv if available in the venv
        uv_path = venv_bin / "uv"
        if uv_path.exists():
            logger.info("Updating yt-dlp using uv in venv")
            cmd = [str(uv_path), "pip", "install", "--upgrade", "yt-dlp"]
            run_command(cmd, check=False)
        # Then try system uv
        elif shutil.which("uv"):
            logger.info("Updating yt-dlp using system uv")
            cmd = ["uv", "pip", "install", "--upgrade", "yt-dlp"]
            run_command(cmd, check=False)
        else:
            # Fall back to pip
            logger.info("Updating yt-dlp using pip")
            cmd = [str(venv_bin / "pip"), "install", "--upgrade", "yt-dlp"]
            run_command(cmd, check=False)
        return True
    except Exception as e:
        logger.warning(f"Failed to update yt-dlp: {e}")
        return False
