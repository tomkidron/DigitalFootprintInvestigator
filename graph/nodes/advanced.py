"""Advanced analysis node for timeline correlation and network analysis"""

from datetime import datetime
from typing import Any, Dict, List

from graph.state import OSINTState


def advanced_analysis_node(state: OSINTState) -> Dict[str, Any]:
    """Perform advanced analysis if enabled"""
    print("Running advanced analysis...")

    config = state.get("config", {})
    advanced = config.get("advanced_analysis", {})

    timeline_data = None
    network_data = None

    if advanced.get("timeline_correlation", False):
        print("  Analyzing timeline correlations...")
        timeline_data = _analyze_timeline_correlation(state)

    if advanced.get("network_analysis", False):
        print("  Performing network analysis...")
        network_data = _analyze_network_connections(state)

    return {"timeline_data": timeline_data, "network_data": network_data}


def _analyze_timeline_correlation(state: OSINTState) -> Dict[str, Any]:
    """Analyze posting patterns across platforms"""
    timestamps = []

    for item in state.get("google_data", []):
        if "timestamp" in item:
            timestamps.append({"platform": "google", "timestamp": item["timestamp"], "content_type": "search_result"})

    for item in state.get("social_data", []):
        if "timestamp" in item:
            timestamps.append(
                {
                    "platform": item.get("platform", "unknown"),
                    "timestamp": item["timestamp"],
                    "content_type": item.get("type", "post"),
                }
            )

    return {
        "total_timestamped_items": len(timestamps),
        "platforms_with_timestamps": list(set(t["platform"] for t in timestamps)),
        "activity_clusters": _find_activity_clusters(timestamps),
        "cross_platform_correlations": _find_cross_platform_correlations(timestamps),
    }


def _analyze_network_connections(state: OSINTState) -> Dict[str, Any]:
    """Analyze connections between platforms"""
    identifiers = set()

    for item in state.get("google_data", []):
        if "username" in item:
            identifiers.add(item["username"])
        if "email" in item:
            identifiers.add(item["email"])

    for item in state.get("social_data", []):
        if "username" in item:
            identifiers.add(item["username"])
        if "profile_url" in item:
            identifiers.add(item["profile_url"])

    return {
        "unique_identifiers": len(identifiers),
        "identifier_list": list(identifiers),
        "platform_connections": _map_platform_connections(state),
        "username_consistency": _analyze_username_consistency(identifiers),
    }


def _find_activity_clusters(timestamps: List[Dict]) -> List[Dict]:
    """Find clusters of activity across time"""
    if not timestamps:
        return []

    clusters = {}
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts["timestamp"].replace("Z", "+00:00"))
            day_key = dt.strftime("%Y-%m-%d")
            clusters.setdefault(day_key, []).append(ts)
        except Exception:
            continue

    return [
        {"date": k, "activity_count": len(v), "platforms": list(set(item["platform"] for item in v))}
        for k, v in clusters.items()
    ]


def _find_cross_platform_correlations(timestamps: List[Dict]) -> List[Dict]:
    """Find correlations between platform activities"""
    by_platform: Dict[str, list] = {}
    for ts in timestamps:
        by_platform.setdefault(ts["platform"], []).append(ts)

    correlations = []
    platforms = list(by_platform.keys())
    for i, p1 in enumerate(platforms):
        for p2 in platforms[i + 1 :]:
            score = _calculate_temporal_correlation(by_platform[p1], by_platform[p2])
            if score > 0:
                correlations.append({"platform_1": p1, "platform_2": p2, "correlation_score": score})

    return correlations


def _map_platform_connections(state: OSINTState) -> Dict[str, List[str]]:
    """Map connections between platforms"""
    platforms = set()

    for item in state.get("google_data", []):
        if "platform" in item:
            platforms.add(item["platform"])

    for item in state.get("social_data", []):
        if "platform" in item:
            platforms.add(item["platform"])

    return {platform: list(platforms - {platform}) for platform in platforms}


def _analyze_username_consistency(identifiers: set) -> Dict[str, Any]:
    """Analyze consistency of usernames across platforms"""
    usernames = [id for id in identifiers if "@" not in id and "http" not in id]

    if not usernames:
        return {"consistency_score": 0, "common_patterns": []}

    common_base = max(set(usernames), key=usernames.count)
    return {
        "consistency_score": len(set(usernames)) / len(usernames),
        "common_patterns": [common_base],
        "total_usernames": len(usernames),
    }


def _calculate_temporal_correlation(activities1: List[Dict], activities2: List[Dict]) -> float:
    """Calculate temporal correlation between two sets of activities"""
    if not activities1 or not activities2:
        return 0.0

    correlations = 0
    total_comparisons = 0

    for a1 in activities1:
        for a2 in activities2:
            total_comparisons += 1
            try:
                dt1 = datetime.fromisoformat(a1["timestamp"].replace("Z", "+00:00"))
                dt2 = datetime.fromisoformat(a2["timestamp"].replace("Z", "+00:00"))
                if abs((dt1 - dt2).total_seconds()) < 86400:  # 24 hours
                    correlations += 1
            except Exception:
                continue

    return correlations / total_comparisons if total_comparisons > 0 else 0.0
