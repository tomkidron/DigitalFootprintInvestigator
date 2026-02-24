import pytest
from tests.healer import SelfHealingPage

def test_ai_healing_flow(page):
    h_page = SelfHealingPage(page)
    
    # Use a completely broken selector but a good description
    # This should trigger AI healing
    print("\n--- Testing AI Healing for Target Input ---")
    h_page.fill("#non_existent_input_id", "AI Test Target", "Target Identifier Input field")
    
    val = page.locator("input[aria-label='Target Identifier']").input_value()
    assert val == "AI Test Target"
    print("✓ Successfully healed Target Input")

    # Repeat for start button
    print("\n--- Testing AI Healing for Start Button ---")
    btn = h_page.find_element(".broken-button-class", "Start Investigation button")
    assert btn is not None
    print("✓ Successfully healed Start Button")
