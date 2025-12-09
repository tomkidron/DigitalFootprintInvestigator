"""Search nodes for parallel execution"""
from datetime import datetime
from graph.state import OSINTState
from tools.search_tools import google_search, social_media_search


def google_node(state: OSINTState) -> dict:
    """Google search node"""
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S')}] 🔍 Google search started...")
    result = google_search(state["target"])
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Google search complete ({duration:.1f}s)")
    return {"google_data": [result]}


def social_node(state: OSINTState) -> dict:
    """Social media search node (parallel)"""
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S')}] 📱 Social media search started...")
    result = social_media_search(state["target"])
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Social media search complete ({duration:.1f}s)")
    return {"social_data": [result]}
