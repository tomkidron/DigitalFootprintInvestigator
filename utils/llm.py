"""Shared LLM factory for the OSINT workflow"""

import os

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(purpose: str = "report"):
    """Return a configured Google Gemini instance."""
    if purpose == "analysis":
        model = os.getenv("LLM_MODEL_FAST", "gemini-2.5-flash")
    else:
        model = os.getenv("LLM_MODEL", "gemini-2.5-pro")
        
    llm = ChatGoogleGenerativeAI(model=model, temperature=0, max_retries=5)
    return llm.with_retry(stop_after_attempt=5)
