"""
Bookmarklet generation and setup for yt-mpv
"""

import base64
import logging
import webbrowser
from pathlib import Path

# Configure logging
logger = logging.getLogger("yt-mpv")


def get_path():
    """Get the path to the bookmark.html file."""
    try:
        # For Python 3.9+
        from importlib.resources import files

        return files("yt_mpv.install.resources").joinpath("bookmark.html")
    except (ImportError, AttributeError):
        # Fallback for earlier Python versions
        import pkg_resources

        return Path(
            pkg_resources.resource_filename("yt_mpv", "install/resources/bookmark.html")
        )


def get_js():
    """Get the JavaScript bookmarklet code."""
    play_only_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv:/?url=' + originalUrl + '&archive=0';})()"
    )

    play_archive_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv:/?url=' + originalUrl + '&archive=1';})()"
    )

    return (play_only_js, play_archive_js)


def open_browser():
    """Open the bookmarklet HTML in a browser using a data URI."""
    try:
        # Get the HTML file content
        html_path = get_path()

        with open(html_path, "r", encoding="utf-8") as f:
            bookmark_content = f.read()

        # Encode the HTML content as a data URI
        encoded_content = base64.b64encode(bookmark_content.encode()).decode()
        data_uri = f"data:text/html;base64,{encoded_content}"

        # Open the data URI in the browser
        logger.info("Opening bookmarklet page...")
        webbrowser.open(data_uri)

        # Also print the JavaScript in case the browser doesn't open
        play_only_js, play_archive_js = get_js()
        print(
            "\nIf your browser doesn't open automatically, you can create these bookmarks manually:"
        )
        print(f"MPV Play: {play_only_js}")
        print(f"MPV Play+Archive: {play_archive_js}")

        return True

    except Exception as e:
        logger.error(f"Could not open bookmarklet HTML: {e}")
        # Provide the bookmarklet JavaScript even if there's an error
        play_only_js, play_archive_js = get_js()
        print("Please manually create bookmarks with the following URLs:")
        print(f"MPV Play: {play_only_js}")
        print(f"MPV Play+Archive: {play_archive_js}")
        return False
