import pytest
from playwright.sync_api import expect


def test_consent_checkbox_visible(page):
    checkbox = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(checkbox).to_be_visible(timeout=8000)


def test_consent_checkbox_unchecked_by_default(page):
    checkbox_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    expect(checkbox_input).to_be_attached(timeout=8000)
    expect(checkbox_input).not_to_be_checked()


def test_start_button_disabled_with_input_but_no_consent(page):
    checkbox_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    expect(checkbox_input).to_be_attached(timeout=8000)
    if checkbox_input.is_checked():
        page.locator("label:has-text('I confirm I have a legitimate purpose')").click()
        expect(checkbox_input).not_to_be_checked(timeout=5000)

    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill("John Doe")

    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_visible(timeout=8000)
    expect(start_btn).to_be_disabled()


def test_start_button_enabled_with_input_and_consent(page):
    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.fill("John Doe")

    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_input.is_checked():
        consent_label.click()

    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=8000)


def test_both_tabs_present(page):
    investigate_tab = page.locator("button.tab:has-text('Investigate')")
    reports_tab = page.locator("button.tab:has-text('Reports')")

    expect(investigate_tab).to_be_visible(timeout=8000)
    expect(reports_tab).to_be_visible(timeout=8000)


def test_reports_tab_navigable(page):
    reports_tab = page.locator("button.tab:has-text('Reports')")
    expect(reports_tab).to_be_visible(timeout=8000)
    reports_tab.click()

    reports_heading = page.get_by_role("heading", name="Saved Reports", exact=False)
    expect(reports_heading).to_be_visible(timeout=8000)


def test_reports_tab_empty_state(page):
    reports_tab = page.locator("button.tab:has-text('Reports')")
    expect(reports_tab).to_be_visible(timeout=8000)
    reports_tab.click()

    empty_msg = page.get_by_text("No reports found", exact=False)
    if not empty_msg.is_visible():
        pytest.skip("Reports exist in reports/ — empty-state not shown")

    expect(empty_msg).to_be_visible(timeout=8000)
