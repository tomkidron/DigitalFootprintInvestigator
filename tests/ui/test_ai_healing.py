from unittest.mock import MagicMock, patch

import pytest

from tests.healer import SelfHealingPage


@pytest.mark.local_only
def test_ai_healing_flow(page):
    h_page = SelfHealingPage(page)

    def side_effect(messages, **kwargs):
        prompt = messages[1].content
        if "Target Identifier" in prompt:
            return MagicMock(
                content='{"suggested_selector": "input[aria-label=\'Target Identifier\']", "reason": "matches description"}'
            )
        else:
            return MagicMock(
                content='{"suggested_selector": "button:has-text(\'Start Investigation\')", "reason": "matches description"}'
            )

    with patch("langchain_anthropic.ChatAnthropic") as mock_chat:
        mock_instance = MagicMock()
        mock_instance.invoke.side_effect = side_effect
        mock_chat.return_value = mock_instance

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
