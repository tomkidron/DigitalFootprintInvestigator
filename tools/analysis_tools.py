"""
Analysis tools for data correlation and pattern extraction
"""

import re
from typing import List, Dict, Any
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from difflib import SequenceMatcher


class DataCorrelationInput(BaseModel):
    """Input schema for Data Correlation"""
    data: str = Field(..., description="The data to analyze and correlate")


class DataCorrelationTool(BaseTool):
    name: str = "Data Correlation"
    description: str = """Correlates information from multiple sources to identify connections
    and build a comprehensive profile. Assesses confidence levels for connections."""
    args_schema: type[BaseModel] = DataCorrelationInput
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.confidence_threshold = config['agents']['analysis_agent']['confidence_threshold']
    
    def _run(self, data: str) -> str:
        """Correlate data and identify connections"""
        try:
            # Extract all identifiers
            emails = self._extract_emails(data)
            usernames = self._extract_usernames(data)
            urls = self._extract_urls(data)
            
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
                username_patterns = self._analyze_username_patterns(usernames)
                for username in usernames:
                    output += f"  - {username}\n"
                if username_patterns:
                    output += f"\nUsername Patterns: {username_patterns}\n"
                output += "\n"
            
            # Analyze URLs
            if urls:
                platforms = self._categorize_urls(urls)
                output += "Platforms Detected:\n"
                for platform, links in platforms.items():
                    output += f"  {platform}: {len(links)} link(s)\n"
                output += "\n"
            
            # Cross-correlation
            output += "Cross-Correlation Analysis:\n"
            correlations = self._find_correlations(emails, usernames, urls)
            if correlations:
                for correlation in correlations:
                    output += f"  - {correlation}\n"
            else:
                output += "  No strong correlations detected\n"
            
            return output
            
        except Exception as e:
            return f"Correlation error: {str(e)}"
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(pattern, text)))
    
    def _extract_usernames(self, text: str) -> List[str]:
        """Extract usernames (@ mentions and profile names)"""
        # @ mentions
        at_mentions = re.findall(r'@([A-Za-z0-9_]+)', text)
        
        # GitHub/Reddit usernames from URLs
        github_users = re.findall(r'github\.com/([A-Za-z0-9_-]+)', text)
        reddit_users = re.findall(r'reddit\.com/user/([A-Za-z0-9_-]+)', text)
        
        all_usernames = at_mentions + github_users + reddit_users
        return list(set(all_usernames))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(pattern, text)))
    
    def _analyze_username_patterns(self, usernames: List[str]) -> str:
        """Analyze patterns in usernames"""
        if len(usernames) < 2:
            return ""
        
        # Find common substrings
        common_parts = set()
        for i, username1 in enumerate(usernames):
            for username2 in usernames[i+1:]:
                # Find longest common substring
                match = SequenceMatcher(None, username1.lower(), username2.lower())
                longest = match.find_longest_match(0, len(username1), 0, len(username2))
                if longest.size >= 4:  # At least 4 characters in common
                    common_parts.add(username1[longest.a:longest.a + longest.size])
        
        if common_parts:
            return f"Common elements: {', '.join(common_parts)}"
        return ""
    
    def _categorize_urls(self, urls: List[str]) -> Dict[str, List[str]]:
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
    
    def _find_correlations(self, emails: List[str], usernames: List[str], urls: List[str]) -> List[str]:
        """Find correlations between different data points"""
        correlations = []
        
        # Check if email username matches any username
        for email in emails:
            email_user = email.split('@')[0]
            for username in usernames:
                similarity = SequenceMatcher(None, email_user.lower(), username.lower()).ratio()
                if similarity > self.confidence_threshold:
                    correlations.append(
                        f"Email '{email}' likely matches username '{username}' "
                        f"(confidence: {similarity:.2%})"
                    )
        
        # Check for username consistency across platforms
        if len(usernames) > 1:
            # If same username appears on multiple platforms
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


class PatternExtractionInput(BaseModel):
    """Input schema for Pattern Extraction"""
    data: str = Field(..., description="The data to extract patterns from")


class PatternExtractionTool(BaseTool):
    name: str = "Pattern Extraction"
    description: str = """Extracts patterns from data including naming conventions,
    posting behaviors, interests, and temporal patterns."""
    args_schema: type[BaseModel] = PatternExtractionInput
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
    
    def _run(self, data: str) -> str:
        """Extract patterns from data"""
        try:
            output = "Pattern Extraction Analysis\n"
            output += "=" * 60 + "\n\n"
            
            # Extract naming patterns
            naming_patterns = self._extract_naming_patterns(data)
            if naming_patterns:
                output += "Naming Patterns:\n"
                output += naming_patterns + "\n\n"
            
            # Extract temporal patterns
            temporal_patterns = self._extract_temporal_patterns(data)
            if temporal_patterns:
                output += "Temporal Patterns:\n"
                output += temporal_patterns + "\n\n"
            
            # Extract interest patterns
            interest_patterns = self._extract_interest_patterns(data)
            if interest_patterns:
                output += "Interest Patterns:\n"
                output += interest_patterns + "\n\n"
            
            # Extract location patterns
            location_patterns = self._extract_location_patterns(data)
            if location_patterns:
                output += "Location Patterns:\n"
                output += location_patterns + "\n\n"
            
            return output
            
        except Exception as e:
            return f"Pattern extraction error: {str(e)}"
    
    def _extract_naming_patterns(self, text: str) -> str:
        """Extract naming convention patterns"""
        patterns = []
        
        # Look for name variations
        names = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
        if names:
            unique_names = list(set(names))
            if len(unique_names) > 0:
                patterns.append(f"  Names found: {', '.join(unique_names[:5])}")
        
        # Look for username patterns (numbers, underscores, etc.)
        usernames = re.findall(r'@([A-Za-z0-9_]+)', text)
        if usernames:
            has_numbers = any(any(c.isdigit() for c in u) for u in usernames)
            has_underscores = any('_' in u for u in usernames)
            
            if has_numbers:
                patterns.append("  Username pattern: Includes numbers")
            if has_underscores:
                patterns.append("  Username pattern: Uses underscores")
        
        return "\n".join(patterns) if patterns else ""
    
    def _extract_temporal_patterns(self, text: str) -> str:
        """Extract temporal patterns (dates, times, etc.)"""
        patterns = []
        
        # Look for years
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years:
            unique_years = sorted(set(years))
            patterns.append(f"  Years mentioned: {', '.join(unique_years)}")
        
        # Look for dates
        dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
        if dates:
            patterns.append(f"  {len(dates)} date(s) found")
        
        return "\n".join(patterns) if patterns else ""
    
    def _extract_interest_patterns(self, text: str) -> str:
        """Extract interest and topic patterns"""
        patterns = []
        
        # Common tech/professional keywords
        tech_keywords = ['python', 'javascript', 'developer', 'engineer', 'data', 
                        'machine learning', 'ai', 'software', 'programming']
        
        found_interests = [kw for kw in tech_keywords if kw.lower() in text.lower()]
        
        if found_interests:
            patterns.append(f"  Technical interests: {', '.join(found_interests[:5])}")
        
        return "\n".join(patterns) if patterns else ""
    
    def _extract_location_patterns(self, text: str) -> str:
        """Extract location patterns"""
        patterns = []
        
        # Look for location indicators
        location_keywords = ['location:', 'based in', 'from', 'lives in']
        
        for keyword in location_keywords:
            if keyword.lower() in text.lower():
                # Try to extract location after keyword
                pattern = rf'{keyword}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    patterns.append(f"  Locations mentioned: {', '.join(set(matches))}")
                    break
        
        return "\n".join(patterns) if patterns else ""
