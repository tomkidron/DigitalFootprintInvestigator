import os
import logging
from playwright.sync_api import Page, ElementHandle
from typing import Optional, List

logger = logging.getLogger(__name__)

class SelfHealingPage:
    def __init__(self, page: Page):
        self.page = page

    def find_element(self, selector: str, description: str = "") -> ElementHandle:
        """
        Attempts to find an element using the primary selector. 
        If it fails, it tries fallback strategies and AI-based healing.
        """
        try:
            # 1. Primary Locator
            element = self.page.wait_for_selector(selector, timeout=5000)
            if element:
                return element
        except Exception as e:
            logger.warning(f"Primary selector '{selector}' failed. Attempting healing...")
            
        # 2. Fallback: Data-Testid
        if "data-testid" not in selector:
            testid_selector = f"[data-testid='{selector.strip('#').strip('.')}']"
            try:
                return self.page.wait_for_selector(testid_selector, timeout=2000)
            except:
                pass

        # 3. Fallback: Text content (if description provided)
        if description:
            try:
                return self.page.locator(f"text='{description}'").first.element_handle(timeout=2000)
            except:
                pass

        # 4. AI Healing (Simulation for now, call LLM if configured)
        return self._ai_heal(selector, description)

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

                snapshot.append({
                    "index": len(snapshot),
                    "tag": tag,
                    "text": text[:100], # Truncate long text
                    "placeholder": placeholder,
                    "testid": testid,
                    "aria-label": aria,
                    "id": el.get_attribute("id") or ""
                })
            except:
                continue
        return snapshot

    def _ai_heal(self, selector: str, description: str) -> ElementHandle:
        """
        Uses an LLM to find the most likely element from a DOM snapshot.
        """
        from langchain_anthropic import ChatAnthropic
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        import json

        logger.info(f"Triggering AI healing for '{description}' (failed selector: {selector})")
        
        dom_snapshot = self._extract_dom_snapshot()
        if not dom_snapshot:
             raise Exception("AI Healing failed: No interactive elements found in DOM snapshot.")

        provider = os.getenv("LLM_PROVIDER", "anthropic")
        model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20240620")
        llm = ChatAnthropic(model=model, temperature=0, timeout=30) if provider == "anthropic" else ChatOpenAI(model=model, temperature=0, timeout=30)

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
            response = llm.invoke([
                SystemMessage(content="You are a QA automation expert specializing in self-healing UI tests."),
                HumanMessage(content=prompt)
            ])
            
            # Extract JSON from response (handling potential markdown wrapping)
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            suggested_selector = result.get("suggested_selector")
            logger.info(f"AI suggested new selector: {suggested_selector} (Reason: {result.get('reason')})")
            
            return self.page.wait_for_selector(suggested_selector, timeout=5000)
        except Exception as e:
            logger.error(f"AI healing failed: {str(e)}")
            raise Exception(f"Failed to find element '{selector}' even with AI healing logic. AI Error: {str(e)}")

    def click(self, selector: str, description: str = ""):
        element = self.find_element(selector, description)
        element.click()

    def fill(self, selector: str, value: str, description: str = ""):
        element = self.find_element(selector, description)
        element.fill(value)
