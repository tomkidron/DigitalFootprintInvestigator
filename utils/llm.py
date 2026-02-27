"""Shared LLM factory for the OSINT workflow"""

import os

from langchain_anthropic import ChatAnthropic


def get_llm() -> ChatAnthropic:
    """Return a configured Anthropic Claude instance."""
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    return ChatAnthropic(model=model, temperature=0)
