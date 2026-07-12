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

### 10. Professional Report Formatting (Course Templates)
- **Status**: Implemented
- **Use case**: Implemented the structure and professional appearance extracted from the OSINT course's client report template.
- **Value for individuals**: HIGH - Generates agency-grade deliverables.

### 11. Input Support: Domain Names
- **Status**: Implemented
- **Use case**: Accept a domain (e.g., `example.com`) as a primary target to immediately trigger WHOIS lookups, subdomain enumeration (crt.sh, capped at 20), and linked email discovery.
- **Implementation**: Added `is_valid_domain()` and updated `detect_target_type()` in `utils/validation.py`; new `domain_search()` orchestrator in `tools/search_tools.py`; routing in `graph/nodes/search.py`; CLI banner and frontend placeholder updated.
- **Value for individuals**: HIGH - Quickest win for expanding footprinting capabilities.

### 12. AI Test Healer Optimization
- **Status**: Implemented
- **Use case**: Optimize Playwright test resilience by utilizing native locators for fallbacks and making LLM-based healing opt-in (`ENABLE_AI_HEALING=true`) to save costs and avoid CI crashes.
- **Implementation**: Refactored `tests/healer.py` to use `get_by_test_id` and `get_by_text`. Added logic to persist healed selectors to `tests/healed_selectors.json`.
- **Value for individuals**: HIGH - Faster, cheaper, and more deterministic CI pipeline while maintaining local vibe-coding benefits.

---

## High Priority (High Value, Lower Effort)

### [Input] Cryptocurrency Wallets
- **Use case**: Accept BTC or ETH addresses to query free APIs (Blockchain.com, Chainabuse) for wallet balance, transaction volume, and scam reports.
- **Effort**: Low/Medium
- **Value for individuals**: HIGH - Essential for financial/crypto scam investigations.

### [Input] Phone Numbers
- **Use case**: Accept international phone numbers (e.g., `+1234567890`) to search breach databases, caller ID services, and reverse lookup tools.
- **Implementation**:
  - Add strict regex to `utils/validation.py`.
  - Use the Python `phonenumbers` library to automatically parse Country Code, Area Code, and Carrier without API calls.
  - Integrate free-tier APIs (like Twilio Lookup or Numverify) to flag VOIP/Burner numbers.
  - Pipe extracted names (via Truecaller) into existing search nodes and breach databases (Dehashed).
- **Effort**: Medium (Requires strict validation rules and new API integrations).
- **Value for individuals**: HIGH - Phone numbers are universal unique identifiers and crucial for OSINT.

### [Data Module] Dehashed (Breach Data)
- **API**: dehashed.com/api
- **Cost**: $5.49/month
- **Use case**: Borderless breach data search yielding cleartext passwords and IP addresses globally.
- **Implementation**: Add to `tools/api_tools.py`
- **Effort**: Low
- **Value for individuals**: HIGH - Cleartext passwords frequently lead to discovering burner accounts via password reuse worldwide.

### ~~[Data Module] Expanded Archival Searches (Beyond Wayback)~~ [COMPLETED]
- ~~**Use case**: Integrate `archive.ph` (archive.today) alongside the Wayback Machine to find deleted posts that blocked the Internet Archive via `robots.txt`.~~
- ~~**Effort**: Low~~
- ~~**Value for individuals**: HIGH - Recovers otherwise lost data.~~

### [Data Module] Unmasking Google Accounts (GHunt integration)
- **Use case**: Automatically pull Google Maps reviews, calendar events, and YouTube channels from a `@gmail.com` input.
- **Effort**: Medium
- **Value for individuals**: VERY HIGH - Reveals real names and location data from just an email address.

### [Data Module] Have I Been Pwned (Free Tier Breach Check)
- **Use case**: Default, free-tier breach check for emails and phone numbers to identify which breaches a target was involved in.
- **Effort**: Low
- **Value for individuals**: HIGH - Crucial for building a target profile before using paid services like Dehashed.

### [Tech Improvement] Rate Limit Manager
- **Use case**: Track and manage API quotas actively rather than relying purely on exception handling.
- **Implementation**: Add `utils/rate_limiter.py`
- **Effort**: Medium
- **Value for individuals**: HIGH - Prevents tool crashes and ensures investigation completeness.

---

## Medium Priority (High Value but High Effort, or Niche but Easy)

### [Input] Photo / Image Uploads
- **Use case**: Allow users to upload an image to perform facial recognition or reverse image search (PimEyes/Google Lens) to find the target's name or social profiles.
- **Implementation**: Requires UI changes to support multipart file uploads, backend handling of binary data, and routing to image search APIs.
- **Effort**: High (Full stack changes required).
- **Value for individuals**: VERY HIGH - The ultimate pivot tool, though technically the most complex to implement robustly.

### [Data Module] EXIF Data & Geolocation Extraction
- **Use case**: When an image is analyzed (via the upcoming Photo Upload feature), automatically extract EXIF metadata (GPS coordinates, camera model, timestamps) to pinpoint physical locations.
- **Implementation**: Integrate Python libraries like `Pillow` or `exifread` into an image processing node before passing the image to the reverse search APIs. Add automated Google Maps link generation for extracted coordinates.
- **Effort**: Medium
- **Value for individuals**: HIGH - Essential for physical location tracking.

### [Data Module] Automated Google Dorking & Document Metadata
- **Use case**: Automatically run Google Dorks for documents (PDF, DOCX) related to a target and extract EXIF/metadata (author name, creation software, OS).
- **Effort**: Medium
- **Value for individuals**: MEDIUM - Can reveal local computer usernames and exact creation dates, useful when social media footprint is small.

### [Data Module] Deepfake & AI Image Detection
- **Use case**: Run scraped profile pictures or uploaded photos through an AI-detection API to determine if the image is AI-generated (e.g., GAN faces for sock puppets).
- **Effort**: Low/Medium
- **Value for individuals**: MEDIUM - Helps identify fake accounts quickly.

### [Tech Improvement] Scheduled Investigations
- **Use case**: Monitor targets over time and detect footprint changes (e.g., account deletions).
- **Implementation**: Add scheduler with a database for tracking state.
- **Effort**: High
- **Value for individuals**: HIGH - Great for continuous monitoring.

### [Tech Improvement] Async API Calls
- **Use case**: Speed up parallel API calls within individual LangGraph nodes.
- **Implementation**: Refactor `tools/api_tools.py` to use `asyncio`
- **Effort**: High
- **Value for individuals**: MEDIUM - Faster execution, but tool already works without it.

### [Tech Improvement] Data Integrity & Source Credibility Scoring
- **Use case**: Add confidence scoring to OSINT results to help users gauge the reliability of collected data (e.g., official `.gov` domain = High, anonymous pastebin = Low).
- **Implementation**: Update `utils/models.py` to include `credibility_level`, modify `analysis.py` to cross-validate findings, and instruct the LLM in `report.py` to explicitly warn about low-confidence data in a new report section.
- **Effort**: Medium
- **Value for individuals**: MEDIUM - Improves report quality but requires heavy prompt/logic tuning.

---

## Low Priority (Nice to Have / Niche)

### [Data Module] Automated Evidence Capture (Full-Page Screenshots)
- **Use case**: Use Playwright in headless mode to take automated, full-page screenshots of positive hits to preserve evidence.
- **Effort**: Medium/High (Computationally heavy)
- **Value for individuals**: LOW - Delays investigation times. Best kept as an optional future feature.

### [Data Module] Surface-to-Darkweb Queries
- **Use case**: Use surface-web gateways like `Ahmia.fi` to search for the target's email or username across indexed `.onion` sites without needing full Tor integration.
- **Effort**: Medium
- **Value for individuals**: LOW/MEDIUM - Niche, but useful for specific investigations.

### [Data Module] YouTube Data / Thumbnail Viewer
- **Use case**: Extract hidden metadata and high-res thumbnails from YouTube links, which can sometimes show deleted video content.
- **Effort**: Low
- **Value for individuals**: LOW - Niche to YouTube investigations.
