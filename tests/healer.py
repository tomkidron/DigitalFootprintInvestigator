import logging
import os
from typing import List

from playwright.sync_api import Locator, Page

logger = logging.getLogger(__name__)


class SelfHealingPage:
    # Class-level cache for healed selectors across the test run
    _healed_cache = {}

    def __init__(self, page: Page):
        self.page = page

    def find_element(self, selector: str, description: str = "") -> Locator:
        """
        Attempts to find an element using the primary selector.
        If it fails, it tries fallback strategies and AI-based healing.
        """
        # 0. Check cache
        cache_key = f"{selector}::{description}"
        if cache_key in self.__class__._healed_cache:
            healed_selector = self.__class__._healed_cache[cache_key]
            logger.info(f"Using cached healed selector: {healed_selector} for {cache_key}")
            return self.page.locator(healed_selector)

        try:
            # 1. Primary Locator
            locator = self.page.locator(selector).first
            locator.wait_for(state="attached", timeout=5000)
            return locator
        except Exception:
            logger.warning(f"Primary selector '{selector}' failed. Attempting healing...")

        # 2. Fallback: Data-Testid
        if "data-testid" not in selector:
            testid = selector.strip('#').strip('.')
            try:
                locator = self.page.get_by_test_id(testid).first
                locator.wait_for(state="attached", timeout=2000)
                return locator
            except Exception:
                pass

        # 3. Fallback: Text content (if description provided)
        if description:
            try:
                locator = self.page.get_by_text(description).first
                locator.wait_for(state="attached", timeout=2000)
                return locator
            except Exception:
                pass

        # 4. AI Healing
        if os.getenv("ENABLE_AI_HEALING", "false").lower() == "true":
            return self._ai_heal(selector, description, cache_key)
        else:
            raise Exception(f"Failed to find element '{selector}'. AI Healing is disabled (set ENABLE_AI_HEALING=true to enable).")

    def _extract_dom_snapshot(self) -> List[dict]:
        """
        Extracts metadata of interactive elements for the LLM context.
        """
        # We only care about buttons, inputs, and elements with data-testid or roles
        elements = self.page.query_selector_all("button, input, [role='button'], [data-testid], select")
        snapshot = []
        for i, el in enumerate(elements):
            try:
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                text = (el.inner_text() or "").strip()
                placeholder = el.get_attribute("placeholder") or ""
                testid = el.get_attribute("data-testid") or ""
                aria = el.get_attribute("aria-label") or ""

                # Only include elements that have SOMETHING identifying them
                if not any([text, placeholder, testid, aria]):
                    continue

                snapshot.append(
                    {
                        "index": len(snapshot),
                        "tag": tag,
                        "text": text[:100],  # Truncate long text
                        "placeholder": placeholder,
                        "testid": testid,
                        "aria-label": aria,
                        "id": el.get_attribute("id") or "",
                    }
                )
            except Exception:
                continue
        return snapshot

    def _ai_heal(self, selector: str, description: str, cache_key: str = None) -> Locator:
        """
        Uses an LLM to find the most likely element from a DOM snapshot.
        """
        import json

        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_google_genai import ChatGoogleGenerativeAI

        logger.info(f"Triggering AI healing for '{description}' (failed selector: {selector})")

        dom_snapshot = self._extract_dom_snapshot()
        if not dom_snapshot:
            raise Exception("AI Healing failed: No interactive elements found in DOM snapshot.")

        model = os.getenv("LLM_MODEL_FAST", "gemini-2.5-flash")
        llm = ChatGoogleGenerativeAI(model=model, temperature=0, timeout=30)

        prompt = f"""
        A UI test failed to find an element with selector: {selector}
        Description of the desired element: {description}

        Here is a snapshot of interactive elements currently on the page:
        {json.dumps(dom_snapshot, indent=2)}

        Identify which element from the list most likely corresponds to the description.
        Return ONLY a JSON object with:
        1. "index": the value of the "index" field from the snapshot for the matching element
        2. "reason": a short explanation of why this matches
        3. "suggested_selector": a reliable Playwright-specific selector for this element.
           - Prefer data-testid: "[data-testid='...']"
           - Or aria-label: "[aria-label='...']"
           - Or placeholder: "input[placeholder='...']"
           - Or text: "button:has-text('...')"
        """

        try:
            response = llm.invoke(
                [
                    SystemMessage(content="You are a QA automation expert specializing in self-healing UI tests."),
                    HumanMessage(content=prompt),
                ]
            )

            # Extract JSON from response (handling potential markdown wrapping)
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            suggested_selector = result.get("suggested_selector")
            logger.info(f"AI suggested new selector: {suggested_selector} (Reason: {result.get('reason')})")

            if cache_key:
                self.__class__._healed_cache[cache_key] = suggested_selector
                self._persist_healed_selector(selector, description, suggested_selector)

            locator = self.page.locator(suggested_selector).first
            locator.wait_for(state="attached", timeout=5000)
            return locator
        except Exception as e:
            logger.error(f"AI healing failed: {str(e)}")
            raise Exception(f"Failed to find element '{selector}' even with AI healing logic. AI Error: {str(e)}")

    def click(self, selector: str, description: str = ""):
        element = self.find_element(selector, description)
        element.click(force=True)

    def fill(self, selector: str, value: str, description: str = ""):
        element = self.find_element(selector, description)
        element.fill(value)

    def _persist_healed_selector(self, original: str, description: str, suggested: str):
        try:
            import json
            filepath = os.path.join("tests", "healed_selectors.json")
            data = {}
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            key = f"{original}::{description}"
            data[key] = suggested
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.warning(f"Failed to persist healed selector: {e}")
