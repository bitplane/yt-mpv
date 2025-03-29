"""
Launcher for yt-mpv: Play videos with mpv, then optionally upload to Internet Archive.
"""

import logging
import os
import sys
import urllib.parse

# Import functionality
from yt_mpv.archive.archive_org import is_archived
from yt_mpv.archive.yt_dlp import archive_url
from yt_mpv.archive.yt_dlp import update as update_yt_dlp
from yt_mpv.player import is_installed as is_mpv_installed
from yt_mpv.player import play
from yt_mpv.utils.config import DL_DIR, VENV_BIN, VENV_DIR
from yt_mpv.utils.url import get_real_url, parse_url_params

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
    if not is_mpv_installed():
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

    # Extract URL and parameters
    params = parse_url_params(raw_url)

    # Handle the new style bookmarklet format with URL parameter
    if "url" in params:
        # Decode the URL parameter since it's URL-encoded
        url = urllib.parse.unquote(params["url"])
        # Explicitly check for the archive parameter
        should_archive = params.get("archive", "1") == "1"
        logger.info(f"Parsed URL: {url}, archive setting: {should_archive}")
    else:
        # Handle legacy URL format
        url = get_real_url(raw_url)
        # Check for archive parameter
        should_archive = params.get("archive", "1") == "1"

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        logger.error(f"Invalid URL format: {url}")
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Update yt-dlp to avoid YouTube API changes breaking functionality
    update_yt_dlp(VENV_DIR, VENV_BIN)

    # Play the video
    if not play(url):
        sys.exit(1)

    # Skip archiving if not requested
    if not should_archive:
        logger.info("Archiving skipped as requested")
        sys.exit(0)

    # Check if already archived before downloading
    archive_url_path = is_archived(url)
    if archive_url_path:
        logger.info(f"Already archived at: {archive_url_path}")
        sys.exit(0)

    # Archive the URL
    if not archive_url(url, DL_DIR, VENV_BIN):
        sys.exit(1)

    logger.info("Process completed successfully")


if __name__ == "__main__":
    main()
