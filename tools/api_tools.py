"""
API tools for enhanced OSINT data collection
"""

import hashlib
import logging
import os
import re
from typing import List
from urllib.parse import quote

import requests

from utils.cache import cached
from utils.retry import retry
from utils.validation import is_valid_email, sanitize_target

logger = logging.getLogger("osint_tool")


@cached(ttl=86400)  # Cache for 24 hours
@retry(max_attempts=2, delay=1)
def search_hibp_breaches(email: str) -> str:
    """Search Have I Been Pwned for email breaches"""
    if not is_valid_email(email):
        return f"[ERROR] Invalid email format: {email}\n"

    api_key = os.getenv("HIBP_API_KEY")
    if not api_key:
        return "[ERROR] HIBP API key not configured\n"

    try:
        headers = {"hibp-api-key": api_key, "User-Agent": "OSINT Tool 1.0"}

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            return f"[OK] No breaches found for: {email}\n"
        elif response.status_code == 200:
            breaches = response.json()
            output = f"[WARN] Found {len(breaches)} breaches for: {email}\n"
            for breach in breaches[:5]:
                output += f"  - {breach['Name']} ({breach['BreachDate']})\n"
            return output
        else:
            return f"[ERROR] HIBP API error: {response.status_code}\n"

    except Exception as e:
        return f"[ERROR] HIBP search error: {str(e)}\n"


@cached(ttl=86400)
@retry(max_attempts=2, delay=1)
def check_gravatar_profile(email: str) -> str:
    """Check Gravatar for an associated profile/avatar"""
    if not is_valid_email(email):
        return ""

    email_hash = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    avatar_url = f"https://gravatar.com/avatar/{email_hash}?d=404"
    profile_url = f"https://gravatar.com/{email_hash}"

    try:
        response = requests.get(avatar_url, timeout=5)
        if response.status_code == 200:
            return f"    - Profile: {profile_url} (Avatar found)\n"
    except Exception as e:
        logger.debug(f"Gravatar check failed for {email}: {str(e)}")

    return ""


@cached(ttl=86400)
@retry(max_attempts=2, delay=1)
def check_wayback_machine(url: str) -> str:
    """Check Wayback Machine for historical snapshots"""
    try:
        api_url = f"https://archive.org/wayback/available?url={quote(url)}"
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest")

            if closest and closest.get("available"):
                timestamp = closest.get("timestamp", "")
                formatted_date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}" if len(timestamp) >= 8 else timestamp
                return f"  Historical Snapshot ({formatted_date}): {closest.get('url')}\n"
    except Exception as e:
        logger.debug(f"Wayback check failed for {url}: {str(e)}")

    return ""


def search_hunter_emails(domain: str, target_name: str) -> str:
    """Search Hunter.io for email patterns"""
    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        return "[ERROR] Hunter.io API key not configured\n"

    try:
        url = "https://api.hunter.io/v2/domain-search"
        params = {"domain": domain, "api_key": api_key, "limit": 10}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            emails = data.get("data", {}).get("emails", [])

            output = f"Hunter.io results for {domain}:\n"

            target_emails = []
            for email_data in emails:
                email = email_data.get("value", "")
                name_parts = target_name.lower().split()
                if any(part in email.lower() for part in name_parts):
                    target_emails.append(email)

            if target_emails:
                output += f"[OK] Potential matches: {', '.join(target_emails)}\n"
            else:
                output += f"[ERROR] No matches for '{target_name}' in {len(emails)} emails\n"

            if emails:
                pattern = data.get("data", {}).get("pattern", "Unknown")
                output += f"  Email pattern: {pattern}\n"

            return output
        else:
            return f"[ERROR] Hunter.io API error: {response.status_code}\n"

    except Exception as e:
        return f"[ERROR] Hunter.io search error: {str(e)}\n"


@cached(ttl=3600)
@retry(max_attempts=3, delay=2)
def search_youtube_channel(target: str) -> str:
    """Search YouTube for channels"""
    target = sanitize_target(target)
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return "[ERROR] YouTube API key not configured\n"

    try:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", developerKey=api_key)

        search_response = youtube.search().list(q=target, part="snippet", type="channel", maxResults=5).execute()

        channels = search_response.get("items", [])

        if not channels:
            return f"[ERROR] No YouTube channels found for: {target}\n"

        output = f"[OK] Found {len(channels)} YouTube channels:\n"

        for channel in channels:
            snippet = channel["snippet"]
            channel_id = channel["id"]["channelId"]

            stats_response = youtube.channels().list(part="statistics", id=channel_id).execute()

            stats = stats_response["items"][0]["statistics"] if stats_response["items"] else {}

            output += f"  Channel: {snippet['title']}\n"
            output += f"    Description: {snippet['description'][:100]}...\n"
            output += f"    Subscribers: {stats.get('subscriberCount', 'Hidden')}\n"
            output += f"    Videos: {stats.get('videoCount', 0)}\n"
            output += f"    Views: {stats.get('viewCount', 0)}\n"
            channel_url = f"https://youtube.com/channel/{channel_id}"
            output += f"    URL: {channel_url}\n"
            wayback = check_wayback_machine(channel_url)
            if wayback:
                output += wayback
            output += "\n"

        return output

    except ImportError:
        return "[ERROR] Google API client not installed: pip install google-api-python-client\n"
    except Exception as e:
        return f"[ERROR] YouTube search error: {str(e)}\n"


@cached(ttl=3600)
@retry(max_attempts=3, delay=2)
def search_twitter_timeline(username: str) -> str:
    """Search Twitter timeline using API v2"""
    username = sanitize_target(username).replace("@", "")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        return "[ERROR] Twitter Bearer Token not configured\n"

    try:
        import tweepy

        client = tweepy.Client(bearer_token=bearer_token)

        user = client.get_user(username=username.replace("@", ""))

        if not user.data:
            return f"[ERROR] Twitter user not found: @{username}\n"

        user_data = user.data

        tweets = client.get_users_tweets(
            id=user_data.id, max_results=10, tweet_fields=["created_at", "public_metrics", "context_annotations"]
        )

        profile_url = f"https://twitter.com/{user_data.username}"
        output = f"[OK] Found Twitter profile: @{user_data.username}\n"
        output += f"  Profile URL: {profile_url}\n"
        wayback = check_wayback_machine(profile_url)
        if wayback:
            output += wayback
        output += f"  Name: {user_data.name}\n"
        output += f"  Description: {user_data.description}\n"
        output += f"  Followers: {user_data.public_metrics['followers_count']}\n"
        output += f"  Following: {user_data.public_metrics['following_count']}\n"
        output += f"  Tweets: {user_data.public_metrics['tweet_count']}\n\n"

        if tweets.data:
            output += f"Recent tweets ({len(tweets.data)}):\n"
            for tweet in tweets.data[:5]:
                metrics = tweet.public_metrics
                output += f"  - {tweet.text[:100]}...\n"
                output += f"    Likes: {metrics['like_count']}, RTs: {metrics['retweet_count']}\n"
                output += f"    Date: {tweet.created_at}\n\n"

        return output

    except ImportError:
        return "[ERROR] Tweepy not installed: pip install tweepy\n"
    except Exception as e:
        return f"[ERROR] Twitter search error: {str(e)}\n"


def discover_emails_from_text(text: str, target_name: str) -> List[str]:
    """Discover potential emails from text content"""
    emails = []

    email_patterns = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        r"\b[A-Za-z0-9._%+-]+\s*\[?at\]?\s*[A-Za-z0-9.-]+\s*\[?dot\]?\s*[A-Z|a-z]{2,}\b",
    ]

    for pattern in email_patterns:
        emails.extend(re.findall(pattern, text, re.IGNORECASE))

    name_parts = target_name.lower().split()
    return [email for email in set(emails) if any(part in email.lower() for part in name_parts)]


def enhanced_email_discovery(target_name: str, domains: List[str] = None, scan_mode: str = "advanced") -> str:
    """Enhanced email discovery using multiple methods"""
    output = f"Email Discovery for: {target_name}\n"
    output += "=" * 50 + "\n"

    discovered_emails = []

    if not domains:
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

    # Method 1: Hunter.io domain search
    if scan_mode == "quick":
        output += "\nHunter.io Domain Search: [SKIP] Hunter.io search skipped in Quick Scan mode.\n"
    else:
        for domain in domains:
            if domain not in ["gmail.com", "yahoo.com", "hotmail.com"]:
                hunter_result = search_hunter_emails(domain, target_name)
                output += f"\nHunter.io - {domain}:\n{hunter_result}"

    # Method 2: Generate common email patterns (ONLY IF HIBP IS CONFIGURED)
    hibp_key = os.getenv("HIBP_API_KEY") if scan_mode != "quick" else None
    name_parts = target_name.lower().split()

    if scan_mode == "quick":
        output += (
            "\n[SKIP] Common Email Pattern Generation skipped in Quick Scan mode (requires breach verification).\n"
        )
    elif not hibp_key:
        output += "\n[SKIP] Common Email Pattern Generation disabled.\n"
        output += "Reason: HIBP_API_KEY is not configured. Generating patterns without breach verification produces unreliable data.\n"
    elif len(name_parts) >= 2:
        first, last = name_parts[0], name_parts[-1]

        patterns = [
            f"{first}.{last}",
            f"{first}{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
            f"{last}.{first}",
            f"{last}{first}",
        ]

        output += "\nCommon Email Patterns:\n"
        for domain in ["gmail.com", "yahoo.com", "outlook.com"]:
            for pattern in patterns[:3]:
                email = f"{pattern}@{domain}"
                output += f"  Potential: {email}\n"
                discovered_emails.append(email)

    # Method 3: Check discovered emails against HIBP
    if discovered_emails and hibp_key:
        output += "\nBreach Check Results:\n"
        for email in discovered_emails[:5]:
            hibp_result = search_hibp_breaches(email)
            if "Found" in hibp_result:
                output += hibp_result

    # Method 4: Check Gravatar for discovered emails
    if discovered_emails:
        gravatar_results = ""
        for email in discovered_emails:
            g_res = check_gravatar_profile(email)
            if g_res:
                gravatar_results += f"  {email}:\n{g_res}"

        if gravatar_results:
            output += f"\nGravatar Profiles Found:\n{gravatar_results}"

    return output
