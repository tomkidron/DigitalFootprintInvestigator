"""Report generation node for LangGraph workflow"""

import json
from datetime import datetime
from pathlib import Path

import markdown
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

    return {"report": report}
