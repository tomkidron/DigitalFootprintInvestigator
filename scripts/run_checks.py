#!/usr/bin/env python3
"""
Run code quality checks and tests locally.
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """Run all checks."""
    checks = [
        ("ruff check .", "Ruff Linting"),
        ("ruff format --check .", "Ruff Format Check"),
        ("venv\\Scripts\\python.exe -m pytest tests/unit/ -v", "Unit Tests"),
    ]

    failed = []
    for cmd, desc in checks:
        if not run_command(cmd, desc):
            failed.append(desc)

    print(f"\n{'=' * 60}")
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    else:
        print("ALL CHECKS PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
