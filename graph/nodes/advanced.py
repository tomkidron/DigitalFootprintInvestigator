"""Advanced analysis node for timeline correlation and network analysis"""
import json
from datetime import datetime
from typing import Dict, List, Any
from graph.state import OSINTState


def advanced_analysis_node(state: OSINTState) -> Dict[str, Any]:
    """Perform advanced analysis if enabled"""
    print("🔬 Running advanced analysis...")
    
    config = state.get('config', {})
    advanced = config.get('advanced_analysis', {})
    
    timeline_data = None
    network_data = None
    
    # Timeline Correlation Analysis
    if advanced.get('timeline_correlation', False):
        print("  📅 Analyzing timeline correlations...")
        timeline_data = _analyze_timeline_correlation(state)
    
    # Network Analysis
    if advanced.get('network_analysis', False):
        print("  🕸️  Performing network analysis...")
        network_data = _analyze_network_connections(state)
    
    # Deep Content Analysis
    if advanced.get('deep_content_analysis', False):
        print("  📝 Deep content analysis...")
        # This would enhance existing data with deeper content analysis
        _enhance_content_analysis(state)
    
    return {
        "timeline_data": timeline_data,
        "network_data": network_data
    }


def _analyze_timeline_correlation(state: OSINTState) -> Dict[str, Any]:
    """Analyze posting patterns across platforms"""
    # Extract timestamps from collected data
    timestamps = []
    
    # Parse Google data for timestamps
    for item in state.get('google_data', []):
        if 'timestamp' in item:
            timestamps.append({
                'platform': 'google',
                'timestamp': item['timestamp'],
                'content_type': 'search_result'
            })
    
    # Parse social data for timestamps
    for item in state.get('social_data', []):
        if 'timestamp' in item:
            timestamps.append({
                'platform': item.get('platform', 'unknown'),
                'timestamp': item['timestamp'],
                'content_type': item.get('type', 'post')
            })
    
    # Analyze patterns
    patterns = {
        'total_timestamped_items': len(timestamps),
        'platforms_with_timestamps': list(set(t['platform'] for t in timestamps)),
        'activity_clusters': _find_activity_clusters(timestamps),
        'cross_platform_correlations': _find_cross_platform_correlations(timestamps)
    }
    
    return patterns


def _analyze_network_connections(state: OSINTState) -> Dict[str, Any]:
    """Analyze connections between platforms"""
    connections = []
    
    # Extract usernames and identifiers
    identifiers = set()
    
    # From Google data
    for item in state.get('google_data', []):
        if 'username' in item:
            identifiers.add(item['username'])
        if 'email' in item:
            identifiers.add(item['email'])
    
    # From social data
    for item in state.get('social_data', []):
        if 'username' in item:
            identifiers.add(item['username'])
        if 'profile_url' in item:
            identifiers.add(item['profile_url'])
    
    # Analyze connections
    network = {
        'unique_identifiers': len(identifiers),
        'identifier_list': list(identifiers),
        'platform_connections': _map_platform_connections(state),
        'username_consistency': _analyze_username_consistency(identifiers)
    }
    
    return network


def _enhance_content_analysis(state: OSINTState) -> None:
    """Enhance existing data with deeper content analysis"""
    # This would add sentiment analysis, topic modeling, etc.
    # For now, just add a flag that deep analysis was performed
    pass


def _find_activity_clusters(timestamps: List[Dict]) -> List[Dict]:
    """Find clusters of activity across time"""
    if not timestamps:
        return []
    
    # Simple clustering by day
    clusters = {}
    for ts in timestamps:
        try:
            # Parse timestamp (assuming ISO format)
            dt = datetime.fromisoformat(ts['timestamp'].replace('Z', '+00:00'))
            day_key = dt.strftime('%Y-%m-%d')
            
            if day_key not in clusters:
                clusters[day_key] = []
            clusters[day_key].append(ts)
        except:
            continue
    
    return [{'date': k, 'activity_count': len(v), 'platforms': list(set(item['platform'] for item in v))} 
            for k, v in clusters.items()]


def _find_cross_platform_correlations(timestamps: List[Dict]) -> List[Dict]:
    """Find correlations between platform activities"""
    correlations = []
    
    # Group by platform
    by_platform = {}
    for ts in timestamps:
        platform = ts['platform']
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(ts)
    
    # Find temporal correlations (activities within same time window)
    platforms = list(by_platform.keys())
    for i, p1 in enumerate(platforms):
        for p2 in platforms[i+1:]:
            correlation = _calculate_temporal_correlation(by_platform[p1], by_platform[p2])
            if correlation > 0:
                correlations.append({
                    'platform_1': p1,
                    'platform_2': p2,
                    'correlation_score': correlation
                })
    
    return correlations


def _map_platform_connections(state: OSINTState) -> Dict[str, List[str]]:
    """Map connections between platforms"""
    connections = {}
    
    # Extract platform data
    platforms = set()
    
    for item in state.get('google_data', []):
        if 'platform' in item:
            platforms.add(item['platform'])
    
    for item in state.get('social_data', []):
        if 'platform' in item:
            platforms.add(item['platform'])
    
    # For each platform, list connected platforms
    for platform in platforms:
        connections[platform] = list(platforms - {platform})
    
    return connections


def _analyze_username_consistency(identifiers: set) -> Dict[str, Any]:
    """Analyze consistency of usernames across platforms"""
    usernames = [id for id in identifiers if not '@' in id and not 'http' in id]
    
    if not usernames:
        return {'consistency_score': 0, 'common_patterns': []}
    
    # Simple consistency analysis
    common_base = None
    if usernames:
        # Find most common base (simplified)
        common_base = max(set(usernames), key=usernames.count) if usernames else None
    
    return {
        'consistency_score': len(set(usernames)) / len(usernames) if usernames else 0,
        'common_patterns': [common_base] if common_base else [],
        'total_usernames': len(usernames)
    }


def _calculate_temporal_correlation(activities1: List[Dict], activities2: List[Dict]) -> float:
    """Calculate temporal correlation between two sets of activities"""
    if not activities1 or not activities2:
        return 0.0
    
    # Simple correlation: count activities within 24 hours of each other
    correlations = 0
    total_comparisons = 0
    
    for a1 in activities1:
        for a2 in activities2:
            total_comparisons += 1
            try:
                dt1 = datetime.fromisoformat(a1['timestamp'].replace('Z', '+00:00'))
                dt2 = datetime.fromisoformat(a2['timestamp'].replace('Z', '+00:00'))
                
                # If within 24 hours, count as correlation
                if abs((dt1 - dt2).total_seconds()) < 86400:  # 24 hours
                    correlations += 1
            except:
                continue
    
    return correlations / total_comparisons if total_comparisons > 0 else 0.0