"""Input validation and sanitization"""

import re


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    """Validate username format (alphanumeric + underscore)"""
    return bool(re.match(r"^[a-zA-Z0-9_]{1,30}$", username.replace("@", "")))


def sanitize_target(target: str) -> str:
    """Sanitize target input"""
    return target.strip().lower()


def detect_target_type(target: str) -> str:
    """Detect if target is email, username, or name"""
    target = sanitize_target(target)

    if is_valid_email(target):
        return "email"
    elif target.startswith("@") or is_valid_username(target):
        return "username"
    elif " " in target:
        return "name"
    else:
        return "unknown"
