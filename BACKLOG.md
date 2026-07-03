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

### 6. Telegram Search
- **Status**: Implemented
- **Use case**: Search public Telegram channels/groups for mentions.
- **Value for individuals**: VERY HIGH - Telegram is globally massive and often overlooked in traditional OSINT.

### 7. Migrate to Next.js + FastAPI
- **Status**: Implemented
- **Use case**: Eliminate Streamlit state issues, support granular streaming logs natively, and create a premium frontend.
- **Value for individuals**: HIGH - Vastly improved user experience and stability.

### 8. Prompt Engineering Refactor (XML Tagging)
- **Status**: Implemented
- **Use case**: Ensure deterministic, structured output from Gemini by using System/Human messages and XML tags.
- **Value for individuals**: HIGH - Prevents parsing errors and improves the reasoning quality of the LLM.

### 9. Report Viewer UI (Modal & Download Options)
- **Status**: Implemented
- **Use case**: Allows users to view reports inline and download them in specific formats (MD, PDF) directly from the Reports tab.
- **Value for individuals**: HIGH - Improves UI navigation and accessibility of generated OSINT reports.

---

## High Priority (Global Focus & High ROI)



### 5. Dehashed (Breach Data)
- **API**: dehashed.com/api
- **Cost**: $5.49/month
- **Use case**: Borderless breach data search yielding cleartext passwords and IP addresses globally.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: HIGH - Cleartext passwords frequently lead to discovering burner accounts via password reuse worldwide.

### 6. Reverse Image Search (PimEyes / Google Lens)
- **API**: pimeyes.com (paid) or SerpAPI Google Images (fallback)
- **Use case**: Pivot from a discovered profile picture to find hidden social/dating profiles across international platforms (e.g., VK, TikTok).
- **Implementation**: Add to `tools/search_tools.py`
- **Effort**: Medium
- **Value for individuals**: HIGH - The ultimate global equalizer for visual identification.

### 7. Phone Number Enrichment (Truecaller / Numverify)
- **API**: Unofficial Truecaller APIs or numverify.com
- **Use case**: Caller ID name resolution for extracted phone numbers.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: HIGH - Truecaller is incredibly powerful internationally (Middle East, India, Europe) for identifying unknown/burner numbers via crowdsourced contacts.

---

## Medium Priority (Powerful but Expensive/Niche)

### 8. Global Identity Resolution (Pipl)
- **API**: pipl.com/api
- **Cost/Access**: High / Requires enterprise approval
- **Use case**: Enrich person data from an email, phone, or social profile globally.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: MEDIUM - While it has excellent global coverage (including Israel/Europe), the high cost and access barriers make it less practical for immediate indie development compared to open-source methods.

### 9. Cryptocurrency Footprinting (Blockchain.com / Etherscan)
- **API**: Various block explorers
- **Free tier**: High limits
- **Use case**: Check activity, balance, and transaction history if a BTC/ETH address is found in a profile.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Medium
- **Value for individuals**: LOW/NICHE - Borderless, but only valuable if the target operates in the crypto space.

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
