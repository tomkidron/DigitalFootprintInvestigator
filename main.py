"""LangGraph-based OSINT tool entry point"""
import sys
from dotenv import load_dotenv
from graph.workflow import create_workflow

# Load environment variables from .env
load_dotenv()


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else input("Target: ")
    
    print("="*60)
    print("Digital Footprint Investigator (LangGraph)")
    print("="*60)
    print(f"\nTarget: {target}")
    print("\nStarting investigation...\n")
    
    # Create workflow
    app = create_workflow()
    
    # Run with checkpointing
    config = {"configurable": {"thread_id": target}}
    result = app.invoke({"target": target}, config)
    
    print(f"\n{'='*60}")
    print("Investigation complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
