"""
Launcher for yt-mpv: Play videos with mpv, then upload to Internet Archive.
"""

import logging
import os
import random
import re
import sys
from pathlib import Path

# Import functionality from separated modules
from yt_mpv.archive import archive_url, check_archive_status
from yt_mpv.cache import purge_cache
from yt_mpv.play import check_mpv_installed, play_video, update_yt_dlp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yt-mpv")

# Constants - consistent naming throughout
HOME = Path.home()
DL_DIR = HOME / ".cache/yt-mpv"
VENV_DIR = Path(os.environ.get("YT_MPV_VENV", HOME / ".local/share/yt-mpv/.venv"))
VENV_BIN = VENV_DIR / "bin"


def get_real_url(raw_url: str) -> str:
    """Convert custom scheme to regular http/https URL."""
    if raw_url.startswith("x-yt-mpvs:"):
        return raw_url.replace("x-yt-mpvs:", "https:", 1)
    elif raw_url.startswith("x-yt-mpv:"):
        return raw_url.replace("x-yt-mpv:", "http:", 1)
    return raw_url


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    # Check for mpv
    if not check_mpv_installed():
        return False

    # Check for Python venv
    if not os.path.isfile(os.path.join(VENV_BIN, "activate")):
        logger.error(f"Python venv not found at {VENV_DIR}")
        return False

    return True


def main():
    """Main function to process URL and orchestrate workflow."""
    # Check if URL provided
    if len(sys.argv) < 2:
        logger.error("No URL provided")
        sys.exit(1)

    # Parse URL
    raw_url = sys.argv[1]
    url = get_real_url(raw_url)

    # Basic URL validation
    if not re.match(r"^https?://", url):
        logger.error(f"Invalid URL format: {url}")
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Update yt-dlp to avoid YouTube API changes breaking functionality
    update_yt_dlp(VENV_DIR, VENV_BIN)

    # Occasionally clean old cache files (once every ~10 runs randomly)
    if random.random() < 0.1:
        try:
            # Clean files older than 30 days
            purge_cache(max_age_days=30)
        except Exception as e:
            logger.warning(f"Cache cleaning failed: {e}")

    # Play the video
    if not play_video(url):
        sys.exit(1)

    # Check if already archived before downloading
    archive_url_path = check_archive_status(url)
    if archive_url_path:
        logger.info(f"Already archived at: {archive_url_path}")
        sys.exit(0)

    # Archive the URL
    if not archive_url(url, DL_DIR, VENV_BIN):
        sys.exit(1)

    logger.info("Process completed successfully")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
