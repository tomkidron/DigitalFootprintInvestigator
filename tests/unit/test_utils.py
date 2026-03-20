"""
Unit tests for utils/llm.py, utils/logger.py, utils/validation.py,
utils/cache.py, utils/retry.py, and utils/models.py
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from utils.llm import get_llm
from utils.logger import ProgressTracker, setup_logger

# ---------------------------------------------------------------------------
# get_llm
# ---------------------------------------------------------------------------


class TestGetLlm:
    def test_returns_chat_anthropic_instance(self):
        mock_llm = MagicMock()
        with patch("utils.llm.ChatAnthropic", return_value=mock_llm) as mock_cls:
            result = get_llm()
        assert result is mock_llm
        mock_cls.assert_called_once()

    def test_uses_env_model_when_set(self):
        with patch("utils.llm.ChatAnthropic") as mock_cls, patch.dict("os.environ", {"LLM_MODEL": "claude-opus-4-6"}):
            get_llm()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "claude-opus-4-6"

    def test_defaults_to_claude_sonnet_when_env_unset(self):
        env_without_model = {k: v for k, v in os.environ.items() if k != "LLM_MODEL"}
        with patch("utils.llm.ChatAnthropic") as mock_cls, patch.dict("os.environ", env_without_model, clear=True):
            get_llm()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-6"

    def test_uses_temperature_zero(self):
        with patch("utils.llm.ChatAnthropic") as mock_cls:
            get_llm()
        call_kwargs = mock_cls.call_args[1]
        assert call_kwargs["temperature"] == 0


# ---------------------------------------------------------------------------
# ProgressTracker
# ---------------------------------------------------------------------------


class TestProgressTracker:
    def _make_tracker(self):
        logger = logging.getLogger("test_progress")
        logger.setLevel(logging.DEBUG)
        return ProgressTracker(logger)

    def test_set_stages_stores_stages(self):
        tracker = self._make_tracker()
        tracker.set_stages(["Alpha", "Beta", "Gamma"])
        assert tracker.stages == ["Alpha", "Beta", "Gamma"]

    def test_set_stages_resets_current_stage(self):
        tracker = self._make_tracker()
        tracker.set_stages(["A"])
        tracker.current_stage = 5
        tracker.set_stages(["X", "Y"])
        assert tracker.current_stage == 0

    def test_start_stage_increments_counter(self):
        tracker = self._make_tracker()
        tracker.set_stages(["Step 1", "Step 2"])
        tracker.start_stage("Step 1")
        assert tracker.current_stage == 1

    def test_complete_stage_logs_ok(self, caplog):
        tracker = self._make_tracker()
        tracker.set_stages(["Step 1"])
        with caplog.at_level(logging.INFO, logger="test_progress"):
            tracker.complete_stage("Step 1")
        assert "[OK]" in caplog.text

    def test_complete_stage_includes_details(self, caplog):
        tracker = self._make_tracker()
        tracker.set_stages(["Step 1"])
        with caplog.at_level(logging.INFO, logger="test_progress"):
            tracker.complete_stage("Step 1", details="3 results")
        assert "3 results" in caplog.text

    def test_log_finding_logs_category_and_finding(self, caplog):
        tracker = self._make_tracker()
        with caplog.at_level(logging.INFO, logger="test_progress"):
            tracker.log_finding("Email", "alice@example.com")
        assert "Email" in caplog.text
        assert "alice@example.com" in caplog.text


# ---------------------------------------------------------------------------
# setup_logger
# ---------------------------------------------------------------------------


class TestSetupLogger:
    def test_returns_logger_instance(self, tmp_path):
        logger = setup_logger("test_logger_instance", log_dir=str(tmp_path))
        assert isinstance(logger, logging.Logger)

    def test_creates_log_directory(self, tmp_path):
        log_dir = str(tmp_path / "sublogs")
        setup_logger("test_mkdir", log_dir=log_dir)
        assert os.path.isdir(log_dir)

    def test_does_not_add_duplicate_handlers(self, tmp_path):
        logger = setup_logger("test_dedup", log_dir=str(tmp_path))
        initial_count = len(logger.handlers)
        logger2 = setup_logger("test_dedup", log_dir=str(tmp_path))
        assert len(logger2.handlers) == initial_count

    def test_log_level_from_env(self, tmp_path):
        with patch.dict("os.environ", {"LOG_LEVEL": "DEBUG"}):
            logger = setup_logger("test_level_debug", log_dir=str(tmp_path))
        assert logger.level == logging.DEBUG

    def test_default_log_level_is_info(self, tmp_path):
        env_without_level = {k: v for k, v in os.environ.items() if k != "LOG_LEVEL"}
        with patch.dict("os.environ", env_without_level, clear=True):
            logger = setup_logger("test_level_default", log_dir=str(tmp_path))
        assert logger.level == logging.INFO

    def test_uses_provided_name(self, tmp_path):
        logger = setup_logger("my_custom_name", log_dir=str(tmp_path))
        assert logger.name == "my_custom_name"


# ---------------------------------------------------------------------------
# utils/validation.py
# ---------------------------------------------------------------------------


class TestIsValidEmail:
    def test_valid_email(self):
        from utils.validation import is_valid_email

        assert is_valid_email("alice@example.com") is True

    def test_valid_email_with_subdomain(self):
        from utils.validation import is_valid_email

        assert is_valid_email("user@mail.example.co.uk") is True

    def test_invalid_missing_at(self):
        from utils.validation import is_valid_email

        assert is_valid_email("notanemail.com") is False

    def test_invalid_missing_domain(self):
        from utils.validation import is_valid_email

        assert is_valid_email("user@") is False

    def test_invalid_empty_string(self):
        from utils.validation import is_valid_email

        assert is_valid_email("") is False

    def test_invalid_spaces(self):
        from utils.validation import is_valid_email

        assert is_valid_email("user @example.com") is False


class TestIsValidUsername:
    def test_valid_simple(self):
        from utils.validation import is_valid_username

        assert is_valid_username("johndoe") is True

    def test_valid_with_at_prefix(self):
        from utils.validation import is_valid_username

        assert is_valid_username("@johndoe") is True

    def test_valid_with_numbers_and_underscore(self):
        from utils.validation import is_valid_username

        assert is_valid_username("john_doe_42") is True

    def test_invalid_with_spaces(self):
        from utils.validation import is_valid_username

        assert is_valid_username("john doe") is False

    def test_invalid_too_long(self):
        from utils.validation import is_valid_username

        assert is_valid_username("a" * 31) is False

    def test_invalid_special_chars(self):
        from utils.validation import is_valid_username

        assert is_valid_username("john-doe") is False


class TestSanitizeTarget:
    def test_strips_whitespace(self):
        from utils.validation import sanitize_target

        assert sanitize_target("  John Doe  ") == "john doe"

    def test_lowercases(self):
        from utils.validation import sanitize_target

        assert sanitize_target("JOHN DOE") == "john doe"

    def test_already_clean(self):
        from utils.validation import sanitize_target

        assert sanitize_target("john doe") == "john doe"


class TestDetectTargetType:
    def test_detects_email(self):
        from utils.validation import detect_target_type

        assert detect_target_type("alice@example.com") == "email"

    def test_detects_username_with_at(self):
        from utils.validation import detect_target_type

        assert detect_target_type("@johndoe") == "username"

    def test_detects_username_without_at(self):
        from utils.validation import detect_target_type

        assert detect_target_type("johndoe") == "username"

    def test_detects_name_with_space(self):
        from utils.validation import detect_target_type

        assert detect_target_type("John Doe") == "name"

    def test_single_word_is_username(self):
        from utils.validation import detect_target_type

        assert detect_target_type("johndoe") == "username"


# ---------------------------------------------------------------------------
# utils/cache.py
# ---------------------------------------------------------------------------


class TestCached:
    def test_caches_result_on_second_call(self, tmp_path):
        from utils.cache import cached

        call_count = {"n": 0}

        @cached(ttl=3600)
        def expensive(x):
            call_count["n"] += 1
            return x * 2

        with patch("utils.cache.CACHE_DIR", tmp_path):
            expensive("hello")
            expensive("hello")

        assert call_count["n"] == 1

    def test_different_args_not_shared(self, tmp_path):
        from utils.cache import cached

        @cached(ttl=3600)
        def fn(x):
            return x

        with patch("utils.cache.CACHE_DIR", tmp_path):
            assert fn("a") == "a"
            assert fn("b") == "b"

    def test_expired_cache_calls_function_again(self, tmp_path):
        from utils.cache import cached

        call_count = {"n": 0}

        @cached(ttl=1)
        def fn(x):
            call_count["n"] += 1
            return x

        with patch("utils.cache.CACHE_DIR", tmp_path):
            fn("x")
            key_data = "fn:('x',):{}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            cache_file = tmp_path / f"{cache_key}.json"
            cache_file.write_text(json.dumps({"timestamp": time.time() - 10, "result": "x"}))
            fn("x")

        assert call_count["n"] == 2

    def test_returns_cached_value(self, tmp_path):
        from utils.cache import cached

        @cached(ttl=3600)
        def fn(x):
            return x + "_result"

        with patch("utils.cache.CACHE_DIR", tmp_path):
            result = fn("test")
        assert result == "test_result"


# ---------------------------------------------------------------------------
# utils/retry.py
# ---------------------------------------------------------------------------


class TestRetry:
    def test_returns_on_first_success(self):
        from utils.retry import retry

        call_count = {"n": 0}

        @retry(max_attempts=3, delay=0)
        def fn():
            call_count["n"] += 1
            return "ok"

        assert fn() == "ok"
        assert call_count["n"] == 1

    def test_retries_on_failure_then_succeeds(self):
        from utils.retry import retry

        call_count = {"n": 0}

        @retry(max_attempts=3, delay=0)
        def fn():
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("fail")
            return "ok"

        with patch("time.sleep"):
            result = fn()
        assert result == "ok"
        assert call_count["n"] == 3

    def test_raises_after_max_attempts(self):
        from utils.retry import retry

        @retry(max_attempts=3, delay=0)
        def fn():
            raise RuntimeError("always fails")

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="always fails"):
                fn()

    def test_exponential_backoff_delays(self):
        from utils.retry import retry

        delays = []

        @retry(max_attempts=3, delay=1, backoff=2)
        def fn():
            raise ValueError("fail")

        with patch("time.sleep", side_effect=lambda d: delays.append(d)):
            with pytest.raises(ValueError):
                fn()

        assert delays == [1, 2]

    def test_preserves_function_name(self):
        from utils.retry import retry

        @retry(max_attempts=2, delay=0)
        def my_function():
            pass

        assert my_function.__name__ == "my_function"


# ---------------------------------------------------------------------------
# utils/models.py
# ---------------------------------------------------------------------------


class TestSocialProfile:
    def test_required_fields(self):
        from utils.models import SocialProfile

        p = SocialProfile(platform="github", username="johndoe", url="https://github.com/johndoe")
        assert p.platform == "github"
        assert p.username == "johndoe"

    def test_optional_fields_default_to_none(self):
        from utils.models import SocialProfile

        p = SocialProfile(platform="x", username="u", url="https://x.com/u")
        assert p.followers is None
        assert p.bio is None
        assert p.verified is False

    def test_verified_can_be_set(self):
        from utils.models import SocialProfile

        p = SocialProfile(platform="x", username="u", url="https://x.com/u", verified=True)
        assert p.verified is True


class TestSearchResult:
    def test_defaults_source_to_google(self):
        from utils.models import SearchResult

        r = SearchResult(title="T", url="https://example.com", snippet="S")
        assert r.source == "google"

    def test_custom_source(self):
        from utils.models import SearchResult

        r = SearchResult(title="T", url="https://example.com", snippet="S", source="bing")
        assert r.source == "bing"


class TestEmailData:
    def test_defaults(self):
        from utils.models import EmailData

        e = EmailData(email="a@b.com", source="hunter")
        assert e.verified is False
        assert e.breached is False
        assert e.breach_count == 0

    def test_breach_fields(self):
        from utils.models import EmailData

        e = EmailData(email="a@b.com", source="hibp", breached=True, breach_count=3)
        assert e.breached is True
        assert e.breach_count == 3


class TestOSINTResult:
    def test_defaults_to_empty_lists(self):
        from utils.models import OSINTResult

        r = OSINTResult(target="John Doe", target_type="name")
        assert r.profiles == []
        assert r.emails == []
        assert r.search_results == []

    def test_timestamp_auto_set(self):
        from utils.models import OSINTResult

        r = OSINTResult(target="John Doe", target_type="name")
        assert isinstance(r.timestamp, datetime)
