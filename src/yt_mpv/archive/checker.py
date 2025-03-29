"""
Archive checking functionality for yt-mpv
"""

import logging
from typing import Optional

from yt_mpv.utils.system import generate_archive_id

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
