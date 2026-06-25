import os
import subprocess
import time
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def bypass_retry_sleep():
    """Bypass time.sleep in the retry decorator during tests to avoid massive bottlenecks."""
    with patch("utils.retry.time.sleep", return_value=None):
        yield


@pytest.fixture(scope="session")
def streamlit_app(worker_id):
    # Determine unique port per worker to avoid conflicts in xdist
    base_port = 8502
    if worker_id != "master":
        try:
            # worker_id is usually 'gw0', 'gw1', etc.
            worker_num = int(worker_id.replace("gw", ""))
            base_port += worker_num
        except ValueError:
            pass

    # If running in Docker (tests service), point to app-test service
    if os.path.exists("/.dockerenv"):
        # In docker-compose, there's only one app-test instance running on 8502
        yield "http://app-test:8502"
    else:
        # Path to venv python
        python_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_path):
            python_path = "python"  # Fallback

        # Start streamlit in the background
        proc = subprocess.Popen(
            [python_path, "-m", "streamlit", "run", "app.py", f"--server.port={base_port}", "--server.headless=true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ},
        )
        # Poll health endpoint instead of sleeping blindly
        health_url = f"http://localhost:{base_port}/_stcore/health"
        for attempt in range(30):
            try:
                urllib.request.urlopen(health_url, timeout=1)
                break  # server is up
            except (urllib.error.URLError, OSError):
                time.sleep(1)
        else:
            proc.terminate()
            raise RuntimeError(f"Streamlit did not start on port {base_port} within 30 seconds")
        yield f"http://localhost:{base_port}"
        proc.terminate()


@pytest.fixture
def page(context, streamlit_app):
    """Override pytest-playwright's page fixture to auto-navigate to the app."""
    page = context.new_page()
    page.goto(streamlit_app)
    yield page
    page.close()
