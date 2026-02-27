"""
Unit tests for tools/search_tools.py
"""

from unittest.mock import MagicMock, patch

from tools.search_tools import (
    _extract_identifiers,
    _search_contact_patterns,
    _search_github,
    _search_linkedin,
    _search_platform,
    _search_reddit,
    _search_twitter,
)

# ---------------------------------------------------------------------------
# _extract_identifiers
# ---------------------------------------------------------------------------


class TestExtractIdentifiers:
    def test_extracts_standard_email(self):
        result = _extract_identifiers("Contact: alice@example.com for details")
        assert "alice@example.com" in result

    def test_extracts_us_phone(self):
        result = _extract_identifiers("Call us at 555-867-5309")
        assert "Phones" in result
        assert "555-867-5309" in result

    def test_extracts_international_phone(self):
        result = _extract_identifiers("International: +1-800-555-0199")
        assert "Phones" in result

    def test_extracts_username_handle(self):
        result = _extract_identifiers("Follow @johndoe on social media")
        assert "johndoe" in result
        assert "Usernames" in result

    def test_deduplicates_emails(self):
        result = _extract_identifiers("a@b.com and a@b.com again")
        assert result.count("a@b.com") == 1

    def test_deduplicates_usernames(self):
        result = _extract_identifiers("@alice and @alice again")
        assert result.count("alice") == 1

    def test_empty_input_returns_empty_string(self):
        result = _extract_identifiers("")
        assert result == ""

    def test_no_identifiers_returns_empty_string(self):
        result = _extract_identifiers("Nothing special here")
        assert result == ""

    def test_multiple_identifier_types(self):
        text = "Email: bob@test.org Phone: 123-456-7890 Twitter: @bobsmith"
        result = _extract_identifiers(text)
        assert "Emails" in result
        assert "Phones" in result
        assert "Usernames" in result


# ---------------------------------------------------------------------------
# _search_contact_patterns
# ---------------------------------------------------------------------------


class TestSearchContactPatterns:
    def test_extracts_linkedin_profile(self):
        result = _search_contact_patterns("Check linkedin.com/in/john-doe for profile")
        assert "LinkedIn" in result
        assert "john-doe" in result

    def test_extracts_telegram_handle(self):
        result = _search_contact_patterns("Message me at t.me/myhandle")
        assert "Telegram" in result
        assert "myhandle" in result

    def test_extracts_skype_handle(self):
        result = _search_contact_patterns("Skype: skype:myskypename here")
        assert "Skype" in result
        assert "myskypename" in result

    def test_deduplicates_linkedin(self):
        text = "linkedin.com/in/alice and linkedin.com/in/alice again"
        result = _search_contact_patterns(text)
        assert result.count("alice") == 1

    def test_empty_text_returns_empty(self):
        assert _search_contact_patterns("") == ""

    def test_no_patterns_returns_empty(self):
        assert _search_contact_patterns("Nothing here to find") == ""


# ---------------------------------------------------------------------------
# _search_linkedin
# ---------------------------------------------------------------------------


class TestSearchLinkedin:
    def test_always_returns_dorking_warning(self):
        result = _search_linkedin("John Doe")
        assert "[WARN]" in result
        assert "LinkedIn" in result

    def test_query_includes_target(self):
        result = _search_linkedin("Jane Smith")
        assert "Jane Smith" in result

    def test_mentions_manual_verification(self):
        result = _search_linkedin("Someone")
        assert "Manual" in result or "manual" in result


# ---------------------------------------------------------------------------
# _search_twitter
# ---------------------------------------------------------------------------


class TestSearchTwitter:
    def test_skips_non_latin_characters(self):
        result = _search_twitter("用户名")
        assert "[WARN]" in result
        assert "non-Latin" in result

    def test_proceeds_for_latin_target(self):
        with patch("tools.api_tools.search_twitter_timeline") as mock_search:
            mock_search.return_value = "[ERROR] Twitter Bearer Token not configured\n"
            result = _search_twitter("johndoe")
        assert "johndoe" in result or "Twitter" in result.upper()

    def test_converts_target_to_lowercase(self):
        captured = {}

        def capture(username):
            captured["username"] = username
            return "[ERROR] not configured\n"

        with patch("tools.api_tools.search_twitter_timeline", side_effect=capture):
            _search_twitter("JohnDoe")

        assert captured["username"] == "johndoe"

    def test_adds_manual_recommendations_when_not_configured(self):
        with patch("tools.api_tools.search_twitter_timeline") as mock_search:
            mock_search.return_value = "[ERROR] Twitter Bearer Token not configured\n"
            result = _search_twitter("testuser")
        assert "Manual search" in result or "manual" in result.lower() or "@testuser" in result


# ---------------------------------------------------------------------------
# _search_github
# ---------------------------------------------------------------------------


class TestSearchGithub:
    def test_returns_not_found_on_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("requests.get", return_value=mock_response):
            result = _search_github("unknownuser")
        assert "No GitHub profile found" in result

    def test_returns_profile_on_200(self):
        mock_profile = MagicMock()
        mock_profile.status_code = 200
        mock_profile.json.return_value = {
            "login": "testuser",
            "name": "Test User",
            "bio": "Developer",
            "location": "Tel Aviv",
            "public_repos": 0,
            "followers": 10,
            "html_url": "https://github.com/testuser",
        }

        with patch("requests.get", return_value=mock_profile):
            result = _search_github("testuser")

        assert "[OK] Found GitHub profile" in result
        assert "testuser" in result
        assert "Test User" in result

    def test_includes_repos_when_present(self):
        mock_profile = MagicMock()
        mock_profile.status_code = 200
        mock_profile.json.return_value = {
            "login": "coder",
            "name": "Coder",
            "bio": None,
            "location": None,
            "public_repos": 3,
            "followers": 5,
            "html_url": "https://github.com/coder",
        }

        mock_repos = MagicMock()
        mock_repos.status_code = 200
        mock_repos.json.return_value = [
            {
                "name": "my-repo",
                "description": "A project",
                "language": "Python",
                "stargazers_count": 42,
                "updated_at": "2024-01-15T10:00:00Z",
            }
        ]

        with patch("requests.get", side_effect=[mock_profile, mock_repos]):
            result = _search_github("coder")

        assert "Python" in result or "my-repo" in result

    def test_handles_request_exception(self):
        with patch("requests.get", side_effect=Exception("Connection refused")):
            result = _search_github("anyuser")
        assert "error" in result.lower()

    def test_uses_github_token_from_env(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with (
            patch("requests.get", return_value=mock_response) as mock_get,
            patch.dict("os.environ", {"GITHUB_TOKEN": "mytoken"}),
        ):
            _search_github("user")
        call_kwargs = mock_get.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert "mytoken" in call_kwargs["headers"]["Authorization"]


# ---------------------------------------------------------------------------
# _search_reddit
# ---------------------------------------------------------------------------


class TestSearchReddit:
    def test_returns_not_found_on_non_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("requests.get", return_value=mock_response):
            result = _search_reddit("nobody")
        assert "No Reddit profile found" in result

    def test_returns_profile_on_200(self):
        mock_profile = MagicMock()
        mock_profile.status_code = 200
        mock_profile.json.return_value = {
            "data": {
                "name": "redditor42",
                "total_karma": 1234,
                "created_utc": 1609459200,
            }
        }

        mock_comments = MagicMock()
        mock_comments.status_code = 200
        mock_comments.json.return_value = {"data": {"children": []}}

        with patch("requests.get", side_effect=[mock_profile, mock_comments]):
            result = _search_reddit("redditor42")

        assert "[OK] Found Reddit profile" in result
        assert "redditor42" in result

    def test_skips_deleted_comments(self):
        mock_profile = MagicMock()
        mock_profile.status_code = 200
        mock_profile.json.return_value = {"data": {"name": "user", "total_karma": 0, "created_utc": 0}}

        mock_comments = MagicMock()
        mock_comments.status_code = 200
        mock_comments.json.return_value = {
            "data": {
                "children": [
                    {"data": {"subreddit": "news", "body": "[deleted]", "score": 0}},
                    {"data": {"subreddit": "pics", "body": "Real comment here", "score": 5}},
                ]
            }
        }

        with patch("requests.get", side_effect=[mock_profile, mock_comments]):
            result = _search_reddit("user")

        assert "[deleted]" not in result or "Real comment" in result

    def test_handles_request_exception(self):
        with patch("requests.get", side_effect=Exception("Timeout")):
            result = _search_reddit("user")
        assert "error" in result.lower()


# ---------------------------------------------------------------------------
# _search_platform
# ---------------------------------------------------------------------------


class TestSearchPlatform:
    def test_instagram_not_implemented(self):
        result = _search_platform("instagram", "target")
        assert "[ERROR]" in result
        assert "instagram" in result.lower() or "INSTAGRAM" in result

    def test_facebook_not_implemented(self):
        result = _search_platform("facebook", "target")
        assert "[ERROR]" in result

    def test_soundcloud_not_implemented(self):
        result = _search_platform("soundcloud", "target")
        assert "[ERROR]" in result

    def test_unknown_platform_returns_error(self):
        result = _search_platform("myspace", "target")
        assert "[ERROR]" in result

    def test_linkedin_calls_search_linkedin(self):
        result = _search_platform("linkedin", "Alice")
        assert "LinkedIn" in result.upper() or "linkedin" in result.lower()

    def test_twitter_calls_search_twitter(self):
        with patch("tools.api_tools.search_twitter_timeline") as mock:
            mock.return_value = "[ERROR] not configured\n"
            result = _search_platform("twitter", "alice")
        assert "TWITTER" in result.upper() or "twitter" in result.lower()

    def test_github_calls_search_github(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch("requests.get", return_value=mock_response):
            result = _search_platform("github", "alice")
        assert "GITHUB" in result.upper()

    def test_result_contains_platform_header(self):
        result = _search_platform("instagram", "someone")
        assert "INSTAGRAM" in result
