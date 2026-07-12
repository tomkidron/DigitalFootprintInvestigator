"""
Search tools for OSINT investigation
"""

import concurrent.futures
import logging
import os
import re

import requests

from utils.cache import cached
from utils.retry import retry
from utils.validation import sanitize_target

logger = logging.getLogger("osint_tool")


def _log_event(msg: str) -> None:
    """Emit a progress message to the frontend log stream, if available."""
    try:
        from langchain_core.callbacks.manager import dispatch_custom_event

        dispatch_custom_event("investigation_log", {"message": msg})
    except Exception:
        pass  # nosec B110


def google_search(query: str, scan_mode: str = "advanced") -> str:
    """
    Performs Google searches and extracts relevant information.
    Use this to find initial information about a target including profiles, mentions,
    and associated identifiers.

    Args:
        query: The search query to execute
        scan_mode: The scan configuration (quick or advanced)

    Returns:
        Search results with URLs and extracted identifiers
    """
    query = sanitize_target(query)
    logger.info(f"Google Search initiated for query: {query}")
    _log_event(f"Querying Web Search for: '{query}'...")

    tavily_key = os.getenv("TAVILY_API_KEY") if scan_mode != "quick" else None
    serpapi_key = os.getenv("SERPAPI_KEY") if scan_mode != "quick" else None

    # 1. Try Tavily
    if tavily_key and tavily_key.strip():
        logger.debug("Using Tavily for web search")
        result = _search_with_tavily(query, tavily_key, scan_mode=scan_mode)
        if "error" not in result.lower():
            return result
        logger.warning(f"Tavily search failed or hit rate limit for query: {query}. Cascading to SerpAPI.")

    # 2. Try SerpAPI
    if serpapi_key and serpapi_key.strip():
        logger.debug("Using SerpAPI for web search")
        result = _search_with_serpapi(query, serpapi_key, scan_mode=scan_mode)
        if "error" not in result.lower() and "[warn]" not in result.lower():
            return result
        logger.warning(f"SerpAPI search failed or hit rate limit for query: {query}. Cascading to Free Fallbacks.")

    # 3. Try DuckDuckGo (Free, robust)
    logger.debug("Using DuckDuckGo for free web search fallback")
    result = _search_with_duckduckgo(query, scan_mode=scan_mode)
    if "error" not in result.lower() and "[warn] no results" not in result.lower():
        return result
    logger.warning(f"DuckDuckGo search failed for query: {query}. Cascading to GoogleSearch.")

    # 4. Try Googlesearch-python (Free, rate-limits easily)
    logger.warning("Using basic googlesearch library (highly unreliable)")
    return _search_with_googlesearch(query)


def _search_with_serpapi(query: str, api_key: str, scan_mode: str = "advanced") -> str:
    """Search using SerpAPI (paid, fastest, most reliable)"""
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

        return _process_search_results(findings, query, provider="SerpAPI", scan_mode=scan_mode)

    except ImportError:
        logger.error("google-search-results library not installed")
        return "google-search-results library not installed. Install with: pip install google-search-results\n"
    except Exception as e:
        logger.error(f"SerpAPI search error: {str(e)}", exc_info=True)
        return f"SerpAPI search error: {str(e)}\nPlease check your SERPAPI_KEY and try again."


def _search_with_tavily(query: str, api_key: str, scan_mode: str = "advanced") -> str:
    """Search using Tavily API (recommended for OSINT, optimized for LLM applications)"""
    try:
        from tavily import TavilyClient

        logger.debug(f"Tavily request: {query}")
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=10,
            search_depth="advanced",
        )

        findings = []
        for result in response.get("results", []):
            findings.append(
                {
                    "title": result.get("title", ""),
                    "link": result.get("url", ""),
                    "snippet": result.get("content", ""),
                }
            )

        return _process_search_results(findings, query, provider="Tavily", scan_mode=scan_mode)

    except ImportError:
        logger.error("tavily-python library not installed")
        return "tavily-python library not installed. Install with: pip install tavily-python\n"
    except Exception as e:
        logger.error(f"Tavily search error: {str(e)}", exc_info=True)
        return f"Tavily search error: {str(e)}\nPlease check your TAVILY_API_KEY and try again."


def _process_search_results(findings: list, query: str, provider: str, scan_mode: str = "advanced") -> str:
    """Shared logic to format findings, extract identifiers, and discover emails"""
    if not findings:
        return f"Google Search Results for: {query}\n\n[No results found via {provider}]\n"

    # Format results
    output = f"Google Search Results for: {query} (via {provider})\n\n"
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
        email_discovery = enhanced_email_discovery(query, scan_mode=scan_mode)
        output += f"\n{email_discovery}"

    logger.info(f"{provider} returned {len(findings)} results for: {query}")
    return output


def _search_with_duckduckgo(query: str, scan_mode: str = "advanced") -> str:
    """Search using duckduckgo-python library (free, highly reliable)"""
    try:
        from ddgs import DDGS

        logger.debug(f"DuckDuckGo request: {query}")
        findings = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, backend="html", max_results=10))
            for result in results:
                findings.append(
                    {
                        "title": result.get("title", ""),
                        "link": result.get("href", ""),
                        "snippet": result.get("body", ""),
                    }
                )

        if not findings:
            return f"\n[WARN] No results returned\n\nSearch Results for: {query}\n"

        return _process_search_results(findings, query, provider="DuckDuckGo", scan_mode=scan_mode)

    except ImportError:
        logger.error("ddgs library not installed")
        return "ddgs library not installed. Install with: pip install ddgs\n"
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {str(e)}")
        return f"DuckDuckGo search error: {str(e)}\n"


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


@cached(ttl=86400)
def _get_wmn_data() -> dict:
    """Fetch WhatsMyName JSON dataset"""
    try:
        url = "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        logger.debug(f"Failed to fetch WhatsMyName data: {e}")
        return {}


def _check_wmn_site(site: dict, username: str) -> str:
    """Check a single site from WhatsMyName JSON"""
    try:
        check_uri = site.get("check_uri", "").replace("{account}", username)
        if not check_uri:
            return ""

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        response = requests.get(check_uri, headers=headers, timeout=5)

        # Check logic based on WMN schema
        if "account_existence_string" in site:
            if site["account_existence_string"] in response.text:
                return site["name"]
        elif "account_missing_string" in site:
            if site["account_missing_string"] not in response.text and response.status_code == int(
                site.get("account_existence_code", 200)
            ):
                return site["name"]
        elif response.status_code == int(site.get("account_existence_code", 200)):
            return site["name"]

    except Exception:
        pass  # nosec B110
    return ""


@cached(ttl=86400)
def enumerate_username(username: str) -> str:
    """Check a username across multiple platforms using WhatsMyName dataset"""
    data = _get_wmn_data()
    sites = data.get("sites", [])
    if not sites:
        return ""

    # Limit to top 50 sites to ensure investigation speed
    sites = sites[:50]

    found_sites = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_check_wmn_site, site, username): site for site in sites}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                site_dict = futures[future]
                profile_url = site_dict.get("uri_check", site_dict.get("url", "")).replace("{account}", username)
                found_sites.append((result, profile_url))

    if not found_sites:
        return ""

    output = f"[OK] Username Enumeration for '{username}' (WhatsMyName):\n"
    for name, url in sorted(found_sites):
        output += f"  - {name}: {url}\n"

    return output


def social_media_search(target: str, scan_mode: str = "advanced") -> str:
    """
    Searches across multiple social media platforms for profiles and activity.
    Supports LinkedIn, Twitter, GitHub, Reddit, and more.

    Args:
        target: The target to search for (name, username, email)
        scan_mode: The scan configuration (quick or advanced)

    Returns:
        Results from multiple social media platforms
    """
    results = []
    results.append(f"Social Media Search for: {target}\n")
    results.append("=" * 60 + "\n")

    platforms = [
        "linkedin",
        "twitter",
        "telegram",
        "github",
        "reddit",
        "youtube",
        "instagram",
        "facebook",
        "soundcloud",
    ]
    for platform in platforms:
        results.append(_search_platform(platform, target, scan_mode=scan_mode))

    if " " not in target and "@" not in target:
        wmn_result = enumerate_username(target)
        if wmn_result:
            results.append(wmn_result)

    return "\n".join(results)


def _search_platform(platform: str, target: str, scan_mode: str = "advanced") -> str:
    """Search a specific platform"""
    output = f"\n{platform.upper()} Search:\n"
    output += "-" * 40 + "\n"

    _log_event(f"Searching {platform.capitalize()}...")

    if platform == "linkedin":
        output += _search_linkedin(target)
    elif platform == "twitter":
        output += _search_twitter(target, scan_mode=scan_mode)
    elif platform == "github":
        output += _search_github(target, scan_mode=scan_mode)
    elif platform == "reddit":
        output += _search_reddit(target)
    elif platform == "youtube":
        output += _search_youtube(target, scan_mode=scan_mode)
    elif platform == "telegram":
        output += _search_telegram(target, scan_mode=scan_mode)
    elif platform in ["instagram", "facebook", "soundcloud"]:
        output += f"[WARN] {platform.upper()}: Direct API not accessible. Using Google dork fallback.\n\n"
        query = f'site:{platform}.com "{target}"'
        output += f"Search query: {query}\n\n"
        output += google_search(query, scan_mode=scan_mode)
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


def _search_twitter(target: str, scan_mode: str = "advanced") -> str:
    """Search Twitter/X with API"""
    if re.search(r"[^\x00-\x7F]", target):
        return (
            "[WARN] TWITTER: Skipped (contains non-Latin characters)\n"
            f"Twitter usernames only support Latin characters (A-Z, 0-9, _)\n"
            f"Manual search required: Search '{target}' on twitter.com\n"
        )

    if scan_mode == "quick":
        result = "[SKIP] Twitter/X: Direct API skipped in Quick Scan mode.\n"
    else:
        from tools.api_tools import search_twitter_timeline

        username = target.replace(" ", "").lower()
        result = search_twitter_timeline(username)

    if (
        "error" in result.lower()
        or "not configured" in result.lower()
        or "not found" in result.lower()
        or "skipped" in result.lower()
    ):
        result += "\n[WARN] Twitter API failed or was skipped. Falling back to Google dork. Manual search/verification recommended:\n\n"
        query = f'site:twitter.com OR site:x.com "{target}"'
        result += f"Search query: {query}\n\n"
        result += google_search(query, scan_mode=scan_mode)

    return result


def _search_telegram(target: str, scan_mode: str = "advanced") -> str:
    """Search Telegram with API"""
    if scan_mode == "quick":
        result = "[SKIP] Telegram: Direct API skipped in Quick Scan mode.\n"
    else:
        from tools.api_tools import search_telegram_channels

        result = search_telegram_channels(target)

    if (
        "error" in result.lower()
        or "not configured" in result.lower()
        or "not authorized" in result.lower()
        or "skipped" in result.lower()
    ):
        result += "\n[WARN] Telegram API failed or was skipped. Falling back to Google dork. Manual search/verification recommended:\n\n"
        query = f'site:t.me "{target}"'
        result += f"Search query: {query}\n\n"
        result += google_search(query, scan_mode=scan_mode)

    return result


@cached(ttl=3600)
@retry(max_attempts=3, delay=2)
def _search_github(target: str, scan_mode: str = "advanced") -> str:
    """Search GitHub with repository analysis"""
    try:
        username = sanitize_target(target).replace(" ", "")
        headers = {"User-Agent": "DigitalFootprintInvestigator/1.0"}
        github_token = os.getenv("GITHUB_TOKEN") if scan_mode != "quick" else None
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

        profile_url = data.get("html_url")
        output += f"  Profile: {profile_url}\n"

        from tools.api_tools import check_wayback_machine, get_archive_ph_link

        wayback = check_wayback_machine(profile_url)
        if wayback:
            output += wayback
            archive_ph = get_archive_ph_link(profile_url)
            if archive_ph:
                output += archive_ph

        return output

    except Exception as e:
        return f"GitHub search error: {str(e)}\n"


@cached(ttl=3600)
@retry(max_attempts=3, delay=2)
def _search_reddit(target: str) -> str:
    """Search Reddit with deep analysis"""
    try:
        username = sanitize_target(target).replace(" ", "")
        headers = {"User-Agent": "platform:DigitalFootprintInvestigator:1.0 (by /u/tomkidron)"}

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

        profile_url = f"https://reddit.com/user/{username}"
        output += f"  Profile: {profile_url}\n"

        from tools.api_tools import check_wayback_machine, get_archive_ph_link

        wayback = check_wayback_machine(profile_url)
        if wayback:
            output += wayback
            archive_ph = get_archive_ph_link(profile_url)
            if archive_ph:
                output += archive_ph

        return output

    except Exception as e:
        return f"Reddit search error: {str(e)}\n"


def _search_youtube(target: str, scan_mode: str = "advanced") -> str:
    """Search YouTube with API"""
    if scan_mode == "quick":
        result = "[SKIP] YouTube: Direct API skipped in Quick Scan mode.\n"
    else:
        from tools.api_tools import search_youtube_channel

        result = search_youtube_channel(target)

    if "not configured" in result or "skipped" in result:
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


def domain_search(domain: str, scan_mode: str = "advanced") -> str:
    """Orchestrate OSINT collection for a bare domain target.

    Runs WHOIS, subdomain enumeration via crt.sh, linked email discovery,
    a Wayback Machine snapshot check, and targeted Google dorks.

    Args:
        domain: A validated bare domain (e.g. example.com).
        scan_mode: 'quick' or 'advanced'.

    Returns:
        Formatted multi-section OSINT report string.
    """
    from tools.api_tools import check_wayback_machine, enhanced_email_discovery, get_archive_ph_link, search_whoisxml

    _log_event(f"Starting domain investigation for: '{domain}'...")

    output = f"Domain Investigation: {domain}\n"
    output += "=" * 60 + "\n\n"

    # --- 1. WHOIS ---
    output += "=== WHOIS RECORD ===\n"
    if scan_mode == "quick":
        output += "[SKIP] WHOIS lookup skipped in Quick Scan mode.\n\n"
    else:
        _log_event(f"Querying WHOIS for {domain}...")
        whois_result = search_whoisxml(domain)
        output += whois_result if whois_result else f"[WARN] No WHOIS data found for {domain}.\n"
        output += "\n"

    # --- 2. Subdomain enumeration via crt.sh ---
    output += "=== SUBDOMAIN ENUMERATION (crt.sh) ===\n"
    _log_event(f"Enumerating subdomains for {domain}...")
    try:
        crt_url = f"https://crt.sh/?q=%.{domain}&output=json"
        resp = requests.get(crt_url, timeout=15, headers={"Accept": "application/json"})
        if resp.status_code == 200:
            entries = resp.json()
            subdomains: set[str] = set()
            for entry in entries:
                name_value = entry.get("name_value", "")
                for name in name_value.splitlines():
                    name = name.strip().lstrip("*.")
                    if name and name.endswith(domain) and name != domain:
                        subdomains.add(name.lower())

            capped = sorted(subdomains)[:20]
            if capped:
                output += f"[OK] Found {len(subdomains)} unique subdomains (showing top 20):\n"
                for sub in capped:
                    output += f"  - {sub}\n"
            else:
                output += f"[OK] No subdomains found in certificate transparency logs for {domain}.\n"
        else:
            output += f"[WARN] crt.sh returned status {resp.status_code}.\n"
    except Exception as e:
        output += f"[ERROR] Subdomain enumeration failed: {str(e)}\n"
    output += "\n"

    # --- 3. Linked email discovery ---
    output += "=== EMAIL DISCOVERY ===\n"
    if scan_mode == "quick":
        output += "[SKIP] Email discovery skipped in Quick Scan mode.\n\n"
    else:
        _log_event(f"Discovering emails for {domain}...")
        email_result = enhanced_email_discovery(domain, domains=[domain], scan_mode=scan_mode)
        output += email_result + "\n"

    # --- 4. Wayback Machine snapshot ---
    output += "=== WAYBACK MACHINE ===\n"
    try:
        wayback = check_wayback_machine(f"https://{domain}")
        output += wayback if wayback else f"[WARN] No Wayback Machine snapshot found for {domain}.\n"
        archive_ph = get_archive_ph_link(f"https://{domain}")
        output += archive_ph if archive_ph else ""
    except Exception as e:
        output += f"[ERROR] Wayback check failed: {str(e)}\n"
    output += "\n"

    # --- 5. Google dorks ---
    output += "=== WEB PRESENCE (Google Dorks) ===\n"
    _log_event(f"Running web search dorks for {domain}...")

    site_query = f"site:{domain}"
    output += f"Site index dork: {site_query}\n"
    output += google_search(site_query, scan_mode=scan_mode) + "\n"

    email_dork = f'"@{domain}"'
    output += f"Email exposure dork: {email_dork}\n"
    output += google_search(email_dork, scan_mode=scan_mode) + "\n"

    return output
