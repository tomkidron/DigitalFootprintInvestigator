# Digital Footprint Investigator

> **EDUCATIONAL USE ONLY**: This tool is designed for educational purposes, security research, and legitimate OSINT investigations. Users must comply with all applicable laws and ethical guidelines. Misuse for stalking, harassment, or illegal activities is strictly prohibited.

A multi-agent OSINT tool built with [LangGraph](https://langchain-ai.github.io/langgraph/) that searches across Google, social media platforms, and enrichment APIs in parallel, then chains the results through an analysis and report-generation stage powered by Claude (Anthropic).

## Features

- **Parallel LangGraph workflow**: Google search and social media search run simultaneously; results feed a single analysis → report pipeline
- **Platform coverage**: Google (SerpAPI or free fallback), GitHub, Reddit, Twitter/X, YouTube, LinkedIn, Instagram (limited), Facebook (limited)
- **API enrichment**: HIBP breach detection, Hunter.io email discovery
- **Streamlit web UI**: interactive interface with real-time log streaming and report download
- **CLI mode**: scriptable via `python main.py`
- **Advanced analysis** (optional): timeline correlation, network analysis, deep content analysis
- **Docker-first**: a single image runs the app, unit tests, and UI tests

## Prerequisites

- Python 3.11+ (or Docker)
- **Required**: Anthropic API key
- **Optional**: additional API keys for richer results (see [Environment](#environment))

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Copy and fill in your API keys
cp .env.example .env   # then edit .env and set ANTHROPIC_API_KEY

# Build and start the web UI
docker compose up --build
```

Open `http://localhost:8501` in your browser.

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

# Start the web UI
streamlit run app.py

# Or use the CLI
python main.py "John Doe"
```

---

### Option 3: VS Code DevContainer

1. Open the project in VS Code
2. Press **F1** → *Dev Containers: Reopen in Container*
3. Wait for the container to build (~5 minutes first time)
4. Set breakpoints and press **F5** to debug with full IDE support

---

## Environment

Copy `.env.example` to `.env` and configure:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-6          # default; change to use a different Claude model

# Optional — the tool works without these, but results improve significantly
SERPAPI_KEY=...                       # Better Google results ($50/mo, 5000 searches)
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
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | Pay-per-use |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → Personal access tokens | Free |
| `YOUTUBE_API_KEY` | [console.developers.google.com](https://console.developers.google.com) → YouTube Data API v3 | Free (quota) |
| `TWITTER_BEARER_TOKEN` | [developer.twitter.com](https://developer.twitter.com) | Free tier |
| `HUNTER_API_KEY` | [hunter.io/api](https://hunter.io/api) | Free tier (25/mo) |
| `HIBP_API_KEY` | [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) | $3.50/mo |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) | $50/mo |

> **Quick start recommendation**: Enable `GITHUB_TOKEN` and `YOUTUBE_API_KEY` first — both are free and require no approval.

## Project Structure

```
DigitalFootprintInvestigator/
├── graph/
│   ├── nodes/
│   │   ├── _timing.py        # Shared log_start / log_done helpers
│   │   ├── search.py         # Google and social search nodes (run in parallel)
│   │   ├── analysis.py       # Data correlation and pattern extraction
│   │   ├── advanced.py       # Optional timeline / network / content analysis
│   │   └── report.py         # Claude-powered report generation
│   ├── state.py              # LangGraph state TypedDict
│   └── workflow.py           # Graph construction and MemorySaver checkpointing
├── tools/
│   ├── search_tools.py       # Google search and platform scrapers
│   └── api_tools.py          # HIBP, Hunter.io, YouTube, Twitter wrappers
├── utils/
│   ├── llm.py                # Shared ChatAnthropic factory
│   └── logger.py             # Logging setup
├── tests/
│   ├── conftest.py           # Playwright session/page fixtures
│   ├── healer.py             # Self-healing Playwright page wrapper
│   ├── unit/                 # 144 unit tests (no browser or live API required)
│   └── ui/                   # 18 Playwright browser tests
├── app.py                    # Streamlit web UI
├── main.py                   # CLI entry point
├── config.yaml               # Platform and analysis settings
├── pytest.ini                # Test markers and paths
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── Dockerfile                # Single image used by all three services
├── docker-compose.yml        # Services: osint-tool, unit-tests, tests
└── .dockerignore             # Docker build exclusions
```

## Running Tests

### Locally

```bash
# Unit tests (no browser, no API key needed)
python -m pytest tests/unit/ -v

# UI tests (starts Streamlit automatically; requires a Playwright browser)
playwright install chromium   # first time only
python -m pytest tests/ui/ -m "not integration" -v

# Integration tests (require ANTHROPIC_API_KEY and a full workflow run)
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

**Advanced analysis** (each option adds an extra LLM pass; all off by default):

```yaml
advanced_analysis:
  timeline_correlation: false   # Build a chronological activity timeline
  network_analysis: false       # Map relationships between accounts
  deep_content_analysis: false  # Sentiment, topics, behavioral patterns
```

**CLI flags:**

```bash
python main.py "Jane Smith" --timeline --network --deep
```

## Usage Examples

```bash
# Name
python main.py "Jane Smith"

# Email
python main.py "jane.smith@example.com"

# Username
python main.py "@janesmith"

# With advanced analysis
python main.py "Jane Smith" --timeline --network --deep
```

Reports are saved to `reports/` with a timestamp, e.g. `reports/Jane_Smith_20260227_143022.md`.

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

**"No Anthropic API key found"** — create `.env` from `.env.example` and set `ANTHROPIC_API_KEY`.

**Google searches return no results** — the free `googlesearch-python` library is rate-limited and unreliable. Add `SERPAPI_KEY` to `.env` for consistent results.

**Page refresh hangs in Docker on Windows** — Streamlit’s file watcher conflicts with Docker volume mounts. `fileWatcherType = "none"` is set in `.streamlit/config.toml`; restore it if it gets removed.

**`Module not found`** — run `pip install -r requirements.txt` and confirm Python 3.11+.

**Console warning: `missing ScriptRunContext`** — harmless startup warning, handled in `app.py`.

**Console warning: `file_cache is only supported with oauth2client<4.0.0`** — harmless warning from the Google API client library.

**Docker Desktop won’t start (WSL error)** — the Ubuntu WSL distro may have auto-shut down. Run `wsl -d Ubuntu` in a terminal first, wait a few seconds, then retry Docker Desktop.

## Privacy & Ethics

**EDUCATIONAL AND LEGITIMATE PURPOSES ONLY**

Appropriate uses: security research, due diligence, investigative journalism, personal privacy audits, OSINT methodology research, identity verification with consent.

Prohibited uses: stalking or harassment, unauthorized surveillance, identity theft, doxxing, any illegal activity.

All searches use publicly available information only. Users are responsible for compliance with local privacy laws (GDPR, CCPA, etc.), platform Terms of Service, and the Computer Fraud and Abuse Act (CFAA).

**By using this tool, you agree to use it responsibly and ethically.**

## License

This project is for educational purposes. Use responsibly and in accordance with applicable laws.
