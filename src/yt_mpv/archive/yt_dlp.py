"""
Video downloading functionality using yt-dlp
"""

import logging
import subprocess
from pathlib import Path

from yt_mpv.archive.archive_org import is_archived, upload
from yt_mpv.utils.cache import remove
from yt_mpv.utils.fs import run_command
from yt_mpv.utils.notify import notify

# Configure logging
logger = logging.getLogger("yt-mpv")


def get_filenames(url: str, dl_dir: Path, venv_bin: Path) -> tuple[Path, Path]:
    """Get filenames yt-dlp would use for a URL."""
    dl_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = f"{dl_dir}/yt-mpv-%(extractor)s-%(id)s.%(ext)s"

    result = subprocess.run(
        [
            str(venv_bin / "yt-dlp"),
            "--print",
            "filename",
            "-o",
            output_pattern,
            "--skip-download",
            url,
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    video_file = Path(result.stdout.strip().split("\n")[0])
    info_file = video_file.with_suffix(".info.json")

    return video_file, info_file


def download(url: str, dl_dir: Path, venv_bin: Path) -> tuple[Path, Path] | None:
    """Download video using yt-dlp and return paths to video and info files."""
    # Get the expected filenames from yt-dlp
    video_file, info_file = get_filenames(url, dl_dir, venv_bin)

    # Define output pattern to use the same name pattern
    output_pattern = str(video_file.with_suffix(".%(ext)s"))

    # Use the best available format
    logger.info("Downloading best available format")

    cmd = [
        str(venv_bin / "yt-dlp"),
        "-f",
        "b[ext=mp4]/b",  # Best mp4 format, fallback to best format
        "--no-check-certificate",
        "--write-info-json",
        "--print",
        "filename",
        "-v",
        "--no-part",
        "--force-overwrites",
        "-o",
        output_pattern,
        url,
    ]

    return_code, stdout, stderr = run_command(cmd, check=False)

    if return_code == 0:
        # Check if the file exists with the expected name
        if video_file.exists() and info_file.exists():
            return video_file, info_file

        # If the file extension is different than expected, find the actual file
        potential_files = list(dl_dir.glob(f"{video_file.stem}.*"))
        potential_files = [f for f in potential_files if f.suffix != ".info.json"]
        if potential_files:
            video_file = potential_files[0]
            info_file = video_file.with_suffix(".info.json")
            if video_file.exists() and info_file.exists():
                return video_file, info_file

    # If download failed
    logger.error(f"Failed to download video: {stderr}")
    notify("Download failed - yt-dlp error")
    return None


def update(venv_dir: Path, venv_bin: Path) -> bool:
    """Update yt-dlp using uv if available."""
    # Prepare environment with venv
    logger.info("Updating yt-dlp using uv in venv")
    cmd = ["uv", "pip", "install", "--upgrade", "yt-dlp"]
    run_command(cmd, check=False)

    return True


def archive_url(url: str, dl_dir: Path, venv_bin: Path) -> bool:
    """Archive a URL to archive.org."""
    # First check if already archived
    archive_url_path = is_archived(url)
    if archive_url_path:
        logger.info(f"URL already archived: {archive_url_path}")
        notify(f"Already archived: {archive_url_path}")
        return True

    try:
        # Get the filenames that yt-dlp would use
        video_file, info_file = get_filenames(url, dl_dir, venv_bin)

        # Check if the files already exist (from previous play)
        if video_file.exists() and info_file.exists():
            logger.info(f"Using existing files: {video_file.name}")
        else:
            # Need to download the video
            logger.info("Downloading video for archiving")
            result = download(url, dl_dir, venv_bin)
            if not result:
                return False

            video_file, info_file = result

    except Exception as e:
        logger.error(f"Error preparing for archive: {e}")
        notify(f"Archive preparation failed: {str(e)}")
        return False

    # Upload to Archive.org
    success = upload(video_file, info_file, url)

    # Clean up files if upload was successful
    if success:
        if remove(video_file, info_file):
            logger.info("Cache files cleaned up successfully")
        else:
            logger.warning("Failed to clean up some cache files")

    return success
