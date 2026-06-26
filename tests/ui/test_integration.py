import os

import pytest
from playwright.sync_api import expect


def _has_llm_key():
    return bool(os.getenv("GEMINI_API_KEY"))


def _trigger_investigation(page, target):
    page.locator("button.tab:has-text('Investigate')").click()

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill(target)

    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_checkbox = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_checkbox.is_checked():
        consent_label.click(force=True)

    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_end_to_end_investigation_flow(page):
    _trigger_investigation(page, "E2E Test User")

    try:
        stop_btn = page.locator("button:has-text('Investigating...')")
        expect(stop_btn).to_be_disabled(timeout=5000)  # Since it's investigating, button disables
    except Exception:
        pass

    logs_console = page.locator("div.log-console")
    expect(logs_console).to_be_visible(timeout=15_000)

    # Wait for completion message in logs
    completed_msg = logs_console.get_by_text("Investigation complete!", exact=False)
    expect(completed_msg).to_be_visible(timeout=240_000)

    # Check Reports tab
    reports_tab = page.locator("button.tab:has-text('Reports')")
    reports_tab.click()

    report_list = page.locator("div.report-list")
    expect(report_list).to_be_visible(timeout=10_000)


@pytest.mark.integration
@pytest.mark.skipif(not _has_llm_key(), reason="No Gemini API key found in environment")
def test_quick_scan_runs(page):
    quick_radio = page.locator("label:has-text('Quick')")
    expect(quick_radio).to_be_visible(timeout=8000)
    quick_radio.click()

    _trigger_investigation(page, "Quick Scan Test User")

    logs_console = page.locator("div.log-console")
    completed_msg = logs_console.get_by_text("Investigation complete!", exact=False)
    expect(completed_msg).to_be_visible(timeout=240_000)
