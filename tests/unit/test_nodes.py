"""Unit tests for graph/nodes/ — search nodes, report helpers, and advanced analysis."""

import re
from datetime import datetime, timedelta
from unittest.mock import MagicMock, mock_open, patch

# ---------------------------------------------------------------------------
# _timing.py
# ---------------------------------------------------------------------------


class TestLogStart:
    def test_returns_datetime(self, capsys):
        from graph.nodes._timing import log_start

        result = log_start("Test")
        assert isinstance(result, datetime)

    def test_prints_label_and_started(self, capsys):
        from graph.nodes._timing import log_start

        log_start("Google search")
        captured = capsys.readouterr()
        assert "Google search started..." in captured.out

    def test_prints_timestamp_format(self, capsys):
        from graph.nodes._timing import log_start

        log_start("Node")
        captured = capsys.readouterr()
        assert re.search(r"\[\d{2}:\d{2}:\d{2}\]", captured.out)


class TestLogDone:
    def test_prints_label_and_complete(self, capsys):
        from graph.nodes._timing import log_done

        start = datetime.now() - timedelta(seconds=1)
        log_done("Google search", start)
        captured = capsys.readouterr()
        assert "Google search complete" in captured.out

    def test_prints_elapsed_seconds(self, capsys):
        from graph.nodes._timing import log_done

        start = datetime.now() - timedelta(seconds=2)
        log_done("Node", start)
        captured = capsys.readouterr()
        assert re.search(r"\d+\.\d+s\)", captured.out)

    def test_elapsed_is_non_negative(self, capsys):
        from graph.nodes._timing import log_done

        start = datetime.now()
        log_done("Node", start)
        captured = capsys.readouterr()
        match = re.search(r"\((\d+\.\d+)s\)", captured.out)
        assert match and float(match.group(1)) >= 0


# ---------------------------------------------------------------------------
# graph/nodes/search.py — google_node and social_node
# ---------------------------------------------------------------------------


class TestGoogleNode:
    def _run(self, env_overrides=None):
        from graph.nodes.search import google_node

        state = {"target": "John Doe"}
        env = {"SERPAPI_KEY": "", "HIBP_API_KEY": "", "HUNTER_API_KEY": ""}
        env.update(env_overrides or {})
        with patch("graph.nodes.search.google_search", return_value="search result"), patch.dict("os.environ", env):
            return google_node(state)

    def test_returns_google_data_list(self):
        result = self._run()
        assert "google_data" in result
        assert isinstance(result["google_data"], list)
        assert len(result["google_data"]) == 1

    def test_serpapi_ok_when_key_present(self):
        result = self._run({"SERPAPI_KEY": "realkey"})
        assert "[OK] SerpAPI" in result["google_data"][0]

    def test_serpapi_warn_when_key_absent(self):
        result = self._run({"SERPAPI_KEY": ""})
        assert "[WARN] Free googlesearch" in result["google_data"][0]

    def test_hibp_ok_when_key_present(self):
        result = self._run({"HIBP_API_KEY": "realkey"})
        assert "[OK] Have I Been Pwned" in result["google_data"][0]

    def test_hibp_error_when_key_absent(self):
        result = self._run({"HIBP_API_KEY": ""})
        assert "[ERROR] HIBP API not configured" in result["google_data"][0]

    def test_hunter_ok_when_key_present(self):
        result = self._run({"HUNTER_API_KEY": "realkey"})
        assert "[OK] Hunter.io" in result["google_data"][0]

    def test_hunter_error_when_key_absent(self):
        result = self._run({"HUNTER_API_KEY": ""})
        assert "[ERROR] Hunter.io API not configured" in result["google_data"][0]

    def test_result_contains_original_search_output(self):
        result = self._run()
        assert "search result" in result["google_data"][0]


class TestSocialNode:
    def _run(self):
        from graph.nodes.search import social_node

        state = {"target": "John Doe"}
        with patch("graph.nodes.search.social_media_search", return_value="social result"):
            return social_node(state)

    def test_returns_social_data_list(self):
        result = self._run()
        assert "social_data" in result
        assert isinstance(result["social_data"], list)

    def test_metadata_includes_github_ok(self):
        result = self._run()
        assert "[OK] GitHub" in result["social_data"][0]

    def test_metadata_includes_reddit_ok(self):
        result = self._run()
        assert "[OK] Reddit" in result["social_data"][0]

    def test_metadata_includes_instagram_error(self):
        result = self._run()
        assert "[ERROR] Instagram" in result["social_data"][0]

    def test_metadata_includes_linkedin_warn(self):
        result = self._run()
        assert "[WARN] LinkedIn" in result["social_data"][0]

    def test_result_contains_original_search_output(self):
        result = self._run()
        assert "social result" in result["social_data"][0]


# ---------------------------------------------------------------------------
# graph/nodes/report.py — _determine_actual_platforms
# ---------------------------------------------------------------------------


class TestDetermineActualPlatforms:
    def _call(self, google="", social=""):
        from graph.nodes.report import _determine_actual_platforms

        return _determine_actual_platforms(google, social)

    def test_google_detected_from_marker_text(self):
        assert "Google" in self._call(google="Google Search Results for: test")

    def test_google_not_detected_without_marker(self):
        assert "Google" not in self._call(google="some random text")

    def test_github_detected_from_ok_marker(self):
        assert "GitHub" in self._call(social="[OK] Found GitHub profile:\n  Username: johndoe")

    def test_reddit_detected_from_ok_marker(self):
        assert "Reddit" in self._call(social="[OK] Found Reddit profile:\n  Username: johndoe")

    def test_linkedin_detected_via_site_operator(self):
        assert "LinkedIn (via Google)" in self._call(social="site:linkedin.com John Doe")

    def test_empty_inputs_return_empty_list(self):
        assert self._call() == []

    def test_multiple_platforms_detected_together(self):
        google = "Google Search Results for: test"
        social = "[OK] Found GitHub profile:\nsome\n[OK] Found Reddit profile:\nmore"
        platforms = self._call(google, social)
        assert "Google" in platforms
        assert "GitHub" in platforms
        assert "Reddit" in platforms

    def test_unknown_platform_not_added(self):
        # TikTok or any unsupported platform should not appear
        platforms = self._call(social="[OK] Found TikTok profile:\n...")
        assert "TikTok" not in platforms


# ---------------------------------------------------------------------------
# graph/nodes/report.py — report_node
# ---------------------------------------------------------------------------


class TestReportNode:
    def _make_state(self, target="John Doe"):
        return {
            "target": target,
            "google_data": ["Google Search Results for: test"],
            "social_data": ["[OK] Found GitHub profile: johndoe"],
            "analysis": "Some analysis text",
        }

    def test_returns_report_key(self):
        from graph.nodes.report import report_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="# Report\nContent")
        with (
            patch("graph.nodes.report.get_llm", return_value=mock_llm),
            patch("builtins.open", mock_open()),
            patch("graph.nodes.report.Path.mkdir"),
        ):
            result = report_node(self._make_state())
        assert "report" in result
        assert result["report"] == "# Report\nContent"

    def test_invokes_llm_once(self):
        from graph.nodes.report import report_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="report text")
        with (
            patch("graph.nodes.report.get_llm", return_value=mock_llm),
            patch("builtins.open", mock_open()),
            patch("graph.nodes.report.Path.mkdir"),
        ):
            report_node(self._make_state())
        mock_llm.invoke.assert_called_once()

    def test_filename_strips_special_characters(self):
        from graph.nodes.report import report_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="report")
        m = mock_open()
        with (
            patch("graph.nodes.report.get_llm", return_value=mock_llm),
            patch("builtins.open", m),
            patch("graph.nodes.report.Path.mkdir"),
        ):
            report_node(self._make_state(target="John & Jane <Test>"))
        # The filepath passed to open should not contain & < >
        call_args = str(m.call_args)
        assert "&" not in call_args
        assert "<" not in call_args
        assert ">" not in call_args

    def test_filename_replaces_spaces_with_underscores(self):
        from graph.nodes.report import report_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="report")
        m = mock_open()
        with (
            patch("graph.nodes.report.get_llm", return_value=mock_llm),
            patch("builtins.open", m),
            patch("graph.nodes.report.Path.mkdir"),
        ):
            report_node(self._make_state(target="John Doe"))
        call_args = str(m.call_args)
        assert "John_Doe" in call_args

    def test_creates_reports_directory(self):
        from graph.nodes.report import report_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="report")
        mock_mkdir = MagicMock()
        with (
            patch("graph.nodes.report.get_llm", return_value=mock_llm),
            patch("builtins.open", mock_open()),
            patch("graph.nodes.report.Path.mkdir", mock_mkdir),
        ):
            report_node(self._make_state())
        mock_mkdir.assert_called_once_with(exist_ok=True)


# ---------------------------------------------------------------------------
# graph/nodes/analysis.py — analysis_node
# ---------------------------------------------------------------------------


class TestAnalysisNode:
    def _make_state(self, google=None, social=None):
        return {
            "target": "John Doe",
            "google_data": google or ["google results"],
            "social_data": social or ["social results"],
        }

    def test_returns_analysis_key(self):
        from graph.nodes.analysis import analysis_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Analysis output")
        with patch("graph.nodes.analysis.get_llm", return_value=mock_llm):
            result = analysis_node(self._make_state())
        assert result == {"analysis": "Analysis output"}

    def test_invokes_llm_with_target_in_prompt(self):
        from graph.nodes.analysis import analysis_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="output")
        with patch("graph.nodes.analysis.get_llm", return_value=mock_llm):
            analysis_node(self._make_state())
        prompt = mock_llm.invoke.call_args[0][0]
        assert "John Doe" in prompt

    def test_handles_empty_google_and_social_data(self):
        from graph.nodes.analysis import analysis_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="result")
        with patch("graph.nodes.analysis.get_llm", return_value=mock_llm):
            result = analysis_node(self._make_state(google=[], social=[]))
        assert "analysis" in result

    def test_concatenates_multiple_google_data_items(self):
        from graph.nodes.analysis import analysis_node

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="result")
        with patch("graph.nodes.analysis.get_llm", return_value=mock_llm):
            analysis_node(self._make_state(google=["part1", "part2"]))
        prompt = mock_llm.invoke.call_args[0][0]
        assert "part1" in prompt
        assert "part2" in prompt


# ---------------------------------------------------------------------------
# graph/nodes/advanced.py — pure analysis helpers
# ---------------------------------------------------------------------------


class TestFindActivityClusters:
    def test_empty_timestamps_returns_empty_list(self):
        from graph.nodes.advanced import _find_activity_clusters

        assert _find_activity_clusters([]) == []

    def test_clusters_activities_on_same_day(self):
        from graph.nodes.advanced import _find_activity_clusters

        timestamps = [
            {"platform": "twitter", "timestamp": "2024-01-15T10:00:00Z"},
            {"platform": "github", "timestamp": "2024-01-15T14:00:00Z"},
            {"platform": "reddit", "timestamp": "2024-01-16T09:00:00Z"},
        ]
        result = _find_activity_clusters(timestamps)
        dates = {c["date"] for c in result}
        assert "2024-01-15" in dates
        assert "2024-01-16" in dates

    def test_cluster_counts_are_correct(self):
        from graph.nodes.advanced import _find_activity_clusters

        timestamps = [
            {"platform": "twitter", "timestamp": "2024-01-15T10:00:00Z"},
            {"platform": "github", "timestamp": "2024-01-15T14:00:00Z"},
        ]
        result = _find_activity_clusters(timestamps)
        jan15 = next(c for c in result if c["date"] == "2024-01-15")
        assert jan15["activity_count"] == 2

    def test_skips_malformed_timestamps_without_raising(self):
        from graph.nodes.advanced import _find_activity_clusters

        timestamps = [
            {"platform": "twitter", "timestamp": "not-a-date"},
            {"platform": "github", "timestamp": "2024-01-15T10:00:00Z"},
        ]
        result = _find_activity_clusters(timestamps)
        assert len(result) == 1
        assert result[0]["date"] == "2024-01-15"


class TestCalculateTemporalCorrelation:
    def test_returns_zero_for_empty_lists(self):
        from graph.nodes.advanced import _calculate_temporal_correlation

        assert _calculate_temporal_correlation([], []) == 0.0

    def test_returns_zero_when_one_list_empty(self):
        from graph.nodes.advanced import _calculate_temporal_correlation

        activities = [{"timestamp": "2024-01-15T10:00:00Z"}]
        assert _calculate_temporal_correlation(activities, []) == 0.0
        assert _calculate_temporal_correlation([], activities) == 0.0

    def test_returns_one_for_identical_timestamps(self):
        from graph.nodes.advanced import _calculate_temporal_correlation

        a = [{"timestamp": "2024-01-15T10:00:00Z"}]
        assert _calculate_temporal_correlation(a, a) == 1.0

    def test_returns_zero_for_activities_far_apart(self):
        from graph.nodes.advanced import _calculate_temporal_correlation

        a1 = [{"timestamp": "2024-01-01T10:00:00Z"}]
        a2 = [{"timestamp": "2024-06-01T10:00:00Z"}]
        assert _calculate_temporal_correlation(a1, a2) == 0.0

    def test_within_24h_window_counts_as_correlated(self):
        from graph.nodes.advanced import _calculate_temporal_correlation

        # 12 hours apart — should count
        a1 = [{"timestamp": "2024-01-15T00:00:00Z"}]
        a2 = [{"timestamp": "2024-01-15T12:00:00Z"}]
        assert _calculate_temporal_correlation(a1, a2) == 1.0

    def test_exactly_at_24h_boundary_not_correlated(self):
        from graph.nodes.advanced import _calculate_temporal_correlation

        # Exactly 24h apart — abs diff == 86400, condition is < 86400, so NOT correlated
        a1 = [{"timestamp": "2024-01-15T00:00:00Z"}]
        a2 = [{"timestamp": "2024-01-16T00:00:00Z"}]
        assert _calculate_temporal_correlation(a1, a2) == 0.0


class TestAnalyzeUsernameConsistency:
    def test_empty_identifiers_returns_zero_score(self):
        from graph.nodes.advanced import _analyze_username_consistency

        result = _analyze_username_consistency(set())
        assert result["consistency_score"] == 0
        assert result["common_patterns"] == []

    def test_filters_out_emails(self):
        from graph.nodes.advanced import _analyze_username_consistency

        result = _analyze_username_consistency({"johndoe", "john@example.com"})
        assert result["total_usernames"] == 1

    def test_filters_out_urls(self):
        from graph.nodes.advanced import _analyze_username_consistency

        result = _analyze_username_consistency({"johndoe", "https://github.com/johndoe"})
        assert result["total_usernames"] == 1

    def test_returns_score_and_patterns_for_valid_usernames(self):
        from graph.nodes.advanced import _analyze_username_consistency

        result = _analyze_username_consistency({"johndoe", "janedoe"})
        assert "consistency_score" in result
        assert "common_patterns" in result
        assert result["total_usernames"] == 2


class TestAdvancedAnalysisNode:
    def _base_state(self, timeline=False, network=False, deep=False):
        return {
            "target": "John Doe",
            "config": {
                "advanced_analysis": {
                    "timeline_correlation": timeline,
                    "network_analysis": network,
                    "deep_content_analysis": deep,
                }
            },
            "google_data": [],
            "social_data": [],
        }

    def test_returns_none_for_both_when_all_disabled(self):
        from graph.nodes.advanced import advanced_analysis_node

        result = advanced_analysis_node(self._base_state())
        assert result["timeline_data"] is None
        assert result["network_data"] is None

    def test_timeline_data_populated_when_flag_enabled(self):
        from graph.nodes.advanced import advanced_analysis_node

        result = advanced_analysis_node(self._base_state(timeline=True))
        assert result["timeline_data"] is not None
        assert "total_timestamped_items" in result["timeline_data"]

    def test_network_data_populated_when_flag_enabled(self):
        from graph.nodes.advanced import advanced_analysis_node

        result = advanced_analysis_node(self._base_state(network=True))
        assert result["network_data"] is not None
        assert "unique_identifiers" in result["network_data"]

    def test_both_disabled_when_only_deep_enabled(self):
        from graph.nodes.advanced import advanced_analysis_node

        # deep_content_analysis stub was removed — only timeline/network populate results
        result = advanced_analysis_node(self._base_state(deep=True))
        assert result["timeline_data"] is None
        assert result["network_data"] is None

    def test_empty_state_with_timeline_returns_zero_timestamps(self):
        from graph.nodes.advanced import advanced_analysis_node

        result = advanced_analysis_node(self._base_state(timeline=True))
        assert result["timeline_data"]["total_timestamped_items"] == 0

    def test_empty_state_with_network_returns_zero_identifiers(self):
        from graph.nodes.advanced import advanced_analysis_node

        result = advanced_analysis_node(self._base_state(network=True))
        assert result["network_data"]["unique_identifiers"] == 0
