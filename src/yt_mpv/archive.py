"""
Archive.org functionality for yt-mpv
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from yt_mpv.cache import cleanup_cache_files
from yt_mpv.utils import (
    extract_video_id,
    generate_archive_id,
    notify,
    run_command,
)

# Configure logging
logger = logging.getLogger("yt-mpv")


def check_archive_status(url: str) -> Optional[str]:
    """Check if a URL has been archived.

    Args:
        url: The URL to check

    Returns:
        str: The archive.org URL if found, otherwise None
    """
    try:
        import internetarchive

        # Generate the identifier that would have been used
        identifier = generate_archive_id(url)

        # Check if item exists
        item = internetarchive.get_item(identifier)
        if item.exists:
            return f"https://archive.org/details/{identifier}"
        else:
            return None

    except ImportError:
        logger.error("internetarchive library not available")
        return None
    except Exception as e:
        logger.error(f"Error checking archive: {e}")
        return None


def extract_metadata(info_file: Path, url: str) -> Dict[str, Any]:
    """Extract metadata from yt-dlp's info.json file.

    Args:
        info_file: Path to the info JSON file
        url: Original URL for fallback

    Returns:
        dict: Metadata dictionary for archive.org
    """
    # Load metadata from yt-dlp's info.json
    try:
        with open(info_file, "r") as f:
            data = json.load(f)

        # Extract metadata
        title = data.get("title", "Untitled Video")
        description = data.get("description") or ""
        tags = data.get("tags") or data.get("categories") or []
        creator = data.get("uploader") or data.get("channel") or ""
        source = data.get("webpage_url") or url

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

        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        # Return minimal metadata if extraction fails
        return {
            "title": "Unknown Video",
            "source": url,
            "mediatype": "movies",
            "collection": "opensource_movies",
        }


def upload_to_archive(video_file: Path, info_file: Path, url: str) -> bool:
    """Upload video to Archive.org using the internetarchive library.

    Args:
        video_file: Path to the video file
        info_file: Path to the info JSON file
        url: Original URL

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import internetarchive

        # Extract metadata from info.json
        metadata = extract_metadata(info_file, url)

        # Generate archive identifier
        username = os.getlogin()
        identifier = generate_archive_id(url, username)

        # Check if item already exists
        item = internetarchive.get_item(identifier)
        if item.exists:
            logger.info(f"Archive item {identifier} already exists. Skipping upload.")
            notify(f"Already archived as {identifier}")
            return True

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


def download_video(
    url: str, dl_dir: Path, venv_bin: Path
) -> Optional[Tuple[Path, Path]]:
    """Download video using yt-dlp and return paths to video and info files.

    Args:
        url: URL to download
        dl_dir: Download directory path
        venv_bin: Path to virtual environment bin directory

    Returns:
        Tuple[Path, Path]: Paths to video and info files, or None if failed
    """
    # Ensure download directory exists
    dl_dir.mkdir(parents=True, exist_ok=True)

    # Extract video ID from URL
    video_id, extractor = extract_video_id(url)

    # Define expected output paths
    info_file = dl_dir / f"yt-mpv-{extractor}-{video_id}.info.json"
    video_file = dl_dir / f"yt-mpv-{extractor}-{video_id}.mp4"

    # Use yt-dlp to download the video
    try:
        logger.info("Downloading video for archiving")
        cmd = [
            str(venv_bin / "yt-dlp"),
            "-f",
            "bestvideo*+bestaudio/best",
            "--merge-output-format",
            "mp4",
            "--write-info-json",
            "-o",
            f"{dl_dir}/yt-mpv-%(extractor)s-%(id)s.%(ext)s",
            url,
        ]

        return_code, _, stderr = run_command(cmd, check=True)

        if return_code != 0:
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

    except Exception as e:
        logger.error(f"Download failed: {e}")
        notify("Download failed")
        return None


def archive_url(url: str, dl_dir: Path, venv_bin: Path) -> bool:
    """Archive a URL to archive.org.

    This is the main entry point for archiving functionality.

    Args:
        url: URL to archive
        dl_dir: Download directory path
        venv_bin: Path to virtual environment bin directory

    Returns:
        bool: True if successful, False otherwise
    """
    # First check if already archived
    archive_url = check_archive_status(url)
    if archive_url:
        logger.info(f"URL already archived: {archive_url}")
        notify(f"Already archived: {archive_url}")
        return True

    # Download video
    result = download_video(url, dl_dir, venv_bin)
    if not result:
        return False

    video_file, info_file = result

    # Upload to Archive.org
    success = upload_to_archive(video_file, info_file, url)

    # Clean up files if upload was successful
    if success:
        if cleanup_cache_files(video_file, info_file):
            logger.info("Cache files cleaned up successfully")
        else:
            logger.warning("Failed to clean up some cache files")

    return success
