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
    if serpapi_key and serpapi_key.strip():
        result += "\n\n=== GOOGLE ANALYSIS METHOD ===\n"
        result += "✓ SerpAPI: Professional Google search with snippets\n"
    else:
        result += "\n\n=== GOOGLE ANALYSIS METHOD ===\n"
        result += "⚠ Free googlesearch library: Limited reliability, no snippets\n"
        result += "💡 Recommendation: Add SERPAPI_KEY for better results\n"
    
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
    result += "⚠ LinkedIn: Google dorking only (no direct API)\n"
    result += "⚠ Twitter/X: Search strategies only (no API access)\n"
    result += "❌ Instagram: Not implemented\n"
    result += "❌ Facebook: Not implemented\n"
    result += "❌ YouTube: Not implemented\n"
    result += "❌ SoundCloud: Not implemented\n"
    
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Social media search complete ({duration:.1f}s)")
    return {"social_data": [result]}
