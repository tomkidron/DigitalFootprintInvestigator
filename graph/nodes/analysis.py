"""Analysis node for LangGraph workflow"""

from langchain_core.messages import HumanMessage, SystemMessage

from graph.nodes._timing import log_done, log_event, log_start
from utils.llm import get_llm


def analysis_node(state):
    """Analyze collected data and extract patterns"""
    start = log_start("Analysis")
    current_date = start.strftime("%Y-%m-%d")
    target = state["target"]
    google_data = "\n".join(state.get("google_data", []))
    social_data = "\n".join(state.get("social_data", []))

    llm = get_llm(purpose="analysis")

    log_event("Correlating intelligence data with AI...")

    system_prompt = (
        "You are an elite Cyber Intelligence (OSINT) Analyst working for a top-tier security firm. "
        "Your analysis must be entirely objective, evidence-based, and free of hallucinations. "
        "You do not make assumptions. You quantify your confidence in every assertion."
    )

    human_prompt = f"""Analyze and correlate all gathered intelligence on: {target}

<rules>
IMPORTANT: Today's date is {current_date}. Use this to validate any dates found in the data. Flag dates that are in the future as potential errors.

CRITICAL ANALYSIS RULES:
- Do NOT extrapolate patterns from single data points
- Do NOT claim "consistent themes" unless you have 3+ examples
- Do NOT assume series/patterns exist based on one video/post
- Always specify sample size when making behavioral claims
- Use phrases like "single example suggests" instead of "consistent pattern"
- Flag insufficient data clearly in your analysis
</rules>

<objectives>
Your objectives:
1. Cross-reference findings from Google and social media searches
2. Identify patterns in usernames, emails, posting behavior
3. Build connections between different profiles and identities
4. Assess confidence levels for each connection
5. Flag any inconsistencies or conflicting information
6. Create a timeline of digital activity
7. Identify gaps in information that need further investigation
8. Validate all dates against today's date ({current_date})
</objectives>

<raw_intelligence>
  <google_search>
{google_data}
  </google_search>

  <social_search>
{social_data}
  </social_search>
</raw_intelligence>

Provide an analytical report containing:
- Correlation matrix showing connections between findings
- Pattern analysis (usernames, emails, behaviors)
- Timeline of digital activity (with date validation)
- Confidence-scored profile of the target
- List of verified facts vs. probable information
- Recommendations for additional investigation"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

    response = llm.invoke(messages)
    log_done("Analysis", start)

    return {"analysis": response.content}
