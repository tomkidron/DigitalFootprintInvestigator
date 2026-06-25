"""
Tests for app behaviour that depends on the runtime configuration
(e.g. presence/absence of API keys).

These tests spin up their own Streamlit instance on port 8503 with a
controlled environment, independent of the main session fixture in conftest.py.
"""

import os
import re
import subprocess
import time
import urllib.error
import urllib.request

import pytest
from playwright.sync_api import expect

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def streamlit_app_no_keys(worker_id):
    """Start Streamlit on a dedicated port with GEMINI_API_KEY cleared."""
    if os.path.exists("/.dockerenv"):
        pytest.skip("No-keys fixture not supported inside Docker (use docker run with custom env)")

    # Avoid conflict with the 8502+ ports used by the main app fixture
    base_port = 9500
    if worker_id != "master":
        try:
            worker_num = int(worker_id.replace("gw", ""))
            base_port += worker_num
        except ValueError:
            pass

    python_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if not os.path.exists(python_path):
        python_path = "python"

    env = {
        **os.environ,
        "GEMINI_API_KEY": "",
    }

    proc = subprocess.Popen(
        [python_path, "-m", "streamlit", "run", "app.py", f"--server.port={base_port}", "--server.headless=true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    health_url = f"http://localhost:{base_port}/_stcore/health"
    for _ in range(30):
        try:
            urllib.request.urlopen(health_url, timeout=1)
            break
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    else:
        proc.terminate()
        raise RuntimeError(f"Streamlit (no-keys) did not start within 30 seconds on port {base_port}")

    yield f"http://localhost:{base_port}"
    proc.terminate()


@pytest.fixture(scope="function")
def page_no_keys(context, streamlit_app_no_keys):
    """Playwright page pointed at the no-keys Streamlit instance."""
    page = context.new_page()
    page.goto(streamlit_app_no_keys)
    expect(page).to_have_title(re.compile("Digital Footprint"), timeout=30000)
    yield page
    page.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_api_key_warning(page_no_keys):
    """When GEMINI_API_KEY is not set, the app must display the warning
    banner pointing users to configure their API key."""
    page = page_no_keys

    warning = page.get_by_text("No Gemini API key found", exact=False)
    expect(warning).to_be_visible(timeout=10000)
    print("[OK] API key warning banner is visible when no key is configured")


def test_main_ui_still_functional_without_key(page_no_keys):
    """Even without an API key the app must render the title, input field,
    and start button so the user can see what the tool does."""
    page = page_no_keys

    target_input = page.locator("input[aria-label='Target Identifier']")
    expect(target_input).to_be_visible(timeout=8000)

    start_btn = page.get_by_text("Start Investigation", exact=False)
    expect(start_btn).to_be_visible(timeout=8000)
    print("[OK] Title, input, and start button are all present without an API key")
