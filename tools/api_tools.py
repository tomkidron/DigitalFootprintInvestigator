"""
API tools for enhanced OSINT data collection
"""

import os
import re
import hashlib
import logging
import requests
from time import sleep
from typing import Dict, List, Optional

logger = logging.getLogger("osint_tool")


def search_hibp_breaches(email: str) -> str:
    """Search Have I Been Pwned for email breaches"""
    api_key = os.getenv("HIBP_API_KEY")
    if not api_key:
        return "❌ HIBP API key not configured\n"
    
    try:
        headers = {
            "hibp-api-key": api_key,
            "User-Agent": "OSINT Tool 1.0"
        }
        
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return f"✓ No breaches found for: {email}\n"
        elif response.status_code == 200:
            breaches = response.json()
            output = f"⚠️ Found {len(breaches)} breaches for: {email}\n"
            for breach in breaches[:5]:  # Show top 5
                output += f"  - {breach['Name']} ({breach['BreachDate']})\n"
            return output
        else:
            return f"❌ HIBP API error: {response.status_code}\n"
            
    except Exception as e:
        return f"❌ HIBP search error: {str(e)}\n"


def search_hunter_emails(domain: str, target_name: str) -> str:
    """Search Hunter.io for email patterns"""
    api_key = os.getenv("HUNTER_API_KEY")
    if not api_key:
        return "❌ Hunter.io API key not configured\n"
    
    try:
        # Search domain email patterns
        url = f"https://api.hunter.io/v2/domain-search"
        params = {
            "domain": domain,
            "api_key": api_key,
            "limit": 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            emails = data.get("data", {}).get("emails", [])
            
            output = f"Hunter.io results for {domain}:\n"
            
            # Look for target name matches
            target_emails = []
            for email_data in emails:
                email = email_data.get("value", "")
                first_name = email_data.get("first_name", "").lower()
                last_name = email_data.get("last_name", "").lower()
                
                name_parts = target_name.lower().split()
                if any(part in email.lower() for part in name_parts):
                    target_emails.append(email)
            
            if target_emails:
                output += f"✓ Potential matches: {', '.join(target_emails)}\n"
            else:
                output += f"❌ No matches for '{target_name}' in {len(emails)} emails\n"
                
            # Show email pattern
            if emails:
                pattern = data.get("data", {}).get("pattern", "Unknown")
                output += f"  Email pattern: {pattern}\n"
                
            return output
        else:
            return f"❌ Hunter.io API error: {response.status_code}\n"
            
    except Exception as e:
        return f"❌ Hunter.io search error: {str(e)}\n"


def search_youtube_channel(target: str) -> str:
    """Search YouTube for channels"""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return "❌ YouTube API key not configured\n"
    
    try:
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Search for channels
        search_response = youtube.search().list(
            q=target,
            part='snippet',
            type='channel',
            maxResults=5
        ).execute()
        
        channels = search_response.get('items', [])
        
        if not channels:
            return f"❌ No YouTube channels found for: {target}\n"
        
        output = f"✓ Found {len(channels)} YouTube channels:\n"
        
        for channel in channels:
            snippet = channel['snippet']
            channel_id = channel['id']['channelId']
            
            # Get channel statistics
            stats_response = youtube.channels().list(
                part='statistics',
                id=channel_id
            ).execute()
            
            stats = stats_response['items'][0]['statistics'] if stats_response['items'] else {}
            
            output += f"  Channel: {snippet['title']}\n"
            output += f"    Description: {snippet['description'][:100]}...\n"
            output += f"    Subscribers: {stats.get('subscriberCount', 'Hidden')}\n"
            output += f"    Videos: {stats.get('videoCount', 0)}\n"
            output += f"    Views: {stats.get('viewCount', 0)}\n"
            output += f"    URL: https://youtube.com/channel/{channel_id}\n\n"
        
        return output
        
    except ImportError:
        return "❌ Google API client not installed: pip install google-api-python-client\n"
    except Exception as e:
        return f"❌ YouTube search error: {str(e)}\n"


def search_twitter_timeline(username: str) -> str:
    """Search Twitter timeline using API v2"""
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        return "❌ Twitter Bearer Token not configured\n"
    
    try:
        import tweepy
        
        client = tweepy.Client(bearer_token=bearer_token)
        
        # Get user by username
        user = client.get_user(username=username.replace('@', ''))
        
        if not user.data:
            return f"❌ Twitter user not found: @{username}\n"
        
        user_data = user.data
        
        # Get recent tweets
        tweets = client.get_users_tweets(
            id=user_data.id,
            max_results=10,
            tweet_fields=['created_at', 'public_metrics', 'context_annotations']
        )
        
        output = f"✓ Found Twitter profile: @{user_data.username}\n"
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
        return "❌ Tweepy not installed: pip install tweepy\n"
    except Exception as e:
        return f"❌ Twitter search error: {str(e)}\n"


def discover_emails_from_text(text: str, target_name: str) -> List[str]:
    """Discover potential emails from text content"""
    emails = []
    
    # Extract all email patterns
    email_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        r'\b[A-Za-z0-9._%+-]+\s*\[?at\]?\s*[A-Za-z0-9.-]+\s*\[?dot\]?\s*[A-Z|a-z]{2,}\b'
    ]
    
    for pattern in email_patterns:
        found_emails = re.findall(pattern, text, re.IGNORECASE)
        emails.extend(found_emails)
    
    # Filter for target name matches
    name_parts = target_name.lower().split()
    target_emails = []
    
    for email in set(emails):
        email_lower = email.lower()
        if any(part in email_lower for part in name_parts):
            target_emails.append(email)
    
    return target_emails


def enhanced_email_discovery(target_name: str, domains: List[str] = None) -> str:
    """Enhanced email discovery using multiple methods"""
    output = f"Email Discovery for: {target_name}\n"
    output += "=" * 50 + "\n"
    
    discovered_emails = []
    
    # Default domains to check
    if not domains:
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    
    # Method 1: Hunter.io domain search
    for domain in domains:
        if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com']:  # Skip personal domains
            hunter_result = search_hunter_emails(domain, target_name)
            output += f"\nHunter.io - {domain}:\n{hunter_result}"
    
    # Method 2: Generate common email patterns
    name_parts = target_name.lower().split()
    if len(name_parts) >= 2:
        first, last = name_parts[0], name_parts[-1]
        
        patterns = [
            f"{first}.{last}",
            f"{first}{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
            f"{last}.{first}",
            f"{last}{first}"
        ]
        
        output += f"\nCommon Email Patterns:\n"
        for domain in ['gmail.com', 'yahoo.com', 'outlook.com']:
            for pattern in patterns[:3]:  # Top 3 patterns
                email = f"{pattern}@{domain}"
                output += f"  Potential: {email}\n"
                discovered_emails.append(email)
    
    # Method 3: Check discovered emails against HIBP
    if discovered_emails:
        output += f"\nBreach Check Results:\n"
        for email in discovered_emails[:5]:  # Check top 5
            hibp_result = search_hibp_breaches(email)
            if "Found" in hibp_result:
                output += hibp_result
    
    return output


def test_youtube_api():
    """Test YouTube API connection"""
    print("Testing YouTube API...")
    result = search_youtube_channel("test")
    print(result)


def test_twitter_api():
    """Test Twitter API connection"""
    print("Testing Twitter API...")
    result = search_twitter_timeline("twitter")
    print(result)


def test_hunter_api():
    """Test Hunter.io API connection"""
    print("Testing Hunter.io API...")
    result = search_hunter_emails("example.com", "John Doe")
    print(result)