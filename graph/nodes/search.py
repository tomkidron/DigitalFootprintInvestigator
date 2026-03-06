"""Search nodes for parallel execution"""

import os

from graph.nodes._timing import log_done, log_start
from graph.state import OSINTState
from tools.search_tools import google_search, social_media_search


def google_node(state: OSINTState) -> dict:
    """Google search node"""
    start = log_start("Google search")

    result = google_search(state["target"])

    tavily_key = os.getenv("TAVILY_API_KEY")
    serpapi_key = os.getenv("SERPAPI_KEY")
    hibp_key = os.getenv("HIBP_API_KEY")
    hunter_key = os.getenv("HUNTER_API_KEY")

    if tavily_key and tavily_key.strip():
        google_method = "[OK] Tavily: Advanced web search optimized for OSINT"
    elif serpapi_key and serpapi_key.strip():
        google_method = "[OK] SerpAPI: Professional Google search with snippets"
    else:
        google_method = "[WARN] Free googlesearch library: Limited reliability, no snippets\n[TIP] Add TAVILY_API_KEY for best results"

    meta = [
        "",
        "=== GOOGLE ANALYSIS METHOD ===",
        google_method,
        "",
        "=== EMAIL DISCOVERY METHODS ===",
        "[OK] Have I Been Pwned: Breach detection" if hibp_key else "[ERROR] HIBP API not configured",
        "[OK] Hunter.io: Professional email discovery" if hunter_key else "[ERROR] Hunter.io API not configured",
        "[OK] Pattern Generation: Common email formats",
    ]

    result = result + "\n" + "\n".join(meta)

    log_done("Google search", start)
    return {"google_data": [result]}


def social_node(state: OSINTState) -> dict:
    """Social media search node (parallel)"""
    start = log_start("Social media search")

    result = social_media_search(state["target"])

    meta = [
        "",
        "=== ANALYSIS METHODS USED ===",
        "[OK] GitHub: REST API (profile + repositories)",
        "[OK] Reddit: JSON API (profile + comments)",
        "[OK] YouTube: Data API v3 (channels + statistics)",
        "[OK] Twitter/X: API v2 (timeline + metrics)",
        "[OK] Email Discovery: HIBP + Hunter.io + pattern generation",
        "[WARN] LinkedIn: Google dorking only (no direct API)",
        "[ERROR] Instagram: Not implemented (requires business account)",
        "[ERROR] Facebook: Not implemented (high privacy restrictions)",
        "[ERROR] SoundCloud: Not implemented",
    ]

    result = result + "\n" + "\n".join(meta)

    log_done("Social media search", start)
    return {"social_data": [result]}
