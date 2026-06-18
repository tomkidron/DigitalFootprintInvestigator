"""Shared LLM factory for the OSINT workflow"""

import os

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(purpose: str = "report") -> ChatGoogleGenerativeAI:
    """Return a configured Google Gemini instance."""
    if purpose == "analysis":
        model = os.getenv("LLM_MODEL_FAST", "gemini-2.5-flash")
    else:
        model = os.getenv("LLM_MODEL", "gemini-2.5-pro")
        
    return ChatGoogleGenerativeAI(model=model, temperature=0)
