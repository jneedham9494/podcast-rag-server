"""
Pytest configuration and shared fixtures for podcast archive tests.
"""

import pytest
from pathlib import Path
import tempfile
import json


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_opml_content():
    """Sample OPML content for testing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Podcast Subscriptions</title>
  </head>
  <body>
    <outline text="Test Podcast 1" type="rss" xmlUrl="https://example.com/feed1.xml"/>
    <outline text="Test Podcast 2" type="rss" xmlUrl="https://example.com/feed2.xml"/>
    <outline text="Another Show" type="rss" xmlUrl="https://example.com/feed3.xml"/>
  </body>
</opml>'''


@pytest.fixture
def sample_opml_file(temp_dir, sample_opml_content):
    """Create a sample OPML file for testing."""
    opml_path = temp_dir / "test.opml"
    opml_path.write_text(sample_opml_content)
    return opml_path


@pytest.fixture
def sample_rss_content():
    """Sample RSS feed content for testing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Podcast</title>
    <description>A test podcast feed</description>
    <item>
      <title>Episode 1: Introduction</title>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
      <description>First episode description</description>
      <enclosure url="https://example.com/ep1.mp3" type="audio/mpeg" length="1000000"/>
    </item>
    <item>
      <title>Episode 2: Deep Dive</title>
      <pubDate>Mon, 08 Jan 2024 00:00:00 GMT</pubDate>
      <description>Second episode description</description>
      <enclosure url="https://example.com/ep2.mp3" type="audio/mpeg" length="2000000"/>
    </item>
  </channel>
</rss>'''


@pytest.fixture
def sample_episode():
    """Sample episode data structure."""
    return {
        'title': 'Test Episode: With Special Characters! (Part 1)',
        'published': 'Mon, 01 Jan 2024 00:00:00 GMT',
        'audio_url': 'https://example.com/test.mp3',
        'description': 'A test episode description'
    }


@pytest.fixture
def sample_metadata(temp_dir):
    """Create sample podcast metadata file."""
    metadata = {
        'title': 'Test Episode',
        'published': '2024-01-01',
        'description': 'Test description',
        'audio_file': str(temp_dir / 'test.mp3')
    }
    metadata_path = temp_dir / 'test.json'
    metadata_path.write_text(json.dumps(metadata, indent=2))
    return metadata_path


@pytest.fixture
def sample_transcript_content():
    """Sample transcript text for testing."""
    return """Welcome to this episode of Test Podcast.

Today we're discussing the book "Thinking Fast and Slow" by Daniel Kahneman.

Our guest today is Dr. Jane Smith from Harvard University.
You can find her on Twitter @drjanesmith.

We also recommend "The Psychology of Money" by Morgan Housel.

Thanks for listening!"""


@pytest.fixture
def sample_transcript_file(temp_dir, sample_transcript_content):
    """Create a sample transcript file."""
    transcript_path = temp_dir / "test_episode.txt"
    transcript_path.write_text(sample_transcript_content)
    return transcript_path
