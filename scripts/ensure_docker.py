#!/usr/bin/env python3
"""
Ensure Docker Desktop is running before executing docker commands.
"""

import subprocess
import sys
import time


def is_docker_running():
    """Check if Docker daemon is responding."""
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_docker_desktop():
    """Attempt to start Docker Desktop on Windows."""
    print("Docker is not running. Attempting to start Docker Desktop...")

    try:
        # Start Docker Desktop (Windows)
        subprocess.Popen(
            ["C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for Docker to be ready (up to 60 seconds)
        for i in range(60):
            time.sleep(2)
            if is_docker_running():
                print(f"[OK] Docker Desktop started successfully (took {i * 2}s)")
                return True
            if i % 5 == 0:
                print(f"  Waiting for Docker to start... ({i * 2}s)")

        print("[ERROR] Docker Desktop did not start within 60 seconds")
        return False

    except FileNotFoundError:
        print("[ERROR] Docker Desktop executable not found at default location")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to start Docker Desktop: {e}")
        return False


def main():
    """Main entry point."""
    if is_docker_running():
        print("[OK] Docker is already running")
        return 0

    if start_docker_desktop():
        return 0

    print("\nPlease start Docker Desktop manually and try again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
