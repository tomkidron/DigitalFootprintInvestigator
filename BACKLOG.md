# Feature Backlog

## Completed Features

### 1. Wayback Machine (Internet Archive)
- **Status**: Implemented
- **Use case**: Historical snapshots of social profiles, deleted posts, profile changes over time
- **Value for individuals**: HIGH - see how profiles evolved, recover deleted content

### 2. Gravatar
- **Status**: Implemented
- **Use case**: Get profile pictures from email addresses
- **Value for individuals**: HIGH - visual identification from email

### 3. WhatsMyName (Mass Username Enumeration)
- **Status**: Implemented
- **Use case**: Check discovered usernames across 50+ niche forums, dating sites, and obscure platforms simultaneously.
- **Value for individuals**: VERY HIGH - Massive expansion of platform coverage with zero API costs.

### 4. WhoisXML API (Domain Enrichment)
- **Status**: Implemented
- **Use case**: Check WHOIS records for custom domains to find alternate registrant emails or names.
- **Value for individuals**: MEDIUM - Useful for uncovering alternate emails tied to domain registrations.

### 5. Export Formats
- **Status**: Implemented
- **Use case**: Export reports as JSON, PDF, HTML for clients and offline reading.
- **Value for individuals**: HIGH - Essential for keeping records or sharing data externally.

---

## High Priority (Identity & Core OSINT)

### 4. Telegram Search
- **Library**: telethon (Python)
- **Free tier**: Open API
- **Use case**: Search public Telegram channels/groups for mentions
- **Implementation**: Add to `tools/search_tools.py`
- **Effort**: High (requires session management)
- **Value for individuals**: HIGH - Telegram is a primary hub for many communities; often overlooked.

### 5. FullContact / Pipl
- **API**: fullcontact.com/developer OR pipl.com/api
- **Free tier**: Limited/Requires approval
- **Use case**: Enrich person data (identity resolution) from an email, phone, or social profile.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: HIGH - The holy grail of correlating identities and finding hidden social accounts.

### 6. Dehashed
- **API**: dehashed.com/api
- **Cost**: $5.49/month (cheaper alternative to HIBP)
- **Use case**: Breach data search yielding cleartext passwords and IP addresses.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: HIGH - Cleartext passwords frequently lead to discovering burner accounts via password reuse.

---

## Medium Priority (Enrichment & Pivoting)

### 7. Reverse Image Search (PimEyes / TinEye / Google Lens)
- **API**: pimeyes.com (paid) or SerpAPI Google Images (fallback)
- **Use case**: Pivot from a discovered Gravatar or LinkedIn profile picture to find hidden social/dating profiles.
- **Implementation**: Add to `tools/search_tools.py`
- **Effort**: Medium
- **Value for individuals**: MEDIUM/HIGH - Extremely powerful pivot vector for visual identification.

### 8. Phone Number Enrichment (Numverify / Truecaller)
- **API**: numverify.com or unofficial Truecaller APIs
- **Use case**: Carrier lookup and Caller ID name resolution for extracted phone numbers.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: MEDIUM - Essential when a target uses a burner or unknown number.

---

## Low Priority (Niche)

### 10. Cryptocurrency Footprinting (Blockchain.com / Etherscan)
- **API**: Various block explorers
- **Free tier**: High limits
- **Use case**: Check activity, balance, and transaction history if a BTC/ETH address is found in a profile or Reddit history.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: LOW/NICHE - Very valuable only if the target operates in the crypto space.

---

## Technical Improvements

### 12. Scheduled Investigations
- **Use case**: Monitor targets over time and detect footprint changes (e.g., account deletions).
- **Implementation**: Add scheduler with a database for tracking state.
- **Effort**: High

### 13. Rate Limit Manager
- **Use case**: Track and manage API quotas actively rather than relying purely on exception handling.
- **Implementation**: Add `utils/rate_limiter.py`
- **Effort**: Medium

### 14. Async API Calls
- **Use case**: Speed up parallel API calls within individual LangGraph nodes.
- **Implementation**: Refactor `tools/api_tools.py` to use `asyncio`
- **Effort**: High
