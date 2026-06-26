import os
import re
import subprocess
import time
import urllib.error
import urllib.request

import pytest
from playwright.sync_api import expect


@pytest.fixture(scope="module")
def fastapi_app_no_keys(worker_id):
    if os.path.exists("/.dockerenv"):
        pytest.skip("No-keys fixture not supported inside Docker (use docker run with custom env)")

    base_port = 9500
    if worker_id != "master":
        try:
            worker_num = int(worker_id.replace("gw", ""))
            base_port += worker_num
        except ValueError:
            pass

    # Ensure frontend is built
    if not os.path.exists(os.path.join("frontend", "out")):
        print("Building Next.js frontend for tests...")
        subprocess.run(["npm", "run", "build"], cwd="frontend", check=True, shell=True)

    python_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if not os.path.exists(python_path):
        python_path = "python"

    env = {
        **os.environ,
        "GEMINI_API_KEY": "",
    }

    proc = subprocess.Popen(
        [python_path, "-m", "uvicorn", "api.main:app", "--port", str(base_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    health_url = f"http://localhost:{base_port}/api/reports"
    for _ in range(30):
        try:
            urllib.request.urlopen(health_url, timeout=1)
            break
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    else:
        proc.terminate()
        raise RuntimeError(f"FastAPI (no-keys) did not start within 30 seconds on port {base_port}")

    yield f"http://localhost:{base_port}"
    proc.terminate()


@pytest.fixture(scope="function")
def page_no_keys(context, fastapi_app_no_keys):
    page = context.new_page()
    page.goto(fastapi_app_no_keys)
    expect(page).to_have_title(re.compile("Digital Footprint"), timeout=30000)
    yield page
    page.close()


def test_main_ui_still_functional_without_key(page_no_keys):
    """Even without an API key the app must render the title, input field,
    and start button so the user can see what the tool does."""
    page = page_no_keys

    target_input = page.locator("input[aria-label='Target Identifier']")
    expect(target_input).to_be_visible(timeout=8000)

    start_btn = page.get_by_text("Start Investigation", exact=False)
    expect(start_btn).to_be_visible(timeout=8000)
    print("[OK] Title, input, and start button are all present without an API key")
