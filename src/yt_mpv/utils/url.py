"""
URL handling utilities for yt-mpv
"""

import urllib.parse


def get_real_url(raw_url: str) -> str:
    """Convert custom scheme to regular http/https URL."""
    # Handle potential URL parameter case
    params = parse_url_params(raw_url)
    if "url" in params:
        # If we have a URL parameter, decode and return it
        return urllib.parse.unquote(params["url"])

    # Otherwise, replace scheme if needed
    scheme_replacements = {
        "x-yt-mpvs:": "https:",
        "x-yt-mpv:": "http:",
    }

    for old_scheme, new_scheme in scheme_replacements.items():
        if raw_url.startswith(old_scheme):
            return raw_url.replace(old_scheme, new_scheme, 1)

    return raw_url


def parse_url_params(url: str) -> dict[str, str]:
    """Parse parameters from a URL."""
    parsed_params = {}

    # Handle x-yt-mpv protocol URLs
    if url.startswith(("x-yt-mpv://", "x-yt-mpvs://")):
        parts = url.split("//", 1)
        query_part = (
            parts[1].split("?", 1)[1] if len(parts) > 1 and "?" in parts[1] else ""
        )
    # Handle regular URLs
    elif "?" in url:
        query_part = url.split("?", 1)[1]
    else:
        return {}

    # Parse the query string
    if query_part:
        params = urllib.parse.parse_qs(query_part, keep_blank_values=True)
        # Convert to simple dict (taking first value if multiple)
        for key, values in params.items():
            parsed_params[key] = values[0] if values else ""

    return parsed_params
