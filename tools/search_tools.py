"""
Search tools for OSINT investigation
"""

import os
import re
import requests
from typing import List, Dict, Any
from crewai_tools import BaseTool
from pydantic import BaseModel, Field


class GoogleSearchInput(BaseModel):
    """Input schema for Google Search"""
    query: str = Field(..., description="The search query to execute")


class GoogleSearchTool(BaseTool):
    name: str = "Google Search"
    description: str = """Performs Google searches and extracts relevant information.
    Use this to find initial information about a target including profiles, mentions,
    and associated identifiers."""
    args_schema: type[BaseModel] = GoogleSearchInput
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.max_results = config['search']['max_results']
        self.timeout = config['search']['timeout']
    
    def _run(self, query: str) -> str:
        """Execute Google search"""
        try:
            # Check if SerpAPI key is available
            serpapi_key = os.getenv("SERPAPI_KEY")
            
            if serpapi_key:
                return self._search_with_serpapi(query, serpapi_key)
            else:
                return self._search_with_googlesearch(query)
                
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def _search_with_serpapi(self, query: str, api_key: str) -> str:
        """Search using SerpAPI (more reliable, requires API key)"""
        try:
            from serpapi import GoogleSearch
            
            params = {
                "q": query,
                "api_key": api_key,
                "num": self.max_results
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract organic results
            findings = []
            if "organic_results" in results:
                for result in results["organic_results"][:self.max_results]:
                    findings.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", "")
                    })
            
            # Format results
            output = f"Google Search Results for: {query}\n\n"
            for i, finding in enumerate(findings, 1):
                output += f"{i}. {finding['title']}\n"
                output += f"   URL: {finding['link']}\n"
                output += f"   {finding['snippet']}\n\n"
            
            # Extract identifiers
            identifiers = self._extract_identifiers("\n".join([f['snippet'] for f in findings]))
            if identifiers:
                output += "\nExtracted Identifiers:\n"
                output += identifiers
            
            return output
            
        except ImportError:
            return "SerpAPI library not installed. Install with: pip install google-search-results"
        except Exception as e:
            return f"SerpAPI search error: {str(e)}"
    
    def _search_with_googlesearch(self, query: str) -> str:
        """Search using googlesearch-python library (free, less reliable)"""
        try:
            from googlesearch import search
            
            results = []
            for url in search(query, num_results=self.max_results, sleep_interval=2):
                results.append(url)
            
            output = f"Google Search Results for: {query}\n\n"
            output += f"Found {len(results)} results:\n\n"
            
            for i, url in enumerate(results, 1):
                output += f"{i}. {url}\n"
            
            output += "\nNote: Using free search. For better results with snippets, add SERPAPI_KEY to .env\n"
            
            return output
            
        except Exception as e:
            return f"Google search error: {str(e)}\nTip: Add SERPAPI_KEY to .env for more reliable searches"
    
    def _extract_identifiers(self, text: str) -> str:
        """Extract emails, phones, usernames from text"""
        identifiers = []
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            identifiers.append(f"Emails: {', '.join(set(emails))}")
        
        # Extract phone numbers (basic pattern)
        phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
        if phones:
            identifiers.append(f"Phones: {', '.join(set(phones))}")
        
        # Extract potential usernames (@ mentions)
        usernames = re.findall(r'@([A-Za-z0-9_]+)', text)
        if usernames:
            identifiers.append(f"Usernames: {', '.join(set(usernames))}")
        
        return "\n".join(identifiers) if identifiers else ""


class SocialMediaSearchInput(BaseModel):
    """Input schema for Social Media Search"""
    target: str = Field(..., description="The target to search for (name, username, email)")
    platforms: List[str] = Field(default=[], description="Specific platforms to search (optional)")


class SocialMediaSearchTool(BaseTool):
    name: str = "Social Media Search"
    description: str = """Searches across multiple social media platforms for profiles and activity.
    Supports LinkedIn, Twitter, GitHub, Reddit, and more."""
    args_schema: type[BaseModel] = SocialMediaSearchInput
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.platforms = {k: v for k, v in config['platforms'].items() if v.get('enabled', False)}
    
    def _run(self, target: str, platforms: List[str] = None) -> str:
        """Search social media platforms"""
        if platforms is None:
            platforms = list(self.platforms.keys())
        
        results = []
        results.append(f"Social Media Search for: {target}\n")
        results.append("=" * 60 + "\n")
        
        for platform in platforms:
            if platform in self.platforms:
                platform_result = self._search_platform(platform, target)
                results.append(platform_result)
        
        return "\n".join(results)
    
    def _search_platform(self, platform: str, target: str) -> str:
        """Search a specific platform"""
        output = f"\n{platform.upper()} Search:\n"
        output += "-" * 40 + "\n"
        
        if platform == "linkedin":
            output += self._search_linkedin(target)
        elif platform == "twitter":
            output += self._search_twitter(target)
        elif platform == "github":
            output += self._search_github(target)
        elif platform == "reddit":
            output += self._search_reddit(target)
        else:
            output += f"Platform {platform} not yet implemented\n"
        
        return output
    
    def _search_linkedin(self, target: str) -> str:
        """Search LinkedIn (via Google dorking)"""
        # LinkedIn requires login for direct API access
        # Using Google dorking as alternative
        query = f'site:linkedin.com/in "{target}"'
        return f"LinkedIn profiles (via Google):\nSearch: {query}\n" \
               f"Tip: Manually search Google for: {query}\n"
    
    def _search_twitter(self, target: str) -> str:
        """Search Twitter/X"""
        # Twitter API requires authentication
        # Providing search strategies
        return f"Twitter/X search strategies:\n" \
               f"1. Search: @{target.replace(' ', '')}\n" \
               f"2. Search: \"{target}\" on twitter.com\n" \
               f"3. Google: site:twitter.com \"{target}\"\n" \
               f"Tip: Add TWITTER_BEARER_TOKEN to .env for API access\n"
    
    def _search_github(self, target: str) -> str:
        """Search GitHub"""
        try:
            # GitHub has a public API
            username = target.replace(" ", "").lower()
            url = f"https://api.github.com/users/{username}"
            
            headers = {}
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers["Authorization"] = f"token {github_token}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                output = f"✓ Found GitHub profile:\n"
                output += f"  Username: {data.get('login')}\n"
                output += f"  Name: {data.get('name', 'N/A')}\n"
                output += f"  Bio: {data.get('bio', 'N/A')}\n"
                output += f"  Location: {data.get('location', 'N/A')}\n"
                output += f"  Public Repos: {data.get('public_repos', 0)}\n"
                output += f"  Followers: {data.get('followers', 0)}\n"
                output += f"  Profile: {data.get('html_url')}\n"
                return output
            else:
                return f"No GitHub profile found for: {username}\n"
                
        except Exception as e:
            return f"GitHub search error: {str(e)}\n"
    
    def _search_reddit(self, target: str) -> str:
        """Search Reddit"""
        try:
            # Reddit has a public API for user profiles
            username = target.replace(" ", "").lower()
            url = f"https://www.reddit.com/user/{username}/about.json"
            
            headers = {"User-Agent": "OSINT Tool 1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get('data', {})
                output = f"✓ Found Reddit profile:\n"
                output += f"  Username: {user_data.get('name')}\n"
                output += f"  Karma: {user_data.get('total_karma', 0)}\n"
                output += f"  Created: {user_data.get('created_utc', 'N/A')}\n"
                output += f"  Profile: https://reddit.com/user/{username}\n"
                return output
            else:
                return f"No Reddit profile found for: {username}\n"
                
        except Exception as e:
            return f"Reddit search error: {str(e)}\n"
