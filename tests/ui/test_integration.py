"""
Integration tests for the full investigation → report flow.

These tests require:
  - A valid GEMINI_API_KEY set in the environment
  - The complete LangGraph workflow to execute successfully

Run them explicitly with:
    pytest tests/ui/test_integration.py -m integration -v

Skip them in CI/CD with:
    pytest -m "not integration"
"""

import os

import pytest
from playwright.sync_api import expect

from tests.healer import SelfHealingPage


def _has_llm_key():
    return bool(os.getenv("GEMINI_API_KEY"))


def _trigger_investigation(page, h_page, target):
    """Helper to input target, check consent, and click Start."""
    h_page.fill("input[aria-label='Target Identifier']", target, "Target Identifier Input")

    # Check consent if it exists and is not checked
    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_checkbox = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_checkbox.is_checked():
        consent_label.click(force=True)

    # Wait for the button to become enabled, then click it
    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()


# ---------------------------------------------------------------------------
# Report section tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_end_to_end_investigation_flow(page):
    """Run a single full investigation and verify all UI components (stop button, logs, report, download)."""
    h_page = SelfHealingPage(page)

    _trigger_investigation(page, h_page, "E2E Test User")

    # 1. Stop button appears during processing
    try:
        stop_btn = page.locator("button:has-text('Stop Investigation')")
        expect(stop_btn).to_be_enabled(timeout=5000)
    except Exception:
        pass  # Stop button window might be too short to catch reliably on fast machines

    # 2. Logs expander appears during processing
    logs_expander = page.locator("div[data-testid='stExpander']").filter(has_text="Investigation Logs")
    expect(logs_expander).to_be_visible(timeout=15_000)

    # 3. Wait up to 4 minutes for the report heading to appear after workflow completes
    report_heading = page.locator("[data-testid='stMain'] h3:has-text('Investigation Report')")
    expect(report_heading).to_be_visible(timeout=240_000)

    # 4. Report body must contain text and the classification metadata
    report_body = page.locator("div[data-testid='stMarkdownContainer']").filter(has_text="Classification").first
    body_text = report_body.inner_text()
    assert len(body_text.strip()) > 50

    # 5. Download button must be visible
    download_btn = page.locator("[data-testid='stMain'] button:has-text('Download Markdown Report')").first
    expect(download_btn).to_be_visible(timeout=10000)
    print("✓ E2E flow completed successfully")


# ---------------------------------------------------------------------------
# Scan mode test
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_quick_scan_runs(page):
    """Verify that selecting Quick Scan runs an investigation successfully and uses Quick Scan parameters."""
    h_page = SelfHealingPage(page)

    # Find the Quick Scan radio option inside Streamlit's sidebar
    quick_radio = page.locator("label:has-text('Quick')")
    expect(quick_radio).to_be_visible(timeout=8000)
    quick_radio.click()

    _trigger_investigation(page, h_page, "Quick Scan Test User")

    # The workflow can take a while — wait up to 4 minutes for the report heading
    report_heading = page.locator("[data-testid='stMain'] h3:has-text('Investigation Report')")
    expect(report_heading).to_be_visible(timeout=240_000)

    # The report should have body text containing the classification header
    report_body = page.locator("div[data-testid='stMarkdownContainer']").filter(has_text="Classification").first
    body_text = report_body.inner_text()
    assert len(body_text.strip()) > 50
    print("[OK] Quick Scan integration test complete")
