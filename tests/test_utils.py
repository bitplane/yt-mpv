"""
Tests for the yt-mpv utils module.
"""

import hashlib
from unittest.mock import patch

from yt_mpv.utils.system import generate_archive_id, run_command
from yt_mpv.utils.url import extract_video_id, get_real_url


def test_generate_archive_id():
    """Test archive ID generation for consistency."""
    # Test with fixed URL and username
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    username = "testuser"

    # Generate ID
    archive_id = generate_archive_id(url, username)

    # Verify format and expected hash
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    expected_id = f"yt-mpv-{username}-{url_hash}"

    assert archive_id == expected_id

    # Test with different URL
    url2 = "https://www.youtube.com/watch?v=different"
    archive_id2 = generate_archive_id(url2, username)
    assert archive_id != archive_id2

    # Test default username (mocked to avoid using actual login)
    with patch("os.getlogin", return_value="defaultuser"):
        archive_id3 = generate_archive_id(url)
        assert "defaultuser" in archive_id3


def test_get_real_url():
    """Test URL scheme conversion."""
    # Test http conversion
    assert get_real_url("x-yt-mpv://example.com") == "http://example.com"

    # Test https conversion
    assert get_real_url("x-yt-mpvs://example.com") == "https://example.com"

    # Test no conversion needed
    assert get_real_url("https://example.com") == "https://example.com"
    assert get_real_url("http://example.com") == "http://example.com"


def test_extract_video_id():
    """Test video ID extraction from URLs."""
    # Test YouTube URL
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    video_id, extractor = extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"
    assert extractor == "youtube"

    # Test YouTube short URL
    url = "https://youtu.be/dQw4w9WgXcQ"
    video_id, extractor = extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"
    assert extractor == "youtube"

    # Test embedded YouTube URL
    url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    video_id, extractor = extract_video_id(url)
    assert video_id == "dQw4w9WgXcQ"
    assert extractor == "youtube"

    # Test non-YouTube URL
    url = "https://vimeo.com/12345"
    video_id, extractor = extract_video_id(url)
    assert extractor == "generic"
    assert len(video_id) == 11  # MD5 hash truncated to 11 chars


def test_run_command():
    """Test command runner functionality."""
    # Test successful command
    status, stdout, stderr = run_command(["echo", "test"])
    assert status == 0
    assert "test" in stdout
    assert stderr == ""

    # Test command with error
    status, stdout, stderr = run_command(["ls", "/nonexistent"], check=False)
    assert status != 0
    assert stderr != ""
