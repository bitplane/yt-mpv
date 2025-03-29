"""
Archive.org functionality for yt-mpv
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from yt_mpv.archive.checker import check_archive_status
from yt_mpv.utils.cache import cleanup_cache_files
from yt_mpv.utils.system import generate_archive_id, notify, run_command
from yt_mpv.utils.url import extract_video_id

# Configure logging
logger = logging.getLogger("yt-mpv")


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


def try_download_format(
    url: str, output_pattern: str, venv_bin: Path, format_spec: str, desc: str = ""
) -> Tuple[int, str, str]:
    """Try to download a video with a specific format specification.

    Args:
        url: URL to download
        output_pattern: Output pattern for yt-dlp
        venv_bin: Path to virtualenv bin directory
        format_spec: Format specification for yt-dlp
        desc: Description of the format for logging

    Returns:
        Tuple[int, str, str]: return code, stdout, stderr
    """
    if desc:
        logger.info(f"Trying with {desc} format...")

    cmd = [
        str(venv_bin / "yt-dlp"),
        "-f",
        format_spec,
        "--no-check-certificate",
        "--write-info-json",
        "--print",
        "filename",  # Explicitly print the filename
        "-v",
        "--no-part",
        "--force-overwrites",
        "-o",
        output_pattern,
        url,
    ]

    return run_command(cmd, check=False)


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

    # Define expected output pattern
    output_pattern = f"{dl_dir}/yt-mpv-%(extractor)s-%(id)s.%(ext)s"

    # Define download formats to try in order of preference
    download_formats = [
        ("b[ext=mp4]", "single file mp4"),
        ("22/best[height<=720][ext=mp4]", "720p mp4"),
        ("18", "360p mp4 (format 18)"),
        ("worst", "lowest quality"),
    ]

    # Try each format in order until one succeeds
    video_file = None
    for format_spec, desc in download_formats:
        return_code, stdout, stderr = try_download_format(
            url, output_pattern, venv_bin, format_spec, desc
        )

        if return_code == 0:
            # Look for printed filename in stdout
            for line in stdout.splitlines():
                if line and not line.startswith("[") and dl_dir.name in line:
                    potential_file = Path(line.strip())
                    if (
                        potential_file.exists()
                        and potential_file.suffix != ".info.json"
                    ):
                        video_file = potential_file
                        break
            if video_file:
                break
        else:
            logger.warning(f"Download attempt with {desc} format failed: {stderr}")

    # If all attempts failed
    if not video_file:
        logger.error("All download attempts failed")
        notify("Download failed - yt-dlp error")
        return None

    # Find the info file
    info_file = dl_dir / f"yt-mpv-{extractor}-{video_id}.info.json"
    if not info_file.exists():
        # Try to find any matching info file if the exact name isn't found
        potential_info_files = list(dl_dir.glob(f"*{video_id}*.info.json"))
        if potential_info_files:
            info_file = potential_info_files[0]
        else:
            logger.error(f"Info file not found at expected path: {info_file}")
            notify("Download appears incomplete - info file missing")
            return None

    return video_file, info_file


def find_video_file(
    dl_dir: Path, extractor: str, video_id: str, stdout: str
) -> Optional[Path]:
    """Find the downloaded video file using various methods.

    Args:
        dl_dir: Download directory
        extractor: Extractor name (e.g., youtube)
        video_id: Video ID
        stdout: stdout from the download command

    Returns:
        Optional[Path]: Path to the video file if found, None otherwise
    """
    # Try to parse the output to find the filename from direct print
    for line in stdout.splitlines():
        if line and not line.startswith("[") and dl_dir.name in line:
            potential_file = Path(line.strip())
            if potential_file.exists() and potential_file.suffix != ".info.json":
                return potential_file

    # Look for the last "[download] Destination:" line
    destination_line = None
    for line in stdout.splitlines():
        if (
            "[download] Destination:" in line
            and f"yt-mpv-{extractor}-{video_id}." in line
        ):
            destination_line = line

    if destination_line:
        potential_path = destination_line.split("Destination:", 1)[1].strip()
        potential_file = Path(potential_path)
        if potential_file.exists() and potential_file.suffix != ".info.json":
            return potential_file

    # Look for "Merging" line
    for line in stdout.splitlines():
        if (
            "[Merger] Merging formats into" in line
            and f"yt-mpv-{extractor}-{video_id}." in line
        ):
            potential_path = line.split("into ", 1)[1].strip().strip('"')
            potential_file = Path(potential_path)
            if potential_file.exists():
                return potential_file

    # Search the directory for matching files
    matching_files = []
    for file in dl_dir.glob(f"yt-mpv-{extractor}-{video_id}.*"):
        if file.suffix != ".info.json" and file.exists():
            # Get file modification time to sort by newest
            matching_files.append((file, file.stat().st_mtime))

    # Sort by modification time (newest first)
    matching_files.sort(key=lambda x: x[1], reverse=True)
    if matching_files:
        return matching_files[0][0]

    # Look for any recently created video files
    import time

    now = time.time()
    recent_files = []

    for file in dl_dir.iterdir():
        if file.is_file() and file.suffix != ".info.json":
            file_age = now - file.stat().st_mtime
            # Look for files created in the last 5 minutes
            if file_age < 300:
                recent_files.append((file, file_age))

    # Sort by age (newest first)
    recent_files.sort(key=lambda x: x[1])
    if recent_files:
        video_file = recent_files[0][0]
        logger.info(f"Found recent file: {video_file}")
        return video_file

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
    archive_url_path = check_archive_status(url)
    if archive_url_path:
        logger.info(f"URL already archived: {archive_url_path}")
        notify(f"Already archived: {archive_url_path}")
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
