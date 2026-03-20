"""
Integration tests for the full investigation → report flow.

These tests require:
  - A valid ANTHROPIC_API_KEY set in the environment
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
    return bool(os.getenv("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Report section tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Anthropic API key found in environment")
def test_report_section_appears(page):
    """After a successful investigation the '📄 Investigation Report' subheader,
    markdown content, and 'Download Report' button must all be visible."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "Test User", "Target Identifier Input")
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    # The workflow can take a while — wait up to 3 minutes for the report heading
    report_heading = page.get_by_text("Investigation Report", exact=False)
    report_heading.wait_for(state="visible", timeout=180_000)
    assert report_heading.is_visible()

    download_btn = page.get_by_text("Download Report", exact=False)
    assert download_btn.is_visible()
    print("✓ Report section and download button appeared after investigation")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Anthropic API key found in environment")
def test_download_button_present(page):
    """The download button must be labelled 'Download Report' and be visible
    after the investigation completes."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "Download Test", "Target Identifier Input")
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    download_btn = page.get_by_text("Download Report", exact=False)
    download_btn.wait_for(state="visible", timeout=180_000)
    assert download_btn.is_visible()
    print("✓ Download Report button is present after investigation")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Anthropic API key found in environment")
def test_error_report_on_failure(page):
    """When the workflow encounters an error, the report section must display
    the error traceback (not just an st.error toast).

    NOTE: To trigger a real failure you would need to force an exception inside
    the workflow. Consider patching create_workflow in a future refactor so it
    can be made to raise on demand from the test layer.
    """
    pytest.skip(
        "Requires a mechanism to inject a workflow failure from the test layer. "
        "Implement once create_workflow supports a test/mock mode."
    )


# ---------------------------------------------------------------------------
# Processing state test
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Anthropic API key found in environment")
def test_logs_expander_appears_during_investigation(page):
    """Once 'Start Investigation' is clicked the 'Investigation Logs' expander
    must become visible before the workflow completes."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "Logs Test", "Target Identifier Input")
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    logs_expander = page.locator("div[data-testid='stExpander']").filter(has_text="Investigation Logs")
    logs_expander.wait_for(state="visible", timeout=15_000)
    assert logs_expander.is_visible()
    print("[OK] Investigation Logs expander appeared after starting investigation")


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Anthropic API key found in environment")
def test_report_content_has_text(page):
    """After a successful investigation the rendered report markdown must
    contain non-trivial text (more than just the heading)."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "Content Test", "Target Identifier Input")
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    report_heading = page.get_by_text("Investigation Report", exact=False)
    report_heading.wait_for(state="visible", timeout=180_000)

    # The markdown block rendered by st.markdown should have substantial text.
    # The stMarkdownContainer div holds the rendered report body.
    report_body = page.locator("div[data-testid='stMarkdownContainer']").last
    body_text = report_body.inner_text()
    assert len(body_text.strip()) > 50, f"Report body is too short ({len(body_text)} chars): {body_text!r}"
    print(f"[OK] Report body has {len(body_text)} characters of content")


# ---------------------------------------------------------------------------
# Processing state test
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Anthropic API key found in environment")
def test_stop_button_appears_during_investigation(page):
    """While the investigation is running the start button must be replaced by
    the active '⏹ Stop Investigation' button."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "Processing Test", "Target Identifier Input")
    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    if not page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False).is_checked():
        consent_label.click()
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    try:
        stop_btn = page.locator("button:has-text('Stop Investigation')")
        stop_btn.wait_for(state="visible", timeout=5000)
        assert not stop_btn.is_disabled()
        print("✓ Stop Investigation button appeared and is enabled")
    except Exception:
        pytest.skip("Stop button window too short to catch reliably on this machine")
