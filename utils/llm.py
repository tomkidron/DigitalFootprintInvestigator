"""Shared LLM factory for the OSINT workflow"""

import os

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(purpose: str = "report"):
    """Return a configured Google Gemini instance."""
    if purpose == "analysis":
        model = os.getenv("LLM_MODEL_FAST", "gemini-2.5-flash")
    else:
        model = os.getenv("LLM_MODEL", "gemini-2.5-pro")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model=model, temperature=0, max_retries=5, api_key=api_key)
    return llm.with_retry(stop_after_attempt=5)
