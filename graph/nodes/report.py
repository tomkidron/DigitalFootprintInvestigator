"""Report generation node for LangGraph workflow"""

from datetime import datetime
from pathlib import Path

from graph.nodes._timing import log_done, log_start
from utils.llm import get_llm


def _determine_actual_platforms(google_data: str, social_data: str) -> list:
    """Determine which platforms were actually analyzed based on data content"""
    platforms = []

    if google_data and "Google Search Results" in google_data:
        platforms.append("Google")

    if social_data:
        if "[OK] Found GitHub profile" in social_data:
            platforms.append("GitHub")
        if "[OK] Found Reddit profile" in social_data:
            platforms.append("Reddit")
        if "LinkedIn profiles" in social_data or "site:linkedin.com" in social_data:
            platforms.append("LinkedIn (via Google)")
        if "Twitter/X search" in social_data:
            platforms.append("Twitter/X (search strategies)")

    return platforms


def report_node(state):
    """Generate final OSINT report"""
    start = log_start("Report generation")
    target = state["target"]
    google_data = "\n".join(state.get("google_data", []))
    social_data = "\n".join(state.get("social_data", []))
    analysis = state.get("analysis", "")
    current_date = datetime.now().strftime("%B %d, %Y")

    llm = get_llm()

    actual_platforms = _determine_actual_platforms(google_data, social_data)
    platform_count = len(actual_platforms)
    platform_list = ", ".join(actual_platforms)

    prompt = f"""Create a comprehensive OSINT investigation report on: {target}

IMPORTANT METADATA:
- Report Generation Date: {current_date}
- Data Collection Date: {current_date}
- Investigation Status: Assess whether ongoing monitoring is recommended or investigation is complete
- Data Quality: Rate the overall quality and completeness of gathered data (High/Medium/Low)
- Platforms Actually Analyzed: {platform_count} ({platform_list})

CRITICAL REPORTING ACCURACY:
- ONLY report platforms that were actually analyzed with tools
- Do NOT claim analysis of platforms without actual data
- Use SPECIFIC, MEASURABLE data instead of vague statements
- Every claim must be verifiable and quantified where possible
- Show confidence scores ONCE per section in headers: "## Section (Confidence: 95%)"
- Include "ANALYSIS METHOD" for each platform showing what tool was used
- Do NOT include comparison tables between subjects unless BOTH have equal analysis depth
- Remove useless timeline entries like "Current investigation date"
- If multiple subjects identified, clearly state analysis limitations for each

Report structure:
- Executive Summary (specific findings, not generalizations)
- Report Metadata (Generation Date: {current_date}, Investigation Status, Data Quality, Actual Platforms Analyzed)
- Target Overview (separate sections per subject if multiple found)
- Digital Footprint Analysis (ONLY for subjects with actual platform data)
- Platform-by-Platform Breakdown (ONLY platforms with actual data, ONLY for primary subject)
- Secondary Subject Status (if applicable - explain why limited analysis)
- Key Findings and Patterns
- Confidence Assessment
- Sources and References
- Data Freshness Disclaimer

GOOGLE SEARCH FINDINGS:
{google_data}

SOCIAL MEDIA FINDINGS:
{social_data}

ANALYSIS:
{analysis}

Format: Professional markdown report with all sources cited and analysis methods documented."""

    response = llm.invoke(prompt)
    report = response.content

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join(c for c in target if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{safe_target}_{timestamp}.md"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    log_done("Report generation", start)
    print(f"Report saved: {filepath}")

    return {"report": report}
