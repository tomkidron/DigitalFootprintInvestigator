"""Input validation and sanitization"""

import re


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_domain(target: str) -> bool:
    """Validate a bare domain name (e.g. example.com, sub.example.co.uk).

    Rejects strings that start with http:// or https://, plain IP addresses,
    and anything without at least one dot separating labels.
    """
    pattern = r"^(?!https?://)([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
    return bool(re.match(pattern, target))


def is_valid_username(username: str) -> bool:
    """Validate username format (alphanumeric + underscore)"""
    return bool(re.match(r"^[a-zA-Z0-9_]{1,30}$", username.replace("@", "")))


def sanitize_target(target: str) -> str:
    """Sanitize target input"""
    return target.strip().lower()


def detect_target_type(target: str) -> str:
    """Detect if target is an email, domain, username, name, or unknown."""
    target = sanitize_target(target)

    if is_valid_email(target):
        return "email"
    elif is_valid_domain(target):
        return "domain"
    elif target.startswith("@") or is_valid_username(target):
        return "username"
    elif " " in target:
        return "name"
    else:
        return "unknown"
