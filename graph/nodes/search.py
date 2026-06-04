"""Search nodes for parallel execution"""

import os

from graph.nodes._timing import log_done, log_start
from graph.state import OSINTState
from tools.search_tools import google_search, social_media_search


def google_node(state: OSINTState) -> dict:
    """Google search node"""
    start = log_start("Google search")

    config = state.get("config", {}) or {}
    scan_mode = config.get("scan_mode", "advanced")

    result = google_search(state["target"], scan_mode=scan_mode)

    if scan_mode == "quick":
        google_method = "[SKIP] Free googlesearch library: Running Quick Scan (unauthenticated fallback)"
        meta = [
            "",
            "=== GOOGLE ANALYSIS METHOD ===",
            google_method,
            "",
            "=== EMAIL DISCOVERY METHODS ===",
            "[SKIP] Have I Been Pwned: Skipped in Quick Scan",
            "[SKIP] Hunter.io: Skipped in Quick Scan",
            "[SKIP] Pattern Generation: Skipped in Quick Scan (requires breach verification)",
        ]
    else:
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

    config = state.get("config", {}) or {}
    scan_mode = config.get("scan_mode", "advanced")

    result = social_media_search(state["target"], scan_mode=scan_mode)

    if scan_mode == "quick":
        meta = [
            "",
            "=== ANALYSIS METHODS USED ===",
            "[OK] GitHub: REST API (profile + repositories)",
            "[OK] Reddit: JSON API (profile + comments)",
            "[SKIP] YouTube: Skipped in Quick Scan",
            "[SKIP] Twitter/X: Skipped in Quick Scan (Google dorking fallback)",
            "[SKIP] Email Discovery: Skipped in Quick Scan",
            "[WARN] LinkedIn: Google dorking fallback",
            "[WARN] Instagram: Google dorking fallback",
            "[WARN] Facebook: Google dorking fallback",
            "[WARN] SoundCloud: Google dorking fallback",
        ]
    else:
        meta = [
            "",
            "=== ANALYSIS METHODS USED ===",
            "[OK] GitHub: REST API (profile + repositories)",
            "[OK] Reddit: JSON API (profile + comments)",
            "[OK] YouTube: Data API v3 (channels + statistics)",
            "[OK] Twitter/X: API v2 (timeline + metrics)",
            "[OK] Email Discovery: HIBP + Hunter.io + pattern generation",
            "[WARN] LinkedIn: Google dorking fallback",
            "[WARN] Instagram: Google dorking fallback",
            "[WARN] Facebook: Google dorking fallback",
            "[WARN] SoundCloud: Google dorking fallback",
        ]

    result = result + "\n" + "\n".join(meta)

    log_done("Social media search", start)
    return {"social_data": [result]}
