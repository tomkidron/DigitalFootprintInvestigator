"""Analysis node for LangGraph workflow"""
import os
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI


def get_llm():
    """Get configured LLM"""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
    
    if provider == "anthropic":
        return ChatAnthropic(model=model, temperature=0)
    else:
        return ChatOpenAI(model=model, temperature=0)


def analysis_node(state):
    """Analyze collected data and extract patterns"""
    start = datetime.now()
    current_date = start.strftime('%Y-%m-%d')
    print(f"\n[{start.strftime('%H:%M:%S')}] 📊 Analysis started...")
    target = state["target"]
    google_data = "\n".join(state.get("google_data", []))
    social_data = "\n".join(state.get("social_data", []))
    
    llm = get_llm()
    
    prompt = f"""Analyze and correlate all gathered intelligence on: {target}

IMPORTANT: Today's date is {current_date}. Use this to validate any dates found in the data. Flag dates that are in the future as potential errors.

CRITICAL ANALYSIS RULES:
- Do NOT extrapolate patterns from single data points
- Do NOT claim "consistent themes" unless you have 3+ examples
- Do NOT assume series/patterns exist based on one video/post
- Always specify sample size when making behavioral claims
- Use phrases like "single example suggests" instead of "consistent pattern"
- Flag insufficient data clearly in your analysis

Your objectives:
1. Cross-reference findings from Google and social media searches
2. Identify patterns in usernames, emails, posting behavior
3. Build connections between different profiles and identities
4. Assess confidence levels for each connection
5. Flag any inconsistencies or conflicting information
6. Create a timeline of digital activity
7. Identify gaps in information that need further investigation
8. Validate all dates against today's date ({current_date})

GOOGLE SEARCH FINDINGS:
{google_data}

SOCIAL MEDIA FINDINGS:
{social_data}

Provide an analytical report containing:
- Correlation matrix showing connections between findings
- Pattern analysis (usernames, emails, behaviors)
- Timeline of digital activity (with date validation)
- Confidence-scored profile of the target
- List of verified facts vs. probable information
- Recommendations for additional investigation"""

    response = llm.invoke(prompt)
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Analysis complete ({duration:.1f}s)")
    
    return {"analysis": response.content}
