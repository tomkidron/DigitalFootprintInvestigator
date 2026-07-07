"""Timing helpers for node logging"""

from datetime import datetime


def log_start(label: str) -> datetime:
    """Print a start message and return the start time."""
    start = datetime.now()
    print(f"[{start.strftime('%H:%M:%S')}] {label} started...")
    return start


def log_done(label: str, start: datetime) -> None:
    """Print a completion message with elapsed time."""
    elapsed = (datetime.now() - start).total_seconds()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {label} complete ({elapsed:.1f}s)")


def log_event(msg: str) -> None:
    """Emit a progress message to the frontend log stream, if available."""
    try:
        from langchain_core.callbacks.manager import dispatch_custom_event

        dispatch_custom_event("investigation_log", {"message": msg})
    except Exception:
        pass  # nosec B110
