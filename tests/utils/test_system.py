"""
Tests for the system utilities.
"""

import hashlib
from unittest.mock import patch

from yt_mpv.utils.system import generate_archive_id, run_command


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


def test_run_command():
    """Test command runner functionality."""
    # Test successful command
    status, stdout, stderr = run_command(["echo", "test"])
    assert status == 0
    assert "test" in stdout
    assert stderr == ""

    # Test command with error
    status, stdout, stderr = run_command(["ls", "/nonexistent"], check=False)
