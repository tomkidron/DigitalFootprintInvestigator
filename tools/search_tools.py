"""
Search tools for OSINT investigation
"""

import logging
import os
import re
from time import sleep

import requests

logger = logging.getLogger("osint_tool")


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
                logger.warning(f"Fallback search returned limited results for query: {query}")
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
            logger.warning(f"SerpAPI timeout/rate limit on query: {query}. Error: {str(timeout_err)}")
            return f"[WARN] SerpAPI Rate Limit or Timeout\n\nQuery: {query}\n\nNote: SerpAPI may have rate-limited this request. Try again in a moment.\n"

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

        # Extract identifiers from all text
        all_text = "\n".join([f["title"] + " " + f["snippet"] for f in findings])
        identifiers = _extract_identifiers(all_text)
        if identifiers:
            output += "\nExtracted Identifiers:\n"
            output += identifiers

        # Search for additional contact patterns
        contact_info = _search_contact_patterns(all_text)
        if contact_info:
            output += "\nContact Information:\n"
            output += contact_info

        # Enhanced email discovery
        from tools.api_tools import discover_emails_from_text, enhanced_email_discovery

        found_emails = discover_emails_from_text(all_text, query)
        if found_emails:
            output += "\nDiscovered Emails:\n"
            for email in found_emails:
                output += f"  - {email}\n"

        if " " in query and "@" not in query:  # Looks like a name
            email_discovery = enhanced_email_discovery(query)
            output += f"\n{email_discovery}"

        logger.info(f"SerpAPI returned {len(findings)} results for: {query}")
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
            logger.warning(f"Googlesearch library error (may be rate limited): {str(e)}")
            return (
                f"\n[WARN] Search results may be incomplete\n\nGoogle Search Results for: {query}\n"
                f"Search Status: Limited/Rate-limited (free library with no API key)\n\n"
                f"Status: {len(results)} results collected before timeout\n\n"
                f"RECOMMENDATION: Add SERPAPI_KEY to .env for reliable Google searches\n"
                f"This will provide accurate result counts and snippets.\n\n"
                f"Current Results:\n"
            )

        if not results:
            output = "\n[WARN] No results returned (possible rate limiting)\n\n"
            output += f"Google Search Results for: {query}\n"
            output += "Search Status: UNRELIABLE (using free googlesearch library without API key)\n\n"
            output += "The free googlesearch library may be rate-limited or blocked.\n"
            output += "RECOMMENDATION: Add SERPAPI_KEY to .env for accurate searches\n"
            return output

        output = f"Google Search Results for: {query}\n"
        output += f"Found {len(results)} results (using free search library):\n\n"

        for i, url in enumerate(results, 1):
            output += f"{i}. {url}\n"

        output += "\n[WARN] Using free search without API key. Results may be incomplete due to rate-limiting.\n"
        output += "For reliable results with snippets, add SERPAPI_KEY to .env\n"

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

    # Extract emails (enhanced patterns)
    email_patterns = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Standard
        r"\b[A-Za-z0-9._%+-]+\s*\[?at\]?\s*[A-Za-z0-9.-]+\s*\[?dot\]?\s*[A-Z|a-z]{2,}\b",  # Obfuscated
    ]
    emails = set()
    for pattern in email_patterns:
        emails.update(re.findall(pattern, text, re.IGNORECASE))
    if emails:
        identifiers.append(f"Emails: {', '.join(emails)}")

    # Extract phone numbers (enhanced patterns)
    phone_patterns = [
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # US format
        r"\+\d{1,3}[-.]?\d{1,4}[-.]?\d{1,4}[-.]?\d{1,9}\b",  # International
        r"\b\d{2,3}[-.]?\d{7,8}\b",  # Israeli format
    ]
    phones = set()
    for pattern in phone_patterns:
        phones.update(re.findall(pattern, text))
    if phones:
        identifiers.append(f"Phones: {', '.join(phones)}")

    # Extract usernames and handles
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

    platforms = ["linkedin", "twitter", "github", "reddit", "youtube", "instagram", "facebook", "soundcloud"]
    for platform in platforms:
        results.append(_search_platform(platform, target))

    return "\n".join(results)


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
    elif platform == "youtube":
        output += _search_youtube(target)
    elif platform in ["instagram", "facebook", "soundcloud"]:
        output += f"[ERROR] {platform.upper()}: Not implemented\n"
        output += f"Manual search required: Search '{target}' on {platform}.com\n"
        output += f"Note: {platform.title()} API requires special access/approval\n"
    else:
        output += f"[ERROR] Platform {platform} not yet implemented\n"

    return output


def _search_linkedin(target: str) -> str:
    """Search LinkedIn (via Google dorking)"""
    query = f'site:linkedin.com/in "{target}"'
    return (
        f"[WARN] LinkedIn: Google dorking only (no direct API)\n"
        f"Search query: {query}\n"
        f"Manual verification required\n"
        f"Note: LinkedIn API requires special partnership\n"
    )


def _search_twitter(target: str) -> str:
    """Search Twitter/X with API"""
    if re.search(r"[^\x00-\x7F]", target):
        return (
            "[WARN] TWITTER: Skipped (contains non-Latin characters)\n"
            f"Twitter usernames only support Latin characters (A-Z, 0-9, _)\n"
            f"Manual search required: Search '{target}' on twitter.com\n"
        )

    from tools.api_tools import search_twitter_timeline

    username = target.replace(" ", "").lower()
    result = search_twitter_timeline(username)

    if "not configured" in result or "not found" in result:
        result += "\nManual search recommendations:\n"
        result += f"1. Search: @{username}\n"
        result += f'2. Search: "{target}" on twitter.com\n'
        result += f'3. Google: site:twitter.com "{target}"\n'

    return result


def _search_github(target: str) -> str:
    """Search GitHub with repository analysis"""
    try:
        username = target.replace(" ", "").lower()
        headers = {"User-Agent": "OSINT Tool 1.0"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        profile_url = f"https://api.github.com/users/{username}"
        response = requests.get(profile_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return f"No GitHub profile found for: {username}\n"

        data = response.json()
        output = "[OK] Found GitHub profile:\n"
        output += f"  Username: {data.get('login')}\n"
        output += f"  Name: {data.get('name', 'N/A')}\n"
        output += f"  Bio: {data.get('bio', 'N/A')}\n"
        output += f"  Location: {data.get('location', 'N/A')}\n"
        output += f"  Public Repos: {data.get('public_repos', 0)}\n"
        output += f"  Followers: {data.get('followers', 0)}\n"

        if data.get("public_repos", 0) > 0:
            repos_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
            try:
                repos_response = requests.get(repos_url, headers=headers, timeout=10)
                if repos_response.status_code == 200:
                    repos = repos_response.json()

                    if repos:
                        languages = set()
                        recent_repos = []

                        for repo in repos[:5]:
                            repo_name = repo.get("name")
                            description = repo.get("description", "No description")
                            language = repo.get("language")
                            stars = repo.get("stargazers_count", 0)
                            updated = repo.get("updated_at", "")[:10]

                            if language:
                                languages.add(language)

                            recent_repos.append(
                                f"{repo_name}: {description[:50]}... ({language}, {stars} stars, {updated})"
                            )

                        output += f"  Languages: {', '.join(list(languages)[:5])}\n"
                        output += "  Recent Repositories:\n"
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

        profile_url = f"https://www.reddit.com/user/{username}/about.json"
        response = requests.get(profile_url, headers=headers, timeout=10)

        if response.status_code != 200:
            return f"No Reddit profile found for: {username}\n"

        data = response.json()
        user_data = data.get("data", {})

        output = "[OK] Found Reddit profile:\n"
        output += f"  Username: {user_data.get('name')}\n"
        output += f"  Karma: {user_data.get('total_karma', 0)}\n"
        output += f"  Created: {user_data.get('created_utc', 'N/A')}\n"

        comments_url = f"https://www.reddit.com/user/{username}/comments.json?limit=25"
        try:
            comments_response = requests.get(comments_url, headers=headers, timeout=10)
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                comments = comments_data.get("data", {}).get("children", [])

                if comments:
                    subreddits = set()
                    recent_activity = []

                    for comment in comments[:10]:
                        comment_data = comment.get("data", {})
                        subreddit = comment_data.get("subreddit")
                        body = comment_data.get("body", "")[:100]
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


def _search_youtube(target: str) -> str:
    """Search YouTube with API"""
    from tools.api_tools import search_youtube_channel

    result = search_youtube_channel(target)

    if "not configured" in result:
        result += f"\nManual search: Search '{target}' on youtube.com\n"

    return result


def _search_contact_patterns(text: str) -> str:
    """Search for contact information patterns"""
    contacts = []

    linkedin_profiles = re.findall(r"linkedin\.com/in/([A-Za-z0-9-]+)", text, re.IGNORECASE)
    if linkedin_profiles:
        contacts.append(f"LinkedIn: {', '.join(set(linkedin_profiles))}")

    skype_handles = re.findall(r"skype:([A-Za-z0-9._-]+)", text, re.IGNORECASE)
    if skype_handles:
        contacts.append(f"Skype: {', '.join(set(skype_handles))}")

    telegram_handles = re.findall(r"t\.me/([A-Za-z0-9_]+)", text, re.IGNORECASE)
    if telegram_handles:
        contacts.append(f"Telegram: {', '.join(set(telegram_handles))}")

    return "\n".join(contacts) if contacts else ""
