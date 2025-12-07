"""
Agent definitions for the OSINT investigation crew
"""

import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from tools.search_tools import GoogleSearchTool, SocialMediaSearchTool
from tools.analysis_tools import DataCorrelationTool, PatternExtractionTool


def get_llm():
    """Get the configured LLM instance"""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    
    if provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=0.1
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=0.1
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def create_agents(config: dict) -> dict:
    """
    Create all agents for the OSINT investigation
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of agent instances
    """
    llm = get_llm()
    
    # Google Search Agent
    google_agent = Agent(
        role="OSINT Researcher",
        goal="Conduct comprehensive Google searches to find initial information about the target",
        backstory="""You are an expert OSINT researcher specializing in Google dorking 
        and advanced search techniques. You know how to find information that others miss 
        by using creative search queries and analyzing search results thoroughly.""",
        tools=[GoogleSearchTool(config)],
        llm=llm,
        verbose=config['agents']['google_agent'].get('verbose', True),
        allow_delegation=False
    )
    
    # Social Media Agent
    social_agent = Agent(
        role="Social Media Investigator",
        goal="Search across multiple social media platforms to find profiles and activity",
        backstory="""You are a social media intelligence specialist with deep knowledge 
        of how people use different platforms. You excel at finding profiles, connections, 
        and digital footprints across Twitter, LinkedIn, GitHub, Reddit, and other platforms.""",
        tools=[SocialMediaSearchTool(config)],
        llm=llm,
        verbose=config['agents']['social_agent'].get('verbose', True),
        allow_delegation=False
    )
    
    # Analysis Agent
    analysis_agent = Agent(
        role="Data Analyst",
        goal="Correlate and analyze findings to build a comprehensive profile",
        backstory="""You are a data analyst specializing in OSINT. You excel at finding 
        patterns, correlating information from different sources, and determining the 
        confidence level of connections. You can spot when different profiles belong to 
        the same person based on subtle clues.""",
        tools=[
            DataCorrelationTool(config),
            PatternExtractionTool(config)
        ],
        llm=llm,
        verbose=config['agents']['analysis_agent'].get('verbose', True),
        allow_delegation=False
    )
    
    # Report Agent
    report_agent = Agent(
        role="Intelligence Reporter",
        goal="Create comprehensive, well-structured OSINT reports",
        backstory="""You are an intelligence analyst who specializes in creating clear, 
        actionable reports. You know how to present complex findings in an organized way, 
        highlight key discoveries, and provide confidence assessments for each piece of 
        information.""",
        tools=[],  # Report agent uses built-in capabilities
        llm=llm,
        verbose=config['agents']['report_agent'].get('verbose', True),
        allow_delegation=False
    )
    
    return {
        'google': google_agent,
        'social': social_agent,
        'analysis': analysis_agent,
        'report': report_agent
    }
