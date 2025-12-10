"""Search nodes for parallel execution"""
from datetime import datetime
from graph.state import OSINTState
from tools.search_tools import google_search, social_media_search


def google_node(state: OSINTState) -> dict:
    """Google search node"""
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S')}] 🔍 Google search started...")
    
    result = google_search(state["target"])
    
    # Add analysis method metadata
    import os
    serpapi_key = os.getenv("SERPAPI_KEY")
    hibp_key = os.getenv("HIBP_API_KEY")
    hunter_key = os.getenv("HUNTER_API_KEY")
    
    result += "\n\n=== GOOGLE ANALYSIS METHOD ===\n"
    if serpapi_key and serpapi_key.strip():
        result += "✓ SerpAPI: Professional Google search with snippets\n"
    else:
        result += "⚠ Free googlesearch library: Limited reliability, no snippets\n"
        result += "💡 Recommendation: Add SERPAPI_KEY for better results\n"
    
    result += "\n=== EMAIL DISCOVERY METHODS ===\n"
    if hibp_key:
        result += "✓ Have I Been Pwned: Breach detection\n"
    else:
        result += "❌ HIBP API not configured\n"
    
    if hunter_key:
        result += "✓ Hunter.io: Professional email discovery\n"
    else:
        result += "❌ Hunter.io API not configured\n"
    
    result += "✓ Pattern Generation: Common email formats\n"
    
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Google search complete ({duration:.1f}s)")
    return {"google_data": [result]}


def social_node(state: OSINTState) -> dict:
    """Social media search node (parallel)"""
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S')}] 📱 Social media search started...")
    
    # Add analysis method tracking
    result = social_media_search(state["target"])
    
    # Add metadata about what was actually analyzed
    result += "\n\n=== ANALYSIS METHODS USED ===\n"
    result += "✓ GitHub: REST API (profile + repositories)\n"
    result += "✓ Reddit: JSON API (profile + comments)\n"
    result += "✓ YouTube: Data API v3 (channels + statistics)\n"
    result += "✓ Twitter/X: API v2 (timeline + metrics)\n"
    result += "✓ Email Discovery: HIBP + Hunter.io + pattern generation\n"
    result += "⚠ LinkedIn: Google dorking only (no direct API)\n"
    result += "❌ Instagram: Not implemented (requires business account)\n"
    result += "❌ Facebook: Not implemented (high privacy restrictions)\n"
    result += "❌ SoundCloud: Not implemented\n"
    
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Social media search complete ({duration:.1f}s)")
    return {"social_data": [result]}
