"""
Unit test configuration.

Redirects the on-disk cache to a per-test temp directory so that tests
calling the same cached function with identical arguments do not share
cached results across tests.
"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def isolate_disk_cache(tmp_path):
    """Give each unit test its own empty cache directory."""
    with patch("utils.cache.CACHE_DIR", tmp_path):
        yield
