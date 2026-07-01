"""Reusable field validators enforcing the data rules in section 2."""
from __future__ import annotations

import re
from datetime import date, datetime

PASSWORD_RE = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
)

DATE_FORMAT = "%d/%m/%Y"  # DD/MM/YYYY


def validate_password(value: str) -> str:
    """Min 8 chars, >=1 uppercase, >=1 number, >=1 special char (rule 2.1)."""
    if not PASSWORD_RE.match(value):
        raise ValueError(
            "Password must be at least 8 characters and contain at least one "
            "uppercase letter, one number, and one special character."
        )
    return value


def parse_future_date(value: str | date) -> date:
    """Parse a DD/MM/YYYY string and require it to be in the future (rule 2.2)."""
    if isinstance(value, date) and not isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.strptime(str(value), DATE_FORMAT).date()
        except ValueError as exc:
            raise ValueError(
                "ExpiryDate must be a valid date formatted as DD/MM/YYYY."
            ) from exc
    if parsed <= date.today():
        raise ValueError("ExpiryDate must be a future date.")
    return parsed


def format_date(value: date) -> str:
    """Render a stored date back out as DD/MM/YYYY for API responses."""
    return value.strftime(DATE_FORMAT)
