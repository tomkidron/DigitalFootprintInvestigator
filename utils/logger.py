"""
Logging configuration with progress tracking
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


class ProgressTracker:
    """Track investigation progress with formatted output"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.stages = []
        self.current_stage = 0

    def set_stages(self, stages: list):
        """Set the investigation stages"""
        self.stages = stages
        self.current_stage = 0
        self.logger.info(f"Investigation plan: {len(stages)} stages")

    def start_stage(self, stage_name: str):
        """Mark the start of a stage"""
        self.current_stage += 1
        total = len(self.stages)
        progress = f"[{self.current_stage}/{total}]"
        self.logger.info(f"{progress} Starting: {stage_name}")
        print(f"\n{'='*60}")
        print(f"Stage {self.current_stage}/{total}: {stage_name}")
        print(f"{'='*60}")

    def complete_stage(self, stage_name: str, details: str = ""):
        """Mark the completion of a stage"""
        msg = f"✓ Completed: {stage_name}"
        if details:
            msg += f" ({details})"
        self.logger.info(msg)
        print(f"✓ {stage_name}")

    def log_finding(self, category: str, finding: str):
        """Log a specific finding"""
        self.logger.info(f"[FINDING] {category}: {finding}")
        print(f"  • {category}: {finding}")


def setup_logger(name: str = "osint_tool", log_dir: str = "logs") -> logging.Logger:
    """
    Setup logger with file and console handlers

    Args:
        name: Logger name
        log_dir: Directory for log files

    Returns:
        Configured logger instance
    """
    # Create logs directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)

    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # File handler (detailed logs)
    timestamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        f"{log_dir}/osint_{timestamp}.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler (simple logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
