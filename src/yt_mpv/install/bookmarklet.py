"""
Bookmarklet generation and setup for yt-mpv
"""

import logging
import webbrowser

# Configure logging
logger = logging.getLogger("yt-mpv")


def get_js():
    """Get the JavaScript bookmarklet code."""
    play_only_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv://?url=' + originalUrl + '&archive=0';})()"
    )

    play_archive_js = (
        "javascript:(function(){var originalUrl = encodeURIComponent(window.location.href); "
        "window.location.href = 'x-yt-mpv://?url=' + originalUrl + '&archive=1';})()"
    )

    return (play_only_js, play_archive_js)


def open_browser():
    """Open the hosted install docs page with bookmarklets."""
    docs_url = "https://bitplane.net/dev/python/yt-mpv/install/"
    try:
        logger.info(f"Opening bookmarklet page: {docs_url}")
        webbrowser.open(docs_url)

        # Print the docs URL and the JavaScript as a fallback
        play_only_js, play_archive_js = get_js()
        print("\nIf your browser doesn't open automatically:")
        print(f"Open: {docs_url}")
        print("Or create bookmarks manually with these URLs:")
        print(f"MPV Play: {play_only_js}")
        print(f"MPV Play+Archive: {play_archive_js}")
        return True
    except Exception as e:
        logger.error(f"Could not open browser: {e}")
        play_only_js, play_archive_js = get_js()
        print("Please open the install page manually and/or create bookmarks with the following URLs:")
        print(f"Install page: {docs_url}")
        print(f"MPV Play: {play_only_js}")
        print(f"MPV Play+Archive: {play_archive_js}")
        return False
