#!/usr/bin/env python3
"""
Launcher for x-yt-ulp:// URL
Plays video with mpv, then uploads to Internet Archive.
"""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("yt-ulp")

# Constants
HOME = Path.home()
DL_DIR = HOME / ".local/share/yt-ulp"
VENV_DIR = DL_DIR / "venv"
VENV_BIN = VENV_DIR / "bin"


def notify(message: str) -> None:
    """Send desktop notification if possible."""
    try:
        subprocess.run(
            ["notify-send", "YouTube ULP", message], check=False, capture_output=True
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        # If notification fails, just log it
        pass


def get_real_url(raw_url: str) -> str:
    """Convert x-yt-ulp custom scheme to regular http/https URL."""
    if raw_url.startswith("x-yt-ulps:"):
        return raw_url.replace("x-yt-ulps:", "https:", 1)
    elif raw_url.startswith("x-yt-ulp:"):
        return raw_url.replace("x-yt-ulp:", "http:", 1)
    return raw_url


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    # Check for mpv
    if not shutil.which("mpv"):
        logger.error("mpv is not installed")
        notify("mpv not found. Please install it.")
        return False

    # Check for Python venv
    if not os.path.isfile(os.path.join(VENV_BIN, "activate")):
        logger.error(f"Python venv not found at {VENV_DIR}")
        notify("Python venv missing: run install.sh")
        return False

    return True


def run_command(cmd: list, desc: str = "", check: bool = True) -> Tuple[int, str, str]:
    """Run a command and return status, stdout, stderr."""
    try:
        if desc:
            logger.info(desc)

        proc = subprocess.run(cmd, check=check, text=True, capture_output=True)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.SubprocessError as e:
        logger.error(f"Command failed: {e}")
        return 1, "", str(e)


def play_video(url: str) -> bool:
    """Play the video with mpv and return success status."""
    status, _, stderr = run_command(
        ["mpv", "--ytdl=no", url, f"--term-status-msg=Playing: {url}"],
        desc=f"Playing {url} with mpv",
        check=False,
    )

    if status != 0:
        logger.error(f"Failed to play video: {stderr}")
        notify("Failed to play video")
        return False

    return True


def download_video(url: str) -> Optional[Tuple[Path, Path]]:
    """Download video using yt-dlp and return paths to video and info files."""
    # Ensure download directory exists
    DL_DIR.mkdir(parents=True, exist_ok=True)

    # Use yt-dlp to download the video
    status, stdout, stderr = run_command(
        [
            os.path.join(VENV_BIN, "yt-dlp"),
            "-f",
            "bestvideo*+bestaudio/best",
            "--merge-output-format",
            "mp4",
            "--write-info-json",
            "-o",
            f"{DL_DIR}/yt-ulp-%(extractor)s-%(id)s.%(ext)s",
            url,
        ],
        desc="Downloading video for archiving",
        check=False,
    )

    if status != 0:
        logger.error(f"Download failed: {stderr}")
        notify("Download failed")
        return None

    # Find the downloaded files
    info_files = list(DL_DIR.glob("yt-ulp-*-*.info.json"))
    if not info_files:
        logger.error("No info file found after download")
        notify("Download appears incomplete - no info file")
        return None

    # Sort by modification time to get the most recent
    info_file = sorted(info_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    video_file = info_file.with_suffix("")  # Remove .info.json suffix

    if not video_file.exists():
        video_file = next(
            (
                f
                for f in video_file.parent.glob(f"{video_file.name}.*")
                if f.suffix != ".json"
            ),
            None,
        )
        if not video_file:
            logger.error("Video file not found after download")
            notify("Download appears incomplete - video file missing")
            return None

    return video_file, info_file


def generate_archive_id(url: str, username: str) -> str:
    """Generate a unique Archive.org identifier for this video."""
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"yt-ulp-{username}-{url_hash}"


def upload_to_archive(video_file: Path, info_file: Path, url: str) -> bool:
    """Upload video to Archive.org using the internetarchive library."""
    try:
        # We import here to ensure we're using the venv's version
        import internetarchive

        # Load metadata from yt-dlp's info.json
        with open(info_file, "r") as f:
            data = json.load(f)

        # Extract metadata
        title = data.get("title", "Untitled Video")
        description = data.get("description") or ""
        tags = data.get("tags") or data.get("categories") or []
        creator = data.get("uploader") or data.get("channel") or ""
        source = data.get("webpage_url") or url

        # Generate archive identifier
        username = os.getlogin()
        identifier = generate_archive_id(url, username)

        # Check if item already exists
        try:
            search = internetarchive.search_items(f"identifier:{identifier}")
            exists = next(search, None) is not None
        except Exception as e:
            logger.warning(f"Archive.org search failed: {e}")
            exists = False

        if exists:
            logger.info(f"Archive item {identifier} already exists. Skipping upload.")
            notify("Already archived on IA (skipping upload)")
            return True

        # Prepare metadata for upload
        metadata = {
            "title": title,
            "description": description,
            "creator": creator,
            "subject": tags,
            "source": source,
            "mediatype": "movies",
            "collection": "opensource_movies",
        }

        logger.info(f"Uploading to archive.org as {identifier}")
        notify(f"Beginning upload to Internet Archive: {identifier}")

        # Perform the upload
        response = internetarchive.upload(
            identifier,
            {video_file.name: str(video_file)},
            metadata=metadata,
            retries=3,
            retries_sleep=10,
        )

        # Check for success
        success = all(r.status_code == 200 for r in response)

        if success:
            logger.info("Upload succeeded")
            notify(f"Upload succeeded: {identifier}")
            return True
        else:
            logger.error("Upload failed")
            notify("Upload to IA failed")
            return False

    except ImportError:
        logger.error("internetarchive module not available")
        notify("internetarchive module missing - run install.sh")
        return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        notify(f"Upload failed: {str(e)}")
        return False


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
        notify("Invalid URL format")
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Try to update yt-dlp to avoid YouTube API changes breaking functionality
    run_command(
        ["pip", "install", "--upgrade", "yt-dlp"], desc="Updating yt-dlp", check=False
    )

    # Play the video
    if not play_video(url):
        sys.exit(1)

    # Download video for archiving
    result = download_video(url)
    if not result:
        sys.exit(1)

    video_file, info_file = result

    # Upload to Archive.org
    if not upload_to_archive(video_file, info_file, url):
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
        notify(f"Error: {str(e)}")
        sys.exit(1)
