"""
Internet Archive functionality for yt-mpv
"""

import json
import logging
from pathlib import Path

from yt_mpv.utils.fs import generate_archive_id
from yt_mpv.utils.notify import notify

# Configure logging
logger = logging.getLogger("yt-mpv")


def is_archived(url: str, upload_date: str = None) -> str | None:
    """
    Check if a URL is already archived in archive.org.

    Args:
        url: The URL to check
        upload_date: Original upload date in YYYYMMDD format

    Returns:
        str: The archive.org URL if found, otherwise None
    """
    try:
        import internetarchive

        # Generate the identifier that would have been used
        identifier = generate_archive_id(url, upload_date)

        # Check if item exists
        item = internetarchive.get_item(identifier)
        if item.exists:
            return f"https://archive.org/details/{identifier}"
        else:
            return None

    except ImportError:
        logger.error("internetarchive library not available")
        return None


def prepare_metadata(info_file: Path, url: str) -> dict[str, any]:
    """Extract and prepare metadata from yt-dlp's info.json file for upload."""
    # Load metadata from yt-dlp's info.json
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
    }

    return metadata


def upload(video_file: Path, info_file: Path, url: str) -> bool:
    """Upload video to Archive.org."""
    try:
        import internetarchive

        # Extract metadata from info.json
        metadata = prepare_metadata(info_file, url)

        # Load info to get upload date
        with open(info_file, "r") as f:
            info_data = json.load(f)
        upload_date = info_data.get("upload_date")

        # Generate archive identifier with original upload date
        identifier = generate_archive_id(url, upload_date)

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
            archive_url = f"https://archive.org/details/{identifier}"
            notify(f"Upload succeeded: {identifier}", url=archive_url)
            return True
        else:
            logger.error("Upload failed")
            notify("Upload to IA failed")
            return False

    except ImportError:
        logger.error("internetarchive module not available")
        notify("internetarchive module missing - run 'yt-mpv install'")
        raise


def configure() -> bool:
    """Configure Internet Archive credentials."""
    try:
        from pathlib import Path

        import internetarchive

        home = Path.home()
        ia_config = home / ".config" / "ia.ini"
        ia_config_alt = home / ".config" / "internetarchive" / "ia.ini"

        # Check if already configured
        if ia_config.exists() or ia_config_alt.exists():
            logger.info("Internet Archive already configured")
            return True

        # Ensure config directory exists
        if not ia_config.parent.exists():
            ia_config.parent.mkdir(parents=True, exist_ok=True)

        # Run ia configure command
        logger.info("Setting up Internet Archive credentials...")
        internetarchive.configure()

        return True
    except ImportError:
        logger.error("internetarchive library not available")
        return False
