"""
Tests for the core archive functionality.
"""

import json

import pytest

from yt_mpv.core.archive import extract_metadata


@pytest.fixture
def sample_info_file(tmp_path):
    """Create a sample info JSON file for testing."""
    info_data = {
        "title": "Test Video",
        "description": "This is a test video description",
        "uploader": "Test Uploader",
        "tags": ["test", "video", "testing"],
        "webpage_url": "https://www.youtube.com/watch?v=test123",
    }

    info_file = tmp_path / "test_info.json"
    with open(info_file, "w") as f:
        json.dump(info_data, f)

    return info_file


def test_extract_metadata(sample_info_file):
    """Test extracting metadata from an info file."""
    url = "https://www.youtube.com/watch?v=test123"
    metadata = extract_metadata(sample_info_file, url)

    # Check that metadata contains expected fields
    assert metadata["title"] == "Test Video"
    assert metadata["description"] == "This is a test video description"
    assert metadata["creator"] == "Test Uploader"
    assert "test" in metadata["subject"]
    assert metadata["source"] == "https://www.youtube.com/watch?v=test123"
    assert metadata["mediatype"] == "movies"
    assert metadata["collection"] == "opensource_movies"


def test_extract_metadata_missing_fields(tmp_path):
    """Test extracting metadata with missing fields."""
    # Create minimal info JSON
    info_data = {"title": "Minimal Video"}

    info_file = tmp_path / "minimal_info.json"
    with open(info_file, "w") as f:
        json.dump(info_data, f)

    url = "https://example.com/video"
    metadata = extract_metadata(info_file, url)

    # Check that metadata has default values for missing fields
    assert metadata["title"] == "Minimal Video"
    assert metadata["description"] == ""
    assert metadata["creator"] == ""
    assert isinstance(metadata["subject"], list)
    assert metadata["source"] == url
    assert metadata["mediatype"] == "movies"
