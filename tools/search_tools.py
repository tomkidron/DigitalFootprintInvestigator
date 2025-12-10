"""
Search tools for OSINT investigation
"""

import os
import re
import logging
import requests
from time import sleep
from pathlib import Path

logger = logging.getLogger("osint_tool")


def write_checkpoint(name, query, output, out_dir, fmt):
    """Stub for checkpoint writing"""
    pass


def google_search(query: str) -> str:
    """
    Performs Google searches and extracts relevant information.
    Use this to find initial information about a target including profiles, mentions,
    and associated identifiers.

    Args:
        query: The search query to execute

    Returns:
        Search results with URLs and extracted identifiers
    """
    logger.info(f"Google Search initiated for query: {query}")

    try:
        # Add delay to avoid rate-limiting (important for free tier)
        sleep(2)

        # Check if SerpAPI key is available
        serpapi_key = os.getenv("SERPAPI_KEY")

        if serpapi_key and serpapi_key.strip():
            logger.debug("Using SerpAPI for Google search")
            return _search_with_serpapi(query, serpapi_key)
        else:
            logger.warning(
                "SERPAPI_KEY not configured. Using fallback googlesearch library (limited reliability). Recommend setting SERPAPI_KEY in .env"
            )
            result = _search_with_googlesearch(query)
            if "error" in result.lower() or "not found" in result.lower():
                logger.warning(
                    f"Fallback search returned limited results for query: {query}"
                )
            return result

    except Exception as e:
        logger.error(f"Google search error: {str(e)}", exc_info=True)
        return f"Search error: {str(e)}"


def _search_with_serpapi(query: str, api_key: str) -> str:
    """Search using SerpAPI (more reliable, requires API key)"""
    try:
        from serpapi import GoogleSearch

        params = {"q": query, "api_key": api_key, "num": 20}

        logger.debug(f"SerpAPI request: {query}")
        search = GoogleSearch(params)

        try:
            results = search.get_dict()
        except Exception as timeout_err:
            logger.warning(
                f"SerpAPI timeout/rate limit on query: {query}. Error: {str(timeout_err)}"
            )
            return f"⚠️ SerpAPI Rate Limit or Timeout\n\nQuery: {query}\n\nNote: SerpAPI may have rate-limited this request. Try again in a moment.\n"

        # Extract organic results
        findings = []
        if "organic_results" in results:
            for result in results["organic_results"][:20]:
                findings.append(
                    {
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                    }
                )

        # Format results
        output = f"Google Search Results for: {query}\n\n"
        for i, finding in enumerate(findings, 1):
            output += f"{i}. {finding['title']}\n"
            output += f"   URL: {finding['link']}\n"
            output += f"   {finding['snippet']}\n\n"

        # Extract identifiers
        identifiers = _extract_identifiers("\n".join([f["snippet"] for f in findings]))
        if identifiers:
            output += "\nExtracted Identifiers:\n"
            output += identifiers

        logger.info(f"SerpAPI returned {len(findings)} results for: {query}")
        # write checkpoint for google search
        try:
            write_checkpoint(
                "google", query, output, out_dir=Path("reports/checkpoints"), fmt="txt"
            )
        except Exception:
            logger.debug("Failed to write google checkpoint")
        return output

    except ImportError:
        logger.error("google-search-results library not installed")
        return "google-search-results library not installed. Install with: pip install google-search-results\n"
    except Exception as e:
        logger.error(f"SerpAPI search error: {str(e)}", exc_info=True)
        return f"SerpAPI search error: {str(e)}\nPlease check your SERPAPI_KEY and try again."


def _search_with_googlesearch(query: str) -> str:
    """Search using googlesearch-python library (free, less reliable)"""
    try:
        from googlesearch import search

        results = []
        try:
            for url in search(query, num_results=20, sleep_interval=2, timeout=10):
                results.append(url)
        except Exception as e:
            logger.warning(
                f"Googlesearch library error (may be rate limited): {str(e)}"
            )
            # Return graceful error message
            return (
                f"\n⚠️ WARNING: Search results may be incomplete\n\nGoogle Search Results for: {query}\n"
                f"Search Status: Limited/Rate-limited (free library with no API key)\n\n"
                f"Status: {len(results)} results collected before timeout\n\n"
                f"RECOMMENDATION: Add SERPAPI_KEY to .env for reliable Google searches\n"
                f"This will provide accurate result counts and snippets.\n\n"
                f"Current Results:\n"
            )

        if not results:
            output = f"\n⚠️ WARNING: No results returned (possible rate limiting)\n\n"
            output += f"Google Search Results for: {query}\n"
            output += f"Search Status: UNRELIABLE (using free googlesearch library without API key)\n\n"
            output += f"The free googlesearch library may be rate-limited or blocked.\n"
            output += f"RECOMMENDATION: Add SERPAPI_KEY to .env for accurate searches\n"
            try:
                write_checkpoint(
                    "google",
                    query,
                    output,
                    out_dir=Path("reports/checkpoints"),
                    fmt="txt",
                )
            except Exception:
                logger.debug("Failed to write google checkpoint")
            return output

        output = f"Google Search Results for: {query}\n"
        output += f"Found {len(results)} results (using free search library):\n\n"

        for i, url in enumerate(results, 1):
            output += f"{i}. {url}\n"

        output += "\n⚠️ Note: Using free search without API key. Results may be incomplete due to rate-limiting.\n"
        output += "For reliable results with snippets, add SERPAPI_KEY to .env\n"

        try:
            write_checkpoint(
                "google", query, output, out_dir=Path("reports/checkpoints"), fmt="txt"
            )
        except Exception:
            logger.debug("Failed to write google checkpoint")

        return output

    except ImportError:
        logger.error("googlesearch library not installed")
        return (
            "googlesearch library not installed. Install with: pip install google-search-results\n"
            "Or add SERPAPI_KEY to .env for more reliable searches."
        )
    except Exception as e:
        logger.error(f"Fallback search error: {str(e)}")
        return f"Google search error: {str(e)}\nTip: Add SERPAPI_KEY to .env for more reliable searches"


def _extract_identifiers(text: str) -> str:
    """Extract emails, phones, usernames from text"""
    identifiers = []

    # Extract emails
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    if emails:
        identifiers.append(f"Emails: {', '.join(set(emails))}")

    # Extract phone numbers (basic pattern)
    phones = re.findall(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", text)
    if phones:
        identifiers.append(f"Phones: {', '.join(set(phones))}")

    # Extract potential usernames (@ mentions)
    usernames = re.findall(r"@([A-Za-z0-9_]+)", text)
    if usernames:
        identifiers.append(f"Usernames: {', '.join(set(usernames))}")

    return "\n".join(identifiers) if identifiers else ""


def social_media_search(target: str) -> str:
    """
    Searches across multiple social media platforms for profiles and activity.
    Supports LinkedIn, Twitter, GitHub, Reddit, and more.

    Args:
        target: The target to search for (name, username, email)

    Returns:
        Results from multiple social media platforms
    """
    results = []
    results.append(f"Social Media Search for: {target}\n")
    results.append("=" * 60 + "\n")

    # Search each platform (only implemented ones)
    platforms = ["linkedin", "twitter", "github", "reddit", "instagram", "facebook", "youtube", "soundcloud"]
    for platform in platforms:
        platform_result = _search_platform(platform, target)
        results.append(platform_result)

    full = "\n".join(results)
    try:
        write_checkpoint(
            "social", target, full, out_dir=Path("reports/checkpoints"), fmt="txt"
        )
    except Exception:
        logger.debug("Failed to write social checkpoint")
    return full


def _search_platform(platform: str, target: str) -> str:
    """Search a specific platform"""
    output = f"\n{platform.upper()} Search:\n"
    output += "-" * 40 + "\n"

    if platform == "linkedin":
        output += _search_linkedin(target)
    elif platform == "twitter":
        output += _search_twitter(target)
    elif platform == "github":
        output += _search_github(target)
    elif platform == "reddit":
        output += _search_reddit(target)
    elif platform in ["instagram", "facebook", "youtube", "soundcloud"]:
        output += f"❌ {platform.upper()}: Not implemented\n"
        output += f"Manual search required: Search '{target}' on {platform}.com\n"
        output += f"Note: {platform.title()} API requires special access/approval\n"
    else:
        output += f"❌ Platform {platform} not yet implemented\n"

    return output


def _search_linkedin(target: str) -> str:
    """Search LinkedIn (via Google dorking)"""
    query = f'site:linkedin.com/in "{target}"'
    return (
        f"⚠️ LinkedIn: Google dorking only (no direct API)\n"
        f"Search query: {query}\n"
        f"Manual verification required\n"
        f"Note: LinkedIn API requires special partnership\n"
    )


def _search_twitter(target: str) -> str:
    """Search Twitter/X"""
    return (
        f"❌ Twitter/X: Not implemented (search strategies only)\n"
        f"Manual search recommendations:\n"
        f"1. Search: @{target.replace(' ', '')}\n"
        f'2. Search: "{target}" on twitter.com\n'
        f'3. Google: site:twitter.com "{target}"\n'
        f"Note: Add TWITTER_BEARER_TOKEN to .env for API access\n"
    )


def _search_github(target: str) -> str:
    """Search GitHub with repository analysis"""
    try:
        username = target.replace(" ", "").lower()
        headers = {"User-Agent": "OSINT Tool 1.0"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        # Get profile info
        profile_url = f"https://api.github.com/users/{username}"
        response = requests.get(profile_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return f"No GitHub profile found for: {username}\n"
            
        data = response.json()
        output = f"✓ Found GitHub profile:\n"
        output += f"  Username: {data.get('login')}\n"
        output += f"  Name: {data.get('name', 'N/A')}\n"
        output += f"  Bio: {data.get('bio', 'N/A')}\n"
        output += f"  Location: {data.get('location', 'N/A')}\n"
        output += f"  Public Repos: {data.get('public_repos', 0)}\n"
        output += f"  Followers: {data.get('followers', 0)}\n"
        
        # Analyze repositories if any exist
        if data.get('public_repos', 0) > 0:
            repos_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
            try:
                repos_response = requests.get(repos_url, headers=headers, timeout=10)
                if repos_response.status_code == 200:
                    repos = repos_response.json()
                    
                    if repos:
                        languages = set()
                        recent_repos = []
                        
                        for repo in repos[:5]:  # Analyze top 5 repos
                            repo_name = repo.get('name')
                            description = repo.get('description', 'No description')
                            language = repo.get('language')
                            stars = repo.get('stargazers_count', 0)
                            updated = repo.get('updated_at', '')[:10]  # Date only
                            
                            if language:
                                languages.add(language)
                            
                            recent_repos.append(f"{repo_name}: {description[:50]}... ({language}, ★{stars}, {updated})")
                        
                        output += f"  Languages: {', '.join(list(languages)[:5])}\n"
                        output += f"  Recent Repositories:\n"
                        for repo_info in recent_repos:
                            output += f"    - {repo_info}\n"
            except Exception:
                output += "  Repository analysis: Limited access\n"
        
        output += f"  Profile: {data.get('html_url')}\n"
        return output
        
    except Exception as e:
        return f"GitHub search error: {str(e)}\n"


def _search_reddit(target: str) -> str:
    """Search Reddit with deep analysis"""
    try:
        username = target.replace(" ", "").lower()
        headers = {"User-Agent": "OSINT Tool 1.0"}
        
        # Get profile info
        profile_url = f"https://www.reddit.com/user/{username}/about.json"
        response = requests.get(profile_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"No Reddit profile found for: {username}\n"
            
        data = response.json()
        user_data = data.get("data", {})
        
        output = f"✓ Found Reddit profile:\n"
        output += f"  Username: {user_data.get('name')}\n"
        output += f"  Karma: {user_data.get('total_karma', 0)}\n"
        output += f"  Created: {user_data.get('created_utc', 'N/A')}\n"
        
        # Get recent comments for activity analysis
        comments_url = f"https://www.reddit.com/user/{username}/comments.json?limit=25"
        try:
            comments_response = requests.get(comments_url, headers=headers, timeout=10)
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                comments = comments_data.get("data", {}).get("children", [])
                
                if comments:
                    subreddits = set()
                    recent_activity = []
                    
                    for comment in comments[:10]:  # Analyze last 10 comments
                        comment_data = comment.get("data", {})
                        subreddit = comment_data.get("subreddit")
                        body = comment_data.get("body", "")[:100]  # First 100 chars
                        score = comment_data.get("score", 0)
                        
                        if subreddit:
                            subreddits.add(subreddit)
                        if body and body != "[deleted]":
                            recent_activity.append(f"r/{subreddit}: {body}... (score: {score})")
                    
                    output += f"  Active Subreddits: {', '.join(list(subreddits)[:5])}\n"
                    output += f"  Recent Comments: {len(recent_activity)}\n"
                    
                    if recent_activity:
                        output += "  Sample Activity:\n"
                        for activity in recent_activity[:3]:
                            output += f"    - {activity}\n"
        except Exception:
            output += "  Comment history: Access limited\n"
        
        output += f"  Profile: https://reddit.com/user/{username}\n"
        return output
        
    except Exception as e:
        return f"Reddit search error: {str(e)}\n"
