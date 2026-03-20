"""
Tests for the consent gate and tab navigation introduced in app.py.

Gaps covered:
- Consent checkbox is visible and unchecked by default
- Start button stays disabled when input is filled but consent is not checked
- Start button becomes enabled only when both input and consent are satisfied
- Both tabs (Investigate / Reports) are present and navigable
- Reports tab shows the empty-state message when no reports exist
"""

import pytest

# ---------------------------------------------------------------------------
# Consent gate
# ---------------------------------------------------------------------------


def test_consent_checkbox_visible(page):
    """Consent checkbox must be rendered on the Investigate tab."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)
    checkbox = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    checkbox.wait_for(state="visible", timeout=8000)
    assert checkbox.is_visible()


def test_consent_checkbox_unchecked_by_default(page):
    """Consent checkbox must be unchecked on initial page load."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)
    checkbox_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    checkbox_input.wait_for(state="attached", timeout=8000)
    assert not checkbox_input.is_checked(), "Consent checkbox should be unchecked on load"


def test_start_button_disabled_with_input_but_no_consent(page):
    """Filling the target input without checking consent must keep Start disabled."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)

    # Ensure consent is unchecked
    checkbox_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    checkbox_input.wait_for(state="attached", timeout=8000)
    if checkbox_input.is_checked():
        page.locator("label:has-text('I confirm I have a legitimate purpose')").click()
        page.wait_for_timeout(500)

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill("John Doe")
    target_input.press("Tab")
    page.wait_for_timeout(600)

    start_btn = page.locator("button:has-text('Start Investigation')")
    start_btn.wait_for(state="visible", timeout=8000)
    assert start_btn.is_disabled(), "Start button must stay disabled without consent"


def test_start_button_enabled_with_input_and_consent(page):
    """Start button must become enabled when both input and consent are provided."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill("John Doe")
    target_input.press("Tab")

    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    consent_label.wait_for(state="visible", timeout=8000)
    consent_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_input.is_checked():
        consent_label.click()

    # Poll for button to become enabled
    start_btn = page.locator("button:has-text('Start Investigation')")
    for _ in range(10):
        if not start_btn.is_disabled():
            break
        page.wait_for_timeout(400)
    else:
        raise AssertionError("Start button did not become enabled after filling input and checking consent")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------


def test_both_tabs_present(page):
    """Both 'Investigate' and 'Reports' tabs must be rendered."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)

    investigate_tab = page.locator("[data-testid='stTab']:has-text('Investigate')")
    reports_tab = page.locator("[data-testid='stTab']:has-text('Reports')")

    investigate_tab.wait_for(state="visible", timeout=8000)
    reports_tab.wait_for(state="visible", timeout=8000)

    assert investigate_tab.is_visible()
    assert reports_tab.is_visible()


def test_reports_tab_navigable(page):
    """Clicking the Reports tab must switch the view without error."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)

    reports_tab = page.locator("[data-testid='stTab']:has-text('Reports')")
    reports_tab.wait_for(state="visible", timeout=8000)
    reports_tab.click()
    page.wait_for_timeout(1000)

    # After clicking, the Reports tab heading must be visible
    reports_heading = page.get_by_role("heading", name="Saved Reports", exact=False)
    reports_heading.wait_for(state="visible", timeout=8000)
    assert reports_heading.is_visible()


def test_reports_tab_empty_state(page):
    """When no reports exist the Reports tab must show the 'No reports found' info message."""
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)

    reports_tab = page.locator("[data-testid='stTab']:has-text('Reports')")
    reports_tab.wait_for(state="visible", timeout=8000)
    reports_tab.click()
    page.wait_for_timeout(1000)

    # The empty-state message is only shown when reports/ has no .md files.
    # If reports exist this assertion is skipped rather than failed.
    selectbox = page.locator("[data-testid='stSelectbox']")
    if selectbox.is_visible():
        pytest.skip("Reports exist in reports/ — empty-state not shown")

    empty_msg = page.get_by_text("No reports found", exact=False)
    empty_msg.wait_for(state="visible", timeout=8000)
    assert empty_msg.is_visible()
