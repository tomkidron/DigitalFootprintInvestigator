import pytest
from tests.healer import SelfHealingPage

def test_app_loads(page):
    # Wait for Streamlit to update the title
    page.wait_for_function("document.title.includes('Digital Footprint')", timeout=10000)
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
    toggles = [
        "Timeline Correlation",
        "Network Analysis",
        "Deep Content Analysis"
    ]
    
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
    
    # Click start
    h_page.click("button:has-text('Start Investigation')", "Start Button")
    
    # Wait for error message - using a more resilient text-based search
    try:
        # Streamlit alerts often have 'stNotification' or 'stAlert'
        error_locator = page.get_by_text("Please enter a valid target")
        error_locator.wait_for(state="visible", timeout=8000)
        assert error_locator.is_visible()
        print("✓ Successfully verified empty input validation")
    except Exception as e:
        print(f"Failed to find error message: {e}")
        # Take a screenshot for debugging
        page.screenshot(path="tests/ui/error_failure.png")
        raise e

def test_investigation_lifecycle_ui(page):
    h_page = SelfHealingPage(page)
    
    # Fill target
    h_page.fill("input[aria-label='Target Identifier']", "Test User", "Target Identifier")
    
    # Click start
    h_page.click("button:has-text('Start Investigation')", "Start Button")
    
    # Verify processing button appears (it might happen fast)
    # The button text changes to "⏳ Investigation in progress..."
    processing_btn = h_page.find_element("button:has-text('Investigation in progress')", "Processing Button")
    assert processing_btn is not None
    assert processing_btn.is_disabled()
    
    # Verify Logs expander appears
    logs = h_page.find_element("div[data-testid='stExpander']:has-text('Investigation Logs')", "Logs Expander")
    assert logs is not None
    print("✓ Successfully verified investigation lifecycle UI changes")


def test_disclaimer_visible(page):
    """The EDUCATIONAL USE ONLY disclaimer must be rendered on page load."""
    disclaimer = page.get_by_text("EDUCATIONAL USE ONLY", exact=False)
    disclaimer.wait_for(state="visible", timeout=8000)
    assert disclaimer.is_visible()
    print("✓ Disclaimer is visible")


def test_input_placeholder_text(page):
    """Target input must show the correct placeholder text."""
    target_input = page.locator("input[aria-label='Target Identifier']")
    target_input.wait_for(state="visible", timeout=8000)
    placeholder = target_input.get_attribute("placeholder")
    assert placeholder == "Enter Name, Email, Username, or Phone Number..."
    print(f"✓ Placeholder text correct: '{placeholder}'")


def test_sidebar_info_text(page):
    """Sidebar must show the API keys reminder info box."""
    info = page.locator("section[data-testid='stSidebar']").get_by_text(
        "Ensure you have set up your API keys", exact=False
    )
    info.wait_for(state="visible", timeout=8000)
    assert info.is_visible()
    print("✓ Sidebar API key info text is visible")


def test_whitespace_only_input(page):
    """Input containing only spaces should trigger the same validation error as empty input."""
    h_page = SelfHealingPage(page)

    h_page.fill("input[aria-label='Target Identifier']", "   ", "Target Identifier Input")
    h_page.click("button:has-text('Start Investigation')", "Start Button")

    try:
        error = page.get_by_text("Please enter a valid target", exact=False)
        error.wait_for(state="visible", timeout=8000)
        assert error.is_visible()
        print("✓ Whitespace-only input correctly rejected")
    except Exception as e:
        page.screenshot(path="tests/ui/whitespace_validation_failure.png")
        raise e


def test_toggle_state_changes(page):
    """Clicking a sidebar toggle must actually change its checked state."""
    toggle_labels = ["Timeline Correlation", "Network Analysis", "Deep Content Analysis"]

    for label in toggle_labels:
        # The toggle <input> is a sibling/child of the label — locate via the
        # stToggle container that contains the label text
        toggle_input = page.locator(
            f"div[data-testid='stToggle']:has(p:has-text('{label}')) input"
        )
        toggle_input.wait_for(state="attached", timeout=5000)

        before = toggle_input.get_attribute("aria-checked")
        toggle_input.click()
        page.wait_for_timeout(500)  # allow Streamlit to re-render
        after = toggle_input.get_attribute("aria-checked")

        assert before != after, f"Toggle '{label}' state did not change (stuck at '{before}')"
        print(f"✓ Toggle '{label}': {before} → {after}")
