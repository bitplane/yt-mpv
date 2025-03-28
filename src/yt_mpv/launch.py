"""
Launcher for yt-mpv: Play videos with mpv, then upload to Internet Archive.
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
logger = logging.getLogger("yt-mpv")

# Constants - consistent naming throughout
HOME = Path.home()
DL_DIR = HOME / ".cache/yt-mpv"
VENV_DIR = Path(os.environ.get("YT_MPV_VENV", HOME / ".local/share/yt-mpv/.venv"))
VENV_BIN = VENV_DIR / "bin"


def notify(message: str) -> None:
    """Send desktop notification if possible."""
    try:
        subprocess.run(
            ["notify-send", "YouTube MPV", message], check=False, capture_output=True
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        # If notification fails, just log it
        pass


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
    if not shutil.which("mpv"):
        logger.error("mpv is not installed")
        notify("mpv not found. Please install it.")
        return False

    # Check for Python venv
    if not os.path.isfile(os.path.join(VENV_BIN, "activate")):
        logger.error(f"Python venv not found at {VENV_DIR}")
        notify("Python venv missing: run 'yt-mpv install'")
        return False

    return True


def run_command(
    cmd: list, desc: str = "", check: bool = True, env=None
) -> Tuple[int, str, str]:
    """Run a command and return status, stdout, stderr."""
    try:
        if desc:
            logger.info(desc)

        proc = subprocess.run(cmd, check=check, text=True, capture_output=True, env=env)
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.SubprocessError as e:
        logger.error(f"Command failed: {e}")
        return 1, "", str(e)


def play_video(url: str) -> bool:
    """Play the video with mpv and return success status."""
    status, _, stderr = run_command(
        ["mpv", "--ytdl=yes", url, f"--term-status-msg=Playing: {url}"],
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

    # Extract video ID from URL (assuming YouTube, but could be expanded)
    video_id = url.split("v=")[-1].split("&")[0]
    extractor = "youtube"  # Could detect this from URL if needed

    # Define expected output paths
    info_file = DL_DIR / f"yt-mpv-{extractor}-{video_id}.info.json"
    video_file = DL_DIR / f"yt-mpv-{extractor}-{video_id}.mp4"

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
            f"{DL_DIR}/yt-mpv-%(extractor)s-%(id)s.%(ext)s",
            url,
        ],
        desc="Downloading video for archiving",
        check=False,
    )

    if status != 0:
        logger.error(f"Download failed: {stderr}")
        notify("Download failed")
        return None

    # Simple check if files exist after download
    if not info_file.exists():
        logger.error(f"Info file not found at expected path: {info_file}")
        notify("Download appears incomplete - info file missing")
        return None

    if not video_file.exists():
        logger.error(f"Video file not found at expected path: {video_file}")
        notify("Download appears incomplete - video file missing")
        return None

    return video_file, info_file


def generate_archive_id(url: str, username: str = None) -> str:
    """Generate a unique Archive.org identifier for this video."""
    if username is None:
        username = os.getlogin()
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"yt-mpv-{username}-{url_hash}"


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
        notify("internetarchive module missing - run 'yt-mpv install'")
        return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        notify(f"Upload failed: {str(e)}")
        return False


def update_yt_dlp():
    """Update yt-dlp using uv if available."""
    try:
        # Prepare environment with venv
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = str(VENV_DIR)
        env["PATH"] = f"{VENV_BIN}:{env.get('PATH', '')}"

        # First try to use uv if available in the venv
        uv_path = VENV_BIN / "uv"
        if uv_path.exists():
            logger.info("Updating yt-dlp using uv in venv")
            cmd = [str(uv_path), "pip", "install", "--upgrade", "yt-dlp"]
            run_command(cmd, env=env, check=False)
        # Then try system uv
        elif shutil.which("uv"):
            logger.info("Updating yt-dlp using system uv")
            cmd = ["uv", "pip", "install", "--upgrade", "yt-dlp"]
            run_command(cmd, env=env, check=False)
        else:
            # Fall back to pip
            logger.info("Updating yt-dlp using pip")
            cmd = [str(VENV_BIN / "pip"), "install", "--upgrade", "yt-dlp"]
            run_command(cmd, check=False)
    except Exception as e:
        logger.warning(f"Failed to update yt-dlp: {e}")


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

    # Update yt-dlp to avoid YouTube API changes breaking functionality
    update_yt_dlp()

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
