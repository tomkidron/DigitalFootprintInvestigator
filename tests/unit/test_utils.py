"""
Unit tests for utils/llm.py and utils/logger.py
"""

import logging
from unittest.mock import MagicMock, patch

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
        import os

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
        import os

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
        import os

        env_without_level = {k: v for k, v in os.environ.items() if k != "LOG_LEVEL"}
        with patch.dict("os.environ", env_without_level, clear=True):
            logger = setup_logger("test_level_default", log_dir=str(tmp_path))
        assert logger.level == logging.INFO

    def test_uses_provided_name(self, tmp_path):
        logger = setup_logger("my_custom_name", log_dir=str(tmp_path))
        assert logger.name == "my_custom_name"
