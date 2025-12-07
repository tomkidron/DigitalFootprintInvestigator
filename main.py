#!/usr/bin/env python3
"""
Digital Footprint Investigator
A multi-agent OSINT tool using CrewAI for orchestration
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from crewai import Crew
from agents.orchestrator import create_agents
from tasks.osint_tasks import create_tasks
from utils.logger import setup_logger
from utils.config import load_config

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger()


def validate_environment():
    """Validate that required environment variables are set"""
    llm_provider = os.getenv("LLM_PROVIDER", "anthropic")
    
    if llm_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY not found in environment")
            return False
    elif llm_provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            logger.error("ANTHROPIC_API_KEY not found in environment")
            return False
    else:
        logger.error(f"Invalid LLM_PROVIDER: {llm_provider}")
        return False
    
    return True


def run_investigation(target: str, config_path: str = "config.yaml"):
    """
    Run OSINT investigation on a target
    
    Args:
        target: The search target (name, email, username, etc.)
        config_path: Path to configuration file
    """
    logger.info(f"Starting investigation for target: {target}")
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Check your .env file")
        return None
    
    # Load configuration
    config = load_config(config_path)
    logger.info("Configuration loaded successfully")
    
    # Create output directory if it doesn't exist
    output_dir = Path(config['report']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create agents
    logger.info("Initializing agents...")
    agents = create_agents(config)
    
    # Create tasks
    logger.info("Creating tasks...")
    tasks = create_tasks(agents, target, config)
    
    # Create crew
    logger.info("Assembling crew...")
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=config['agents']['orchestrator']['verbose']
    )
    
    # Run investigation
    logger.info("Starting investigation workflow...")
    try:
        result = crew.kickoff()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = "".join(c for c in target if c.isalnum() or c in (' ', '-', '_')).strip()
        report_filename = f"{safe_target}_{timestamp}.{config['report']['format']}"
        report_path = output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(str(result))
        
        logger.info(f"Investigation complete! Report saved to: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Investigation failed: {str(e)}", exc_info=True)
        return None


def main():
    """Main entry point"""
    print("=" * 60)
    print("Digital Footprint Investigator")
    print("Multi-Agent OSINT Tool")
    print("=" * 60)
    print()
    
    # Get target from command line or prompt
    if len(sys.argv) > 1:
        target = " ".join(sys.argv[1:])
    else:
        target = input("Enter search target (name, email, username, etc.): ").strip()
    
    if not target:
        print("Error: No target provided")
        sys.exit(1)
    
    # Run investigation
    report_path = run_investigation(target)
    
    if report_path:
        print(f"\n✅ Investigation complete!")
        print(f"📄 Report: {report_path}")
    else:
        print("\n❌ Investigation failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
