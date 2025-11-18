"""
Unit tests for refactored extraction package.

Tests cover:
- Episode detection (non-guest episodes)
- Name cleaning and normalization
- Twitter handle extraction
- Title-based guest extraction
- Description-based guest extraction
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from extraction.episode_detector import is_non_guest_episode
from extraction.name_cleaner import clean_guest_name
from extraction.twitter_finder import extract_twitter_handles
from extraction.title_extractor import extract_guest_from_title
from extraction.description_extractor import extract_guest_from_description


class TestIsNonGuestEpisode:
    """Tests for is_non_guest_episode function."""

    def test_compilation_episode(self):
        """GIVEN compilation title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Best of 2023", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "compilation"

    def test_highlights_episode(self):
        """GIVEN highlights title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Season 5 Highlights", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "compilation"

    def test_ama_episode(self):
        """GIVEN AMA title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "AMA: Your Questions Answered", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "ama/q&a"

    def test_qa_episode(self):
        """GIVEN Q&A title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Q&A Special", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "ama/q&a"

    def test_trailer_episode(self):
        """GIVEN trailer title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Season 3 Preview",
            "New season coming soon!",
            "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "trailer/announcement"

    def test_cross_promotion(self):
        """GIVEN cross-promotion title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Introducing: New Show", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "cross_promotion"

    def test_rerelease(self):
        """GIVEN rerelease title WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Episode 50 (Rerelease)", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "rerelease"

    def test_sponsored_content(self):
        """GIVEN sponsored content WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Sponsored Content: Product Review", "", "Test Podcast"
        )
        assert is_non_guest is True
        assert episode_type == "sponsored"

    def test_normal_episode(self):
        """GIVEN normal episode WHEN checking THEN returns False."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Episode 100: Interview with Guest", "", "Test Podcast"
        )
        assert is_non_guest is False
        assert episode_type is None

    def test_odd_lots_roundup(self):
        """GIVEN Odd Lots roundup WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Lots More on Market Volatility",
            "",
            "Odd Lots"
        )
        assert is_non_guest is True
        assert episode_type == "roundup"

    def test_chapo_special_series(self):
        """GIVEN Chapo special series WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Movie Mindset: Die Hard",
            "",
            "Chapo Trap House"
        )
        assert is_non_guest is True
        assert episode_type == "special_series"

    def test_trueanon_tip_line(self):
        """GIVEN TRUE ANON tip line WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Tip Line Episode",
            "",
            "TRUE ANON TRUTH FEED"
        )
        assert is_non_guest is True
        assert episode_type == "tip_line"

    def test_sad_boyz_solo(self):
        """GIVEN Sad Boyz solo episode WHEN checking THEN detects non-guest."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Episode 50: Just Us",
            "Jarvis and Jordan discuss life",
            "Sad Boyz"
        )
        assert is_non_guest is True
        assert episode_type == "solo_hosts"

    def test_sad_boyz_with_guest(self):
        """GIVEN Sad Boyz with guest WHEN checking THEN returns False."""
        is_non_guest, episode_type = is_non_guest_episode(
            "Episode 50 (w/ Guest Name)",
            "",
            "Sad Boyz"
        )
        assert is_non_guest is False


class TestCleanGuestName:
    """Tests for clean_guest_name function."""

    def test_removes_with_prefix(self):
        """GIVEN name with 'with' prefix WHEN cleaning THEN removes it."""
        result = clean_guest_name("with John Smith")
        assert result == "John Smith"

    def test_removes_featuring_prefix(self):
        """GIVEN name with 'featuring' WHEN cleaning THEN removes it."""
        result = clean_guest_name("featuring Jane Doe")
        assert result == "Jane Doe"

    def test_removes_ft_prefix(self):
        """GIVEN name with 'ft.' WHEN cleaning THEN removes it."""
        result = clean_guest_name("ft. Bob Jones")
        assert result == "Bob Jones"

    def test_removes_parenthetical(self):
        """GIVEN name with parentheses WHEN cleaning THEN removes them."""
        result = clean_guest_name("John Smith (Author)")
        assert result == "John Smith"

    def test_removes_trailing_returns(self):
        """GIVEN name with 'returns' WHEN cleaning THEN removes it."""
        result = clean_guest_name("John Smith returns")
        assert result == "John Smith"

    def test_removes_part_number(self):
        """GIVEN name with part number WHEN cleaning THEN removes it."""
        result = clean_guest_name("Jane Doe Part 2")
        assert result == "Jane Doe"

    def test_removes_trailing_discuss(self):
        """GIVEN trailing 'to discuss' WHEN cleaning THEN removes it."""
        result = clean_guest_name("John Smith to discuss")
        assert result == "John Smith"

    def test_removes_job_title_prefix(self):
        """GIVEN name with job title WHEN cleaning THEN removes title."""
        result = clean_guest_name("Author Jane Doe")
        assert result == "Jane Doe"

    def test_extracts_from_ceo_pattern(self):
        """GIVEN 'Company CEO Name' WHEN cleaning THEN extracts name."""
        result = clean_guest_name("Mercury Group CEO Anton Posner")
        assert result == "Anton Posner"

    def test_extracts_from_fed_president(self):
        """GIVEN Fed President pattern WHEN cleaning THEN extracts name."""
        result = clean_guest_name("Chicago Fed President Austan Goolsbee")
        assert result == "Austan Goolsbee"

    def test_returns_none_for_empty(self):
        """GIVEN empty string WHEN cleaning THEN returns None."""
        result = clean_guest_name("")
        assert result is None

    def test_returns_none_for_short(self):
        """GIVEN name < 3 chars WHEN cleaning THEN returns None."""
        result = clean_guest_name("Jo")
        assert result is None

    def test_returns_none_for_podcast_term(self):
        """GIVEN generic term WHEN cleaning THEN returns None."""
        result = clean_guest_name("Special Podcast Episode")
        assert result is None

    def test_returns_none_for_question_word(self):
        """GIVEN question word start WHEN cleaning THEN returns None."""
        result = clean_guest_name("How to Win Friends")
        assert result is None

    def test_returns_none_for_article_start(self):
        """GIVEN article start WHEN cleaning THEN returns None."""
        result = clean_guest_name("The Best Guest")
        assert result is None

    def test_returns_none_for_vs(self):
        """GIVEN ' vs ' in name WHEN cleaning THEN returns None."""
        result = clean_guest_name("Team A vs Team B")
        assert result is None

    def test_returns_none_for_digit_start(self):
        """GIVEN digit start WHEN cleaning THEN returns None."""
        result = clean_guest_name("10 Best Guests")
        assert result is None

    def test_normalizes_whitespace(self):
        """GIVEN extra whitespace WHEN cleaning THEN normalizes."""
        result = clean_guest_name("John   Smith")
        assert result == "John Smith"


class TestExtractTwitterHandles:
    """Tests for extract_twitter_handles function."""

    def test_extracts_single_handle(self):
        """GIVEN single handle WHEN extracting THEN returns it."""
        result = extract_twitter_handles("Follow @johndoe")
        assert result == ["johndoe"]

    def test_extracts_multiple_handles(self):
        """GIVEN multiple handles WHEN extracting THEN returns all."""
        result = extract_twitter_handles("@user1 and @user2")
        assert result == ["user1", "user2"]

    def test_filters_email_domains(self):
        """GIVEN email domains WHEN extracting THEN filters them."""
        result = extract_twitter_handles("@gmail @googlemail email")
        assert result == []

    def test_filters_platform_names(self):
        """GIVEN platform names WHEN extracting THEN filters them."""
        result = extract_twitter_handles("@twitter @instagram @facebook")
        assert result == []

    def test_filters_numeric_handles(self):
        """GIVEN numeric handles WHEN extracting THEN filters them."""
        result = extract_twitter_handles("@123456")
        assert result == []

    def test_respects_handle_length(self):
        """GIVEN valid length handles WHEN extracting THEN accepts."""
        result = extract_twitter_handles("@a @validhandle123")
        assert "a" in result
        assert "validhandle123" in result

    def test_handles_underscores(self):
        """GIVEN handle with underscore WHEN extracting THEN accepts."""
        result = extract_twitter_handles("@john_doe")
        assert result == ["john_doe"]

    def test_empty_string(self):
        """GIVEN empty string WHEN extracting THEN returns empty list."""
        result = extract_twitter_handles("")
        assert result == []

    def test_no_handles(self):
        """GIVEN text without handles WHEN extracting THEN returns empty."""
        result = extract_twitter_handles("No handles here")
        assert result == []


class TestExtractGuestFromTitle:
    """Tests for extract_guest_from_title function."""

    def test_adam_buxton_format(self):
        """GIVEN Adam Buxton title format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "EP.198 - JOE CORNISH",
            "THE ADAM BUXTON PODCAST"
        )
        assert result == "Joe Cornish"

    def test_rhlstp_format(self):
        """GIVEN RHLSTP title format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "RHLSTP 587 - David Mitchell",
            "RHLSTP with Richard Herring"
        )
        assert result == "David Mitchell"

    def test_grounded_format(self):
        """GIVEN Grounded title format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "18. Olivia Colman",
            "Grounded with Louis Theroux"
        )
        assert result == "Olivia Colman"

    def test_chapo_feat_format(self):
        """GIVEN Chapo feat. format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "Episode 500 feat. Nathan Robinson",
            "Chapo Trap House"
        )
        assert result == "Nathan Robinson"

    def test_chapo_skips_hosts(self):
        """GIVEN Chapo host name WHEN extracting THEN returns None."""
        result = extract_guest_from_title(
            "Episode 500 feat. Felix",
            "Chapo Trap House"
        )
        assert result is None

    def test_odd_lots_on_format(self):
        """GIVEN Odd Lots 'on' format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "David Woo on Market Volatility",
            "Odd Lots"
        )
        assert result == "David Woo"

    def test_odd_lots_with_format(self):
        """GIVEN Odd Lots 'with' format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "Lots More With Claudia Sahm on Inflation",
            "Odd Lots"
        )
        assert result == "Claudia Sahm"

    def test_generic_ft_format(self):
        """GIVEN generic 'ft.' format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "Episode 50 ft. Guest Name",
            "Random Podcast"
        )
        assert result == "Guest Name"

    def test_generic_w_format(self):
        """GIVEN generic '(w/ )' format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "Episode 50 (w/ Guest Name)",
            "Random Podcast"
        )
        assert result == "Guest Name"

    def test_no_guest_found(self):
        """GIVEN no guest pattern WHEN extracting THEN returns None."""
        result = extract_guest_from_title(
            "Episode 50",
            "Random Podcast"
        )
        assert result is None

    def test_citarella_doomscroll(self):
        """GIVEN Citarella Doomscroll format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "Doomscroll 31.5: Anna Khachiyan",
            "Joshua Citarella"
        )
        assert result == "Anna Khachiyan"

    def test_friedland_talks_format(self):
        """GIVEN Friedland 'Talks' format WHEN extracting THEN gets guest."""
        result = extract_guest_from_title(
            "NICK MULLEN Talks Comedy",
            "The Adam Friedland Show Podcast"
        )
        assert result == "Nick Mullen"


class TestExtractGuestFromDescription:
    """Tests for extract_guest_from_description function."""

    def test_adam_buxton_talks_with(self):
        """GIVEN Adam Buxton 'talks with' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "Adam talks with British comedian Joe Wilkinson about life",
            "THE ADAM BUXTON PODCAST"
        )
        assert "Joe Wilkinson" in result

    def test_adam_buxton_old_friend(self):
        """GIVEN Adam Buxton 'old friend' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "Adam talks with old friend Joe Cornish about movies",
            "THE ADAM BUXTON PODCAST"
        )
        assert "Joe Cornish" in result

    def test_adam_and_joe_episode(self):
        """GIVEN Adam and Joe episode WHEN extracting THEN returns Joe."""
        result = extract_guest_from_description(
            "Adam and Joe return for a special episode",
            "THE ADAM BUXTON PODCAST"
        )
        assert result == "Joe Cornish"

    def test_louis_theroux_sits_down(self):
        """GIVEN Louis 'sits down with' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "Louis sits down with actor Tom Hanks,",
            "The Louis Theroux Podcast"
        )
        assert "Tom Hanks" in result

    def test_rhlstp_his_guest_is(self):
        """GIVEN RHLSTP 'His guest is' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "His guest is comedian Sarah Millican.",
            "RHLSTP with Richard Herring"
        )
        assert "Sarah Millican" in result

    def test_odd_lots_speak_with(self):
        """GIVEN Odd Lots 'speak with' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "we speak with Joe Weisenthal, a Bloomberg host",
            "Odd Lots"
        )
        assert "Joe Weisenthal" in result

    def test_chapo_joined_by(self):
        """GIVEN Chapo 'joined by' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "We're joined by author Nathan Robinson to discuss",
            "Chapo Trap House"
        )
        assert "Nathan Robinson" in result

    def test_trueanon_talk_to(self):
        """GIVEN TRUE ANON 'talk to' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "We talk to journalist Jane Doe about the story",
            "TRUE ANON TRUTH FEED"
        )
        assert "Jane Doe" in result

    def test_citarella_my_guest_is(self):
        """GIVEN Citarella 'My guest is' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "My guest is Anna Khachiyan, a co-host of",
            "Joshua Citarella"
        )
        assert result == "Anna Khachiyan"

    def test_universal_interview_with(self):
        """GIVEN universal 'interview with' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "An interview with John Smith about his new book",
            "Random Podcast"
        )
        assert "John Smith" in result

    def test_universal_joins(self):
        """GIVEN universal 'joins' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "Jane Doe joins us to discuss her work",
            "Random Podcast"
        )
        assert "Jane Doe" in result

    def test_empty_description(self):
        """GIVEN empty description WHEN extracting THEN returns None."""
        result = extract_guest_from_description("", "Test Podcast")
        assert result is None

    def test_no_pattern_match(self):
        """GIVEN no matching pattern WHEN extracting THEN returns None."""
        result = extract_guest_from_description(
            "This episode covers various topics",
            "Test Podcast"
        )
        assert result is None

    def test_removes_html_tags(self):
        """GIVEN HTML tags WHEN extracting THEN removes them first."""
        result = extract_guest_from_description(
            "<p>Adam talks with <b>Joe Cornish</b> about films</p>",
            "THE ADAM BUXTON PODCAST"
        )
        assert "Joe Cornish" in result

    def test_trueanon_welcome_back(self):
        """GIVEN TRUE ANON 'welcome back' WHEN extracting THEN gets guest."""
        result = extract_guest_from_description(
            "We welcome back journalist Corey Pein to discuss",
            "TRUE ANON TRUTH FEED"
        )
        assert "Corey Pein" in result


class TestModuleImports:
    """Tests to verify all extraction module imports work correctly."""

    def test_can_import_extraction_package(self):
        """GIVEN extraction package WHEN importing THEN succeeds."""
        from extraction import (
            is_non_guest_episode,
            clean_guest_name,
            extract_twitter_handles,
            extract_guest_from_title,
            extract_guest_from_description,
            extract_guests_with_twitter,
        )
        assert callable(is_non_guest_episode)
        assert callable(clean_guest_name)
        assert callable(extract_twitter_handles)
        assert callable(extract_guest_from_title)
        assert callable(extract_guest_from_description)
        assert callable(extract_guests_with_twitter)

    def test_package_exports_all(self):
        """GIVEN extraction package WHEN checking __all__ THEN exports key items."""
        from extraction import __all__
        assert 'is_non_guest_episode' in __all__
        assert 'clean_guest_name' in __all__
        assert 'extract_twitter_handles' in __all__
        assert 'extract_guest_from_title' in __all__
        assert 'extract_guest_from_description' in __all__
        assert 'extract_guests_with_twitter' in __all__
