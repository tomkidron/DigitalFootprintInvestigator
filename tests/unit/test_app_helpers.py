"""
Unit tests for helper functions in app.py
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from app import get_saved_reports


class TestGetSavedReports:
    @patch("app.Path.exists", return_value=True)
    def test_get_saved_reports_filters_out_traversal(self, mock_exists):
        reports_dir = Path("reports").resolve()

        valid_path = reports_dir / "valid_report.md"
        traversal_path = reports_dir / "../danger.md"

        mock_glob = MagicMock(return_value=[valid_path, traversal_path])

        with patch("app.Path.glob", mock_glob), patch("app.Path.stat") as mock_stat:
            mock_stat.return_value.st_mtime = 12345
            results = get_saved_reports()

        assert len(results) == 1
        assert results[0] == valid_path.resolve()
        assert traversal_path.resolve() not in results
