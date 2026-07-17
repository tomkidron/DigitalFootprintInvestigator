# Digital Footprint Investigator

> **EDUCATIONAL USE ONLY**: This tool is designed for educational purposes, security research, and legitimate OSINT investigations. Users must comply with all applicable laws and ethical guidelines. Misuse for stalking, harassment, or illegal activities is strictly prohibited.

A multi-agent OSINT tool built with [LangGraph](https://langchain-ai.github.io/langgraph/) that searches across Google, social media platforms, and enrichment APIs in parallel, then chains the results through an analysis and report-generation stage powered by Google Gemini.

## Features

- **Parallel LangGraph workflow**: Google search and social media search run simultaneously; results feed a single analysis → report pipeline
- **Platform coverage**: Google (Tavily → SerpAPI → free fallback), GitHub, Reddit, Twitter/X (with dork fallback), YouTube, LinkedIn, Telegram, Instagram (dork fallback), Facebook (dork fallback), SoundCloud (dork fallback)
- **Domain investigation**: Accept a bare domain (e.g. `example.com`) as a target — automatically runs WHOIS lookup, crt.sh subdomain enumeration (capped at 20), linked email discovery, Wayback Machine snapshot, and Google dorks
- **API enrichment**: HIBP breach detection, Hunter.io email discovery, Gravatar profile pictures, Wayback Machine historical snapshots
- **Resilient execution**: Automatic retry with exponential backoff, disk-based caching to avoid rate limits
- **Input validation**: Accepts Name, Email, Username, Domain, or Phone Number — auto-detected and routed to the correct pipeline
- **Next.js & FastAPI web UI**: decoupled modern architecture with a Next.js static React frontend and a FastAPI backend for granular, real-time SSE log streaming and report management
- **CLI mode**: scriptable via `python main.py`
- **Advanced analysis** (optional): timeline correlation, social connection analysis, deep content analysis
- **Scan Modes**: choose between **Quick Scan** (free, unauthenticated fallbacks only) and **Advanced Scan** (premium integrations using configured API keys)
- **Docker-first**: a single image runs the app, unit tests, and UI tests

## Prerequisites

- Python 3.11+ (or Docker)
- **Required**: Google Gemini API key
- **Optional**: additional API keys for richer results (see [Environment](#environment))

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Copy and fill in your API keys
cp .env.example .env   # then edit .env and set GEMINI_API_KEY

# Build and start the web UI
docker compose up --build
```

Open `http://localhost:8000` in your browser.

**CLI via Docker:**
```bash
docker compose run --rm osint-tool python main.py "John Doe"
```

---

### Option 2: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env   # then edit .env

# Start the backend (FastAPI)
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start the frontend development server (Next.js)
cd frontend
npm install
npm run dev

# Or use the CLI
python main.py "John Doe"
```

---

## Environment

Copy `.env.example` to `.env` and configure:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-pro             # default reasoning model
LLM_MODEL_FAST=gemini-2.5-flash      # default fast analysis model

# Optional — the tool works without these, but results improve significantly
TAVILY_API_KEY=...                    # Best Google results (free tier available)
SERPAPI_KEY=...                       # Google results fallback ($50/mo, 5000 searches)
GITHUB_TOKEN=...                      # Higher rate limits (free personal access token)
TWITTER_BEARER_TOKEN=...              # Twitter timeline access (free tier available)
YOUTUBE_API_KEY=...                   # YouTube channel data (free, 10 000 units/day)
HUNTER_API_KEY=...                    # Email discovery (free tier: 25 searches/month)
HIBP_API_KEY=...                      # Breach detection ($3.50/month)

# Logging
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
```

**Getting API keys:**

| Key | Where to get it | Cost |
|-----|----------------|------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com/) | Pay-per-use |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens | Free |
| `YOUTUBE_API_KEY` | [console.developers.google.com](https://console.developers.google.com) → YouTube Data API v3 | Free (quota) |
| `TWITTER_BEARER_TOKEN` | [developer.twitter.com](https://developer.twitter.com) | Free tier |
| `HUNTER_API_KEY` | [hunter.io/api](https://hunter.io/api) | Free tier (25/mo) |
| `HIBP_API_KEY` | [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) | $3.50/mo |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | Free tier available |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | $50/mo |

> **Quick start recommendation**: Enable `TAVILY_API_KEY`, `GITHUB_TOKEN`, and `YOUTUBE_API_KEY` first — all have free tiers and require no approval.

## Project Structure

```
DigitalFootprintInvestigator/
├── graph/
│   ├── nodes/
│   │   ├── _timing.py        # Shared log_start / log_done / log_event helpers
│   │   ├── search.py         # Google and social search nodes (run in parallel)
│   │   ├── analysis.py       # Data correlation and pattern extraction
│   │   ├── advanced.py       # Optional timeline / network / content analysis
│   │   └── report.py         # Gemini-powered report generation
│   ├── state.py              # LangGraph state TypedDict
│   └── workflow.py           # Graph construction and MemorySaver checkpointing
├── tools/
│   ├── search_tools.py       # Google search and platform scrapers
│   └── api_tools.py          # HIBP, Hunter.io, YouTube, Twitter wrappers
├── utils/
│   ├── llm.py                # Shared Google GenAI factory
│   ├── logger.py             # Logging setup
│   ├── cache.py              # Disk-based caching for API calls
│   ├── retry.py              # Exponential backoff retry logic
│   ├── validation.py         # Input validation and sanitization
│   └── models.py             # Pydantic data models
├── tests/
│   ├── conftest.py           # Playwright session/page fixtures
│   ├── healer.py             # Self-healing Playwright page wrapper
│   ├── unit/                 # 246 unit tests (no browser or live API required)
│   └── ui/                   # 25 Playwright browser tests
├── api/
│   └── main.py               # FastAPI backend entry point
├── frontend/
│   ├── src/app/              # Next.js app router and components
│   └── package.json          # Node dependencies
├── main.py                   # CLI entry point
├── config.yaml               # Platform and analysis settings
├── pytest.ini                # Test markers and paths
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── Dockerfile                # Single image used by all three services
├── docker-compose.yml        # Services: osint-tool, unit-tests, tests
├── pyproject.toml            # Bandit security scan config
├── .pre-commit-config.yaml   # Pre-commit hooks
└── .dockerignore             # Docker build exclusions
```

## Running Tests

### Locally

```bash
# Unit tests (no browser, no API key needed)
python -m pytest tests/unit/ -v

# UI tests (starts FastAPI + Next.js automatically; requires a Playwright browser)
playwright install chromium   # first time only
python -m pytest tests/ui/ -m "not integration" -v

# UI tests with AI self-healing enabled (requires GEMINI_API_KEY)
# Note: On Windows PowerShell use: $env:ENABLE_AI_HEALING="true"; python -m pytest ...
ENABLE_AI_HEALING=true python -m pytest tests/ui/ -m "not integration" -v

# Integration tests (require GEMINI_API_KEY and a full workflow run)
python -m pytest tests/ui/ -m integration -v
```

### In Docker

```bash
# Unit tests — no running app needed
docker compose run --rm unit-tests

# UI tests — automatically starts the app and waits for it to be healthy
docker compose run --rm tests
```

> Integration tests are excluded by default in Docker (`-m "not integration"`).
> To run them: `docker compose run --rm tests pytest tests/ui/ -v`

## Configuration

`config.yaml` controls platforms and advanced analysis defaults. The Streamlit sidebar and CLI flags override these values per run.

**Scan Modes**:
* **Quick Scan**: Runs unauthenticated, utilizing free, as-is tools (e.g. Google dorking fallbacks) and bypassing all premium services (skips Tavily, SerpAPI, Hunter.io, HIBP, Twitter, YouTube API keys/tokens).
* **Advanced Scan**: The default mode, executing full query logic via any configured premium APIs in `.env`.

**Advanced analysis** (all off by default; processed locally during the analysis phase):

```yaml
advanced_analysis:
  timeline_correlation: false   # Build a chronological activity timeline
  network_analysis: false       # Map social connections (displays as "Social Connection Analysis" in UI)
  deep_content_analysis: false  # Sentiment, topics, behavioral patterns
```

**CLI flags:**

```bash
# Run a quick scan (free services only)
python main.py "Jane Smith" --quick

# Run an advanced scan with timeline and social connection correlation enabled
python main.py "Jane Smith" --timeline --network --deep
```

## Usage Examples

```bash
# Name (default Advanced scan)
python main.py "Jane Smith"

# Quick scan mode (no API tokens or secrets required)
python main.py "Jane Smith" --quick

# Email
python main.py "jane.smith@example.com"

# Username
python main.py "@janesmith"

# Domain — triggers WHOIS, subdomain enumeration, email discovery, Wayback, and Google dorks
python main.py "example.com"

# With advanced analysis enabled
python main.py "Jane Smith" --timeline --network --deep
```

Reports are saved to `reports/` with a timestamp, e.g. `reports/Jane_Smith_20260227_143022.md`.

## Code Quality

Pre-commit hooks run automatically on `git commit`:

```bash
pip install pre-commit
pre-commit install
```

Hooks: `detect-secrets`, `ruff` (lint + format), merge-conflict detection, large-file guard, YAML/JSON/TOML validation, debug-statement blocking, and `bandit` security scanning. Bandit config lives in `pyproject.toml`.

To run all hooks manually: `pre-commit run --all-files`

## Customization

### Adding a platform

1. Add a search function to `tools/search_tools.py` following the `_search_github` / `_search_reddit` pattern.
2. Register it in the `_search_platform` dispatch table in the same file.
3. Optionally add platform config to `config.yaml`.

### Adding a graph node

1. Create `graph/nodes/my_node.py`:

```python
from graph.state import OSINTState
from graph.nodes._timing import log_start, log_done

def my_node(state: OSINTState) -> dict:
    start = log_start("My Node")
    # ... process state ...
    log_done("My Node", start)
    return {"my_key": result}
```

2. Register in `graph/workflow.py`:

```python
from .nodes.my_node import my_node

workflow.add_node("my_node", my_node)
workflow.add_edge("analysis", "my_node")
```

## Troubleshooting

**"No Gemini API key found"** — create `.env` from `.env.example` and set `GEMINI_API_KEY`.

**Google searches return no results** — the free `googlesearch-python` library is rate-limited and unreliable. Add `TAVILY_API_KEY` or `SERPAPI_KEY` to `.env` for consistent results (Tavily is tried first, then SerpAPI, then the free fallback).

**Page refresh hangs in Docker on Windows** — Streamlit's file watcher was previously problematic. With the new Next.js migration, if `uvicorn` or Next.js hangs, verify your Docker Volume mounts and file watching permissions.

**`Module not found`** — run `pip install -r requirements.txt` and confirm Python 3.11+.

**Console warning: `missing ScriptRunContext`** — harmless startup warning, handled in `app.py`.

**Console warning: `file_cache is only supported with oauth2client<4.0.0`** — harmless warning from the Google API client library.

**Docker Desktop won’t start (WSL error)** — the Ubuntu WSL distro may have auto-shut down. Run `wsl -d Ubuntu` in a terminal first, wait a few seconds, then retry Docker Desktop.

**Warning regarding Telegram** — This tool uses Telethon with a user session to search Telegram. Telegram's automated systems may flag this as a "Userbot" and ban the associated phone number. It is highly recommended to use a burner or secondary phone number when authenticating the Telegram client.

## Privacy & Ethics

**EDUCATIONAL AND LEGITIMATE PURPOSES ONLY**

Appropriate uses: security research, due diligence, investigative journalism, personal privacy audits, OSINT methodology research, identity verification with consent.

Prohibited uses: stalking or harassment, unauthorized surveillance, identity theft, doxxing, any illegal activity.

All searches use publicly available information only. Users are responsible for compliance with:
- Local privacy laws (GDPR, CCPA, etc.)
- Platform Terms of Service (including Twitter/X, Reddit, YouTube, and others)
- The Computer Fraud and Abuse Act (CFAA) and equivalent local laws

The consent checkbox in the UI is not a legal shield — you remain fully responsible for how you use this tool.

**By using this tool, you agree to use it responsibly and ethically.**

*Disclaimer: This tool automates interactions with various third-party APIs and websites. The authors are not responsible for any Terms of Service (ToS) violations caused by running this tool. Users are solely responsible for ensuring their usage complies with the policies of the platforms queried.*

## Performance & Reliability

The tool includes built-in optimizations:

- **Caching**: API responses cached for 1-24 hours to reduce quota usage and improve speed. Repeated searches are significantly faster.
- **Retry logic**: Failed API calls automatically retry up to 3 times with exponential backoff for resilience against network issues.
- **Input validation**: All inputs sanitized and validated before processing to prevent errors and improve security.

Cache files are stored in `.cache/` and automatically expire based on TTL. To clear cache: `rm -rf .cache/` (Unix) or `rmdir /s .cache` (Windows).

## License

This project is for educational purposes. Use responsibly and in accordance with applicable laws.
