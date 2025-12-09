#!/usr/bin/env python3
"""
Digital Footprint Investigator
A multi-agent OSINT tool using CrewAI for orchestration
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

from crewai import Crew
from agents.orchestrator import create_agents
from tasks.osint_tasks import create_tasks
from utils.logger import setup_logger, ProgressTracker
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
    
    # Check for SerpAPI key and warn if missing (not required, but strongly recommended)
    serpapi_key = os.getenv("SERPAPI_KEY", "").strip()
    if not serpapi_key:
        logger.warning("⚠️ SERPAPI_KEY not configured")
        logger.warning("Google searches will use unreliable free library with rate-limiting")
        logger.warning("For accurate results, sign up at https://serpapi.com (free tier: 100 searches/month)")
        logger.warning("Then add SERPAPI_KEY to your .env file")
    else:
        logger.info("✓ SerpAPI configured - Google searches will use reliable API")
    
    return True
def run_investigation(target: str, config_path: str = "config.yaml"):
    """
    Run OSINT investigation on a target

    Args:
        target: The search target (name, email, username, etc.)
        config_path: Path to configuration file
    """
    logger.info(f"Starting investigation for target: {target}")
    progress = ProgressTracker(logger)

    # Define investigation stages
    stages = [
        "Environment Validation",
        "Configuration Loading",
        "Agent Initialization",
        "Task Creation",
        "Crew Assembly",
        "Investigation Execution",
        "Report Generation",
    ]
    progress.set_stages(stages)

    # Stage 1: Validate environment
    progress.start_stage("Environment Validation")
    if not validate_environment():
        logger.error("Environment validation failed. Check your .env file")
        return None
    progress.complete_stage("Environment Validation")

    # Stage 2: Load configuration
    progress.start_stage("Configuration Loading")
    config = load_config(config_path)
    logger.info("Configuration loaded successfully")
    output_dir = Path(config["report"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    progress.complete_stage("Configuration Loading", f"Output dir: {output_dir}")

    # Stage 3: Create agents
    progress.start_stage("Agent Initialization")
    agents = create_agents(config)
    agent_names = list(agents.keys())
    logger.info(f"Created {len(agents)} agents: {', '.join(agent_names)}")
    progress.complete_stage("Agent Initialization", f"{len(agents)} agents")

    # Stage 4: Create tasks
    progress.start_stage("Task Creation")
    tasks = create_tasks(agents, target, config)
    logger.info(f"Created {len(tasks)} tasks")
    progress.complete_stage("Task Creation", f"{len(tasks)} tasks")

    # Stage 5: Assemble crew
    progress.start_stage("Crew Assembly")
    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        verbose=config["agents"]["orchestrator"]["verbose"],
    )
    progress.complete_stage("Crew Assembly")

    # Stage 6: Run investigation
    progress.start_stage("Investigation Execution")
    try:
        logger.info(f"Executing investigation workflow for target: {target}")
        result = crew.kickoff()
        progress.complete_stage("Investigation Execution", "Workflow completed")

        # Stage 7: Generate report
        progress.start_stage("Report Generation")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = "".join(
            c for c in target if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        report_filename = f"{safe_target}_{timestamp}.{config['report']['format']}"
        report_path = output_dir / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(str(result))

        progress.complete_stage("Report Generation", f"Saved to {report_path}")
        logger.info(f"Investigation complete! Report saved to: {report_path}")
        return report_path

    except Exception as e:
        logger.error(f"Investigation failed: {str(e)}", exc_info=True)
        progress.logger.error(f"Investigation failed at stage: Investigation Execution")
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Digital Footprint Investigator - Multi-Agent OSINT Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "John Doe"
  python main.py --target "jane@example.com"
  python main.py --config custom_config.yaml "username123"
        """,
    )

    parser.add_argument(
        "target", nargs="?", help="Search target (name, email, username, etc.)"
    )
    parser.add_argument(
        "--target",
        "-t",
        dest="target_flag",
        help="Search target (alternative to positional argument)",
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    # Get target from either positional arg or flag
    target = args.target or args.target_flag

    print("=" * 60)
    print("Digital Footprint Investigator")
    print("Multi-Agent OSINT Tool")
    print("=" * 60)
    print()

    # If no target provided, prompt for it
    if not target:
        target = input("Enter search target (name, email, username, etc.): ").strip()

    if not target:
        print("Error: No target provided")
        parser.print_help()
        sys.exit(1)

    # Run investigation
    report_path = run_investigation(target, args.config)

    if report_path:
        print(f"\n✅ Investigation complete!")
        print(f"📄 Report: {report_path}")
    else:
        print("\n❌ Investigation failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
