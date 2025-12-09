"""Report generation node for LangGraph workflow"""
import os
from datetime import datetime
from pathlib import Path


def report_node(state):
    """Generate final OSINT report"""
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    
    start = datetime.now()
    print(f"\n[{start.strftime('%H:%M:%S')}] 📝 Report generation started...")
    target = state["target"]
    google_data = "\n".join(state.get("google_data", []))
    social_data = "\n".join(state.get("social_data", []))
    analysis = state.get("analysis", "")
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Get LLM
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
    llm = ChatAnthropic(model=model, temperature=0) if provider == "anthropic" else ChatOpenAI(model=model, temperature=0)
    
    # Generate comprehensive report using LLM
    prompt = f"""Create a comprehensive OSINT investigation report on: {target}

IMPORTANT METADATA:
- Report Generation Date: {current_date}
- Data Collection Date: {current_date}
- Investigation Status: Assess whether ongoing monitoring is recommended or investigation is complete
- Data Quality: Rate the overall quality and completeness of gathered data (High/Medium/Low)

CRITICAL REPORTING STANDARDS:
- Use SPECIFIC, MEASURABLE data instead of vague statements
- Every claim must be verifiable and quantified where possible
- Show confidence scores ONCE per section in headers: "## Section (Confidence: 95%)"

Report structure:
- Executive Summary (specific findings, not generalizations)
- Report Metadata (Generation Date: {current_date}, Investigation Status, Data Quality)
- Target Overview
- Digital Footprint Analysis
- Platform-by-Platform Breakdown
- Timeline of Activity
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

Format: Professional markdown report with all sources cited."""
    
    response = llm.invoke(prompt)
    report = response.content
    
    # Save report
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = "".join(c for c in target if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    filename = f"{safe_target}_{timestamp}.md"
    filepath = output_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    end = datetime.now()
    duration = (end - start).total_seconds()
    print(f"[{end.strftime('%H:%M:%S')}] ✓ Report generation complete ({duration:.1f}s)")
    print(f"✅ Report saved: {filepath}")
    
    return {"report": report}
