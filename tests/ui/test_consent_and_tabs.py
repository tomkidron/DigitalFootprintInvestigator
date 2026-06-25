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
from playwright.sync_api import expect

# ---------------------------------------------------------------------------
# Consent gate
# ---------------------------------------------------------------------------


def test_consent_checkbox_visible(page):
    """Consent checkbox must be rendered on the Investigate tab."""
    checkbox = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(checkbox).to_be_visible(timeout=8000)


def test_consent_checkbox_unchecked_by_default(page):
    """Consent checkbox must be unchecked on initial page load."""
    checkbox_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    expect(checkbox_input).to_be_attached(timeout=8000)
    expect(checkbox_input).not_to_be_checked()


def test_start_button_disabled_with_input_but_no_consent(page):
    """Filling the target input without checking consent must keep Start disabled."""

    # Ensure consent is unchecked
    checkbox_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    expect(checkbox_input).to_be_attached(timeout=8000)
    if checkbox_input.is_checked():
        page.locator("label:has-text('I confirm I have a legitimate purpose')").click()
        expect(checkbox_input).not_to_be_checked(timeout=5000)

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill("John Doe")
    target_input.press("Tab")

    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_visible(timeout=8000)
    expect(start_btn).to_be_disabled()


def test_start_button_enabled_with_input_and_consent(page):
    """Start button must become enabled when both input and consent are provided."""

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill("John Doe")
    target_input.press("Tab")

    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_input.is_checked():
        consent_label.click()

    # Poll for button to become enabled
    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=8000)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------


def test_both_tabs_present(page):
    """Both 'Investigate' and 'Reports' tabs must be rendered."""

    investigate_tab = page.locator("[data-testid='stTab']:has-text('Investigate')")
    reports_tab = page.locator("[data-testid='stTab']:has-text('Reports')")

    expect(investigate_tab).to_be_visible(timeout=8000)
    expect(reports_tab).to_be_visible(timeout=8000)


def test_reports_tab_navigable(page):
    """Clicking the Reports tab must switch the view without error."""

    reports_tab = page.locator("[data-testid='stTab']:has-text('Reports')")
    expect(reports_tab).to_be_visible(timeout=8000)
    reports_tab.click()

    # After clicking, the Reports tab heading must be visible
    reports_heading = page.get_by_role("heading", name="Saved Reports", exact=False)
    expect(reports_heading).to_be_visible(timeout=8000)


def test_reports_tab_empty_state(page):
    """When no reports exist the Reports tab must show the 'No reports found' info message."""

    reports_tab = page.locator("[data-testid='stTab']:has-text('Reports')")
    expect(reports_tab).to_be_visible(timeout=8000)
    reports_tab.click()

    # The empty-state message is only shown when reports/ has no .md files.
    # If reports exist this assertion is skipped rather than failed.
    selectbox = page.locator("[data-testid='stSelectbox']")
    if selectbox.is_visible():
        pytest.skip("Reports exist in reports/ — empty-state not shown")

    empty_msg = page.get_by_text("No reports found", exact=False)
    expect(empty_msg).to_be_visible(timeout=8000)
