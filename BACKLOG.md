# Feature Backlog

## High Priority

### 1. Wayback Machine (Internet Archive)
- **API**: archive.org/help/wayback_api.php
- **Free tier**: Unlimited
- **Use case**: Historical snapshots of social profiles, deleted posts, profile changes over time
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: HIGH - see how profiles evolved, recover deleted content

### 2. Gravatar
- **API**: Simple hash-based URL (no key needed)
- **Free tier**: Unlimited
- **Use case**: Get profile pictures from email addresses
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Very Low
- **Value for individuals**: HIGH - visual identification from email

### 3. FullContact
- **API**: fullcontact.com/developer
- **Free tier**: 100 lookups/month
- **Use case**: Enrich person data from email/phone/social profiles
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: HIGH - comprehensive person enrichment

### 4. Telegram Search
- **Library**: telethon (Python)
- **Free tier**: Open API
- **Use case**: Search public Telegram channels/groups for mentions
- **Implementation**: Add to `tools/search_tools.py`
- **Effort**: High (requires session management)
- **Value for individuals**: HIGH - Telegram is widely used, often overlooked

### 5. Pipl
- **API**: pipl.com/api
- **Free tier**: Limited (requires approval)
- **Use case**: Deep people search across web
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: HIGH - specialized for person search

## Medium Priority

### 6. Clearbit
- **API**: clearbit.com/enrichment
- **Free tier**: 100 lookups/month
- **Use case**: Enrich email addresses with company/person info
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: MEDIUM - good for professional context

### 7. WhoisXML API
- **API**: whoisxmlapi.com
- **Free tier**: 500 queries/month
- **Use case**: Domain registration info if person owns websites
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: MEDIUM - useful if target has personal domain

### 8. Dehashed
- **API**: dehashed.com/api
- **Cost**: $5.49/month (cheaper alternative to HIBP)
- **Use case**: Breach data search with more comprehensive data
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: MEDIUM - more breach data than HIBP

## Low Priority (Infrastructure/Company-focused)

### 9. Shodan
- **API**: shodan.io/api
- **Free tier**: 100 queries/month
- **Use case**: Find exposed devices/services (limited value for individuals)
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: LOW - only useful if target has exposed infrastructure

### 10. IPinfo
- **API**: ipinfo.io
- **Free tier**: 50k requests/month
- **Use case**: Geolocate IPs (requires finding IPs first)
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: LOW - secondary data source

### 11. VirusTotal
- **API**: virustotal.com/api
- **Free tier**: 4 requests/minute, 500/day
- **Use case**: Check URLs/domains for malicious activity
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: LOW - more relevant for threat intelligence

### 12. Spyse
- **API**: spyse.com/api
- **Free tier**: 100 queries/month
- **Use case**: Find domains, IPs, SSL certificates
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: LOW - infrastructure-focused

### 13. SecurityTrails
- **API**: securitytrails.com/api
- **Free tier**: 50 queries/month
- **Use case**: Historical DNS records, subdomain enumeration
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: LOW - infrastructure-focused

## Technical Improvements

### 14. Async API Calls
- **Use case**: Speed up parallel API calls within nodes
- **Implementation**: Refactor `tools/api_tools.py` to use `asyncio`
- **Effort**: High
- **Note**: LangGraph already parallelizes nodes, but within-node calls are sequential

### 15. Rate Limit Manager
- **Use case**: Track and manage API quotas across all services
- **Implementation**: Add `utils/rate_limiter.py`
- **Effort**: Medium
- **Note**: Currently relies on API errors and retry logic

### 16. Export Formats
- **Use case**: Export reports as JSON, PDF, HTML
- **Implementation**: Add export options to `graph/nodes/report.py`
- **Effort**: Medium

### 17. Scheduled Investigations
- **Use case**: Monitor targets over time, detect changes
- **Implementation**: Add scheduler with database for tracking
- **Effort**: High

### 18. Web Scraping Fallbacks
- **Use case**: Scrape platforms when APIs unavailable (Instagram, Facebook, LinkedIn)
- **Implementation**: Add Playwright-based scrapers to `tools/search_tools.py`
- **Effort**: Very High (maintenance burden, legal concerns)
- **Note**: Playwright available for tests only

## Notes

- All integrations should use `@cached` and `@retry` decorators
- Add comprehensive error handling for each API
- never Update `.env.example` with API keys! use fake or placeholders!
- Update README with new service documentation
- Add unit tests for each new integration
