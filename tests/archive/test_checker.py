"""
Tests for the archive.org status checker.
"""

from unittest.mock import patch

from yt_mpv.archive.archive_org import is_archived
from yt_mpv.utils.fs import generate_archive_id


def test_is_archived_not_found():
    """Test checking an archive status when item doesn't exist."""
    mock_item = type("MockItem", (), {"exists": False})

    with patch("internetarchive.get_item", return_value=mock_item):
        result = is_archived("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert result is None


def test_is_archived_found():
    """Test checking an archive status when item exists."""
    mock_item = type("MockItem", (), {"exists": True})
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_id = generate_archive_id(test_url)

    with patch("internetarchive.get_item", return_value=mock_item):
        with patch("yt_mpv.utils.fs.generate_archive_id", return_value=test_id):
            result = is_archived(test_url)

    assert result is not None
    assert f"https://archive.org/details/{test_id}" == result
