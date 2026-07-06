"""Report generation node for LangGraph workflow"""

import json
from datetime import datetime
from pathlib import Path

import markdown
from langchain_core.messages import HumanMessage, SystemMessage
from xhtml2pdf import pisa

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
    config = state.get("config", {})
    scan_mode = config.get("scan_mode", "Advanced").capitalize()

    llm = get_llm(purpose="report")

    try:
        from langchain_core.callbacks.manager import dispatch_custom_event

        dispatch_custom_event("investigation_log", {"message": "Generating final Markdown report..."})
    except Exception:
        pass  # nosec B110

    actual_platforms = _determine_actual_platforms(google_data, social_data)
    platform_count = len(actual_platforms)
    platform_list = ", ".join(actual_platforms)

    system_prompt = (
        "You are an elite Cyber Intelligence (OSINT) Analyst working for a top-tier security firm. "
        "Your analysis must be entirely objective, evidence-based, and free of hallucinations. "
        "You do not make assumptions. You quantify your confidence in every assertion. "
        "Your sole duty is to synthesize raw intelligence and analysis into a highly structured, professional Markdown report."
    )

    human_prompt = f"""Create a comprehensive OSINT investigation report on: {target}

<metadata>
IMPORTANT METADATA:
- Report Generation Date: {current_date}
- Data Collection Date: {current_date}
- Investigation Status: Assess whether ongoing monitoring is recommended or investigation is complete
- Data Quality: Rate the overall quality and completeness of gathered data (High/Medium/Low)
- Platforms Actually Analyzed: {platform_count} ({platform_list})
- Scan Mode: {scan_mode}
</metadata>

<formatting_rules>
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
- NEVER report an email address as a finding unless it is explicitly verified by HIBP or extracted verbatim from a real source snippet or API.
- Do NOT use the tilde character (~) for approximations (e.g., use "approx. 50" instead of "~50") as multiple tildes cause unintended markdown strikethrough rendering.
- FORMATTING CRITICAL: Do NOT use <br> or any HTML tags anywhere in the report. For newlines, use standard Markdown (double blank lines for new paragraphs, or two spaces at the end of a line for soft breaks).

REPORT HEADER BLOCK (mandatory, immediately after the main # title):
Immediately after the main `# OSINT Investigation Report: <target>` title line, include exactly this compact block — no extra text between the title and the block:

**Classification:** Open Source Intelligence (OSINT) — Public Information Only
**Report Generation Date:** {current_date}
**Data Collection Date:** {current_date}
**Scan Mode:** {scan_mode}
**Prepared By:** Automated OSINT Analysis System
**Distribution:** Authorized Recipients Only

Report structure (Strictly follow this professional format):
- 1. Executive Summary (Overview, Objective, Summary of specific findings, Initial Recommendations)
- 2. Scope of Investigation (Subject of Investigation, Scope and Limitations, Timeframe, Scan Mode: {scan_mode})
- 3. Research Methodology (Data Quality, Actual Platforms Analyzed: {platform_count} ({platform_list}), Tools & Techniques Used)
- 4. Findings
  - 4.1. Entity Overview (Basic Information, Aliases, Target Overview)
  - 4.2. Online Presence & Social Media Analysis (Platform-by-Platform Breakdown, ONLY for platforms with actual data)
  - 4.3. Public Records & Data Breaches (Breach data and associated risks)
  - 4.4. Network Analysis (Secondary Subjects and their connections, if applicable)
- 5. Risks & Concerns (Privacy Concerns, Data Exposure Risks)
- 6. Conclusion & Recommendations (Key Findings, Next Steps)
- 7. Appendix (Sources and References, Confidence Assessment, Data Freshness Disclaimer)
Format: Professional agency-grade markdown report with all sources cited and analysis methods documented.
</formatting_rules>

<intelligence_data>
  <google_search>
{google_data}
  </google_search>

  <social_search>
{social_data}
  </social_search>

  <analysis>
{analysis}
  </analysis>
</intelligence_data>"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]

    response = llm.invoke(messages)
    report = response.content

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join(c for c in target if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    base_filename = f"{safe_target}_{scan_mode}_{timestamp}"

    # Paths for all formats
    md_path = (output_dir / f"{base_filename}.md").resolve()
    json_path = (output_dir / f"{base_filename}.json").resolve()
    html_path = (output_dir / f"{base_filename}.html").resolve()
    pdf_path = (output_dir / f"{base_filename}.pdf").resolve()

    if not str(md_path).startswith(str(output_dir.resolve())):
        raise ValueError(f"Invalid report path: {md_path}")

    # 1. Save Markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report)

    # 2. Save JSON
    report_data = {
        "target": target,
        "scan_mode": scan_mode,
        "timestamp": timestamp,
        "report_markdown": report,
        "metadata": {"platforms_analyzed": actual_platforms},
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # 3. Generate & Save HTML
    html_content = markdown.markdown(report, extensions=["tables", "fenced_code"])
    # Wrap in basic HTML structure for PDF rendering
    full_html = f"<html><head><style>body {{ font-family: Helvetica, Arial, sans-serif; line-height: 1.4; }} h1, h2, h3 {{ color: #333; }} table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #ddd; padding: 8px; }}</style></head><body>{html_content}</body></html>"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    # 4. Generate & Save PDF
    with open(pdf_path, "wb") as f:
        pisa_status = pisa.CreatePDF(full_html, dest=f)
        if pisa_status.err:
            print(f"Error generating PDF: {pisa_status.err}")

    log_done("Report generation", start)
    print(f"Reports saved in {output_dir} with base name {base_filename}")

    return {"report": report, "report_filename": base_filename}
