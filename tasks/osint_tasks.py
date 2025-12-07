"""
Task definitions for the OSINT investigation workflow
"""

from crewai import Task


def create_tasks(agents: dict, target: str, config: dict) -> list:
    """
    Create investigation tasks
    
    Args:
        agents: Dictionary of agent instances
        target: The search target
        config: Configuration dictionary
        
    Returns:
        List of Task instances
    """
    
    # Task 1: Google Search
    google_search_task = Task(
        description=f"""
        Conduct a comprehensive Google search investigation on: {target}
        
        Your objectives:
        1. Perform initial broad search to understand who/what the target is
        2. Extract key identifiers: emails, phone numbers, usernames, locations
        3. Find associated websites, social media profiles, and online presence
        4. Use advanced search operators to find additional information
        5. Document all findings with source URLs
        
        Search strategies to use:
        - Direct name search
        - Email/username variations
        - Professional affiliations
        - Location-based searches
        - Quoted exact matches
        
        Provide a structured summary of all findings with confidence levels.
        """,
        agent=agents['google'],
        expected_output="""A detailed report containing:
        - Summary of who/what the target is
        - List of discovered identifiers (emails, phones, usernames)
        - URLs of relevant websites and profiles
        - Key facts and timeline information
        - Confidence assessment for each finding"""
    )
    
    # Task 2: Social Media Search
    social_media_task = Task(
        description=f"""
        Based on the Google search findings, conduct deep social media investigation on: {target}
        
        Your objectives:
        1. Search for profiles on enabled platforms: {', '.join([p for p, c in config['platforms'].items() if c.get('enabled', False)])}
        2. For each found profile, collect:
           - Profile information (bio, location, links)
           - Recent activity and posts
           - Connections and interactions
           - Posting patterns and interests
        3. Cross-reference information to verify it's the same person
        4. Look for additional identifiers or aliases
        
        Focus on platforms where the target is most active.
        Document everything with timestamps and URLs.
        """,
        agent=agents['social'],
        expected_output="""A comprehensive social media report containing:
        - List of confirmed profiles with URLs
        - Profile details and activity summaries
        - Common themes and interests
        - Posting patterns and timeline
        - Additional identifiers discovered
        - Confidence scores for each profile match""",
        context=[google_search_task]  # Depends on Google search results
    )
    
    # Task 3: Data Analysis and Correlation
    analysis_task = Task(
        description=f"""
        Analyze and correlate all gathered intelligence on: {target}
        
        Your objectives:
        1. Cross-reference findings from Google and social media searches
        2. Identify patterns in usernames, emails, posting behavior
        3. Build connections between different profiles and identities
        4. Assess confidence levels for each connection
        5. Flag any inconsistencies or conflicting information
        6. Create a timeline of digital activity
        7. Identify gaps in information that need further investigation
        
        Use data correlation and pattern extraction tools to:
        - Find common elements across platforms
        - Detect username patterns
        - Link related accounts
        - Assess reliability of information
        """,
        agent=agents['analysis'],
        expected_output="""An analytical report containing:
        - Correlation matrix showing connections between findings
        - Pattern analysis (usernames, emails, behaviors)
        - Timeline of digital activity
        - Confidence-scored profile of the target
        - List of verified facts vs. probable information
        - Recommendations for additional investigation""",
        context=[google_search_task, social_media_task]
    )
    
    # Task 4: Final Report Generation
    current_date = datetime.now().strftime("%B %d, %Y")
    
    report_task = Task(
        description=f"""
        Create a comprehensive OSINT investigation report on: {target}
        
        IMPORTANT METADATA:
        - Report Generation Date: {current_date}
        - Data Collection Date: {current_date}
        - Investigation Status: Assess whether ongoing monitoring is recommended or investigation is complete
        - Data Quality: Rate the overall quality and completeness of gathered data (High/Medium/Low)
        - Primary Intelligence Value: Identify the most valuable source or platform for this target
        - Note: This report is based on publicly available information as of {current_date}
        - LLM Knowledge Cutoff: The AI assistant's training data may not include events after its cutoff date
        
        Your objectives:
        1. Synthesize all findings into a clear, professional report
        2. Organize information by category (identity, social media, activity, etc.)
        3. Include confidence scores and source citations
        4. Highlight key discoveries and patterns
        5. Provide executive summary
        6. Include methodology and tools used
        7. CLEARLY STATE the report date as {current_date}
        8. Include a disclaimer about data freshness and LLM knowledge limitations
        9. Assess investigation status (ongoing monitoring vs. complete)
        10. Rate data quality and identify most valuable intelligence sources
        
        Report structure:
        - Executive Summary
        - Report Metadata (Generation Date: {current_date}, Investigation Status, Data Quality, Primary Intelligence Value)
        - Target Overview
        - Digital Footprint Analysis
        - Platform-by-Platform Breakdown
        - Timeline of Activity
        - Key Findings and Patterns
        - Confidence Assessment
        - Sources and References
        - Recommendations
        - Data Freshness Disclaimer
        
        Format: Markdown
        Include: sources, timestamps, and confidence scores
        
        CRITICAL: The report date MUST be {current_date}, not any other date.
        Include a section explaining data freshness and potential limitations.
        """,
        agent=agents['report'],
        expected_output="""A professional OSINT report in markdown format with:
        - Clear executive summary
        - Report metadata with current date and data freshness information
        - Organized findings by category
        - All sources cited with URLs
        - Confidence scores for each claim
        - Visual timeline if applicable
        - Actionable insights and patterns
        - Professional formatting and structure
        - Data freshness disclaimer explaining when information was collected""",
        context=[google_search_task, social_media_task, analysis_task]
    )
    
    return [
        google_search_task,
        social_media_task,
        analysis_task,
        report_task
    ]
