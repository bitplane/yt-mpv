"""
Tests for the system utilities.
"""

import hashlib
import re

from yt_mpv.utils.fs import generate_archive_id, run_command


def test_generate_archive_id():
    """Test archive ID generation for consistency."""
    # Test with fixed URL
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Generate ID
    archive_id = generate_archive_id(url)

    # Verify format: YYYY_MM_DD-url_with_underscores-hash
    assert re.match(r"^\d{4}_\d{2}_\d{2}-.+-[a-f0-9]{8}$", archive_id)

    # Verify hash portion matches MD5
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    assert archive_id.endswith(f"-{url_hash}")

    # Verify URL portion is cleaned
    assert "www_youtube_com" in archive_id
    assert "dQw4w9WgXcQ" in archive_id

    # Test with different URL generates different ID
    url2 = "https://www.youtube.com/watch?v=different"
    archive_id2 = generate_archive_id(url2)
    assert archive_id != archive_id2

    # Test length limit (max 80 chars)
    long_url = "https://www.example.com/" + "a" * 200
    long_id = generate_archive_id(long_url)
    assert len(long_id) <= 80


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
