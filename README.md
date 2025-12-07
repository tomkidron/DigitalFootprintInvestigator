# Digital Footprint Investigator

A multi-agent OSINT (Open Source Intelligence) tool built with CrewAI for investigating digital footprints across the web.

## 🎯 Features

- **Multi-Agent Architecture**: Specialized agents working together
  - Google Search Agent: Initial reconnaissance
  - Social Media Agent: Platform-specific searches
  - Analysis Agent: Data correlation and pattern extraction
  - Report Agent: Professional intelligence reports

- **Platform Coverage**:
  - Google Search (with SerpAPI support)
  - LinkedIn
  - Twitter/X
  - GitHub
  - Reddit
  - Instagram (limited)
  - Facebook (limited)

- **Configurable**: YAML-based configuration for easy customization
- **Extensible**: Modular design for adding new platforms and tools
- **Privacy-Aware**: Optional sensitive data redaction

## 📋 Prerequisites

- Python 3.9 or higher
- API key for either OpenAI or Anthropic (Claude)
- Optional: SerpAPI key for enhanced Google searches

## 🚀 Quick Start

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
LLM_MODEL=claude-3-5-sonnet-20241022

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

Or run interactively:

```bash
python main.py
```

## 📁 Project Structure

```
AgentOrchestration/
├── agents/
│   ├── __init__.py
│   └── orchestrator.py       # Agent definitions
├── tasks/
│   ├── __init__.py
│   └── osint_tasks.py        # Task workflow
├── tools/
│   ├── __init__.py
│   ├── search_tools.py       # Google & social media search
│   └── analysis_tools.py     # Data correlation & patterns
├── utils/
│   ├── __init__.py
│   ├── logger.py             # Logging configuration
│   └── config.py             # Config loader
├── reports/                  # Generated reports (created automatically)
├── logs/                     # Log files (created automatically)
├── main.py                   # Entry point
├── config.yaml               # Main configuration
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
LLM_MODEL=claude-3-5-sonnet-20241022

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

**Important**: This tool is for legitimate OSINT purposes only:
- ✅ Security research
- ✅ Due diligence
- ✅ Journalism
- ✅ Personal privacy audits
- ❌ Stalking or harassment
- ❌ Unauthorized surveillance
- ❌ Illegal activities

Always:
- Respect privacy laws and regulations
- Only use publicly available information
- Get proper authorization when required
- Use responsibly and ethically

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new platforms
- Improve search algorithms
- Enhance analysis tools
- Add visualization features

## 📚 Learn More

- [CrewAI Documentation](https://docs.crewai.com/)
- [OSINT Framework](https://osintframework.com/)
- [Anthropic Claude](https://www.anthropic.com/)
- [OpenAI API](https://platform.openai.com/)

## 📄 License

This project is for educational purposes. Use responsibly and in accordance with applicable laws.
