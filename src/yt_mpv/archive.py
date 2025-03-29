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

    # Define expected output pattern
    output_pattern = f"{dl_dir}/yt-mpv-%(extractor)s-%(id)s.%(ext)s"

    # Use yt-dlp to download the video
    try:
        logger.info("Downloading video for archiving")

        # First attempt with single file format (no need to merge)
        cmd = [
            str(venv_bin / "yt-dlp"),
            "-f",
            "b[ext=mp4]",  # Single file mp4 format, no separate audio/video that needs merging
            "--no-check-certificate",  # Bypass certificate verification for compatibility
            "--write-info-json",
            "-v",  # Verbose output to help diagnose issues
            "--no-part",  # Don't use .part files
            "--force-overwrites",  # Overwrite existing files
            "-o",
            output_pattern,
            url,
        ]

        return_code, stdout, stderr = run_command(cmd, check=False)

        # If the first attempt failed, try with 720p mp4 format
        if return_code != 0:
            logger.warning(f"First download attempt failed: {stderr}")
            logger.info("Trying with 720p mp4 format...")

            cmd = [
                str(venv_bin / "yt-dlp"),
                "-f",
                "22/best[height<=720][ext=mp4]",  # Try format 22 (720p MP4) or similar
                "--no-check-certificate",
                "--write-info-json",
                "-v",
                "--no-part",
                "--force-overwrites",
                "-o",
                output_pattern,
                url,
            ]

            return_code, stdout, stderr = run_command(cmd, check=False)

            # If still failing, try with format 18 (360p) which is usually available
            if return_code != 0:
                logger.warning(f"Second download attempt failed: {stderr}")
                logger.info("Trying with 360p format...")

                cmd = [
                    str(venv_bin / "yt-dlp"),
                    "-f",
                    "18",  # Format 18 is 360p MP4, very widely available
                    "--no-check-certificate",
                    "--write-info-json",
                    "-v",
                    "--no-part",
                    "--force-overwrites",
                    "-o",
                    output_pattern,
                    url,
                ]

                return_code, stdout, stderr = run_command(cmd, check=False)

                # Last resort - try with very low quality but reliable format
                if return_code != 0:
                    logger.warning(f"Third download attempt failed: {stderr}")
                    logger.info("Trying with lowest quality format...")

                    cmd = [
                        str(venv_bin / "yt-dlp"),
                        "-f",
                        "worst",  # Last resort - lowest quality but likely to work
                        "--no-check-certificate",
                        "--write-info-json",
                        "-v",
                        "--no-part",
                        "--force-overwrites",
                        "-o",
                        output_pattern,
                        url,
                    ]

                    return_code, stdout, stderr = run_command(cmd, check=False)

        # If all attempts failed
        if return_code != 0:
            logger.error(f"All download attempts failed. Last error: {stderr}")
            notify("Download failed - yt-dlp error")
            return None

        # Find the info file
        info_file = dl_dir / f"yt-mpv-{extractor}-{video_id}.info.json"
        if not info_file.exists():
            logger.error(f"Info file not found at expected path: {info_file}")
            notify("Download appears incomplete - info file missing")
            return None

        # Find the video file - need to identify the extension from yt-dlp output
        # or check the files in the directory matching the pattern
        video_file = None

        # Try to parse the output to find the filename
        destination_line = None
        if stdout:
            # Look for the last "[download] Destination:" line which contains the full path
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
                    video_file = potential_file

        # If we couldn't find it in the output, look for "Merging" line
        if not video_file and stdout:
            for line in stdout.splitlines():
                if (
                    "[Merger] Merging formats into" in line
                    and f"yt-mpv-{extractor}-{video_id}." in line
                ):
                    potential_path = line.split("into ", 1)[1].strip().strip('"')
                    potential_file = Path(potential_path)
                    if potential_file.exists():
                        video_file = potential_file
                        break

        # If still not found, search the directory for matching files
        if not video_file:
            recent_video_files = []
            for file in dl_dir.glob(f"yt-mpv-{extractor}-{video_id}.*"):
                if file.suffix != ".info.json" and file.exists():
                    # Get file creation/modification time to sort by newest
                    recent_video_files.append((file, file.stat().st_mtime))

            # Sort by modification time (newest first)
            recent_video_files.sort(key=lambda x: x[1], reverse=True)

            if recent_video_files:
                video_file = recent_video_files[0][0]

        # If still not found, look for any recently created video files
        if not video_file:
            logger.info("Trying to find recently created video file...")
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

        if not video_file or not video_file.exists():
            logger.error(f"Video file not found for: yt-mpv-{extractor}-{video_id}.*")
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
