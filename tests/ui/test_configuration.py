"""
Tests for app behaviour that depends on the runtime configuration
(e.g. presence/absence of API keys).

These tests spin up their own Streamlit instance on port 8503 with a
controlled environment, independent of the main session fixture in conftest.py.
"""

import os
import subprocess
import time
import urllib.error
import urllib.request

import pytest
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def streamlit_app_no_keys():
    """Start Streamlit on port 8503 with ANTHROPIC_API_KEY cleared.

    python-dotenv's load_dotenv() (override=False) will not overwrite vars
    that are already set in the process env, so passing an empty string here
    keeps it empty even after load_dotenv() runs inside app.py.
    """
    if os.path.exists("/.dockerenv"):
        # Inside Docker the osint-tool service is the app — skip this fixture
        pytest.skip("No-keys fixture not supported inside Docker (use docker run with custom env)")

    python_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if not os.path.exists(python_path):
        python_path = "python"

    env = {
        **os.environ,
        "ANTHROPIC_API_KEY": "",
    }

    proc = subprocess.Popen(
        [python_path, "-m", "streamlit", "run", "app.py", "--server.port=8503", "--server.headless=true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    health_url = "http://localhost:8503/_stcore/health"
    for _ in range(30):
        try:
            urllib.request.urlopen(health_url, timeout=1)
            break
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    else:
        proc.terminate()
        raise RuntimeError("Streamlit (no-keys) did not start within 30 seconds")

    yield "http://localhost:8503"
    proc.terminate()


@pytest.fixture(scope="function")
def page_no_keys(streamlit_app_no_keys):
    """Playwright page pointed at the no-keys Streamlit instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        page = browser.new_page()
        page.goto(streamlit_app_no_keys)
        yield page
        browser.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_api_key_warning(page_no_keys):
    """When ANTHROPIC_API_KEY is not set, the app must display the warning
    banner pointing users to configure their API key."""
    page = page_no_keys

    warning = page.get_by_text("No Anthropic API key found", exact=False)
    warning.wait_for(state="visible", timeout=10000)
    assert warning.is_visible()
    print("[OK] API key warning banner is visible when no key is configured")


def test_main_ui_still_functional_without_key(page_no_keys):
    """Even without an API key the app must render the title, input field,
    and start button so the user can see what the tool does."""
    page = page_no_keys

    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)
    assert "Digital Footprint" in page.title()

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.wait_for(state="visible", timeout=8000)
    assert target_input.is_visible()

    start_btn = page.get_by_text("Start Investigation", exact=False)
    start_btn.wait_for(state="visible", timeout=8000)
    assert start_btn.is_visible()
    print("[OK] Title, input, and start button are all present without an API key")
