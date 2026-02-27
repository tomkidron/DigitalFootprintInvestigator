"""Unit tests for graph/workflow.py — routing logic."""

from graph.workflow import should_run_advanced_analysis


class TestShouldRunAdvancedAnalysis:
    """Tests for the conditional-routing function used as a LangGraph edge."""

    # --- routes to "report" ---

    def test_all_flags_false_routes_to_report(self):
        state = {
            "config": {
                "advanced_analysis": {
                    "timeline_correlation": False,
                    "network_analysis": False,
                    "deep_content_analysis": False,
                }
            }
        }
        assert should_run_advanced_analysis(state) == "report"

    def test_empty_config_routes_to_report(self):
        assert should_run_advanced_analysis({}) == "report"

    def test_missing_advanced_analysis_key_routes_to_report(self):
        assert should_run_advanced_analysis({"config": {}}) == "report"

    def test_empty_advanced_analysis_dict_routes_to_report(self):
        assert should_run_advanced_analysis({"config": {"advanced_analysis": {}}}) == "report"

    # --- routes to "advanced_analysis" ---

    def test_timeline_flag_routes_to_advanced(self):
        state = {
            "config": {
                "advanced_analysis": {
                    "timeline_correlation": True,
                    "network_analysis": False,
                    "deep_content_analysis": False,
                }
            }
        }
        assert should_run_advanced_analysis(state) == "advanced_analysis"

    def test_network_flag_routes_to_advanced(self):
        state = {
            "config": {
                "advanced_analysis": {
                    "timeline_correlation": False,
                    "network_analysis": True,
                    "deep_content_analysis": False,
                }
            }
        }
        assert should_run_advanced_analysis(state) == "advanced_analysis"

    def test_deep_flag_routes_to_advanced(self):
        state = {
            "config": {
                "advanced_analysis": {
                    "timeline_correlation": False,
                    "network_analysis": False,
                    "deep_content_analysis": True,
                }
            }
        }
        assert should_run_advanced_analysis(state) == "advanced_analysis"

    def test_all_flags_true_routes_to_advanced(self):
        state = {
            "config": {
                "advanced_analysis": {
                    "timeline_correlation": True,
                    "network_analysis": True,
                    "deep_content_analysis": True,
                }
            }
        }
        assert should_run_advanced_analysis(state) == "advanced_analysis"
