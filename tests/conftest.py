import pytest
import subprocess
import time
import os
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def streamlit_app():
    # If running in Docker (tests service), point to osint-tool service
    if os.path.exists("/.dockerenv"):
        yield "http://osint-tool:8501"
    else:
        # Path to venv python
        python_path = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_path):
             python_path = "python" # Fallback
             
        # Start streamlit in the background
        proc = subprocess.Popen(
            [python_path, "-m", "streamlit", "run", "app.py", "--server.port=8502", "--server.headless=true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ}
        )
        time.sleep(10) # Give it time to start
        yield "http://localhost:8502"
        proc.terminate()

@pytest.fixture(scope="function")
def page(streamlit_app):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = browser.new_page()
        page.goto(streamlit_app)
        yield page
        browser.close()
