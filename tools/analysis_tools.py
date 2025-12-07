"""
Analysis tools for data correlation and pattern extraction
"""

import re
from typing import List
from crewai.tools import tool
from difflib import SequenceMatcher


@tool("Data Correlation")
def correlate_data(data: str) -> str:
    """
    Correlates information from multiple sources to identify connections
    and build a comprehensive profile. Assesses confidence levels for connections.
    
    Args:
        data: The data to analyze and correlate
        
    Returns:
        Correlation analysis with confidence scores
    """
    try:
        # Extract all identifiers
        emails = _extract_emails(data)
        usernames = _extract_usernames(data)
        urls = _extract_urls(data)
        
        output = "Data Correlation Analysis\n"
        output += "=" * 60 + "\n\n"
        
        # Analyze emails
        if emails:
            output += f"Email Addresses Found: {len(emails)}\n"
            for email in emails:
                output += f"  - {email}\n"
            output += "\n"
        
        # Analyze usernames
        if usernames:
            output += f"Usernames Found: {len(usernames)}\n"
            username_patterns = _analyze_username_patterns(usernames)
            for username in usernames:
                output += f"  - {username}\n"
            if username_patterns:
                output += f"\nUsername Patterns: {username_patterns}\n"
            output += "\n"
        
        # Analyze URLs
        if urls:
            platforms = _categorize_urls(urls)
            output += "Platforms Detected:\n"
            for platform, links in platforms.items():
                output += f"  {platform}: {len(links)} link(s)\n"
            output += "\n"
        
        # Cross-correlation
        output += "Cross-Correlation Analysis:\n"
        correlations = _find_correlations(emails, usernames, urls)
        if correlations:
            for correlation in correlations:
                output += f"  - {correlation}\n"
        else:
            output += "  No strong correlations detected\n"
        
        return output
        
    except Exception as e:
        return f"Correlation error: {str(e)}"


@tool("Pattern Extraction")
def extract_patterns(data: str) -> str:
    """
    Extracts patterns from data including naming conventions,
    posting behaviors, interests, and temporal patterns.
    
    Args:
        data: The data to extract patterns from
        
    Returns:
        Pattern analysis results
    """
    try:
        output = "Pattern Extraction Analysis\n"
        output += "=" * 60 + "\n\n"
        
        # Extract naming patterns
        naming_patterns = _extract_naming_patterns(data)
        if naming_patterns:
            output += "Naming Patterns:\n"
            output += naming_patterns + "\n\n"
        
        # Extract temporal patterns
        temporal_patterns = _extract_temporal_patterns(data)
        if temporal_patterns:
            output += "Temporal Patterns:\n"
            output += temporal_patterns + "\n\n"
        
        # Extract interest patterns
        interest_patterns = _extract_interest_patterns(data)
        if interest_patterns:
            output += "Interest Patterns:\n"
            output += interest_patterns + "\n\n"
        
        # Extract location patterns
        location_patterns = _extract_location_patterns(data)
        if location_patterns:
            output += "Location Patterns:\n"
            output += location_patterns + "\n\n"
        
        return output
        
    except Exception as e:
        return f"Pattern extraction error: {str(e)}"


# Helper functions
def _extract_emails(text: str) -> List[str]:
    """Extract email addresses"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(pattern, text)))


def _extract_usernames(text: str) -> List[str]:
    """Extract usernames (@ mentions and profile names)"""
    at_mentions = re.findall(r'@([A-Za-z0-9_]+)', text)
    github_users = re.findall(r'github\.com/([A-Za-z0-9_-]+)', text)
    reddit_users = re.findall(r'reddit\.com/user/([A-Za-z0-9_-]+)', text)
    
    all_usernames = at_mentions + github_users + reddit_users
    return list(set(all_usernames))


def _extract_urls(text: str) -> List[str]:
    """Extract URLs"""
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return list(set(re.findall(pattern, text)))


def _analyze_username_patterns(usernames: List[str]) -> str:
    """Analyze patterns in usernames"""
    if len(usernames) < 2:
        return ""
    
    common_parts = set()
    for i, username1 in enumerate(usernames):
        for username2 in usernames[i+1:]:
            match = SequenceMatcher(None, username1.lower(), username2.lower())
            longest = match.find_longest_match(0, len(username1), 0, len(username2))
            if longest.size >= 4:
                common_parts.add(username1[longest.a:longest.a + longest.size])
    
    if common_parts:
        return f"Common elements: {', '.join(common_parts)}"
    return ""


def _categorize_urls(urls: List[str]) -> dict:
    """Categorize URLs by platform"""
    platforms = {}
    
    platform_patterns = {
        "LinkedIn": r'linkedin\.com',
        "Twitter/X": r'(twitter\.com|x\.com)',
        "GitHub": r'github\.com',
        "Reddit": r'reddit\.com',
        "Facebook": r'facebook\.com',
        "Instagram": r'instagram\.com',
    }
    
    for url in urls:
        categorized = False
        for platform, pattern in platform_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                if platform not in platforms:
                    platforms[platform] = []
                platforms[platform].append(url)
                categorized = True
                break
        
        if not categorized:
            if "Other" not in platforms:
                platforms["Other"] = []
            platforms["Other"].append(url)
    
    return platforms


def _find_correlations(emails: List[str], usernames: List[str], urls: List[str]) -> List[str]:
    """Find correlations between different data points"""
    correlations = []
    confidence_threshold = 0.7
    
    # Check if email username matches any username
    for email in emails:
        email_user = email.split('@')[0]
        for username in usernames:
            similarity = SequenceMatcher(None, email_user.lower(), username.lower()).ratio()
            if similarity > confidence_threshold:
                correlations.append(
                    f"Email '{email}' likely matches username '{username}' "
                    f"(confidence: {similarity:.2%})"
                )
    
    # Check for username consistency across platforms
    if len(usernames) > 1:
        username_counts = {}
        for username in usernames:
            username_lower = username.lower()
            username_counts[username_lower] = username_counts.get(username_lower, 0) + 1
        
        for username, count in username_counts.items():
            if count > 1:
                correlations.append(
                    f"Username '{username}' appears on {count} platforms "
                    f"(high confidence of same person)"
                )
    
    return correlations


def _extract_naming_patterns(text: str) -> str:
    """Extract naming convention patterns"""
    patterns = []
    
    names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
    if names:
        unique_names = list(set(names))
        if len(unique_names) > 0:
            patterns.append(f"  Names found: {', '.join(unique_names[:5])}")
    
    usernames = re.findall(r'@([A-Za-z0-9_]+)', text)
    if usernames:
        has_numbers = any(any(c.isdigit() for c in u) for u in usernames)
        has_underscores = any('_' in u for u in usernames)
        
        if has_numbers:
            patterns.append("  Username pattern: Includes numbers")
        if has_underscores:
            patterns.append("  Username pattern: Uses underscores")
    
    return "\n".join(patterns) if patterns else ""


def _extract_temporal_patterns(text: str) -> str:
    """Extract temporal patterns (dates, times, etc.)"""
    patterns = []
    
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    if years:
        unique_years = sorted(set(years))
        patterns.append(f"  Years mentioned: {', '.join(unique_years)}")
    
    dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
    if dates:
        patterns.append(f"  {len(dates)} date(s) found")
    
    return "\n".join(patterns) if patterns else ""


def _extract_interest_patterns(text: str) -> str:
    """Extract interest and topic patterns"""
    patterns = []
    
    tech_keywords = ['python', 'javascript', 'developer', 'engineer', 'data', 
                    'machine learning', 'ai', 'software', 'programming']
    
    found_interests = [kw for kw in tech_keywords if kw.lower() in text.lower()]
    
    if found_interests:
        patterns.append(f"  Technical interests: {', '.join(found_interests[:5])}")
    
    return "\n".join(patterns) if patterns else ""


def _extract_location_patterns(text: str) -> str:
    """Extract location patterns"""
    patterns = []
    
    location_keywords = ['location:', 'based in', 'from', 'lives in']
    
    for keyword in location_keywords:
        if keyword.lower() in text.lower():
            pattern = rf'{keyword}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                patterns.append(f"  Locations mentioned: {', '.join(set(matches))}")
                break
    
    return "\n".join(patterns) if patterns else ""
