"""LangGraph-based OSINT tool entry point"""

import argparse

import yaml
from dotenv import load_dotenv

from graph.workflow import create_workflow
from utils.validation import detect_target_type

# Load environment variables from .env
load_dotenv()


def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Default config if file doesn't exist
        return {
            "advanced_analysis": {
                "timeline_correlation": False,
                "network_analysis": False,
                "deep_content_analysis": False,
            }
        }


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Digital Footprint Investigator")
    parser.add_argument("target", nargs="?", help="Investigation target")
    parser.add_argument("--timeline", action="store_true", help="Enable timeline correlation analysis")
    parser.add_argument("--network", action="store_true", help="Enable social connection analysis")
    parser.add_argument("--deep", action="store_true", help="Enable deep content analysis")
    parser.add_argument("--quick", action="store_true", help="Enable Quick Scan (free, unauthenticated services only)")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config()

    # Get target
    target = args.target if args.target else input("Target: ")

    # Override config with CLI flags
    if args.quick:
        config["scan_mode"] = "quick"
    else:
        config["scan_mode"] = config.get("search", {}).get("mode", "advanced")

    if args.timeline:
        config["advanced_analysis"]["timeline_correlation"] = True
    if args.network:
        config["advanced_analysis"]["network_analysis"] = True
    if args.deep:
        config["advanced_analysis"]["deep_content_analysis"] = True

    print("=" * 60)
    print("Digital Footprint Investigator (LangGraph)")
    print("=" * 60)
    print(f"\nTarget: {target}")
    print(f"Target type: {detect_target_type(target).capitalize()}")
    print(f"Scan Mode: {config.get('scan_mode', 'advanced').capitalize()}")

    # Show enabled advanced features
    advanced = config["advanced_analysis"]
    if any(advanced.values()):
        print("\nAdvanced Analysis Enabled:")
        if advanced["timeline_correlation"]:
            print("  - Timeline Correlation")
        if advanced["network_analysis"]:
            print("  - Social Connection Analysis")
        if advanced["deep_content_analysis"]:
            print("  - Deep Content Analysis")

    print("\nStarting investigation...\n")

    app = create_workflow()

    # Run with checkpointing
    thread_config = {"configurable": {"thread_id": target}}
    app.invoke({"target": target, "config": config}, thread_config)

    print(f"\n{'=' * 60}")
    print("Investigation complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
