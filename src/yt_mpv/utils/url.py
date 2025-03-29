"""
URL handling utilities for yt-mpv
"""

import hashlib
import re
import urllib.parse
from typing import Dict, Tuple


def get_real_url(raw_url: str) -> str:
    """Convert custom scheme to regular http/https URL.

    Args:
        raw_url: URL possibly using custom x-yt-mpv scheme

    Returns:
        str: URL with standard http/https scheme
    """
    # Handle potential URL parameter case
    params = parse_url_params(raw_url)
    if "url" in params:
        # If we have a URL parameter, return that directly
        return params["url"]

    # Otherwise, replace scheme if needed
    if raw_url.startswith("x-yt-mpvs:"):
        return raw_url.replace("x-yt-mpvs:", "https:", 1)
    elif raw_url.startswith("x-yt-mpv:"):
        return raw_url.replace("x-yt-mpv:", "http:", 1)

    return raw_url


def extract_video_id(url: str) -> Tuple[str, str]:
    """Extract video ID and extractor name from URL.

    Args:
        url: URL to extract ID from

    Returns:
        Tuple[str, str]: Video ID and extractor name
    """
    # YouTube format
    youtube_pattern = (
        r"(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|"
        r"(?:v|e(?:mbed)?)\/|"
        r"\S*?[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
    )
    youtube_match = re.search(youtube_pattern, url)

    if youtube_match:
        return youtube_match.group(1), "youtube"

    # For other URLs, use a hash of the URL as fallback
    # This is simplified and would ideally be improved with more extractors
    url_hash = hashlib.md5(url.encode()).hexdigest()[:11]
    return url_hash, "generic"


def parse_url_params(url: str) -> Dict[str, str]:
    """Parse parameters from a URL.

    Args:
        url: URL potentially containing parameters

    Returns:
        Dict[str, str]: Dictionary of parameters
    """
    parsed_params = {}

    # Check if URL has parameters
    if "?" in url:
        query_string = url.split("?", 1)[1]

        # Parse the query string
        params = urllib.parse.parse_qs(query_string, keep_blank_values=True)

        # Convert to simple dict (taking first value if multiple)
        for key, values in params.items():
            if values:
                parsed_params[key] = values[0]
            else:
                parsed_params[key] = ""

    return parsed_params
