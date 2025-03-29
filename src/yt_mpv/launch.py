"""
Launcher for yt-mpv: Play videos with mpv, then optionally upload to Internet Archive.
"""

import logging
import os
import random
import re
import sys
import urllib.parse

# Import functionality from separated modules
from yt_mpv.archive import archive_url, check_archive_status
from yt_mpv.cache import purge_cache
from yt_mpv.play import check_mpv_installed, play_video, update_yt_dlp
from yt_mpv.utils import DL_DIR, VENV_BIN, VENV_DIR, get_real_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yt-mpv")


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

    # Extract url and query parameters
    if "?" in raw_url:
        base_url, query = raw_url.split("?", 1)
        params = urllib.parse.parse_qs(query)
        should_archive = params.get("archive", ["1"])[0] == "1"
        url = get_real_url(base_url)
    else:
        url = get_real_url(raw_url)
        # Default to archiving if not specified
        should_archive = True

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

    # Skip archiving if not requested
    if not should_archive:
        logger.info("Archiving skipped as requested")
        sys.exit(0)

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
