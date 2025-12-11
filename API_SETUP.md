# API Setup Guide

## Quick Start APIs (No Approval Required)

### 1. Have I Been Pwned API
**Purpose**: Email breach detection
**Cost**: Free tier available
**Setup**:
1. Go to https://haveibeenpwned.com/API/Key
2. Purchase API key ($3.50/month)
3. Add to `.env`: `HIBP_API_KEY=your_key_here`

### 2. Hunter.io API  
**Purpose**: Professional email discovery
**Cost**: 25 searches/month free
**Setup**:
1. Sign up at https://hunter.io/api
2. Get free API key
3. Add to `.env`: `HUNTER_API_KEY=your_key_here`

### 3. YouTube Data API
**Purpose**: Channel analysis, video statistics
**Cost**: Free (quota limits)
**Setup**:
1. Go to https://console.developers.google.com
2. Create project → Enable YouTube Data API v3
3. Create credentials → API Key
4. Add to `.env`: `YOUTUBE_API_KEY=your_key_here`

### 4. Twitter API v2
**Purpose**: Timeline analysis, tweet metrics
**Cost**: Free tier available
**Setup**:
1. Apply at https://developer.twitter.com
2. Create app → Get Bearer Token
3. Add to `.env`: `TWITTER_BEARER_TOKEN=your_token_here`

## Usage Examples

```bash
# With all APIs configured
python main.py "John Doe"

# Check API status
python -c "from tools.api_tools import *; print('APIs ready!')"

# Test specific API
python -c "from tools.api_tools import search_hibp_breaches; print(search_hibp_breaches('test@example.com'))"
```

## API Status Indicators

The tool will show which APIs are configured:
- ✅ **Configured and working**
- ⚠️ **Configured but limited** 
- ❌ **Not configured**

## Rate Limits

- **HIBP**: 1 request per 1.5 seconds
- **Hunter.io**: 25/month free, then paid
- **YouTube**: 10,000 units/day free
- **Twitter**: 300 requests/15 minutes

## Troubleshooting

**"API key not configured"**: Add key to `.env` file
**"Rate limit exceeded"**: Wait or upgrade plan
**"Invalid credentials"**: Check key format and permissions