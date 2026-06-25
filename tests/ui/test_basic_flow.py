import pytest
from playwright.sync_api import expect

from tests.healer import SelfHealingPage


def test_app_loads(page):
    # Wait for Streamlit to update the title
    title = page.title()
    print(f"DEBUG: Page Title is '{title}'")
    assert "Digital Footprint" in title

    # Check if main components are visible
    h_page = SelfHealingPage(page)

    # Test sidebar presence
    sidebar = h_page.find_element("section[data-testid='stSidebar']", "Sidebar")
    assert sidebar is not None


def test_investigation_input(page):
    h_page = SelfHealingPage(page)

    # Fill target input
    # Note: Streamlit generates dynamic IDs, so we use description-based healing
    h_page.fill("input[aria-label='Target Identifier']", "John Doe", "Target Identifier Input")

    # Check if button exists
    start_btn = h_page.find_element("button:has-text('Start Investigation')", "Start Button")
    assert start_btn is not None


def test_sidebar_toggles(page):
    h_page = SelfHealingPage(page)

    # Check sidebar toggles
    # Streamlit toggles are often divs or labels containing the text
    toggles = ["Timeline Correlation", "Social Connection Analysis", "Deep Content Analysis"]

    for toggle_text in toggles:
        # Toggles in Streamlit have data-testid='stCheckbox' or labels
        toggle = h_page.find_element(f"label:has-text('{toggle_text}')", f"Toggle {toggle_text}")
        assert toggle is not None
        # Click the toggle
        toggle.click()
        # Verify it changed state (label structure might vary, but we check clickability)
        print(f"✓ Clicked toggle: {toggle_text}")


def test_empty_input_validation(page):
    h_page = SelfHealingPage(page)

    # Ensure input is empty
    h_page.fill("input[aria-label='Target Identifier']", "", "Empty Target Identifier")

    # Start button should be disabled
    start_btn = h_page.find_element("button:has-text('Start Investigation')", "Start Button")
    expect(start_btn).to_be_disabled()
    print("✓ Successfully verified empty input disables Start button")


@pytest.mark.local_only
def test_investigation_lifecycle_ui(page):
    h_page = SelfHealingPage(page)

    # Check consent first — required since the consent gate was added
    consent_label = page.locator("label:has-text('I confirm I have a legitimate purpose')")
    expect(consent_label).to_be_visible(timeout=8000)
    consent_input = page.get_by_role("checkbox", name="I confirm I have a legitimate purpose", exact=False)
    if not consent_input.is_checked():
        consent_label.click(force=True)

    # Fill target and trigger input event
    input_field = page.locator("input[aria-label='Target Identifier']")
    input_field.fill("Test User")
    input_field.press("Tab")  # Trigger blur event to ensure Streamlit detects the change

    # Wait for button to become enabled
    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_enabled(timeout=10000)

    # Click start
    start_btn.click()

    # Verify stop button appears (replaces start button while running)
    stop_btn = h_page.find_element("button:has-text('Stop Investigation')", "Stop Button")
    expect(stop_btn).to_be_enabled()

    # Verify Logs expander appears
    logs = h_page.find_element("div[data-testid='stExpander']:has-text('Investigation Logs')", "Logs Expander")
    assert logs is not None
    print("✓ Successfully verified investigation lifecycle UI changes")


def test_disclaimer_visible(page):
    """The EDUCATIONAL USE ONLY disclaimer must be rendered on page load."""
    disclaimer = page.get_by_text("EDUCATIONAL USE ONLY", exact=False)
    expect(disclaimer).to_be_visible(timeout=8000)
    print("✓ Disclaimer is visible")


def test_input_placeholder_text(page):
    """Target input must show the correct placeholder text."""
    target_input = page.locator("input[aria-label='Target Identifier']")
    expect(target_input).to_be_visible(timeout=8000)
    placeholder = target_input.get_attribute("placeholder")
    assert placeholder == "Enter Name, Email, Username, or Phone Number..."
    print(f"✓ Placeholder text correct: '{placeholder}'")


def test_sidebar_info_text(page):
    """Sidebar must show the API keys reminder info box."""
    info = page.locator("section[data-testid='stSidebar']").get_by_text(
        "Ensure you have set up your API keys", exact=False
    )
    expect(info).to_be_visible(timeout=8000)
    print("✓ Sidebar API key info text is visible")


def test_whitespace_only_input(page):
    """Input containing only spaces should also disable the Start button."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "   ", "Target Identifier Input")

    start_btn = h_page.find_element("button:has-text('Start Investigation')", "Start Button")
    expect(start_btn).to_be_disabled()
    print("✓ Whitespace-only input correctly disables button")


def test_toggle_state_changes(page):
    """Clicking a sidebar toggle must actually change its checked state."""
    toggle_labels = ["Timeline Correlation", "Social Connection Analysis", "Deep Content Analysis"]

    for label in toggle_labels:
        toggle_label = page.locator(f"label:has-text('{label}')")
        toggle_label.wait_for(state="attached", timeout=5000)
        toggle_input = toggle_label.locator("input")

        before = toggle_input.get_attribute("aria-checked")
        toggle_label.click()

        # Streamlit toggles take a moment to update aria-checked
        if before == "true":
            expect(toggle_input).to_have_attribute("aria-checked", "false", timeout=5000)
        else:
            expect(toggle_input).to_have_attribute("aria-checked", "true", timeout=5000)

        after = toggle_input.get_attribute("aria-checked")

        print(f"[OK] Toggle '{label}': {before} -> {after}")


def test_report_section_absent_on_initial_load(page):
    """Before any investigation is triggered the 'Investigation Report'
    heading and 'Download Report' button must NOT be present in the DOM."""

    # Neither element should be visible in the main investigation area
    # Note: We use a more specific selector to avoid matching content in the 'Reports' tab
    report_heading = page.locator("[data-testid='stMain'] h3:has-text('Investigation Report')")
    download_btn = page.locator("[data-testid='stMain'] button:has-text('Download Report')")

    expect(report_heading).not_to_be_visible()
    expect(download_btn).not_to_be_visible()
    print("[OK] Report section is correctly absent before any investigation")


def test_start_button_disabled_on_load(page):
    """The 'Start Investigation' button must be present but disabled on initial
    page load because the target identifier is empty."""
    start_btn = page.locator("button:has-text('Start Investigation')")
    expect(start_btn).to_be_visible(timeout=8000)
    expect(start_btn).to_be_disabled()
    print("[OK] Start Investigation button is correctly disabled on initial load")


def test_config_header_visible(page):
    """The sidebar must display a 'Configuration' header."""
    config_header = page.locator("section[data-testid='stSidebar']").get_by_text("Configuration", exact=True)
    expect(config_header).to_be_visible(timeout=8000)
    print("[OK] Configuration header is visible in the sidebar")


def test_advanced_analysis_subheader_visible(page):
    """The sidebar must show the 'Advanced Analysis' subheader above the three toggles."""
    subheader = page.locator("section[data-testid='stSidebar']").get_by_text("Advanced Analysis", exact=False)
    expect(subheader).to_be_visible(timeout=8000)
    print("[OK] Advanced Analysis subheader is visible in the sidebar")


def test_title_visible(page):
    """The main page heading 'Digital Footprint Investigator' must be rendered."""
    heading = page.get_by_role("heading", name="Digital Footprint Investigator", exact=False)
    expect(heading).to_be_visible(timeout=8000)
    print("[OK] Main page title is visible")


def test_quick_scan_hides_advanced_options(page):
    """Selecting 'Quick' scan must hide the 'Advanced Analysis' section and its toggles."""
    subheader = page.locator("section[data-testid='stSidebar']").get_by_text("Advanced Analysis", exact=False)
    expect(subheader).to_be_visible(timeout=8000)

    toggles = ["Timeline Correlation", "Social Connection Analysis", "Deep Content Analysis"]
    for label in toggles:
        toggle = page.locator(f"label:has-text('{label}')")
        expect(toggle).to_be_visible(timeout=5000)

    # Select Quick Scan
    quick_radio = page.locator("label:has-text('Quick')")
    quick_radio.click()

    # Verify hidden
    expect(subheader).not_to_be_visible(timeout=5000)
    for label in toggles:
        toggle = page.locator(f"label:has-text('{label}')")
        expect(toggle).not_to_be_visible(timeout=5000)

    # Select Advanced Scan to restore
    advanced_radio = page.locator("label:has-text('Advanced')")
    advanced_radio.click()

    # Verify visible again
    expect(subheader).to_be_visible(timeout=5000)
    for label in toggles:
        toggle = page.locator(f"label:has-text('{label}')")
        expect(toggle).to_be_visible(timeout=5000)

    print("[OK] Quick Scan correctly hides Advanced Analysis options in the UI")
