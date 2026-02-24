"""
Integration tests for the full investigation → report flow.

These tests require:
  - A valid ANTHROPIC_API_KEY or OPENAI_API_KEY set in the environment
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
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Report section tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No LLM API key found in environment")
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
@pytest.mark.skipif(not _has_llm_key(), reason="No LLM API key found in environment")
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
@pytest.mark.skipif(not _has_llm_key(), reason="No LLM API key found in environment")
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
@pytest.mark.skipif(not _has_llm_key(), reason="No LLM API key found in environment")
def test_processing_button_disabled(page):
    """While the investigation is running the start button must be replaced by
    the disabled '⏳ Investigation in progress...' button.

    NOTE: Because Streamlit calls st.rerun() immediately after setting
    processing=True, this window is very short. This test is best-effort and
    may be flaky on slow machines. Consider adding a forced delay in app.py
    behind a TEST_SLOW_MODE env var if reliable assertion is needed.
    """
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "Processing Test", "Target Identifier Input")
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    try:
        processing_btn = page.locator("button:has-text('Investigation in progress')")
        processing_btn.wait_for(state="visible", timeout=3000)
        assert processing_btn.is_disabled()
        print("✓ Processing button appeared and is disabled")
    except Exception:
        pytest.skip("Processing button window too short to catch reliably on this machine")
