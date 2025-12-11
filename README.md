# Digital Footprint Investigator

> **⚠️ EDUCATIONAL USE ONLY**: This tool is designed for educational purposes, security research, and legitimate OSINT investigations. Users must comply with all applicable laws and ethical guidelines. Misuse for stalking, harassment, or illegal activities is strictly prohibited.

A multi-agent OSINT (Open Source Intelligence) tool built with LangGraph for investigating digital footprints across the web.

## 🎯 Features

- **LangGraph Workflow**: Parallel execution with state management
  - Google Search: Initial reconnaissance (runs in parallel)
  - Social Media Search: Platform-specific searches (runs in parallel)
  - Analysis: Data correlation and pattern extraction
  - Report Generation: Professional intelligence reports

- **Platform Coverage**:
  - Google Search (with SerpAPI support)
  - LinkedIn
  - Twitter/X
  - GitHub
  - Reddit
  - Instagram (limited)
  - Facebook (limited)

- **Parallel Execution**: Google and social media searches run simultaneously
- **Checkpointing**: Built-in state management for resumable workflows
- **Extensible**: Modular design for adding new platforms and nodes
- **Privacy-Aware**: Uses publicly available information only

## 📋 Prerequisites

- Python 3.11 or 3.12 (or use Docker)
- API key for Anthropic Claude Sonnet 4.5 (recommended) or OpenAI
- Optional: SerpAPI key for enhanced Google searches

## 🚀 Quick Start

### Option 1: Docker (Recommended - Cross-Platform)

**Prerequisites**: Docker Desktop installed

1. **Build the container**:
```bash
docker-compose build
```

2. **Configure API keys**:
```bash
copy .env.example .env
notepad .env
```

Add your API key to `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

3. **Run investigation**:
```bash
docker-compose run --rm osint-tool python main.py "John Doe"
```

**Why Docker?**
- ✅ Works identically on Windows, Mac, and Linux
- ✅ No Python version conflicts
- ✅ All dependencies pre-installed
- ✅ Isolated from your system
- ✅ Easy to share and deploy

**How it works:**
- `Dockerfile` defines the container image (Python 3.12 + all dependencies)
- `docker-compose.yml` configures how to run the container
- Your code is mounted as a volume (changes reflected instantly)
- Reports and logs are saved to your local machine
- `.env` file is loaded at runtime (secrets stay local)

---

### Option 2: Local Python Installation

**Prerequisites**: Python 3.11 or 3.12

---

### Option 3: VS Code DevContainer (For Debugging)

**Prerequisites**: Docker Desktop + VS Code with "Dev Containers" extension

1. Open project in VS Code
2. Press **F1** → "Dev Containers: Reopen in Container"
3. Wait for container to build (~5 minutes first time)
4. Set breakpoints in code
5. Press **F5** to debug with full IDE support

**Perfect for:**
- Learning how the agents work
- Debugging tool behavior
- Developing new features
- Understanding CrewAI internals

---

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
copy .env.example .env
```

Edit `.env` and add your API key:

```env
# For Anthropic (Claude) - Recommended
ANTHROPIC_API_KEY=your_api_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5

# OR for OpenAI
OPENAI_API_KEY=your_api_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4

# Optional: For better Google results
SERPAPI_KEY=your_serpapi_key_here
```

### 3. Customize Configuration

Edit `config.yaml` to enable/disable platforms and adjust settings:

```yaml
platforms:
  linkedin:
    enabled: true
  twitter:
    enabled: true
  github:
    enabled: true
```

### 4. Run Investigation

```bash
python main.py "John Doe"
```

## 📁 Project Structure

```
DigitalFootprintInvestigator/
├── graph/
│   ├── nodes/
│   │   ├── search.py         # Search nodes (Google, Social)
│   │   ├── analysis.py       # Analysis node
│   │   └── report.py         # Report generation node
│   ├── state.py              # LangGraph state definition
│   └── workflow.py           # Workflow orchestration
├── tools/
│   ├── __init__.py
│   └── search_tools.py       # Google & social media search functions
├── utils/
│   ├── __init__.py
│   ├── logger.py             # Logging configuration
│   └── config.py             # Config loader
├── reports/                  # Generated reports (created automatically)
├── logs/                     # Log files (created automatically)
├── main.py                   # Entry point
├── .env                      # API keys (create from .env.example)
├── .env.example              # Environment template
└── requirements.txt          # Python dependencies
```

## ⚙️ Configuration

### config.yaml

The main configuration file controls all aspects of the tool:

**Search Settings**:
```yaml
search:
  max_results: 20           # Max Google results
  timeout: 30               # Request timeout (seconds)
```

**Platform Settings**:
```yaml
platforms:
  linkedin:
    enabled: true
    deep_search: true       # Search for posts, connections
  twitter:
    enabled: true
    max_tweets: 50
```

**Agent Settings**:
```yaml
agents:
  google_agent:
    enabled: true
    retry_attempts: 3
    extract_emails: true    # Extract emails from results
```

**Report Settings**:
```yaml
report:
  format: markdown          # markdown, html, json, or pdf
  output_dir: ./reports
  include_sources: true
```

### .env

Environment variables for API keys and sensitive settings:

```env
# LLM Provider (required)
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5

# Optional APIs
SERPAPI_KEY=...             # Better Google results
TWITTER_BEARER_TOKEN=...    # Twitter API access
GITHUB_TOKEN=...            # GitHub API (higher rate limits)

# Application Settings
DEBUG_MODE=false
LOG_LEVEL=INFO
```

## 🔧 Usage Examples

### Basic Investigation

```bash
python main.py "Jane Smith"
```

### With Email

```bash
python main.py "jane.smith@example.com"
```

### With Username

```bash
python main.py "@janesmith"
```

## 📊 Output

Reports are saved to the `reports/` directory with timestamps:

```
reports/
└── Jane_Smith_20241207_143022.md
```

Example report structure:
- Executive Summary
- Target Overview
- Digital Footprint Analysis
- Platform-by-Platform Breakdown
- Timeline of Activity
- Key Findings and Patterns
- Confidence Assessment
- Sources and References

## 🛠️ Customization

### Adding a New Platform

1. Add platform config to `config.yaml`:
```yaml
platforms:
  new_platform:
    enabled: true
    custom_setting: value
```

2. Add search method to `tools/search_tools.py`:
```python
def _search_new_platform(self, target: str) -> str:
    # Implementation
    pass
```

### Adding a New Tool

1. Create tool in `tools/`:
```python
from crewai_tools import BaseTool

class MyCustomTool(BaseTool):
    name: str = "My Tool"
    description: str = "What it does"
    
    def _run(self, input: str) -> str:
        # Implementation
        pass
```

2. Add to agent in `agents/orchestrator.py`:
```python
from tools.my_tools import MyCustomTool

agent = Agent(
    tools=[MyCustomTool(config)],
    ...
)
```

## 🐛 Troubleshooting

### "API key not found"
- Make sure you've created `.env` from `.env.example`
- Verify your API key is correct
- Check `LLM_PROVIDER` matches your key (anthropic or openai)

### "Search failed"
- Without SerpAPI: Google searches use free library (less reliable)
- Add `SERPAPI_KEY` to `.env` for better results
- Check your internet connection

### "Module not found"
- Run `pip install -r requirements.txt`
- Make sure you're using Python 3.9+

### Rate Limiting
- Adjust `rate_limit` in `config.yaml`
- Add API keys for platforms (GitHub, Twitter)
- Use SerpAPI for Google searches

## 📝 Logs

Logs are saved to `logs/osint_YYYYMMDD.log` with detailed information about:
- Agent activities
- Tool executions
- Errors and warnings
- API calls

Set log level in `.env`:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 🔒 Privacy & Ethics

**⚠️ IMPORTANT DISCLAIMER**: This tool is for **EDUCATIONAL AND LEGITIMATE PURPOSES ONLY**

### ✅ Appropriate Uses:
- **Security research** and vulnerability assessment
- **Due diligence** for business purposes
- **Journalism** and investigative reporting
- **Personal privacy audits** (your own digital footprint)
- **Academic research** on OSINT methodologies
- **Privacy awareness education**
- **Identity verification** with proper consent

### ❌ Prohibited Uses:
- **Stalking or harassment** of any individual
- **Unauthorized surveillance** or monitoring
- **Identity theft** or fraudulent activities
- **Discrimination** in employment, housing, or services
- **Doxxing** or publishing private information
- **Any illegal activities** under applicable laws

### 🛡️ Ethical Guidelines:
- **Respect privacy laws** (GDPR, CCPA, etc.)
- **Use only publicly available information**
- **Obtain proper authorization** when required
- **Minimize data collection** to what's necessary
- **Secure any collected data** appropriately
- **Delete data** when no longer needed
- **Report responsibly** - don't cause harm

### ⚖️ Legal Compliance:
Users are responsible for ensuring their use complies with:
- Local and international privacy laws
- Platform Terms of Service
- Computer Fraud and Abuse Act (CFAA)
- Data protection regulations
- Professional ethical standards

**By using this tool, you agree to use it responsibly and ethically.**

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new platforms
- Improve search algorithms
- Enhance analysis tools
- Add visualization features

## 📚 Learn More

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [OSINT Framework](https://osintframework.com/)
- [Anthropic Claude](https://www.anthropic.com/)
- [OpenAI API](https://platform.openai.com/)

## 📄 License

This project is for educational purposes. Use responsibly and in accordance with applicable laws.
