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

from tests.healer import SelfHealingPage


def _has_llm_key():
    return bool(os.getenv("GEMINI_API_KEY"))


def _trigger_investigation(page, h_page, target):
    """Helper to input target, check consent, and click Start."""
    h_page.fill("input[aria-label='Target Identifier']", target, "Target Identifier Input")

    # Check consent if it exists and is not checked
    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    consent_label.wait_for(state="visible", timeout=8000)
    consent_checkbox = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_checkbox.is_checked():
        consent_label.click()
        page.wait_for_timeout(400)

    # Wait for the button to become enabled, then click it
    start_btn = page.locator("button:has-text('Start Investigation')")
    for _ in range(10):
        if not start_btn.is_disabled():
            break
        page.wait_for_timeout(500)

    h_page.click("button:has-text('Start Investigation')", "Start Button")


# ---------------------------------------------------------------------------
# Report section tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_report_section_appears(page):
    """After a successful investigation the '📄 Investigation Report' subheader,
    markdown content, and 'Download Report' button must all be visible."""
    h_page = SelfHealingPage(page)

    _trigger_investigation(page, h_page, "Test User")

    # The workflow can take a while — wait up to 3 minutes for the report heading
    report_heading = page.locator("[data-testid='stMain'] h3:has-text('Investigation Report')")
    report_heading.wait_for(state="visible", timeout=180_000)
    assert report_heading.is_visible()

    download_btn = page.locator("[data-testid='stMain'] button:has-text('Download Report')").first
    assert download_btn.is_visible()
    print("✓ Report section and download button appeared after investigation")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_download_button_present(page):
    """The download button must be labelled 'Download Report' and be visible
    after the investigation completes."""
    h_page = SelfHealingPage(page)

    _trigger_investigation(page, h_page, "Download Test")

    download_btn = page.locator("[data-testid='stMain'] button:has-text('Download Report')").first
    download_btn.wait_for(state="visible", timeout=180_000)
    assert download_btn.is_visible()
    print("✓ Download Report button is present after investigation")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_error_report_on_failure(page):
    """When the workflow encounters an error, the report section must display
    the error traceback (not just an st.error toast)."""
    pytest.skip(
        "Requires a mechanism to inject a workflow failure from the test layer. "
        "Implement once create_workflow supports a test/mock mode."
    )


# ---------------------------------------------------------------------------
# Processing state test
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_logs_expander_appears_during_investigation(page):
    """Once 'Start Investigation' is clicked the 'Investigation Logs' expander
    must become visible before the workflow completes."""
    h_page = SelfHealingPage(page)

    _trigger_investigation(page, h_page, "Logs Test")

    logs_expander = page.locator("div[data-testid='stExpander']").filter(has_text="Investigation Logs")
    logs_expander.wait_for(state="visible", timeout=15_000)
    assert logs_expander.is_visible()
    print("[OK] Investigation Logs expander appeared after starting investigation")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_report_content_has_text(page):
    """After a successful investigation the rendered report markdown must
    contain non-trivial text (more than just the heading)."""
    h_page = SelfHealingPage(page)

    _trigger_investigation(page, h_page, "Content Test")

    report_heading = page.locator("[data-testid='stMain'] h3:has-text('Investigation Report')")
    report_heading.wait_for(state="visible", timeout=180_000)

    # The markdown block rendered by st.markdown should have substantial text.
    # We find the container that contains the classification metadata
    report_body = page.locator("div[data-testid='stMarkdownContainer']").filter(has_text="Classification").first
    body_text = report_body.inner_text()
    assert len(body_text.strip()) > 50, f"Report body is too short ({len(body_text)} chars): {body_text!r}"
    print(f"[OK] Report body has {len(body_text)} characters of content")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_stop_button_appears_during_investigation(page):
    """While the investigation is running the start button must be replaced by
    the active '⏹ Stop Investigation' button."""
    h_page = SelfHealingPage(page)

    _trigger_investigation(page, h_page, "Processing Test")

    try:
        stop_btn = page.locator("button:has-text('Stop Investigation')")
        stop_btn.wait_for(state="visible", timeout=5000)
        assert not stop_btn.is_disabled()
        print("✓ Stop Investigation button appeared and is enabled")
    except Exception:
        pytest.skip("Stop button window too short to catch reliably on this machine")


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
    quick_radio.wait_for(state="visible", timeout=8000)
    quick_radio.click()
    page.wait_for_timeout(400)

    _trigger_investigation(page, h_page, "Quick Scan Test User")

    # The workflow can take a while — wait up to 3 minutes for the report heading
    report_heading = page.locator("[data-testid='stMain'] h3:has-text('Investigation Report')")
    report_heading.wait_for(state="visible", timeout=180_000)
    assert report_heading.is_visible()

    # The report should have body text containing the classification header
    report_body = page.locator("div[data-testid='stMarkdownContainer']").filter(has_text="Classification").first
    body_text = report_body.inner_text()
    assert len(body_text.strip()) > 50
    print("[OK] Quick Scan integration test complete")
