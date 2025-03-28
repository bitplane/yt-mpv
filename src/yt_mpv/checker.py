"""
Archive checking functionality for yt-mpv
"""

import hashlib
import os
import sys


def generate_archive_id(url, username=None):
    """Generate a unique Archive.org identifier for a video URL.

    This must match the ID generation in launch.py.

    Args:
        url: The URL to generate an ID for
        username: Optional username, defaults to current user

    Returns:
        str: The archive identifier
    """
    if username is None:
        username = os.getlogin()
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"yt-mpv-{username}-{url_hash}"


def check_archive_status(url):
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

        # Search archive.org
        search = internetarchive.search_items(f"identifier:{identifier}")
        item = next(search, None)

        if item:
            item_url = f"https://archive.org/details/{identifier}"
            return item_url
        else:
            return None

    except ImportError:
        print("Error: internetarchive library not available", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error checking archive: {e}", file=sys.stderr)
        return None


def main():
    """Command line entry point for checking archive status."""
    if len(sys.argv) < 2:
        print("Usage: python -m yt_mpv.checker URL", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    result = check_archive_status(url)

    if result:
        print(result)
        sys.exit(0)
    else:
        print(f"URL not found in archive.org: {url}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
