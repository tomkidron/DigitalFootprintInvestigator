import pytest
from playwright.sync_api import expect

from tests.healer import SelfHealingPage


def test_app_loads(page):
    title = page.title()
    print(f"DEBUG: Page Title is '{title}'")
    assert "Digital Footprint" in title

    h_page = SelfHealingPage(page)
    # Check if main title is visible
    main_title = h_page.find_element("h1:has-text('Digital Footprint Investigator')", "Main Title")
    assert main_title is not None


def test_investigation_input(page):
    h_page = SelfHealingPage(page)
    h_page.fill("input[aria-label='Target Identifier']", "John Doe", "Target Identifier Input")

    start_btn = h_page.find_element("button:has-text('Start Investigation')", "Start Button")
    assert start_btn is not None


def test_sidebar_toggles(page):
    h_page = SelfHealingPage(page)
    # Toggles are checkboxes in Next.js app
    toggles = ["Timeline Correlation", "Social Connection Analysis", "Deep Content Analysis"]

    for toggle_text in toggles:
        toggle = h_page.find_element(f"label:has-text('{toggle_text}')", f"Toggle {toggle_text}")
        assert toggle is not None
        toggle.click()
        print(f"✓ Clicked toggle: {toggle_text}")


def test_empty_input_validation(page):
    h_page = SelfHealingPage(page)
    h_page.fill("input[aria-label='Target Identifier']", "", "Empty Target Identifier")
    start_btn = h_page.find_element("button:has-text('Start Investigation')", "Start Button")
    expect(start_btn).to_be_disabled()


@pytest.mark.local_only
def test_investigation_lifecycle_ui(page):
    h_page = SelfHealingPage(page)

    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_label.click(force=True)

    input_field = page.locator("input[aria-label='Target Identifier']")
    input_field.fill("Test User")

    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=10000)
    start_btn.click()

    stop_btn = h_page.find_element("button:has-text('Investigating...')", "Investigating Button")
    expect(stop_btn).to_be_visible()

    logs = h_page.find_element("div.log-console", "Logs Console")
    assert logs is not None


def test_disclaimer_visible(page):
    disclaimer = page.get_by_text("EDUCATIONAL USE ONLY", exact=False)
    expect(disclaimer).to_be_visible(timeout=8000)


def test_input_placeholder_text(page):
    target_input = page.locator("input[aria-label='Target Identifier']")
    expect(target_input).to_be_visible(timeout=8000)
    placeholder = target_input.get_attribute("placeholder")
    assert placeholder == "Enter Name, Email, Username, or Phone Number..."


def test_sidebar_info_text(page):
    info = page.locator("div.sidebar").get_by_text("Ensure you have set up your API keys", exact=False)
    expect(info).to_be_visible(timeout=8000)


def test_whitespace_only_input(page):
    h_page = SelfHealingPage(page)
    h_page.fill("input[aria-label='Target Identifier']", "   ", "Target Identifier Input")
    start_btn = h_page.find_element("button:has-text('Start Investigation')", "Start Button")
    expect(start_btn).to_be_disabled()


def test_start_button_disabled_on_load(page):
    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_visible(timeout=8000)
    expect(start_btn).to_be_disabled()


def test_config_header_visible(page):
    config_header = page.locator("div.sidebar").get_by_text("Configuration", exact=True)
    expect(config_header).to_be_visible(timeout=8000)


def test_advanced_analysis_subheader_visible(page):
    subheader = page.locator("div.sidebar").get_by_text("Advanced Analysis", exact=False)
    expect(subheader).to_be_visible(timeout=8000)


def test_quick_scan_hides_advanced_options(page):
    subheader = page.locator("div.sidebar").get_by_text("Advanced Analysis", exact=False)
    expect(subheader).to_be_visible(timeout=8000)

    quick_radio = page.locator("label:has-text('Quick')")
    quick_radio.click()

    expect(subheader).not_to_be_visible(timeout=5000)

    advanced_radio = page.locator("label:has-text('Advanced')")
    advanced_radio.click()

    expect(subheader).to_be_visible(timeout=5000)
