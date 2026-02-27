"""
Unit tests for tools/api_tools.py
"""

from unittest.mock import MagicMock, patch

from tools.api_tools import (
    discover_emails_from_text,
    search_hibp_breaches,
    search_hunter_emails,
    search_twitter_timeline,
    search_youtube_channel,
)

# ---------------------------------------------------------------------------
# search_hibp_breaches
# ---------------------------------------------------------------------------


class TestSearchHibpBreaches:
    def test_returns_error_when_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_hibp_breaches("user@example.com")
        assert "[ERROR]" in result
        assert "HIBP" in result

    def test_returns_ok_on_404(self):
        mock_response = MagicMock()
        mock_response.status_code = 404
        with (
            patch("requests.get", return_value=mock_response),
            patch.dict("os.environ", {"HIBP_API_KEY": "testkey"}),
        ):  # pragma: allowlist secret
            result = search_hibp_breaches("clean@example.com")
        assert "[OK]" in result
        assert "No breaches" in result

    def test_returns_breach_list_on_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"Name": "Adobe", "BreachDate": "2013-10-04"},
            {"Name": "LinkedIn", "BreachDate": "2016-05-05"},
        ]
        with (
            patch("requests.get", return_value=mock_response),
            patch.dict("os.environ", {"HIBP_API_KEY": "testkey"}),
        ):  # pragma: allowlist secret
            result = search_hibp_breaches("pwned@example.com")
        assert "[WARN]" in result
        assert "Adobe" in result
        assert "LinkedIn" in result

    def test_limits_to_5_breaches(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"Name": f"Site{i}", "BreachDate": "2020-01-01"} for i in range(10)]
        with (
            patch("requests.get", return_value=mock_response),
            patch.dict("os.environ", {"HIBP_API_KEY": "testkey"}),
        ):  # pragma: allowlist secret
            result = search_hibp_breaches("many@breaches.com")
        # Should show at most 5
        assert result.count("Site") <= 5

    def test_returns_error_on_other_status(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        with (
            patch("requests.get", return_value=mock_response),
            patch.dict("os.environ", {"HIBP_API_KEY": "badkey"}),  # pragma: allowlist secret
        ):
            result = search_hibp_breaches("user@example.com")
        assert "[ERROR]" in result

    def test_handles_request_exception(self):
        with (
            patch("requests.get", side_effect=Exception("Timeout")),
            patch.dict("os.environ", {"HIBP_API_KEY": "testkey"}),  # pragma: allowlist secret
        ):
            result = search_hibp_breaches("user@example.com")
        assert "[ERROR]" in result


# ---------------------------------------------------------------------------
# search_hunter_emails
# ---------------------------------------------------------------------------


class TestSearchHunterEmails:
    def test_returns_error_when_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_hunter_emails("example.com", "John Doe")
        assert "[ERROR]" in result
        assert "Hunter" in result

    def test_returns_matches_on_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "emails": [
                    {"value": "john.doe@example.com"},
                    {"value": "jane.smith@example.com"},
                ],
                "pattern": "{first}.{last}",
            }
        }
        with patch("requests.get", return_value=mock_response), patch.dict("os.environ", {"HUNTER_API_KEY": "testkey"}):
            result = search_hunter_emails("example.com", "John Doe")
        assert "[OK]" in result
        assert "john.doe@example.com" in result

    def test_reports_no_matches_when_none_found(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "emails": [{"value": "other.person@example.com"}],
                "pattern": "{first}.{last}",
            }
        }
        with patch("requests.get", return_value=mock_response), patch.dict("os.environ", {"HUNTER_API_KEY": "testkey"}):
            result = search_hunter_emails("example.com", "John Doe")
        assert "[ERROR]" in result or "No matches" in result

    def test_returns_error_on_non_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        with patch("requests.get", return_value=mock_response), patch.dict("os.environ", {"HUNTER_API_KEY": "testkey"}):
            result = search_hunter_emails("example.com", "John Doe")
        assert "[ERROR]" in result

    def test_handles_request_exception(self):
        with (
            patch("requests.get", side_effect=Exception("Connection error")),
            patch.dict("os.environ", {"HUNTER_API_KEY": "testkey"}),
        ):
            result = search_hunter_emails("example.com", "John Doe")
        assert "[ERROR]" in result


# ---------------------------------------------------------------------------
# discover_emails_from_text
# ---------------------------------------------------------------------------


class TestDiscoverEmailsFromText:
    def test_finds_matching_email(self):
        text = "Contact john.doe@example.com for info"
        result = discover_emails_from_text(text, "john doe")
        assert "john.doe@example.com" in result

    def test_ignores_non_matching_emails(self):
        text = "Contact admin@example.com for info"
        result = discover_emails_from_text(text, "john doe")
        assert result == []

    def test_deduplicates_emails(self):
        text = "john@example.com and john@example.com again"
        result = discover_emails_from_text(text, "john")
        assert len(result) == 1

    def test_empty_text_returns_empty_list(self):
        result = discover_emails_from_text("", "john")
        assert result == []

    def test_returns_list_type(self):
        result = discover_emails_from_text("no emails here", "john")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# search_youtube_channel
# ---------------------------------------------------------------------------


class TestSearchYoutubeChannel:
    def test_returns_error_when_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_youtube_channel("testchannel")
        assert "[ERROR]" in result
        assert "YouTube" in result or "API" in result

    def test_returns_error_when_googleapiclient_missing(self):
        with (
            patch.dict("os.environ", {"YOUTUBE_API_KEY": "testkey"}),
            patch("builtins.__import__", side_effect=ImportError("No module")),
        ):
            result = search_youtube_channel("testchannel")
        assert "[ERROR]" in result

    def test_returns_not_found_when_no_channels(self):
        mock_youtube = MagicMock()
        mock_youtube.search().list().execute.return_value = {"items": []}

        with (
            patch.dict("os.environ", {"YOUTUBE_API_KEY": "testkey"}),
            patch("googleapiclient.discovery.build", return_value=mock_youtube),
        ):
            result = search_youtube_channel("nobody")
        assert "[ERROR]" in result
        assert "No YouTube channels" in result

    def test_returns_channel_info_on_success(self):
        mock_youtube = MagicMock()
        mock_youtube.search().list().execute.return_value = {
            "items": [
                {
                    "id": {"channelId": "UC123"},
                    "snippet": {
                        "title": "Test Channel",
                        "description": "A test channel for testing",
                    },
                }
            ]
        }
        mock_youtube.channels().list().execute.return_value = {
            "items": [
                {
                    "statistics": {
                        "subscriberCount": "1000",
                        "videoCount": "50",
                        "viewCount": "50000",
                    }
                }
            ]
        }

        with (
            patch.dict("os.environ", {"YOUTUBE_API_KEY": "testkey"}),
            patch("googleapiclient.discovery.build", return_value=mock_youtube),
        ):
            result = search_youtube_channel("testchannel")

        assert "[OK]" in result
        assert "Test Channel" in result


# ---------------------------------------------------------------------------
# search_twitter_timeline
# ---------------------------------------------------------------------------


class TestSearchTwitterTimeline:
    def test_returns_error_when_token_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_twitter_timeline("testuser")
        assert "[ERROR]" in result
        assert "Twitter" in result or "Bearer" in result

    def test_returns_error_when_tweepy_missing(self):
        import sys

        original = sys.modules.get("tweepy")
        sys.modules["tweepy"] = None  # Simulate ImportError on import
        try:
            # We need to reload the function without the module
            with patch.dict("os.environ", {"TWITTER_BEARER_TOKEN": "testtoken"}):
                with patch("builtins.__import__", side_effect=ImportError("No tweepy")):
                    result = search_twitter_timeline("testuser")
            assert "[ERROR]" in result
        finally:
            if original is None:
                sys.modules.pop("tweepy", None)
            else:
                sys.modules["tweepy"] = original

    def test_returns_not_found_when_user_missing(self):
        mock_client = MagicMock()
        mock_user_response = MagicMock()
        mock_user_response.data = None
        mock_client.get_user.return_value = mock_user_response

        mock_tweepy = MagicMock()
        mock_tweepy.Client.return_value = mock_client

        import sys

        with (
            patch.dict("os.environ", {"TWITTER_BEARER_TOKEN": "testtoken"}),
            patch.dict(sys.modules, {"tweepy": mock_tweepy}),
        ):
            result = search_twitter_timeline("nobody")

        assert "[ERROR]" in result
        assert "not found" in result

    def test_returns_profile_when_user_found(self):
        mock_user_data = MagicMock()
        mock_user_data.id = "123"
        mock_user_data.username = "testuser"
        mock_user_data.name = "Test User"
        mock_user_data.description = "A test user"
        mock_user_data.public_metrics = {
            "followers_count": 100,
            "following_count": 50,
            "tweet_count": 200,
        }

        mock_client = MagicMock()
        mock_client.get_user.return_value = MagicMock(data=mock_user_data)
        mock_client.get_users_tweets.return_value = MagicMock(data=None)

        mock_tweepy = MagicMock()
        mock_tweepy.Client.return_value = mock_client

        import sys

        with (
            patch.dict("os.environ", {"TWITTER_BEARER_TOKEN": "testtoken"}),
            patch.dict(sys.modules, {"tweepy": mock_tweepy}),
        ):
            result = search_twitter_timeline("testuser")

        assert "[OK]" in result
        assert "testuser" in result
        assert "Test User" in result
