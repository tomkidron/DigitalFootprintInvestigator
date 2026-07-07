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
def fastapi_app(worker_id):
    # Determine unique port per worker to avoid conflicts in xdist
    base_port = 8600
    if worker_id != "master":
        try:
            # worker_id is usually 'gw0', 'gw1', etc.
            worker_num = int(worker_id.replace("gw", ""))
            base_port += worker_num
        except ValueError:
            pass

    # If running in Docker (tests service), point to app-test service
    if os.path.exists("/.dockerenv"):
        # In docker-compose, there's only one app-test instance running on 8000
        yield "http://app-test:8000"
    else:
        # Build frontend if it doesn't exist or if source files are newer than the build
        out_file = os.path.join("frontend", "out", "index.html")
        src_dir = os.path.join("frontend", "src")
        needs_build = True
        
        if os.path.exists(out_file) and os.path.exists(src_dir):
            out_mtime = os.path.getmtime(out_file)
            src_newer = False
            for root, _, files in os.walk(src_dir):
                for f in files:
                    if os.path.getmtime(os.path.join(root, f)) > out_mtime:
                        src_newer = True
                        break
                if src_newer:
                    break
            if not src_newer:
                needs_build = False

        if needs_build:
            print("Frontend changes detected or missing build. Building Next.js frontend for tests...")
            # Note: requires npm to be in PATH
            try:
                subprocess.run(["npm", "run", "build"], cwd="frontend", check=True, shell=True)
            except Exception as e:
                print(f"Failed to build frontend: {e}")

        # Path to venv python
        python_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_path):
            python_path = "python"  # Fallback

        # Start FastAPI in the background
        proc = subprocess.Popen(
            [python_path, "-m", "uvicorn", "api.main:app", "--port", str(base_port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ},
        )
        # Poll health endpoint instead of sleeping blindly
        health_url = f"http://localhost:{base_port}/api/reports"
        for attempt in range(30):
            try:
                urllib.request.urlopen(health_url, timeout=1)
                break  # server is up
            except (urllib.error.URLError, OSError):
                time.sleep(1)
        else:
            proc.terminate()
            raise RuntimeError(f"FastAPI did not start on port {base_port} within 30 seconds")
        yield f"http://localhost:{base_port}"
        proc.terminate()


@pytest.fixture
def page(context, fastapi_app):
    """Override pytest-playwright's page fixture to auto-navigate to the app."""
    import re

    from playwright.sync_api import expect

    page = context.new_page()
    page.goto(fastapi_app)
    expect(page).to_have_title(re.compile("Digital Footprint"), timeout=30000)
    yield page
    page.close()
